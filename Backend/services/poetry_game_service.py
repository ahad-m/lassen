"""
خدمة لعبة حفظ الأبيات (جلسة محلية بدون تخزين دائم).
poetry_game_service.py
"""

from __future__ import annotations

import random
from typing import Any

try:
    from .supabase_client import get_supabase_client
except ImportError:
    from supabase_client import get_supabase_client

TABLE_NAME = "poetry_verses"
ROUNDS_PER_GAME = 5


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


def _fetch_random_verse_rows(limit: int) -> list[dict[str, Any]]:
    # نجلب مجموعة كبيرة ثم نأخذ عشوائيًا منها داخل بايثون.
    response = (
        get_supabase_client()
        .table(TABLE_NAME)
        .select("id,poem_id,verse_index,verse,poet_name")
        .limit(max(120, limit * 20))
        .execute()
    )
    return response.data or []


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

    for seed in seed_rows:
        poem_id = _safe_text(seed.get("poem_id"))
        if not poem_id or poem_id in seen_poems:
            continue
        poem_rows = _fetch_poem_rows(poem_id)
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
        seen_poems.add(poem_id)

        if len(selected_rounds) >= desired_rounds:
            break

    return selected_rounds


def get_poetry_game_round(
    used_poem_ids: list[str] | None = None,
    used_verse_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    واجهة توافقية مع endpoint اللعبة:
    - تتجاهل currently used_verse_ids لأن الجولة مبنية على زوج أبيات متتالٍ.
    - تتجنب قصائد سبق استخدامها في نفس الجلسة إن أمكن.
    """
    used_poem_ids = [str(x) for x in (used_poem_ids or []) if str(x).strip()]
    rounds_pool = build_game_rounds(rounds=max(6, ROUNDS_PER_GAME * 2))
    if not rounds_pool:
        return {"success": False, "message": "لا توجد أبيات كافية لبدء اللعبة."}

    selected = None
    for row in rounds_pool:
        row_poem_id = str(row.get("poem_id") or "").strip()
        if row_poem_id and row_poem_id in used_poem_ids:
            continue
        selected = row
        break

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
