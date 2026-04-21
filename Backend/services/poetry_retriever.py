# =============================================================
# poetry_retriever.py for MoodOfTheDay
# services/poetry_retriever.py
# يقرأ الأبيات من poems_db.json المحلي (بعد تشغيل download_dataset.py)
# =============================================================

import json
import random
import os
from MoodOfTheDay_promts import MOOD_TO_CATEGORY, AVAILABLE_CATEGORIES

# مسار الملف المحلي
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "poems_db.json")

# cache في الذاكرة — يُحمَّل مرة واحدة
_poems_db: dict[str, list[dict]] | None = None


def _load_db() -> dict[str, list[dict]]:
    """يحمّل poems_db.json في الذاكرة مرة واحدة."""
    global _poems_db
    if _poems_db is not None:
        return _poems_db

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            "❌ ملف poems_db.json غير موجود!\n"
            "   شغّل أولاً: python download_dataset.py"
        )

    with open(DB_PATH, "r", encoding="utf-8") as f:
        _poems_db = json.load(f)

    total = sum(len(v) for v in _poems_db.values())
    print(f"✅ تم تحميل قاعدة الأبيات: {total:,} بيت في {len(_poems_db)} تصنيف")
    return _poems_db


def detect_category(user_input: str) -> str:
    """
    يكتشف التصنيف الأنسب من مشاعر المستخدم.
    يبحث في الكلمات المفتاحية ويُرجع أول تصنيف متاح.
    """
    text = user_input.lower()

    for keyword, categories in MOOD_TO_CATEGORY.items():
        if keyword in text:
            db = _load_db()
            for cat in categories:
                if cat in db and len(db[cat]) > 0:
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
    db = _load_db()
    category = detect_category(user_input)

    poems = db.get(category, [])

    # إذا أقل من المطلوب، أضف من تصنيفات قريبة
    if len(poems) < count:
        for cat in AVAILABLE_CATEGORIES:
            if cat != category and cat in db:
                poems = poems + db[cat]
            if len(poems) >= count:
                break

    selected = random.sample(poems, min(count, len(poems)))
    return category, selected


def get_db_stats() -> dict:
    """إحصائيات قاعدة البيانات — للـ health endpoint."""
    try:
        db = _load_db()
        return {cat: len(poems) for cat, poems in db.items()}
    except FileNotFoundError:
        return {"error": "poems_db.json غير موجود"}
    