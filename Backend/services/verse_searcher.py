

# =============================================================
# services/verse_searcher.py
# يبحث عن أبيات تحتوي الكلمة في poems_db.json
# مع تنوع العصور وتطابق حقيقي
# =============================================================

import json
import os
import re
import random
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "poems_db.json")

_poems_db: dict | None = None

# تصنيف العصور — لتنويع الأبيات
ERA_GROUPS = {
    "قديم":  ["جاهلي", "إسلامي", "أموي", "عباسي", "قديم"],
    "وسيط": ["أندلسي", "مملوكي", "أيوبي", "وسيط"],
    "حديث": ["حديث", "معاصر", "عصر النهضة"],
}


def _load_db() -> dict:
    global _poems_db
    if _poems_db is not None:
        return _poems_db
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        _poems_db = json.load(f)
    return _poems_db


def _normalize(text: str) -> str:
    """
    تطبيع النص:
    - إزالة التشكيل
    - توحيد التاء المربوطة والهاء (كلاهما يصبح ه)
    - توحيد الألف والهمزات
    """
    # إزالة التشكيل
    text = re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC]", "", text)
    # توحيد التاء المربوطة والهاء في نهاية الكلمة
    text = re.sub(r"ة(\s|$)", r"ه\1", text)
    # توحيد الألف والهمزات
    text = re.sub(r"[أإآ]", "ا", text)
    # توحيد الواو بدون همزة
    text = text.replace("ؤ", "و")
    # توحيد الياء
    text = text.replace("ئ", "ي").replace("ى", "ي")
    return text.strip()


def _get_root_variants(word: str) -> list[str]:
    """
    يولّد أشكالاً مختلفة للكلمة للبحث:
    - الكلمة الأصلية
    - بعد التطبيع
    - بعد حذف الأحرف الزائدة الشائعة
    """
    normalized = _normalize(word)
    variants = {normalized}

    # إضافة نسخة بالتاء المربوطة والهاء
    if normalized.endswith("ه"):
        variants.add(normalized[:-1] + "ة")
        variants.add(normalized[:-1])  # بدون الأخير
    if normalized.endswith("ة"):
        variants.add(normalized[:-1] + "ه")
        variants.add(normalized[:-1])

    # حذف ال التعريف
    if normalized.startswith("ال"):
        stripped = normalized[2:]
        variants.add(stripped)
        if stripped.endswith("ه"):
            variants.add(stripped[:-1] + "ة")

    # إضافة ال التعريف
    variants.add("ال" + normalized)

    # حذف حرف أخير (للأفعال المتصرفة)
    if len(normalized) > 4:
        variants.add(normalized[:-1])

    return list(variants)


def _verse_contains_word(verse_normalized: str, word_variants: list[str]) -> bool:
    """يتحقق إذا البيت يحتوي على الكلمة أو أي شكل منها."""
    for variant in word_variants:
        if len(variant) < 3:
            continue
        if variant in verse_normalized:
            return True
    return False


def _detect_era(poem: dict) -> str:
    """يحاول يكتشف عصر البيت من الميتاداتا."""
    raw_label = poem.get("raw_label", "").lower()
    poet = poem.get("poet", "").lower()

    for era_key, keywords in ERA_GROUPS.items():
        for kw in keywords:
            if kw in raw_label or kw in poet:
                return era_key

    # إذا ما عُرف العصر → نعتبره قديم بالافتراضي
    return "قديم"


def search_verses_for_word(word: str, max_results: int = 6) -> list[dict]:
    """
    يبحث عن أبيات تحتوي على الكلمة مع:
    1. تطابق حقيقي للكلمة أو جذرها
    2. تنوع في العصور
    3. عشوائية في الاختيار لتجنب التكرار

    Returns:
        list of {verse, poet, source, era}
    """
    db = _load_db()
    if not db:
        return []

    word_variants = _get_root_variants(word)
    normalized_word = _normalize(word)

    # ── جمع كل الأبيات المطابقة من كل التصنيفات ──────────────
    matched_by_era: dict[str, list[dict]] = {"قديم": [], "وسيط": [], "حديث": []}
    all_matched: list[dict] = []

    for category, poems in db.items():
        # نبحث في عينة كبيرة — كلما كانت الكلمة نادرة احتجنا عينة أكبر
        # 2000 بيت لكل تصنيف يغطي معظم الحالات مع سرعة معقولة
        sample = random.sample(poems, min(len(poems), 2000))

        for poem in sample:
            verse = poem.get("verse", "")
            if not verse:
                continue

            verse_normalized = _normalize(verse)
            if _verse_contains_word(verse_normalized, word_variants):
                era = _detect_era(poem)
                entry = {
                    "verse":  verse,
                    "poet":   poem.get("poet", "مجهول"),
                    "source": "database",
                    "era":    era,
                }
                matched_by_era[era].append(entry)
                all_matched.append(entry)

                # نوقف البحث في هذا التصنيف إذا وجدنا كافياً
                if len(all_matched) >= 50:
                    break

    # ── اختيار متنوع من العصور ────────────────────────────────
    selected: list[dict] = []

    # أولاً: نحاول نأخذ من كل عصر
    target_per_era = max(1, max_results // 3)

    for era in ["حديث", "وسيط", "قديم"]:  # الأولوية للحديث
        era_pool = matched_by_era[era]
        if era_pool:
            take = min(target_per_era, len(era_pool))
            chosen = random.sample(era_pool, take)
            selected.extend(chosen)

    # إذا ما اكتملت النتائج، أكمل من الباقي
    if len(selected) < max_results and all_matched:
        already = {v["verse"] for v in selected}
        remaining = [v for v in all_matched if v["verse"] not in already]
        if remaining:
            extra = min(max_results - len(selected), len(remaining))
            selected.extend(random.sample(remaining, extra))

    return selected[:max_results]
