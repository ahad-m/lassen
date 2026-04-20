# =============================================================
# services/verse_searcher.py
# يبحث في poems_db.json عن أبيات تحتوي على الكلمة المطلوبة
# =============================================================

import json
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "poems_db.json")

_poems_db = None


def _load_db() -> dict:
    global _poems_db
    if _poems_db is not None:
        return _poems_db
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        _poems_db = json.load(f)
    return _poems_db


def _strip_tashkeel(text: str) -> str:
    """يحذف التشكيل للمقارنة."""
    return re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670]', '', text)


def _extract_root_variants(word: str) -> list[str]:
    """
    يولّد أشكال مختلفة من الكلمة للبحث.
    مثال: "سَلَوتُ" → ["سلوت", "سلو", "سلا", "يسلو"]
    """
    clean = _strip_tashkeel(word)

    variants = [clean]

    # أخذ أول 3-4 حروف كجذر تقريبي
    if len(clean) >= 4:
        variants.append(clean[:4])
    if len(clean) >= 3:
        variants.append(clean[:3])

    # إزالة ال التعريف إن وُجدت
    if clean.startswith("ال") and len(clean) > 3:
        variants.append(clean[2:])

    # إزالة التاء المربوطة أو الهاء من النهاية
    if clean.endswith(("ة", "ه", "ت")) and len(clean) > 3:
        variants.append(clean[:-1])

    return list(set(variants))


def search_verses_for_word(word: str, max_results: int = 3) -> list[dict]:
    """
    يبحث في الداتاست عن أبيات تحتوي على الكلمة أو جذرها.

    Returns:
        list of {"verse": str, "poet": str, "category": str}
    """
    db = _load_db()
    if not db:
        return []

    variants = _extract_root_variants(word)
    found = []

    for category, poems in db.items():
        for poem in poems:
            verse_clean = _strip_tashkeel(poem.get("verse", ""))

            # البحث عن أي variant في البيت
            for variant in variants:
                if len(variant) >= 3 and variant in verse_clean:
                    found.append({
                        "verse":    poem["verse"],
                        "poet":     poem.get("poet", "مجهول"),
                        "category": category,
                    })
                    break  # ما نكرر نفس البيت

            if len(found) >= max_results:
                return found

    return found# =============================================================
# services/verse_searcher.py
# يبحث في poems_db.json عن أبيات تحتوي على الكلمة المطلوبة
# =============================================================

import json
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "poems_db.json")

_poems_db = None


def _load_db() -> dict:
    global _poems_db
    if _poems_db is not None:
        return _poems_db
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        _poems_db = json.load(f)
    return _poems_db


def _strip_tashkeel(text: str) -> str:
    """يحذف التشكيل للمقارنة."""
    return re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670]', '', text)


def _extract_root_variants(word: str) -> list[str]:
    """
    يولّد أشكال مختلفة من الكلمة للبحث.
    مثال: "سَلَوتُ" → ["سلوت", "سلو", "سلا", "يسلو"]
    """
    clean = _strip_tashkeel(word)

    variants = [clean]

    # أخذ أول 3-4 حروف كجذر تقريبي
    if len(clean) >= 4:
        variants.append(clean[:4])
    if len(clean) >= 3:
        variants.append(clean[:3])

    # إزالة ال التعريف إن وُجدت
    if clean.startswith("ال") and len(clean) > 3:
        variants.append(clean[2:])

    # إزالة التاء المربوطة أو الهاء من النهاية
    if clean.endswith(("ة", "ه", "ت")) and len(clean) > 3:
        variants.append(clean[:-1])

    return list(set(variants))


def search_verses_for_word(word: str, max_results: int = 3) -> list[dict]:
    """
    يبحث في الداتاست عن أبيات تحتوي على الكلمة أو جذرها.

    Returns:
        list of {"verse": str, "poet": str, "category": str}
    """
    db = _load_db()
    if not db:
        return []

    variants = _extract_root_variants(word)
    found = []

    for category, poems in db.items():
        for poem in poems:
            verse_clean = _strip_tashkeel(poem.get("verse", ""))

            # البحث عن أي variant في البيت
            for variant in variants:
                if len(variant) >= 3 and variant in verse_clean:
                    found.append({
                        "verse":    poem["verse"],
                        "poet":     poem.get("poet", "مجهول"),
                        "category": category,
                    })
                    break  # ما نكرر نفس البيت

            if len(found) >= max_results:
                return found

    return found
