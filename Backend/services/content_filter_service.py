"""
خدمة فلترة محتوى الأبيات الشعرية.
content_filter_service.py

تتأكد من خلو الأبيات من:
- المحتوى غير اللائق (كلمات غير محترمة، محتوى جنسي صريح)
- الإشارات الدينية غير الإسلامية (يسوع، الرب بمعنى مسيحي، الثالوث، إلخ)
- الكفر الصريح أو السب
"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

# ── عميل OpenAI ───────────────────────────────────────────────
_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY غير موجود")
        _client = OpenAI(api_key=api_key)
    return _client


# ── الفلتر السريع بالكلمات المفتاحية ──────────────────────────
# كلمات وعبارات ترفع علم أحمر فوراً
_FORBIDDEN_KEYWORDS = {
    # إشارات دينية غير إسلامية
    "يسوع", "المسيح عيسى", "الصليب", "الصلبان", "التثليث", "الأقانيم",
    "اللات", "العزى", "مناة", "هبل",
    # محتوى فاضح/إباحي صريح
    "العاهرة", "العاهرات", "الزانية", "الزاني",
    # سب وشتم
    "لعنة الله", "اللعين",
}

# كلمات حساسة تحتاج فحص LLM (قد تكون بريئة أو غير لائقة حسب السياق)
_SENSITIVE_WORDS = {
    "خمر", "خمرة", "الخمر", "النبيذ", "السكر", "سكران",
    "العشق", "عاشق", "قبلة", "قبّل", "ضم", "عانق",
    "الصدر", "النهد", "النهود", "الردف",
    "الرب",  # قد تكون إسلامية (رب العالمين) أو مسيحية
}


def _contains_forbidden_keyword(text: str) -> bool:
    """فحص سريع بالكلمات المفتاحية الممنوعة."""
    if not text:
        return False
    # نطبّق نورمالايز بسيط للمقارنة
    normalized = text.replace("َ", "").replace("ُ", "").replace("ِ", "")
    normalized = normalized.replace("ّ", "").replace("ْ", "").replace("ـ", "")
    for keyword in _FORBIDDEN_KEYWORDS:
        if keyword in normalized:
            return True
    return False


def _contains_sensitive_keyword(text: str) -> bool:
    """فحص إذا الأبيات فيها كلمات حساسة تحتاج مراجعة LLM."""
    if not text:
        return False
    normalized = text.replace("َ", "").replace("ُ", "").replace("ِ", "")
    normalized = normalized.replace("ّ", "").replace("ْ", "").replace("ـ", "")
    for keyword in _SENSITIVE_WORDS:
        if keyword in normalized:
            return True
    return False


# ── فلتر LLM للحالات الدقيقة ──────────────────────────────────
_FILTER_SYSTEM_PROMPT = """أنت مُراجع محتوى لتطبيق شعر عربي موجّه لجمهور مسلم غير مسيحي او يهودي.

مهمتك: تقييم أبيات شعرية وتحديد ما إذا كانت **مناسبة** للعرض أم لا.

معايير الرفض (يُرفض البيت إذا احتوى على أيٍّ مما يلي):
1. إشارات دينية غير إسلامية صريحة (ذكر يسوع أو المسيح كإله، الصليب كرمز ديني مسيحي، التثليث، آلهة الجاهلية كمعبودات).
2. ألفاظ جنسية فاحشة أو وصف مباشر لأعضاء حميمة بشكل مبتذل.
3. سب صريح للذات الإلهية أو الأنبياء أو الصحابة.
4. شتائم بذيئة أو ألفاظ نابية.
5. دعوة مباشرة للمعاصي الكبرى (الزنا، شرب الخمر مع تمجيده).

معايير القبول (يُقبل البيت إذا):
1. غزل عفيف (حتى لو ذكر الحب، الشوق، القبلة بشكل غير فاحش).
2. ذكر الخمر في سياق الذم أو الرمز الصوفي (مقبول عموماً في الشعر العربي الكلاسيكي).
3. استخدام كلمة "الرب" بمعنى إسلامي (رب العالمين، ربي، يا رب ).
4. شعر جاهلي يصف معبودات بشكل تاريخي/وصفي بدون تمجيد.
5. أي محتوى أدبي كلاسيكي معتاد في كتب الأدب العربي.

أرجع JSON فقط بالصيغة التالية:
{
  "is_appropriate": true/false,
  "reason": "سبب الرفض المختصر إذا كان غير مناسب، أو null إذا كان مناسباً"
}"""


def _check_with_llm(verses: list[str]) -> dict[str, Any]:
    """يستخدم LLM للتحقق من مناسبة الأبيات."""
    verses_text = "\n".join(f"{i+1}. {v}" for i, v in enumerate(verses))
    user_message = f"قيّم الأبيات التالية:\n\n{verses_text}"

    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",  # سريع ورخيص
            messages=[
                {"role": "system", "content": _FILTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=150,
        )
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        return {
            "is_appropriate": bool(result.get("is_appropriate", True)),
            "reason": result.get("reason"),
        }
    except Exception as e:
        # عند الفشل، نسمح بالمرور (fail-open) لتجنب حجب كل المحتوى بسبب خطأ API
        print(f" خطأ في فلتر LLM: {e}")
        return {"is_appropriate": True, "reason": None}


# ── الدالة الرئيسية ───────────────────────────────────────────

def is_content_appropriate(verses: list[str]) -> tuple[bool, str | None]:
    """
    تتحقق من مناسبة قائمة أبيات للعرض.

    ترجع tuple: (is_appropriate, rejection_reason)
    - is_appropriate: True إذا الأبيات مناسبة، False إذا يجب رفضها.
    - rejection_reason: سبب الرفض إن وجد (للتسجيل/الـ logging).
    """
    if not verses:
        return True, None

    full_text = " ".join(str(v) for v in verses if v)

    # المستوى 1: فلتر كلمات مفتاحية ممنوعة (رفض فوري)
    if _contains_forbidden_keyword(full_text):
        return False, "keyword_match_forbidden"

    # المستوى 2: فلتر كلمات حساسة (نستدعي LLM فقط إذا لزم)
    if _contains_sensitive_keyword(full_text):
        llm_result = _check_with_llm(verses)
        if not llm_result["is_appropriate"]:
            return False, llm_result.get("reason") or "llm_rejected"

    return True, None


def filter_appropriate_rounds(
    rounds_pool: list[dict[str, Any]],
    verses_key: str = "verses",
) -> list[dict[str, Any]]:
    """
    تفلتر قائمة جولات محتملة وترجع فقط الجولات ذات المحتوى المناسب.
    """
    filtered: list[dict[str, Any]] = []
    for round_data in rounds_pool:
        verses = round_data.get(verses_key) or []
        if not isinstance(verses, list):
            continue
        is_ok, reason = is_content_appropriate([str(v) for v in verses])
        if is_ok:
            filtered.append(round_data)
        else:
            # تسجيل للمراجعة
            poem_id = round_data.get("poem_id", "unknown")
            poet = round_data.get("poet_name", "unknown")
            print(f" تم رفض بيت — poem_id: {poem_id}, poet: {poet}, reason: {reason}")

    return filtered

