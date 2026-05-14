"""
services/verse_searcher.py
بحث أبيات "كنوز الكلمات" من Supabase مع الحفاظ على منطق الملف السابق:
- تطبيع عربي
- توليد مشتقات للكلمة
- مطابقة حقيقية
- تنويع في العصور
"""

from __future__ import annotations

import random
import re
from typing import Any

try:
    # عند التشغيل كحزمة: services.verse_searcher
    from .supabase_client import get_supabase_client
except ImportError:
    # fallback للتشغيل المباشر في بيئات التطوير السريعة
    from supabase_client import get_supabase_client

TABLE_NAME = "poetry_verses"
DEFAULT_WORD_MAX_RESULTS = 6
MAX_MATCH_POOL = 50
PER_VARIANT_LIMIT = 40

# تصنيف العصور — للحفاظ على التنويع
ERA_GROUPS = {
    "قديم": ["جاهلي", "اسلامي", "إسلامي", "أموي", "عباسي", "قديم"],
    "وسيط": ["أندلسي", "مملوكي", "أيوبي", "وسيط"],
    "حديث": ["حديث", "معاصر", "نهضة", "عصر النهضة"],
}


def _normalize(text: str) -> str:
    text = str(text or "")
    text = re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC]", "", text)
    text = re.sub(r"ة(\s|$)", r"ه\1", text)
    text = re.sub(r"[أإآ]", "ا", text)
    text = text.replace("ؤ", "و")
    text = text.replace("ئ", "ي").replace("ى", "ي")
    return text.strip()


def _get_root_variants(word: str) -> list[str]:
    normalized = _normalize(word)
    variants = {normalized}

    if normalized.endswith("ه"):
        variants.add(normalized[:-1] + "ة")
        variants.add(normalized[:-1])
    if normalized.endswith("ة"):
        variants.add(normalized[:-1] + "ه")
        variants.add(normalized[:-1])

    if normalized.startswith("ال"):
        stripped = normalized[2:]
        variants.add(stripped)
        if stripped.endswith("ه"):
            variants.add(stripped[:-1] + "ة")

    variants.add("ال" + normalized)
    if len(normalized) > 4:
        variants.add(normalized[:-1])

    return [v for v in variants if v]


def _verse_contains_word(verse_normalized: str, word_variants: list[str]) -> bool:
    for variant in word_variants:
        if len(variant) < 3:
            continue
        if variant in verse_normalized:
            return True
    return False


def _detect_era(row: dict[str, Any]) -> str:
    text_blob = " ".join(
        [
            str(row.get("poet_era") or ""),
            str(row.get("poem_theme") or ""),
            str(row.get("poet_name") or ""),
        ]
    ).lower()

    for era_key, keywords in ERA_GROUPS.items():
        for kw in keywords:
            if kw.lower() in text_blob:
                return era_key
    return "قديم"


def _fetch_rows_for_variants(variants: list[str], limit: int) -> list[dict[str, Any]]:
    """Fetch rows matching any of the given variants in a single query."""
    usable = [v for v in variants if len(v.strip()) >= 3]
    if not usable:
        return []

    or_filter = ",".join(f"verse.ilike.%{v}%" for v in usable)
    response = (
        get_supabase_client()
        .table(TABLE_NAME)
        .select("id,verse,poet_name,poet_era,poem_theme")
        .or_(or_filter)
        .limit(max(1, int(limit)))
        .execute()
    )
    return response.data or []


def search_verses_for_word(word: str, max_results: int = DEFAULT_WORD_MAX_RESULTS) -> list[dict]:
    query = str(word or "").strip()
    if not query:
        return []

    word_variants = _get_root_variants(query)
    matched_by_era: dict[str, list[dict]] = {"قديم": [], "وسيط": [], "حديث": []}
    all_matched: list[dict] = []
    seen_ids: set[str] = set()

    rows = _fetch_rows_for_variants(word_variants, limit=PER_VARIANT_LIMIT)
    for row in rows:
        verse = str(row.get("verse") or "").strip()
        if not verse:
            continue
        row_id = str(row.get("id") or verse)
        if row_id in seen_ids:
            continue

        verse_normalized = _normalize(verse)
        if not _verse_contains_word(verse_normalized, word_variants):
            continue

        seen_ids.add(row_id)
        era = _detect_era(row)
        entry = {
            "verse": verse,
            "poet": str(row.get("poet_name") or "مجهول").strip() or "مجهول",
            "source": "database",
            "era": era,
        }
        matched_by_era[era].append(entry)
        all_matched.append(entry)

        if len(all_matched) >= MAX_MATCH_POOL:
            break

    if not all_matched:
        return []

    selected: list[dict] = []
    target_per_era = max(1, max(1, int(max_results)) // 3)

    for era in ["حديث", "وسيط", "قديم"]:
        era_pool = matched_by_era.get(era, [])
        if era_pool:
            take = min(target_per_era, len(era_pool))
            selected.extend(random.sample(era_pool, take))

    if len(selected) < max_results:
        already = {v["verse"] for v in selected}
        remaining = [v for v in all_matched if v["verse"] not in already]
        if remaining:
            extra = min(max_results - len(selected), len(remaining))
            selected.extend(random.sample(remaining, extra))

    return selected[: max(1, int(max_results))]