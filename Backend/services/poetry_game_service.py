"""
خدمة لعبة حفظ الأبيات (جلسة محلية بدون تخزين دائم).
poetry_game_service.py

تحسينات الأداء:
- كاش للعدد الكلي (يقلّ طلبات count)
- طلبات متوازية (concurrent.futures) لجلب عدة عينات بنفس الوقت
- كاش للـ seed rows لفترة قصيرة لتقليل طلبات Supabase المتكررة
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

try:
    from .supabase_client import get_supabase_client
except ImportError:
    from supabase_client import get_supabase_client

TABLE_NAME = "poetry_verses"
ROUNDS_PER_GAME = 5

# ── كاش داخلي ─────────────────────────────────────────────────
# كاش للعدد الكلي لقاعدة البيانات (يتجدد كل 5 دقائق)
_TOTAL_COUNT_CACHE: dict[str, Any] = {"count": 0, "timestamp": 0.0}
_COUNT_CACHE_TTL_SECONDS = 300  # 5 دقائق

# كاش بسيط للـ seed rows (يتجدد كل 30 ثانية) — يسرع الجولات المتتالية
_SEED_ROWS_CACHE: dict[str, Any] = {"rows": [], "timestamp": 0.0}
_SEED_CACHE_TTL_SECONDS = 30


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_for_match(text: str) -> str:
    normalized = str(text or "")
    normalized = normalized.replace("ى", "ي")
    normalized = normalized.replace("ة", "ه")
    normalized = normalized.replace("إ", "ا")
    normalized = normalized.replace("أ", "ا")
    normalized = normalized.replace("آ", "ا")
    normalized = normalized.replace("ٱ", "ا")
    normalized = normalized.replace("ـ", "")
    normalized = "".join(ch for ch in normalized if ch not in "\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670")
    normalized = " ".join(normalized.split())
    return normalized


def _get_total_count() -> int:
    """يجلب العدد الكلي للأبيات مع كاش 5 دقائق."""
    now = time.time()
    if (
        _TOTAL_COUNT_CACHE["count"] > 0
        and (now - _TOTAL_COUNT_CACHE["timestamp"]) < _COUNT_CACHE_TTL_SECONDS
    ):
        return _TOTAL_COUNT_CACHE["count"]

    response = (
        get_supabase_client()
        .table(TABLE_NAME)
        .select("id", count="exact")
        .limit(1)
        .execute()
    )
    total = response.count or 0
    _TOTAL_COUNT_CACHE["count"] = total
    _TOTAL_COUNT_CACHE["timestamp"] = now
    return total


def _fetch_single_batch(offset: int, batch_size: int) -> list[dict[str, Any]]:
    """يجلب دفعة واحدة من الصفوف بدءاً من offset محدد."""
    response = (
        get_supabase_client()
        .table(TABLE_NAME)
        .select("id,poem_id,verse_index,verse,poet_name")
        .range(offset, offset + batch_size - 1)
        .execute()
    )
    return response.data or []


def _fetch_random_verse_rows(limit: int) -> list[dict[str, Any]]:
    """
    يجلب صفوف عشوائية فعلاً من قاعدة البيانات
    باستخدام offsets عشوائية بالتوازي لتجاوز مشكلة ترتيب Supabase الافتراضي.

    تحسينات الأداء:
    - يستخدم كاش 30 ثانية للعينات (يقلل طلبات متتالية)
    - ينفذ 4 طلبات بالتوازي باستخدام ThreadPoolExecutor
    - يستخدم كاش العدد الكلي
    """
    # ── 1) جرّب الكاش أولاً ──────────────────────────────────
    now = time.time()
    cached_rows = _SEED_ROWS_CACHE.get("rows") or []
    if (
        cached_rows
        and (now - _SEED_ROWS_CACHE["timestamp"]) < _SEED_CACHE_TTL_SECONDS
    ):
        # نرجّع نسخة عشوائية من الكاش
        shuffled = list(cached_rows)
        random.shuffle(shuffled)
        return shuffled

    # ── 2) اجلب العدد الكلي (من الكاش أو من قاعدة البيانات) ─
    total_count = _get_total_count()
    if total_count == 0:
        return []

    # ── 3) حدّد أحجام الدفعات ────────────────────────────────
    batch_size = 20
    num_batches = 4  # 4 طلبات بالتوازي

    # ── 4) ولّد offsets عشوائية (متباعدة قدر الإمكان) ──────
    offsets: list[int] = []
    for _ in range(num_batches):
        if total_count <= batch_size:
            offsets.append(0)
        else:
            offsets.append(random.randint(0, max(0, total_count - batch_size)))

    # ── 5) نفّذ الطلبات بالتوازي ─────────────────────────────
    all_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    with ThreadPoolExecutor(max_workers=num_batches) as executor:
        futures = [
            executor.submit(_fetch_single_batch, off, batch_size)
            for off in offsets
        ]
        for fut in futures:
            try:
                batch = fut.result()
            except Exception:
                batch = []
            for row in batch:
                row_id = str(row.get("id") or "")
                if row_id and row_id not in seen_ids:
                    seen_ids.add(row_id)
                    all_rows.append(row)

    random.shuffle(all_rows)

    # ── 6) حدّث الكاش ────────────────────────────────────────
    _SEED_ROWS_CACHE["rows"] = list(all_rows)
    _SEED_ROWS_CACHE["timestamp"] = now

    return all_rows


def _fetch_poem_rows(poem_id: str) -> list[dict[str, Any]]:
    response = (
        get_supabase_client()
        .table(TABLE_NAME)
        .select("id,verse_index,verse,poet_name")
        .eq("poem_id", poem_id)
        .order("verse_index")
        .execute()
    )
    return response.data or []


def build_game_rounds(rounds: int = ROUNDS_PER_GAME) -> list[dict[str, Any]]:
    desired_rounds = max(1, int(rounds))
    seed_rows = _fetch_random_verse_rows(limit=desired_rounds)
    if not seed_rows:
        return []

    random.shuffle(seed_rows)
    selected_rounds: list[dict[str, Any]] = []
    seen_poems: set[str] = set()

    # ── نجمع poem_ids الفريدة أولاً من الـ seed ─────────────
    unique_poem_ids: list[str] = []
    for seed in seed_rows:
        pid = _safe_text(seed.get("poem_id"))
        if pid and pid not in seen_poems:
            seen_poems.add(pid)
            unique_poem_ids.append(pid)
        if len(unique_poem_ids) >= desired_rounds * 2:
            break

    if not unique_poem_ids:
        return []

    # ── نجلب أبيات القصائد بالتوازي (تحسين أداء كبير) ──────
    poem_rows_map: dict[str, list[dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=min(6, len(unique_poem_ids))) as executor:
        future_to_pid = {
            executor.submit(_fetch_poem_rows, pid): pid
            for pid in unique_poem_ids
        }
        for fut in future_to_pid:
            pid = future_to_pid[fut]
            try:
                poem_rows_map[pid] = fut.result() or []
            except Exception:
                poem_rows_map[pid] = []

    # ── نبني الجولات ────────────────────────────────────────
    for poem_id in unique_poem_ids:
        poem_rows = poem_rows_map.get(poem_id) or []
        if len(poem_rows) < 2:
            continue

        # اختيار بيتين متتالين بشكل عشوائي من نفس القصيدة.
        max_start = len(poem_rows) - 2
        start_idx = random.randint(0, max_start)
        pair = poem_rows[start_idx : start_idx + 2]
        if len(pair) < 2:
            continue

        first_verse = _safe_text(pair[0].get("verse"))
        second_verse = _safe_text(pair[1].get("verse"))
        if not first_verse or not second_verse:
            continue

        poet_name = _safe_text(pair[0].get("poet_name"), "مجهول")
        round_payload = {
            "poem_id": poem_id,
            "verse_ids": [
                str(pair[0].get("id") or ""),
                str(pair[1].get("id") or ""),
            ],
            "poet_name": poet_name,
            "verses": [first_verse, second_verse],
            "expected_text_normalized": _normalize_for_match(f"{first_verse}\n{second_verse}"),
        }
        selected_rounds.append(round_payload)

        if len(selected_rounds) >= desired_rounds:
            break

    return selected_rounds


def get_poetry_game_round(
    used_poem_ids: list[str] | None = None,
    used_verse_ids: list[str] | None = None,
    used_poet_names: list[str] | None = None,
) -> dict[str, Any]:
    """
    واجهة توافقية مع endpoint اللعبة:
    - تتجاهل used_verse_ids لأن الجولة مبنية على زوج أبيات متتالٍ.
    - تتجنب قصائد سبق استخدامها في نفس الجلسة.
    - تتجنب شعراء سبق استخدامهم (إن أمكن) لتنويع التجربة.
    """
    used_poem_ids = [str(x) for x in (used_poem_ids or []) if str(x).strip()]
    used_poet_names = [str(x) for x in (used_poet_names or []) if str(x).strip()]

    rounds_pool = build_game_rounds(rounds=max(10, ROUNDS_PER_GAME * 3))
    if not rounds_pool:
        return {"success": False, "message": "لا توجد أبيات كافية لبدء اللعبة."}

    # ── أولاً: تجنب الشعراء والقصائد المستخدمين ─────────────
    selected = None
    for row in rounds_pool:
        row_poem_id = str(row.get("poem_id") or "").strip()
        row_poet = str(row.get("poet_name") or "").strip()
        if row_poem_id and row_poem_id in used_poem_ids:
            continue
        if row_poet and row_poet in used_poet_names:
            continue
        selected = row
        break

    # ── ثانياً: تجنب القصائد فقط ────────────────────────────
    if not selected:
        for row in rounds_pool:
            row_poem_id = str(row.get("poem_id") or "").strip()
            if row_poem_id and row_poem_id in used_poem_ids:
                continue
            selected = row
            break

    # ── أخيراً: عشوائي ──────────────────────────────────────
    if not selected:
        selected = random.choice(rounds_pool)

    return {
        "success": True,
        "round": {
            "poem_id": str(selected.get("poem_id") or ""),
            "verse_ids": [str(v) for v in (selected.get("verse_ids") or [])],
            "poet_name": str(selected.get("poet_name") or "مجهول"),
            "verses": [str(v) for v in (selected.get("verses") or [])][:2],
        },
        "message": None,
    }


def evaluate_round_answer(expected_normalized: str, user_answer: str) -> bool:
    answer_normalized = _normalize_for_match(user_answer or "")
    expected = _normalize_for_match(expected_normalized or "")
    if not expected or not answer_normalized:
        return False
    return answer_normalized == expected
