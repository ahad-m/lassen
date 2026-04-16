import argparse
import csv
import io
import os
import time

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
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1536"))
OPENAI_BATCH_SIZE = int(os.getenv("OPENAI_BATCH_SIZE", "512"))
STOP_AFTER = int(os.getenv("STOP_AFTER", "50000"))
SLEEP_BETWEEN = float(os.getenv("SLEEP_BETWEEN", "0.02"))
RETRY_COUNT = int(os.getenv("OPENAI_RETRIES", "5"))

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


def get_embeddings(texts):
    """Get embeddings from OpenAI with retry."""
    for attempt in range(RETRY_COUNT):
        try:
            response = openai_client.embeddings.create(
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


def prepare_temp_table(cur):
    cur.execute(
        """
        CREATE TEMP TABLE IF NOT EXISTS tmp_poetry_embeddings (
            id BIGINT PRIMARY KEY,
            embedding_text TEXT NOT NULL
        ) ON COMMIT PRESERVE ROWS;
        """
    )


def vector_to_text(vector):
    # Shorter float precision keeps payload smaller without hurting retrieval quality.
    return "[" + ",".join(f"{value:.7f}" for value in vector) + "]"


def batch_update_embeddings(conn, rows):
    """
    Fast upload path:
      1) COPY rows into a temp table
      2) single UPDATE ... FROM temp_table
    """
    with conn.cursor() as cur:
        cur.execute("TRUNCATE tmp_poetry_embeddings;")
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        for row_id, embedding in rows:
            writer.writerow([row_id, vector_to_text(embedding)])
        buffer.seek(0)

        cur.copy_expert(
            "COPY tmp_poetry_embeddings (id, embedding_text) FROM STDIN WITH (FORMAT csv)",
            buffer,
        )
        cur.execute(
            """
            UPDATE poetry_verses p
            SET embedding = t.embedding_text::vector
            FROM tmp_poetry_embeddings t
            WHERE p.id = t.id;
            """
        )
        updated = cur.rowcount
    conn.commit()
    return updated


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


def main():
    args = parse_args()
    validate_env()

    if args.ensure_index:
        print("Preparing optional resume index...")
        ensure_resume_index()

    run_all = args.all
    stop_after = None if run_all else args.stop_after
    batch_size = max(1, args.batch_size)

    print("=" * 68)
    print("  EMBEDDING GENERATOR (FAST + SAFE DB MODE)")
    print(f"  Model: {EMBEDDING_MODEL} ({EMBEDDING_DIMS} dims)")
    print(f"  OpenAI batch size: {batch_size:,}")
    print(f"  Mode: {'Process ALL' if run_all else f'Process {stop_after:,} then stop'}")
    print("=" * 68)

    conn = get_connection(autocommit=False)
    try:
        with conn.cursor() as cur:
            prepare_temp_table(cur)

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

            processed = 0
            start_time = time.time()

            while processed < target:
                fetch_limit = min(batch_size, target - processed)
                cur.execute(
                    """
                    SELECT id, btrim(verse_normalized) AS verse_text
                    FROM poetry_verses
                    WHERE embedding IS NULL
                      AND verse_normalized IS NOT NULL
                      AND btrim(verse_normalized) <> ''
                    ORDER BY id
                    LIMIT %s
                    """,
                    (fetch_limit,),
                )
                batch = cur.fetchall()
                if not batch:
                    break

                ids = [row[0] for row in batch]
                texts = [row[1] for row in batch]

                try:
                    embeddings = get_embeddings(texts)
                except Exception as err:  # pylint: disable=broad-except
                    print(f"\n  Error at {processed:,}: {err}")
                    print("  Safe to restart — auto-resume will continue later.")
                    break

                try:
                    updated_rows = batch_update_embeddings(
                        conn, list(zip(ids, embeddings))
                    )
                except Exception as err:  # pylint: disable=broad-except
                    conn.rollback()
                    print(f"\n  DB update error at {processed:,}: {err}")
                    print("  Last batch rolled back. Safe to restart.")
                    break

                processed += updated_rows
                elapsed = max(time.time() - start_time, 1e-6)
                rate = processed / elapsed
                eta_seconds = max(target - processed, 0) / max(rate, 1e-6)
                global_done = done + processed
                global_pct = (global_done / total * 100) if total else 100.0

                print(
                    f"  Session: {processed:,}/{target:,} "
                    f"({processed / target * 100:.1f}%) | "
                    f"Global: {global_done:,}/{total:,} ({global_pct:.1f}%) | "
                    f"{rate:.0f} verses/s | ETA: {eta_seconds / 60:.1f} min"
                )

                if args.sleep_between > 0:
                    time.sleep(args.sleep_between)

            elapsed = time.time() - start_time

            done_after, remaining_after, empty_after = get_counts(cur)
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


if __name__ == "__main__":
    main()