"""
جلب أبيات "مزاج اليوم" من Supabase بدلاً من poems_db.json المحلي.
"""

from __future__ import annotations

import random

from MoodOfTheDay_promts import MOOD_TO_CATEGORY, AVAILABLE_CATEGORIES
try:
    from .supabase_client import get_supabase_client
except ImportError:
    from supabase_client import get_supabase_client

TABLE_NAME = "poetry_verses"
MAX_ROWS_PER_THEME = 600

# تحويل تصنيفات مزاج اليوم إلى قيم poem_theme في قاعدة البيانات.
CATEGORY_TO_DB_THEMES: dict[str, list[str]] = {
    "حزن": ["قصيدة حزينه"],
    "رثاء": ["قصيدة رثاء"],
    "دينية": ["قصيدة دينية"],
    "سياسية": ["قصيدة سياسية"],
    "رومانسية": ["قصيدة رومنسيه", "قصيدة رومانسية"],
    "ذم": ["قصيدة ذم"],
    "شوق": ["قصيدة شوق"],
    "عتاب": ["قصيدة عتاب"],
    "غزل": ["قصيدة غزل"],
    "فراق": ["قصيدة فراق"],
    "مدح": ["قصيدة مدح"],
    "هجاء": ["قصيدة هجاء"],
    "اعتذار": ["قصيدة اعتذار"],
    "أناشيد": ["قصيدة أناشيد"],
    "معلقات": ["قصيدة معلقات", "قصيدة المعلقات"],
    "وطنية": ["قصيدة وطنية"],
}

_category_cache: dict[str, list[dict]] = {}


def _fetch_poems_by_category(category: str) -> list[dict]:
    if category in _category_cache:
        return _category_cache[category]

    themes = CATEGORY_TO_DB_THEMES.get(category, [])
    if not themes:
        _category_cache[category] = []
        return []

    supabase = get_supabase_client()
    rows: list[dict] = []
    seen: set[str] = set()

    for theme in themes:
        response = (
            supabase
            .table(TABLE_NAME)
            .select("verse,poet_name,poem_theme,id")
            .eq("poem_theme", theme)
            .limit(MAX_ROWS_PER_THEME)
            .execute()
        )
        data = response.data or []
        for item in data:
            verse = str(item.get("verse") or "").strip()
            if not verse:
                continue
            unique_key = str(item.get("id") or verse)
            if unique_key in seen:
                continue
            seen.add(unique_key)
            rows.append(
                {
                    "verse": verse,
                    "poet": str(item.get("poet_name") or "مجهول").strip() or "مجهول",
                    "raw_label": str(item.get("poem_theme") or "").strip(),
                }
            )

    _category_cache[category] = rows
    return rows


def detect_category(user_input: str) -> str:
    """
    يكتشف التصنيف الأنسب من مشاعر المستخدم.
    يبحث في الكلمات المفتاحية ويُرجع أول تصنيف متاح.
    """
    text = user_input.lower()

    for keyword, categories in MOOD_TO_CATEGORY.items():
        if keyword in text:
            for cat in categories:
                if len(_fetch_poems_by_category(cat)) > 0:
                    return cat

    # افتراضي: شوق (أكثر شيء شامل)
    return "شوق"


def get_poems_for_mood(user_input: str, count: int = 20) -> tuple[str, list[dict]]:
    """
    يُرجع (التصنيف المختار، قائمة الأبيات).

    Args:
        user_input: ما كتبه المستخدم
        count:      عدد الأبيات للإرسال لـ GPT

    Returns:
        (category_name, list of {verse, poet, raw_label})
    """
    category = detect_category(user_input)
    poems = list(_fetch_poems_by_category(category))

    # إذا أقل من المطلوب، أضف من تصنيفات قريبة
    if len(poems) < count:
        for cat in AVAILABLE_CATEGORIES:
            if cat != category:
                poems.extend(_fetch_poems_by_category(cat))
            if len(poems) >= count:
                break

    if not poems:
        return category, []

    selected = random.sample(poems, min(count, len(poems)))
    return category, selected


def get_db_stats() -> dict:
    """إحصائيات قاعدة البيانات — للـ health endpoint."""
    stats: dict[str, int] = {}
    for cat in AVAILABLE_CATEGORIES:
        try:
            stats[cat] = len(_fetch_poems_by_category(cat))
        except Exception:
            stats[cat] = 0
    return stats