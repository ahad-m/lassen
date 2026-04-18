import argparse
import csv
import io
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import psycopg2
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ============================================================
# CONFIG
# ============================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "6543")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "768"))
OPENAI_BATCH_SIZE = int(os.getenv("OPENAI_BATCH_SIZE", "768"))
STOP_AFTER = int(os.getenv("STOP_AFTER", "500000"))
SLEEP_BETWEEN = float(os.getenv("SLEEP_BETWEEN", "0.002"))
RETRY_COUNT = int(os.getenv("OPENAI_RETRIES", "5"))
WORKERS = int(os.getenv("EMBEDDING_WORKERS", "1"))

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate embeddings for poetry verses and upload to Supabase in batches."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all rows without STOP_AFTER limit.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=OPENAI_BATCH_SIZE,
        help=f"Verses per OpenAI request (default: {OPENAI_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--stop-after",
        type=int,
        default=STOP_AFTER,
        help=f"Stop after this many verses unless --all is used (default: {STOP_AFTER}).",
    )
    parser.add_argument(
        "--sleep-between",
        type=float,
        default=SLEEP_BETWEEN,
        help=f"Seconds between OpenAI calls (default: {SLEEP_BETWEEN}).",
    )
    parser.add_argument(
        "--ensure-index",
        action="store_true",
        help="Create a partial index (CONCURRENTLY) to speed up resume queries.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=WORKERS,
        help=f"Parallel workers inside one run (default: {WORKERS}).",
    )
    parser.add_argument(
        "--allow-concurrent",
        action="store_true",
        help="Allow concurrent runs (disabled by default for safety).",
    )
    return parser.parse_args()


def validate_env():
    required = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "DB_HOST": DB_HOST,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def get_connection(autocommit=False):
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        options="-c statement_timeout=300000",  # 5 دقائق
    )
    conn.autocommit = autocommit
    return conn


def ensure_resume_index():
    statement = (
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_poetry_verses_null_embedding_id "
        "ON poetry_verses (id) WHERE embedding IS NULL;"
    )
    conn = get_connection(autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(statement)
        print("  Partial index ready: idx_poetry_verses_null_embedding_id")
    finally:
        conn.close()


def acquire_run_lock(cur):
    """
    Acquire a lightweight DB-wide lock for this job.
    This prevents accidental duplicate runs without heavy row locking.
    """
    cur.execute("SELECT pg_try_advisory_lock(%s);", (2026041601,))
    return bool(cur.fetchone()[0])


def get_embeddings(texts, client):
    """Get embeddings from OpenAI with retry."""
    for attempt in range(RETRY_COUNT):
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
                dimensions=EMBEDDING_DIMS,
            )
            return [item.embedding for item in response.data]
        except Exception as err:  # pylint: disable=broad-except
            if attempt < RETRY_COUNT - 1:
                wait = 2 ** (attempt + 1)
                print(f"  OpenAI error: {err}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def prepare_staging_table(cur, worker_id):
    """
    جدول عادي (مو temp) — يبقى موجود حتى لو انقطع الاتصال.
    نظيف دائماً في بداية كل worker.
    """
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS _tmp_embeddings_{worker_id} (
            id BIGINT PRIMARY KEY,
            embedding_text TEXT NOT NULL
        );
        """
    )
    cur.execute(f"TRUNCATE _tmp_embeddings_{worker_id};")


def vector_to_text(vector):
    return "[" + ",".join(f"{value:.7f}" for value in vector) + "]"


def batch_update_embeddings(conn, rows, worker_id):
    """
    Fast upload path:
      1) COPY rows into worker-specific staging table
      2) single UPDATE ... FROM staging table
    """
    table = f"_tmp_embeddings_{worker_id}"
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {table};")
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        for row_id, embedding in rows:
            writer.writerow([row_id, vector_to_text(embedding)])
        buffer.seek(0)

        cur.copy_expert(
            f"COPY {table} (id, embedding_text) FROM STDIN WITH (FORMAT csv)",
            buffer,
        )
        cur.execute(
            f"""
            UPDATE poetry_verses p
            SET embedding = t.embedding_text::vector
            FROM {table} t
            WHERE p.id = t.id
              AND p.embedding IS NULL;
            """
        )
        updated = cur.rowcount
    conn.commit()
    return updated


def fetch_locked_batch(cur, fetch_limit):
    cur.execute(
        """
        SELECT id, btrim(verse_normalized) AS verse_text
        FROM poetry_verses
        WHERE embedding IS NULL
          AND verse_normalized IS NOT NULL
          AND btrim(verse_normalized) <> ''
        ORDER BY id
        FOR UPDATE SKIP LOCKED
        LIMIT %s
        """,
        (fetch_limit,),
    )
    return cur.fetchall()


def get_counts(cur):
    cur.execute(
        """
        SELECT
            count(*) FILTER (WHERE embedding IS NOT NULL) AS done,
            count(*) FILTER (
                WHERE embedding IS NULL
                  AND verse_normalized IS NOT NULL
                  AND btrim(verse_normalized) <> ''
            ) AS remaining_processable,
            count(*) FILTER (
                WHERE embedding IS NULL
                  AND (verse_normalized IS NULL OR btrim(verse_normalized) = '')
            ) AS remaining_empty
        FROM poetry_verses;
        """
    )
    return cur.fetchone()


def is_connection_alive(conn):
    """تحقق إذا الاتصال لا زال شغال"""
    try:
        conn.isolation_level
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


class ProgressState:
    def __init__(self, target, done_start, total_rows):
        self.target = target
        self.done_start = done_start
        self.total_rows = total_rows
        self.remaining_budget = target
        self.processed = 0
        self.start_time = time.time()
        self.stop_requested = False
        self.lock = threading.Lock()

    def reserve(self, max_batch):
        with self.lock:
            if self.stop_requested or self.remaining_budget <= 0:
                return 0
            fetch_limit = min(max_batch, self.remaining_budget)
            self.remaining_budget -= fetch_limit
            return fetch_limit

    def release(self, count):
        if count <= 0:
            return
        with self.lock:
            self.remaining_budget += count

    def request_stop(self):
        with self.lock:
            self.stop_requested = True

    def record_processed(self, delta):
        with self.lock:
            self.processed += delta
            processed = self.processed
            target = self.target
            done_start = self.done_start
            total_rows = self.total_rows
            elapsed = max(time.time() - self.start_time, 1e-6)

        rate = processed / elapsed
        eta_seconds = max(target - processed, 0) / max(rate, 1e-6)
        global_done = done_start + processed
        global_pct = (global_done / total_rows * 100) if total_rows else 100.0
        print(
            f"  Session: {processed:,}/{target:,} "
            f"({processed / target * 100:.1f}%) | "
            f"Global: {global_done:,}/{total_rows:,} ({global_pct:.1f}%) | "
            f"{rate:.0f} verses/s | ETA: {eta_seconds / 60:.1f} min"
        )


def make_connection(worker_id):
    """أنشئ connection جديد وجهز الـ staging table"""
    conn = get_connection(autocommit=False)
    with conn.cursor() as cur:
        prepare_staging_table(cur, worker_id)
    conn.commit()
    return conn


def worker_loop(worker_id, batch_size, sleep_between, progress):
    conn = make_connection(worker_id)
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        while True:
            fetch_limit = progress.reserve(batch_size)
            if fetch_limit <= 0:
                break

            # ── Reconnect تلقائي لو انقطع الاتصال ──
            if not is_connection_alive(conn):
                print(f"  Worker {worker_id} — connection lost, reconnecting...")
                try:
                    conn.close()
                except Exception:
                    pass
                try:
                    conn = make_connection(worker_id)
                    print(f"  Worker {worker_id} — reconnected ✓")
                except Exception as err:
                    progress.release(fetch_limit)
                    progress.request_stop()
                    print(f"  Worker {worker_id} — reconnect failed: {err}")
                    break

            # ── جلب الـ batch ──
            try:
                with conn.cursor() as cur:
                    batch = fetch_locked_batch(cur, fetch_limit)
            except Exception as err:
                conn.rollback()
                progress.release(fetch_limit)
                print(f"  Worker {worker_id} fetch error: {err}")
                break

            if not batch:
                conn.rollback()
                progress.release(fetch_limit)
                break

            if len(batch) < fetch_limit:
                progress.release(fetch_limit - len(batch))

            ids = [row[0] for row in batch]
            texts = [row[1] for row in batch]

            # ── OpenAI ──
            try:
                embeddings = get_embeddings(texts, client)
            except Exception as err:  # pylint: disable=broad-except
                conn.rollback()
                progress.release(len(batch))
                progress.request_stop()
                print(f"\n  Worker {worker_id} OpenAI error: {err}")
                print("  Safe to restart — auto-resume will continue later.")
                break

            # ── كتابة في الداتابيس ──
            try:
                updated_rows = batch_update_embeddings(
                    conn, list(zip(ids, embeddings)), worker_id
                )
            except Exception as err:  # pylint: disable=broad-except
                conn.rollback()
                progress.release(len(batch))
                progress.request_stop()
                print(f"\n  Worker {worker_id} DB update error: {err}")
                print("  Last batch rolled back. Safe to restart.")
                break

            if updated_rows < len(batch):
                progress.release(len(batch) - updated_rows)
            progress.record_processed(updated_rows)

            if sleep_between > 0:
                time.sleep(sleep_between)
    finally:
        # نظف الـ staging table بعد الانتهاء
        try:
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE _tmp_embeddings_{worker_id};")
            conn.commit()
        except Exception:
            pass
        conn.close()


def main():
    args = parse_args()
    validate_env()

    if args.ensure_index:
        print("Preparing optional resume index...")
        ensure_resume_index()

    run_all = args.all
    stop_after = None if run_all else args.stop_after
    batch_size = max(1, args.batch_size)
    workers = max(1, args.workers)
    lock_conn = None

    print("=" * 68)
    print("  EMBEDDING GENERATOR (FAST + SAFE DB MODE)")
    print(f"  Model: {EMBEDDING_MODEL} ({EMBEDDING_DIMS} dims)")
    print(f"  OpenAI batch size: {batch_size:,}")
    print(f"  Workers: {workers}")
    print(f"  Mode: {'Process ALL' if run_all else f'Process {stop_after:,} then stop'}")
    print("=" * 68)

    if not args.allow_concurrent:
        lock_conn = get_connection(autocommit=False)
        with lock_conn.cursor() as lock_cur:
            if not acquire_run_lock(lock_cur):
                print(
                    "\n  Another embedding run appears to be active."
                    " Exiting to avoid duplicate work/cost."
                )
                lock_conn.close()
                return
        print("  Safety lock acquired (single-run mode).")
    else:
        print("  Concurrent mode enabled by user (--allow-concurrent).")

    conn = get_connection(autocommit=False)
    try:
        with conn.cursor() as cur:
            done, remaining_processable, remaining_empty = get_counts(cur)
            total = done + remaining_processable + remaining_empty
            print(f"\n  Already embedded: {done:,}")
            print(f"  Remaining processable: {remaining_processable:,}")
            print(f"  Remaining empty text: {remaining_empty:,}")
            print(f"  Total rows: {total:,}")

            if remaining_processable == 0:
                print("\n  Nothing to process. All non-empty verses are embedded.")
                return

            target = min(remaining_processable, stop_after) if stop_after else remaining_processable
            estimated_cost = target * 0.00001
            print(f"\n  Will process this run: {target:,}")
            print(f"  Estimated cost: ~${estimated_cost:.2f}")
            print("\n" + "=" * 68)
            print("  Processing...")
            print("=" * 68)

        progress = ProgressState(target=target, done_start=done, total_rows=total)

        if workers == 1:
            worker_loop(
                worker_id=1,
                batch_size=batch_size,
                sleep_between=args.sleep_between,
                progress=progress,
            )
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        worker_loop,
                        worker_id=i + 1,
                        batch_size=batch_size,
                        sleep_between=args.sleep_between,
                        progress=progress,
                    )
                    for i in range(workers)
                ]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as err:
                        print(f"  Worker error: {err}")

        elapsed = time.time() - progress.start_time
        processed = progress.processed

        # connection منفصلة للـ final counts عشان ما تنقطع
        count_conn = get_connection(autocommit=True)
        try:
            with count_conn.cursor() as count_cur:
                done_after, remaining_after, empty_after = get_counts(count_cur)
        finally:
            count_conn.close()

        print(f"\n" + "=" * 68)
        print("  SESSION COMPLETE")
        print(f"  Processed this session: {processed:,}")
        print(f"  Time: {elapsed / 60:.1f} minutes")
        print(f"  Total embedded now: {done_after:,}")
        print(f"  Remaining processable: {remaining_after:,}")
        print(f"  Remaining empty text: {empty_after:,}")
        if remaining_after > 0:
            print("\n  Run again to continue from where you stopped.")
        else:
            print("\n  ALL DONE! Every non-empty verse has an embedding.")
        print("=" * 68)

    finally:
        conn.close()
        if lock_conn is not None:
            lock_conn.close()


if __name__ == "__main__":
    main()