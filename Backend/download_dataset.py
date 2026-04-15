# =============================================================
# download_dataset.py
# شغّله مرة واحدة فقط — النتيجة: poems_db.json
# تشغيل: python download_dataset.py
# =============================================================

import json
import os
from datasets import load_dataset

# ── التصنيفات الحقيقية في عمود "poem theme" ──────────────────
TARGET_CATEGORIES = {
    "قصيدة حزينه":   "حزن",       # 2,277
    "قصيدة رثاء":    "رثاء",      # 917
    "قصيدة دينية":   "دينية",     # 1,186
    "قصيدة سياسية":  "سياسية",    # 16
    "قصيدة رومنسيه": "رومانسية",  # 4,074
    "قصيدة ذم":      "ذم",        # 420
    "قصيدة شوق":     "شوق",       # 901
    "قصيدة عتاب":    "عتاب",      # 2,032
    "قصيدة غزل":     "غزل",       # 1,416
    "قصيدة فراق":    "فراق",      # 591
    "قصيدة مدح":     "مدح",       # 5,165
    "قصيدة هجاء":    "هجاء",      # 1,614
    "قصيدة قصيره":   "حكمة",      # 25,911 ← كثيرة جداً
    "قصيدة عامه":    "متنوعة",    # 20,611
}
# TARGET_CATEGORIES = {
#     "قصيدة حزينه":   "حزن",
#     "قصيدة رثاء":    "رثاء",
#     "قصيدة دينية":   "دينية",
#     "قصيدة سياسية":  "سياسية",
#     "قصيدة رومنسيه": "رومانسية",
#     "قصيدة ذم":      "ذم",
#     "قصيدة شوق":     "شوق",
#     "قصيدة عتاب":    "عتاب",
#     "قصيدة غزل":     "غزل",
#     "قصيدة فراق":    "فراق",
#     "قصيدة مدح":     "مدح",
#     "قصيدة هجاء":    "هجاء",
# }

MAX_PER_CATEGORY = 2000  # لتقليل حجم الملف النهائي، نأخذ فقط 2000 بيت لكل تصنيف    


def get_first_verse(verses) -> str:
    if isinstance(verses, list) and verses:
        lines = [v.strip() for v in verses[:2] if v and v.strip()]
        return " / ".join(lines)
    if isinstance(verses, str):
        return verses.strip().split("\n")[0]
    return ""


def main():
    print("⏳ تحميل داتاست ashaar من HuggingFace...")
    dataset = load_dataset("arbml/ashaar", split="train")
    print(f"✅ {len(dataset):,} سجل محمّل")

    poems_db: dict[str, list[dict]] = {
        cat: [] for cat in set(TARGET_CATEGORIES.values())
    }

    skipped = 0
    for item in dataset:
        raw_theme = item.get("poem theme", "")
        if not raw_theme:
            skipped += 1
            continue

        our_category = TARGET_CATEGORIES.get(raw_theme.strip())
        if not our_category:
            skipped += 1
            continue

        if len(poems_db[our_category]) >= MAX_PER_CATEGORY:
            continue

        verse = get_first_verse(item.get("poem verses", []))
        if not verse or len(verse) < 10:
            continue

        poet = str(item.get("poet name", "مجهول") or "مجهول").strip()

        poems_db[our_category].append({
            "verse": verse,
            "poet":  poet,
        })

    print("\n📊 نتيجة التصفية:")
    total = 0
    for category, poems in poems_db.items():
        print(f"  {category:<15}: {len(poems):,} بيت")
        total += len(poems)
    print(f"\n  المجموع: {total:,} | تم تخطي: {skipped:,}")

    output_path = "poems_db.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(poems_db, f, ensure_ascii=False, indent=2)

    size_mb = os.path.getsize(output_path) / 1e6
    print(f"\n✅ تم الحفظ: {output_path} ({size_mb:.1f} MB)")
    print("   الآن شغّل: uvicorn main:app --reload --port 8000")


if __name__ == "__main__":
    main()