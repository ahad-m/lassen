# =============================================================
# explore_dataset.py
# شغّله مرة واحدة فقط لاستكشاف بنية الداتاست
# تشغيل: python explore_dataset.py
# =============================================================

from datasets import load_dataset

print("⏳ تحميل الداتاست...")
dataset = load_dataset("arbml/ashaar", split="train")
print(f"✅ عدد السجلات: {len(dataset):,}")
print(f"📋 الأعمدة: {dataset.column_names}")

print("\n" + "="*60)
print("🔍 أول 3 سجلات كاملة:")
print("="*60)

for i in range(3):
    item = dataset[i]
    print(f"\n--- سجل {i+1} ---")
    for key, val in item.items():
        if isinstance(val, list):
            print(f"  [{key}] list({len(val)}): {str(val[:3])[:120]}")
        else:
            print(f"  [{key}] {type(val).__name__}: {str(val)[:120]}")

print("\n" + "="*60)
print("📊 القيم الفريدة في كل عمود محتمل للتصنيف:")
print("="*60)

for col in dataset.column_names:
    try:
        sample = dataset[0][col]
        # تجاهل الأعمدة النصية الطويلة
        if isinstance(sample, list):
            # أخذ أول قيمة من كل list
            vals = []
            for item in dataset:
                v = item[col]
                if isinstance(v, list) and v:
                    vals.append(str(v[0]).strip())
                elif v:
                    vals.append(str(v).strip())
            unique = list(set(vals))
        else:
            unique = list(set(
                str(item[col]).strip()
                for item in dataset
                if item[col] and len(str(item[col])) < 50
            ))

        if 2 <= len(unique) <= 80:
            print(f"\n  عمود: {col} ({len(unique)} قيمة فريدة)")
            for v in sorted(unique)[:20]:
                count = sum(1 for item in dataset
                           if (item[col][0] if isinstance(item[col], list) and item[col]
                               else str(item[col])).strip() == v)
                print(f"    • {v:<25} ({count:,})")
    except Exception as e:
        print(f"  ⚠️ {col}: {e}")
