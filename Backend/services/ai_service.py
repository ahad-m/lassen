# =============================================================
# services/ai_service.py — منطق GPT
# =============================================================

import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

from TreasuresOfWords_promts import (
    TREASURES_SYSTEM_PROMPT,
    TREASURES_USER_PROMPT,
    SIWAR_BLOCK_TEMPLATE,
    SIWAR_ROOT_LINE,
    VERSES_FROM_DB_TEMPLATE,
    VERSE_LINE_TEMPLATE,
    VERSE_CONTEXT_TEMPLATE,
    FOLLOWUP_BLOCK_TEMPLATE,
)
from MoodOfTheDay_promts import (
    MOOD_SYSTEM_PROMPT,
    MOOD_USER_PROMPT,
    CONTEXT_BLOCK_TEMPLATE,
    POEMS_BLOCK_TEMPLATE,
    POEM_LINE_TEMPLATE,
    MOOD_TO_CATEGORY,
    AVAILABLE_CATEGORIES,
)
from JourneyThroughTime_prompts import (
    JOURNEY_SUMMARY_SYSTEM_PROMPT,
    JOURNEY_SUMMARY_USER_PROMPT,
)

load_dotenv()

GPT_MODEL = "gpt-4o"
_client   = None

def get_client():
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


# =============================================================
# 🔌 كنوز الكلمات
# =============================================================

async def explain_word(
    word: str,
    siwar_result: dict,
    db_verses: list[dict],
    verse: str | None = None,
    is_followup: bool = False,
) -> dict:

    # ── جزء سوار ──────────────────────────────────────────────
    if siwar_result.get("found") and siwar_result.get("definition"):
        root_line = (
            SIWAR_ROOT_LINE.format(root=siwar_result["root"])
            if siwar_result.get("root") else ""
        )
        siwar_block = SIWAR_BLOCK_TEMPLATE.format(
            definition=siwar_result["definition"],
            root_line=root_line,
        )
    else:
        siwar_block = "[معجم سوار: لم يُجد تعريف — اعتمد على معرفتك]"

    # ── أبيات الداتاست ────────────────────────────────────────
    if db_verses:
        lines = [
            VERSE_LINE_TEMPLATE.format(
                verse=v["verse"], poet=v.get("poet", "مجهول")
            )
            for v in db_verses
        ]
        verses_from_db_block = VERSES_FROM_DB_TEMPLATE.format(
            verses_list="\n".join(lines)
        )
    else:
        verses_from_db_block = "[لم تُوجد أبيات في مجموعة الأشعار — أضف من معرفتك وضع source: 'gpt']"

    verse_context_block = (
        VERSE_CONTEXT_TEMPLATE.format(verse=verse.strip())
        if verse and verse.strip() else ""
    )
    followup_block = FOLLOWUP_BLOCK_TEMPLATE if is_followup else ""

    user_msg = TREASURES_USER_PROMPT.format(
        word=word,
        siwar_block=siwar_block,
        verses_from_db_block=verses_from_db_block,
        verse_context_block=verse_context_block,
        followup_block=followup_block,
    )

    response = await get_client().chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": TREASURES_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=600,
        temperature=0.3,
        timeout=30,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "status": "ok", "primary_meaning": raw,
            "meanings": [], "poetic_usage": "", "symbolism": "",
            "example_verses": [], "simple_tip": "", "confidence": "low",
            "plural": None,
        }
    return result


# =============================================================
# 🔌 مزاج اليوم
# =============================================================

def _quick_detect_category(text: str) -> str | None:
    """
    كشف سريع للتصنيف من الكلمات المفتاحية.
    يُستخدم فقط لاختيار الأبيات — GPT يحدد الدقيق.
    """
    text_lower = text.lower()
    for keyword, categories in MOOD_TO_CATEGORY.items():
        if keyword in text_lower:
            return categories[0]
    return None


async def get_mood_response(
    user_input: str,
    conversation_history: list[dict],
    poems: list[dict],
    category: str,
) -> dict:
    """
    يرد على المستخدم بذكاء — يحدد نوع الرد المناسب.

    Args:
        user_input:           رسالة المستخدم
        conversation_history: المحادثة السابقة [{"role": "user/assistant", "content": "..."}]
        poems:                أبيات من الداتاست
        category:             التصنيف المقترح

    Returns:
        dict مع response_type: "poems" | "clarify" | "redirect" | "confirm"
    """

    # ── بناء سياق المحادثة ────────────────────────────────────
    if conversation_history:
        history_lines = []
        for msg in conversation_history[-6:]:  # آخر 6 رسائل فقط
            role    = "المستخدم" if msg["role"] == "user" else "بيت القصيد"
            content = msg["content"]
            history_lines.append(f"{role}: {content}")
        context_block = CONTEXT_BLOCK_TEMPLATE.format(
            history="\n".join(history_lines)
        )
    else:
        context_block = ""

    # ── بناء قائمة الأبيات (فقط إذا عندنا أبيات) ────────────
    if poems:
        poems_lines = [
            POEM_LINE_TEMPLATE.format(
                verse=p.get("verse", ""),
                poet=p.get("poet", "مجهول"),
            )
            for p in poems
        ]
        poems_block = POEMS_BLOCK_TEMPLATE.format(
            category=category,
            poems_list="\n".join(poems_lines),
        )
    else:
        poems_block = "[لا توجد أبيات محملة — إذا قررت تقديم poems، أضف أبياتاً من معرفتك]"

    user_msg = MOOD_USER_PROMPT.format(
        user_input=user_input,
        context_block=context_block,
        poems_block=poems_block,
    )

    response = await get_client().chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": MOOD_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=1000,
        temperature=0.5,
        timeout=30,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "response_type":  "redirect",
            "message":        "حدث خطأ، حاول مرة أخرى.",
        }

    # ضمان وجود response_type
    if "response_type" not in result:
        result["response_type"] = "redirect"

    return result


# للتوافق مع الكود القديم في main.py
async def get_mood_poems(
    user_input: str,
    category: str,
    poems: list[dict],
) -> dict:
    return await get_mood_response(
        user_input=user_input,
        conversation_history=[],
        poems=poems,
        category=category,
    )


# =============================================================
# TODO: باقي الصفحات
# =============================================================
async def generate_verse(idea: str) -> dict:
    raise NotImplementedError

async def get_time_journey(topic: str) -> dict:
    raise NotImplementedError

async def interpret_verses(verses: str) -> dict:
    raise NotImplementedError


async def summarize_journey(theme: str, eras_payload: list[dict]) -> dict:
    """
    يلخص التشابه والاختلاف الجوهري بين التعبير الشعري عبر العصور.
    """
    user_msg = JOURNEY_SUMMARY_USER_PROMPT.format(
        theme=theme,
        eras_block=json.dumps(eras_payload, ensure_ascii=False, indent=2),
    )

    response = await get_client().chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": JOURNEY_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=500,
        temperature=0.4,
        timeout=30,
        response_format={"type": "json_object"},
    )

    raw = (response.choices[0].message.content or "").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "similarities": [],
            "core_difference": "تعذّر بناء مقارنة دقيقة حالياً.",
            "final_line": "هذه نهاية الرحلة عبر الزمن.",
        }

    # حماية بسيطة للقيم
    if not isinstance(result.get("similarities"), list):
        result["similarities"] = []
    result["core_difference"] = str(result.get("core_difference", "")).strip()
    result["final_line"] = str(result.get("final_line", "")).strip() or "هذه نهاية الرحلة عبر الزمن."

    return result


