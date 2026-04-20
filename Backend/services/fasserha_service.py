"""
خدمة ميزة "فسرها لي" — تشغيل التصنيف عن بُعد عبر HF Space.
نسخة محسّنة لمعالجة الأبيات الطويلة.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI

from typing import Generator
import time

from Fasserha_prompts import FASSERHA_SYSTEM_PROMPT, build_user_prompt

load_dotenv()


# =============================================================
# ENV helpers
# =============================================================

def _required_env(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise RuntimeError(f"المتغير '{key}' غير موجود")
    return value


def _optional_env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _get_openai_client() -> OpenAI:
    return OpenAI(api_key=_required_env("OPENAI_API_KEY"))


# =============================================================
# Remote classifier
# =============================================================

def _remote_classify(poem_text: str) -> dict[str, Any]:
    url = _required_env("FASSERHA_REMOTE_URL")
    api_key = _required_env("FASSERHA_REMOTE_API_KEY")
    timeout_sec = float(_optional_env("FASSERHA_REMOTE_TIMEOUT", "90"))

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    hf_bearer = _optional_env("HF_SPACE_BEARER_TOKEN")
    if hf_bearer:
        headers["Authorization"] = f"Bearer {hf_bearer}"

    try:
        resp = requests.post(
            url,
            headers=headers,
            json={"poem": poem_text},
            timeout=timeout_sec,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"تعذر الاتصال بخدمة التصنيف الخارجية: {e}") from e
    except ValueError as e:
        raise RuntimeError("رد خدمة التصنيف ليس JSON صالح") from e

    for key in ("meter", "era", "topic"):
        if key not in data:
            raise RuntimeError(f"رد خدمة التصنيف ناقص: {key}")

    return data


# =============================================================
# عدّ الأبيات بدقة
# =============================================================

# فواصل شائعة بين شطرين أو بين بيتين
_VERSE_SEPARATORS = re.compile(r"[\.\،\؛\;\*\—\–\-]{2,}|\s{4,}|\t+")


def _count_verses(poem_text: str) -> int:
    """
    عدّ الأبيات بطريقة أذكى:
    - يتعامل مع البيت المكتوب على سطر واحد أو على شطرين منفصلين.
    - يتعامل مع الفواصل (نجوم، شرطات، مسافات طويلة).
    """
    if not poem_text or not poem_text.strip():
        return 1

    # تنظيف
    text = poem_text.strip()

    # توحيد الفواصل
    text = _VERSE_SEPARATORS.sub("\n", text)

    # السطور غير الفارغة
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if not lines:
        return 1

    # هيوريستيك بسيط:
    # - إذا كل سطر طويل (>40 حرف) فهو بيت كامل
    # - إذا السطور قصيرة (<40 حرف) فالغالب أنها شطور → كل سطرين = بيت
    avg_len = sum(len(l) for l in lines) / len(lines)

    if avg_len < 40 and len(lines) >= 2:
        # شطور قصيرة → كل سطرين بيت
        return max(1, (len(lines) + 1) // 2)

    return max(1, len(lines))


# =============================================================
# حساب max_tokens ديناميكياً للأبيات الطويلة
# =============================================================

def _calc_max_tokens(depth: str, verses_count: int) -> int:
    """
    حساب الـ tokens بناءً على عدد الأبيات والمستوى.
    لكل بيت في deep ~250 token (verse + meaning + بنية JSON).
    """
    if depth == "brief":
        # brief: تفسير قصير حتى للأبيات الكثيرة
        if verses_count <= 5:
            return 800
        if verses_count <= 15:
            return 1200
        return 1800

    # deep: يحتاج tokens كثيرة لكل بيت
    base = 1500  # explanation + imagery + meter_effect + summary + mood
    per_verse = 280  # verse text + meaning في JSON

    # الحد الأقصى لـ gpt-4o في الرد ~16000، لكن نضع سقف آمن
    estimated = base + (verses_count * per_verse)
    return min(estimated, 12000)


# =============================================================
# تنظيف الرموز والإيموجي من الردّ
# =============================================================

# Emoji ranges
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0000FE00-\U0000FE0F"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)

# رموز زخرفية شائعة يضعها GPT أحياناً
_DECORATIVE_CHARS = re.compile(r"[★✦◆▪▫■□●○♦♥♠♣→←↑↓⇒⇐⇑⇓✓✗❌✅═━─┃│┌┐└┘├┤┬┴┼]")


def _strip_decorations(text: str) -> str:
    """يزيل الإيموجي والرموز الزخرفية من النص."""
    if not isinstance(text, str):
        return text
    text = _EMOJI_PATTERN.sub("", text)
    text = _DECORATIVE_CHARS.sub("", text)
    # تنظيف Markdown bold/headers لو ظهرت
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # تنظيف مسافات زائدة
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _clean_payload(obj: Any) -> Any:
    """ينظّف الإيموجي والرموز من كل النصوص في الـ dict/list."""
    if isinstance(obj, str):
        return _strip_decorations(obj)
    if isinstance(obj, list):
        return [_clean_payload(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _clean_payload(v) for k, v in obj.items()}
    return obj


# =============================================================
# تحليل JSON آمن مع محاولة استرجاع
# =============================================================

def _try_extract_json(raw: str) -> dict[str, Any] | None:
    """
    محاولة استخراج JSON صالح حتى لو الرد فيه نص قبل/بعد
    أو لو القوس النهائي مفقود (انقطاع التوليد).
    """
    if not raw:
        return None

    # محاولة 1: مباشرة
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # محاولة 2: استخراج أول { وآخر }
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw[start:end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # محاولة 3: إذا الرد انقطع، نحاول إغلاق الأقواس
    if start != -1:
        candidate = raw[start:]
        # موازنة الأقواس
        open_braces = candidate.count("{")
        close_braces = candidate.count("}")
        open_brackets = candidate.count("[")
        close_brackets = candidate.count("]")

        # نحذف من الآخر حتى آخر فاصلة أو اقتباس مغلق
        # ثم نضيف إغلاقات
        # تجربة: قص حتى آخر " ثم إضافة الإغلاقات
        last_quote = candidate.rfind('"')
        if last_quote > 0:
            trimmed = candidate[:last_quote + 1]
            # إضافة الإغلاقات الناقصة
            trimmed += "]" * (open_brackets - close_brackets)
            trimmed += "}" * (open_braces - close_braces)
            try:
                parsed = json.loads(trimmed)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

    return None


def _safe_parse_json(raw: str, depth: str, verses_count: int) -> dict[str, Any]:
    """يحاول تحليل JSON، ولو فشل يرجع fallback نظيف بدون نص خام."""
    parsed = _try_extract_json(raw)

    if parsed is not None:
        # تأكد من الحقول الأساسية
        parsed.setdefault("status", "ok")
        parsed.setdefault("depth", depth)
        parsed.setdefault("verses_count", verses_count)
        parsed.setdefault("summary", "")
        parsed.setdefault("explanation", "")
        parsed.setdefault("verses_breakdown", [])
        parsed.setdefault("imagery", "")
        parsed.setdefault("meter_effect", "")
        parsed.setdefault("mood", "")
        return _clean_payload(parsed)

    # fallback نظيف — لا نضع raw في explanation أبداً
    return {
        "status": "ok",
        "depth": depth,
        "verses_count": verses_count,
        "summary": "تعذّر إكمال التفسير — حاول مرة أخرى.",
        "explanation": (
            "حدث خطأ أثناء توليد التفسير. "
            "إذا كانت الأبيات طويلة جداً، جرّب تقسيمها على جزئين."
        ),
        "verses_breakdown": [],
        "imagery": "",
        "meter_effect": "",
        "mood": "",
    }


# =============================================================
# توليد التفسير عبر GPT
# =============================================================

def _generate_explanation(
    poem_text: str,
    meter_name: str,
    era_name: str,
    topic_name: str,
    depth: str = "brief",
) -> dict[str, Any]:
    verses_count = _count_verses(poem_text)

    user_prompt = build_user_prompt(
        poem_text=poem_text,
        meter_name=meter_name,
        era_name=era_name,
        topic_name=topic_name,
        depth=depth,
        verses_count=verses_count,
    )

    model_name = _optional_env("FASSERHA_LLM_MODEL", "gpt-4o")
    max_tokens = _calc_max_tokens(depth, verses_count)

    response = _get_openai_client().chat.completions.create(
        model=model_name,
        max_tokens=max_tokens,
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": FASSERHA_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = (response.choices[0].message.content or "").strip()
    parsed = _safe_parse_json(raw, depth, verses_count)

    # ضمان أن depth صحيح
    parsed["depth"] = depth

    # في deep: إذا verses_breakdown فارغة، نحاول تعبئتها على الأقل بالنص الخام
    if depth == "deep" and not parsed.get("verses_breakdown"):
        # نقسّم النص إلى أبيات يدوياً ونضع شرحاً عاماً
        verses_list = _split_into_verses(poem_text)
        parsed["verses_breakdown"] = [
            {"verse": v, "meaning": "تعذّر توليد شرح تفصيلي لهذا البيت — راجع التفسير العام أعلاه."}
            for v in verses_list
        ]

    return parsed


def _split_into_verses(poem_text: str) -> list[str]:
    """يقسّم النص إلى أبيات للـ fallback عند فشل verses_breakdown."""
    text = _VERSE_SEPARATORS.sub("\n", poem_text.strip())
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if not lines:
        return [poem_text.strip()]

    avg_len = sum(len(l) for l in lines) / len(lines)

    # شطور قصيرة → جمع كل سطرين
    if avg_len < 40 and len(lines) >= 2:
        verses = []
        for i in range(0, len(lines), 2):
            pair = lines[i:i + 2]
            verses.append(" ... ".join(pair))
        return verses

    return lines


# =============================================================
# الواجهات العامة
# =============================================================

def fasserha_li(poem_text: str, depth: str = "brief") -> dict[str, Any]:
    cls = _remote_classify(poem_text)

    meter_result = cls.get("meter", {})
    era_result = cls.get("era", {})
    topic_result = cls.get("topic", {})

    meter_name = meter_result.get("meter_ar", "غير محدد")
    era_name = era_result.get("era", "غير محدد")
    topic_name = topic_result.get("topic", "غير محدد")

    gpt = _generate_explanation(
        poem_text=poem_text,
        meter_name=meter_name,
        era_name=era_name,
        topic_name=topic_name,
        depth=depth,
    )

    return {
        "poem": poem_text,
        "meter": meter_result,
        "era": era_result,
        "topic": topic_result,
        "gpt": gpt,
    }


def fasserha_api_response(poem_text: str, depth: str = "brief") -> dict[str, Any]:
    if not poem_text or not poem_text.strip():
        return {
            "success": False,
            "error_type": "invalid_text",
            "message": "النص فارغ",
        }

    if depth not in ("brief", "deep"):
        depth = "brief"

    try:
        result = fasserha_li(poem_text, depth)
    except Exception as e:
        return {
            "success": False,
            "error_type": "classifier_unavailable",
            "message": str(e),
        }

    gpt = result["gpt"]

    if gpt.get("status") == "error":
        return {
            "success": False,
            "error_type": gpt.get("error_type", "unknown"),
            "message": gpt.get("message", "تعذّر التفسير"),
        }

    meter = result["meter"]
    era = result["era"]
    topic = result["topic"]

    # تنظيف نهائي للـ verses_breakdown — نضمن أن كل entry فيه verse و meaning
    raw_breakdown = gpt.get("verses_breakdown", []) or []
    cleaned_breakdown = []
    for item in raw_breakdown:
        if not isinstance(item, dict):
            continue
        verse_txt = _strip_decorations(str(item.get("verse", "")).strip())
        meaning_txt = _strip_decorations(str(item.get("meaning", "")).strip())
        if verse_txt and meaning_txt:
            cleaned_breakdown.append({"verse": verse_txt, "meaning": meaning_txt})

    return {
        "success": True,
        "data": {
            "meter": {
                "arabic": meter.get("meter_ar", "غير محدد"),
                "english": meter.get("meter_en", "unknown"),
                "confidence": float(meter.get("confidence", 0.0)),
            },
            "era": {
                "label": era.get("era", "غير محدد"),
                "classical_prob": float(era.get("classical_probability", 0.0)),
                "modern_prob": float(era.get("modern_probability", 0.0)),
            },
            "topic": {
                "label": topic.get("topic", "غير محدد"),
                "confidence": float(topic.get("confidence", 0.0)),
                "top3": topic.get("top3", []),
            },
            "depth": gpt.get("depth", depth),
            "summary": _strip_decorations(gpt.get("summary", "")),
            "explanation": _strip_decorations(gpt.get("explanation", "")),
            "verses_breakdown": cleaned_breakdown,
            "imagery": _strip_decorations(gpt.get("imagery", "")),
            "meter_effect": _strip_decorations(gpt.get("meter_effect", "")),
            "key_word": "",
            "mood": _strip_decorations(gpt.get("mood", "")),
        },
    }
    
    
    
 
def _generate_explanation_stream(
    poem_text: str,
    meter_name: str,
    era_name: str,
    topic_name: str,
    depth: str = "deep",
) -> Generator[str, None, dict[str, Any]]:
    """
    نسخة streaming من _generate_explanation.
    yields chunks of text كما تأتي من GPT.
    في النهاية يرجع الـ dict المحلَّل (بعد جمع كل الأجزاء).
    """
    verses_count = _count_verses(poem_text)
 
    user_prompt = build_user_prompt(
        poem_text=poem_text,
        meter_name=meter_name,
        era_name=era_name,
        topic_name=topic_name,
        depth=depth,
        verses_count=verses_count,
    )
 
    model_name = _optional_env("FASSERHA_LLM_MODEL", "gpt-4o")
    max_tokens = _calc_max_tokens(depth, verses_count)
 
    stream = _get_openai_client().chat.completions.create(
        model=model_name,
        max_tokens=max_tokens,
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": FASSERHA_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,  # ← المفتاح
    )
 
    accumulated = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            accumulated += delta
            yield delta  # نبث القطعة للفرونت
 
    # بعد انتهاء البث، نحلّل الـ JSON الكامل
    parsed = _safe_parse_json(accumulated, depth, verses_count)
    parsed["depth"] = depth
 
    if depth == "deep" and not parsed.get("verses_breakdown"):
        verses_list = _split_into_verses(poem_text)
        parsed["verses_breakdown"] = [
            {"verse": v, "meaning": "تعذّر توليد شرح تفصيلي لهذا البيت."}
            for v in verses_list
        ]
 
    return parsed
 
 
def fasserha_stream(
    poem_text: str,
    depth: str = "deep",
) -> Generator[dict[str, Any], None, None]:
    """
    Generator يبث أحداث SSE:
      {"event": "classify", "data": {...}}     — نتائج التصنيف
      {"event": "chunk", "data": "نص جزئي"}    — قطع GPT
      {"event": "done", "data": {...}}         — الرد النهائي الكامل
      {"event": "error", "data": {...}}        — خطأ
      {"event": "ping", "data": ""}            — keep-alive كل 15 ثانية
    """
    if not poem_text or not poem_text.strip():
        yield {"event": "error", "data": {"error_type": "invalid_text", "message": "النص فارغ"}}
        return
 
    if depth not in ("brief", "deep"):
        depth = "deep"
 
    # ─── 1) التصنيف ─────────────────────────────────────────
    try:
        cls = _remote_classify(poem_text)
    except Exception as e:
        yield {"event": "error", "data": {"error_type": "classifier_unavailable", "message": str(e)}}
        return
 
    meter_result = cls.get("meter", {})
    era_result = cls.get("era", {})
    topic_result = cls.get("topic", {})
 
    classify_payload = {
        "meter": {
            "arabic": meter_result.get("meter_ar", "غير محدد"),
            "english": meter_result.get("meter_en", "unknown"),
            "confidence": float(meter_result.get("confidence", 0.0)),
        },
        "era": {
            "label": era_result.get("era", "غير محدد"),
            "classical_prob": float(era_result.get("classical_probability", 0.0)),
            "modern_prob": float(era_result.get("modern_probability", 0.0)),
        },
        "topic": {
            "label": topic_result.get("topic", "غير محدد"),
            "confidence": float(topic_result.get("confidence", 0.0)),
            "top3": topic_result.get("top3", []),
        },
    }
    yield {"event": "classify", "data": classify_payload}
 
    # ─── 2) بث GPT ──────────────────────────────────────────
    accumulated = ""
    last_ping = time.time()
 
    try:
        gen = _generate_explanation_stream(
            poem_text=poem_text,
            meter_name=meter_result.get("meter_ar", "غير محدد"),
            era_name=era_result.get("era", "غير محدد"),
            topic_name=topic_result.get("topic", "غير محدد"),
            depth=depth,
        )
 
        # نستهلك الـ generator يدوياً عشان نلتقط القيمة المُرجعة
        gpt_result = None
        try:
            while True:
                chunk = next(gen)
                accumulated += chunk
                yield {"event": "chunk", "data": chunk}
 
                # ping كل 15 ثانية (يمنع Render من قطع الاتصال)
                now = time.time()
                if now - last_ping > 15:
                    yield {"event": "ping", "data": ""}
                    last_ping = now
 
        except StopIteration as stop:
            gpt_result = stop.value
 
    except Exception as e:
        yield {"event": "error", "data": {"error_type": "gpt_error", "message": str(e)}}
        return
 
    # ─── 3) التنظيف النهائي وإرسال الرد الكامل ──────────────
    if not isinstance(gpt_result, dict):
        gpt_result = _safe_parse_json(accumulated, depth, _count_verses(poem_text))
 
    if gpt_result.get("status") == "error":
        yield {
            "event": "error",
            "data": {
                "error_type": gpt_result.get("error_type", "unknown"),
                "message": gpt_result.get("message", "تعذّر التفسير"),
            },
        }
        return
 
    raw_breakdown = gpt_result.get("verses_breakdown", []) or []
    cleaned_breakdown = []
    for item in raw_breakdown:
        if not isinstance(item, dict):
            continue
        verse_txt = _strip_decorations(str(item.get("verse", "")).strip())
        meaning_txt = _strip_decorations(str(item.get("meaning", "")).strip())
        if verse_txt and meaning_txt:
            cleaned_breakdown.append({"verse": verse_txt, "meaning": meaning_txt})
 
    final_payload = {
        **classify_payload,
        "depth": gpt_result.get("depth", depth),
        "summary": _strip_decorations(gpt_result.get("summary", "")),
        "explanation": _strip_decorations(gpt_result.get("explanation", "")),
        "verses_breakdown": cleaned_breakdown,
        "imagery": _strip_decorations(gpt_result.get("imagery", "")),
        "meter_effect": _strip_decorations(gpt_result.get("meter_effect", "")),
        "key_word": "",
        "mood": _strip_decorations(gpt_result.get("mood", "")),
    }
 
    yield {"event": "done", "data": final_payload}
 