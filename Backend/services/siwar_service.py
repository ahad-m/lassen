# =============================================================
# services/siwar_service.py
# معجم سوار — مع تطبيع التاء المربوطة والهاء
# البحث عبر واجهة سوار العامة دون تقييد بنوع معجم محدد.
# =============================================================

import httpx
import re
import os
from dotenv import load_dotenv

load_dotenv()

SIWAR_API_KEY  = os.getenv("SIWAR_API_KEY")
SIWAR_BASE_URL = os.getenv("SIWAR_BASE_URL", "https://siwar.ksaa.gov.sa")
TIMEOUT        = 10.0

# أقل طول لسطر معنى يُعتبر مفيداً (تجنّب الضجيج الفارغ)
MIN_DEFINITION_LEN = 2
SEARCH_LIMIT       = 30


def _strip_tashkeel(text: str) -> str:
    return re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC]", "", text).strip()


def _is_arabic(text: str) -> bool:
    clean = _strip_tashkeel(text)
    return bool(re.compile(r"[\u0621-\u063A\u0641-\u064A]").search(clean))


def _normalize_ta_ha(word: str) -> str:
    """
    يوحّد التاء المربوطة والهاء في نهاية الكلمة.
    مثال: "عسجديه" → "عسجدية"
    هذا يساعد في البحث في المعاجم التي تخزن الكلمة بالتاء المربوطة.
    """
    clean = _strip_tashkeel(word)
    # إذا ينتهي بـ ه → حوّله لـ ة للبحث
    if clean.endswith("ه"):
        return clean[:-1] + "ة"
    return clean


def _get_search_variants(word: str) -> list[str]:
    """
    يولّد أشكالاً مختلفة للكلمة للبحث في سوار:
    1. الكلمة بعد تحويل ه → ة
    2. الكلمة الأصلية
    3. الكلمة بعد ة → ه (للعكس)
    4. بدون ال التعريف
    5. توحيد همزة الألف في بداية الكلمة (أ/إ/آ → ا) إن وُجدت
    """
    base       = _strip_tashkeel(word)
    normalized = _normalize_ta_ha(base)

    variants = [normalized]  # الأولوية للمطبّعة

    # إضافة الأصلية إذا مختلفة
    if base != normalized:
        variants.append(base)

    # العكس: إذا ة → ه
    if normalized.endswith("ة"):
        variants.append(normalized[:-1] + "ه")

    # بدون ال التعريف
    for v in list(variants):
        if v.startswith("ال") and len(v) > 4:
            variants.append(v[2:])

    # همزة الألف على السطر الأول
    for v in list(variants):
        if v and v[0] in "أإآ":
            variants.append("ا" + v[1:])

    # إزالة المكررات مع الحفاظ على الترتيب
    seen = set()
    unique = []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            unique.append(v)

    return unique


def _coerce_to_entry_list(payload: object) -> list:
    """يحوّل جسم JSON سوار إلى قائمة مداخل (list أو dict يلفّ قائمة)."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("content", "data", "results", "items", "records", "elements"):
            v = payload.get(key)
            if isinstance(v, list):
                return v
    return []


def _lexicon_label(entry: dict) -> str:
    for k in ("lexiconName", "dictionaryName", "lexicon", "source"):
        v = entry.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "معجم"


def _sense_definition_text(sense: object) -> str:
    """يستخرج نص التعريف سواء أكان sense نصاً أم كائناً (مثل /senses)."""
    if isinstance(sense, str):
        return sense.strip()
    if not isinstance(sense, dict):
        return str(sense).strip() if sense else ""

    for key in ("definition", "text", "gloss", "meaning", "sense", "description"):
        val = sense.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    # أي قيمة نصية قصيرة في القاموس
    for val in sense.values():
        if isinstance(val, str) and len(val.strip()) > MIN_DEFINITION_LEN:
            return val.strip()
    return ""


def _parse_senses_response(payload: object) -> dict:
    data = _coerce_to_entry_list(payload)
    if not data:
        return {}

    all_definitions: list[dict] = []

    for entry in data:
        if not isinstance(entry, dict):
            continue
        lexicon_name = _lexicon_label(entry)
        senses = entry.get("senses") or []
        if isinstance(senses, dict):
            senses = [senses]
        if not isinstance(senses, list):
            continue
        for sense in senses:
            defn = _sense_definition_text(sense)
            if defn and len(defn) >= MIN_DEFINITION_LEN:
                root_val = None
                if isinstance(sense, dict):
                    r = sense.get("root") or sense.get("lemma")
                    if isinstance(r, str) and r.strip():
                        root_val = r.strip()
                all_definitions.append({
                    "definition":  defn,
                    "source_dict": lexicon_name,
                    "root":        root_val,
                })

    if not all_definitions:
        return {}

    # ترتيب ثابت باسم المعجم فقط (بدون تفضيل معجم معيّن على آخر)
    all_definitions.sort(key=lambda x: x.get("source_dict") or "")

    combined_parts = []
    for i, d in enumerate(all_definitions[:6]):
        combined_parts.append(f"{i+1}. [{d['source_dict']}] {d['definition']}")

    root = next((d["root"] for d in all_definitions if d.get("root")), None)

    return {
        "definition":      "\n".join(combined_parts),
        "all_definitions": all_definitions,
        "root":            root,
    }


def _parse_search_response(payload: object) -> dict:
    data = _coerce_to_entry_list(payload)
    if not data:
        return {}

    all_definitions: list[dict] = []

    for entry in data:
        if not isinstance(entry, dict):
            continue
        lexicon_name = _lexicon_label(entry)
        root_raw = entry.get("root", "")
        senses = entry.get("senses") or []
        if isinstance(senses, dict):
            senses = [senses]
        if not isinstance(senses, list):
            continue
        for sense in senses:
            defn = _sense_definition_text(sense)
            if defn and len(defn) >= MIN_DEFINITION_LEN:
                all_definitions.append({
                    "definition":  defn,
                    "source_dict": lexicon_name,
                    "root":        (root_raw or "").strip() or None,
                })

    if not all_definitions:
        return {}

    all_definitions.sort(key=lambda x: x.get("source_dict") or "")

    combined_parts = []
    for i, d in enumerate(all_definitions[:6]):
        combined_parts.append(f"{i+1}. [{d['source_dict']}] {d['definition']}")

    root = next((d["root"] for d in all_definitions if d.get("root")), None)

    return {
        "definition":      "\n".join(combined_parts),
        "all_definitions": all_definitions,
        "root":            root,
    }


async def _search_siwar_single(client: httpx.AsyncClient, query: str, headers: dict) -> dict:
    """يبحث بكلمة واحدة ويرجع النتيجة (بدون فلترة حسب نوع المعجم)."""
    params = {"query": query, "limit": SEARCH_LIMIT}

    # المحاولة 1: senses
    try:
        resp = await client.get(
            f"{SIWAR_BASE_URL}/api/v1/external/public/senses",
            headers=headers,
            params=params,
        )
        if resp.status_code == 200:
            result = _parse_senses_response(resp.json())
            if result.get("definition"):
                return result
    except Exception:
        pass

    # المحاولة 2: search
    try:
        resp2 = await client.get(
            f"{SIWAR_BASE_URL}/api/v1/external/public/search",
            headers=headers,
            params=params,
        )
        if resp2.status_code == 200:
            result2 = _parse_search_response(resp2.json())
            if result2.get("definition"):
                return result2
    except Exception:
        pass

    return {}


async def get_siwar_definition(word: str) -> dict:
    """
    يبحث عن الكلمة في معجم سوار.
    يجرب أشكالاً مختلفة للكلمة (تاء مربوطة / هاء / بدون ال / همزة الألف).
    """
    NOT_FOUND = {
        "found":           False,
        "is_arabic":       True,
        "definition":      None,
        "all_definitions": [],
        "root":            None,
    }

    if not _is_arabic(word):
        return {**NOT_FOUND, "is_arabic": False}

    if not SIWAR_API_KEY:
        print("⚠️ SIWAR_API_KEY مفقود")
        return NOT_FOUND

    headers  = {"apikey": SIWAR_API_KEY, "Accept": "application/json"}
    variants = _get_search_variants(word)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for variant in variants:
            result = await _search_siwar_single(client, variant, headers)
            if result.get("definition"):
                print(f"✅ سوار وجد '{word}' (بحث: '{variant}')")
                return {"found": True, "is_arabic": True, **result}

    print(f"ℹ️ سوار ما وجد '{word}' — GPT يعتمد على معرفته")
    return NOT_FOUND
