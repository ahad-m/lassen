# # يكلم GPT
# # ياخذ الـ prompt
# # يرسل الـ user input
# # يرجع الناتج

# # يعني هنا المنطق الحقيقي للذكاء الاصطناعي.

# =============================================================
# services/ai_service.py — منطق GPT لكل الصفحات
# =============================================================

import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# ── برومتات كنوز الكلمات ──────────────────────────────────────
from TreasuresOfWords_promts import (
    TREASURES_SYSTEM_PROMPT,
    TREASURES_USER_PROMPT,
    SIWAR_BLOCK_TEMPLATE,
    SIWAR_ROOT_LINE,
    VERSE_BLOCK_TEMPLATE,
    FOLLOWUP_BLOCK_TEMPLATE,
)

# ── برومتات مزاج اليوم ────────────────────────────────────────
from MoodOfTheDay_promts import (
    MOOD_SYSTEM_PROMPT,
    MOOD_USER_PROMPT,
    POEM_LINE_TEMPLATE,
)

load_dotenv()

GPT_MODEL   = "gpt-4o"
TEMPERATURE = 0.35

_client = None

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
    verse: str | None = None,
    is_followup: bool = False,
) -> dict:

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
        siwar_block = "[معجم سوار: الكلمة غير موجودة - اعتمد على معرفتك]"

    verse_block    = VERSE_BLOCK_TEMPLATE.format(verse=verse.strip()) if verse and verse.strip() else ""
    followup_block = FOLLOWUP_BLOCK_TEMPLATE if is_followup else ""

    user_msg = TREASURES_USER_PROMPT.format(
        word=word,
        siwar_block=siwar_block,
        verse_block=verse_block,
        followup_block=followup_block,
    )

    response = await get_client().chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": TREASURES_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=500,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"meaning": raw, "poetic_usage": "", "symbolism": "",
                  "example_verse": "", "simple_tip": "", "confidence": "low"}

    defaults = {"meaning": "", "poetic_usage": "", "symbolism": "",
                "example_verse": "", "simple_tip": "", "confidence": "medium"}
    return {**defaults, **result}


# =============================================================
# 🔌 مزاج اليوم
# =============================================================

async def get_mood_poems(
    user_input: str,
    category: str,
    poems: list[dict],
) -> dict:
    """
    يُرسل الأبيات من الداتاست لـ GPT ليختار ويشرح.

    Args:
        user_input: ما كتبه المستخدم
        category:   التصنيف المكتشف
        poems:      قائمة الأبيات من poetry_retriever
    """

    # بناء قائمة الأبيات للبرومت
    poems_lines = [
        POEM_LINE_TEMPLATE.format(
            verse=p.get("verse", ""),
            poet=p.get("poet", "مجهول"),
        )
        for p in poems
    ]
    poems_context = "\n".join(poems_lines) or "لا توجد أبيات متاحة"

    user_msg = MOOD_USER_PROMPT.format(
        user_input=user_input,
        category=category,
        poems_context=poems_context,
    )

    response = await get_client().chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": MOOD_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=1000,
        temperature=0.5,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "feeling_detected":  "غير محدد",
            "feeling_intensity": "متوسط",
            "category_used":     category,
            "opening_line":      "وصلت مشاعرك",
            "poems":             [],
            "closing_line":      raw,
        }

    defaults = {
        "feeling_detected": "غير محدد",
        "feeling_intensity": "متوسط",
        "category_used": category,
        "opening_line": "",
        "poems": [],
        "closing_line": "",
    }
    return {**defaults, **result}


# =============================================================
# TODO: باقي الصفحات
# =============================================================

async def generate_verse(idea: str) -> dict:
    raise NotImplementedError  # مكان ربط ساعدني أكتب

async def get_time_journey(topic: str) -> dict:
    raise NotImplementedError  # مكان ربط رحلة عبر الزمن

async def interpret_verses(verses: str) -> dict:
    raise NotImplementedError  # مكان ربط تفسير الأبيات











#=====*************************************************8==========================
#هذي اول جزئية سويتها شغالة تمام
# # =============================================================
# # services/ai_service.py
# # منطق GPT لكل الصفحات - حالياً: كنوز الكلمات فقط
# # =============================================================

# import json
# import os
# from openai import AsyncOpenAI
# from dotenv import load_dotenv

# from TreasuresOfWords_promts import (
#     TREASURES_SYSTEM_PROMPT,
#     TREASURES_USER_PROMPT,
#     SIWAR_BLOCK_TEMPLATE,
#     SIWAR_ROOT_LINE,
#     VERSE_BLOCK_TEMPLATE,
#     FOLLOWUP_BLOCK_TEMPLATE,
# )

# load_dotenv()

# client      = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# GPT_MODEL   = "gpt-4o"
# MAX_TOKENS  = 500
# TEMPERATURE = 0.35


# # =============================================================
# # 🔌 كنوز الكلمات
# # =============================================================

# async def explain_word(
#     word: str,
#     siwar_result: dict,
#     verse: str | None = None,
#     is_followup: bool = False,
# ) -> dict:
#     """
#     يشرح الكلمة العربية ويُرجع dict منظّم.

#     Returns:
#         {
#           "meaning": str,
#           "poetic_usage": str,
#           "symbolism": str,
#           "example_verse": str,
#           "simple_tip": str,
#           "confidence": "high"|"medium"|"low"
#         }
#     """

#     # ── بناء جزء سوار ─────────────────────────────────────────
#     if siwar_result.get("found") and siwar_result.get("definition"):
#         root_line = (
#             SIWAR_ROOT_LINE.format(root=siwar_result["root"])
#             if siwar_result.get("root") else ""
#         )
#         siwar_block = SIWAR_BLOCK_TEMPLATE.format(
#             definition=siwar_result["definition"],
#             root_line=root_line,
#         )
#     else:
#         siwar_block = "[معجم سوار: الكلمة غير موجودة - اعتمد على معرفتك]"

#     # ── بناء جزء البيت ────────────────────────────────────────
#     verse_block = (
#         VERSE_BLOCK_TEMPLATE.format(verse=verse.strip())
#         if verse and verse.strip() else ""
#     )

#     # ── بناء جزء المتابعة ─────────────────────────────────────
#     followup_block = FOLLOWUP_BLOCK_TEMPLATE if is_followup else ""

#     # ── بناء الرسالة ──────────────────────────────────────────
#     user_msg = TREASURES_USER_PROMPT.format(
#         word=word,
#         siwar_block=siwar_block,
#         verse_block=verse_block,
#         followup_block=followup_block,
#     )

#     # ── إرسال لـ GPT ──────────────────────────────────────────
#     response = await client.chat.completions.create(
#         model=GPT_MODEL,
#         messages=[
#             {"role": "system", "content": TREASURES_SYSTEM_PROMPT},
#             {"role": "user",   "content": user_msg},
#         ],
#         max_tokens=MAX_TOKENS,
#         temperature=TEMPERATURE,
#         response_format={"type": "json_object"},  # يضمن JSON دائماً
#     )

#     raw = response.choices[0].message.content.strip()

#     # ── تحليل JSON ────────────────────────────────────────────
#     try:
#         result = json.loads(raw)
#     except json.JSONDecodeError:
#         # fallback إذا GPT ما رجع JSON نظيف
#         result = {
#             "meaning":       raw,
#             "poetic_usage":  "",
#             "symbolism":     "",
#             "example_verse": "",
#             "simple_tip":    "",
#             "confidence":    "low",
#         }

#     # ضمان وجود كل المفاتيح
#     defaults = {
#         "meaning": "", "poetic_usage": "", "symbolism": "",
#         "example_verse": "", "simple_tip": "", "confidence": "medium"
#     }
#     return {**defaults, **result}


# # =============================================================
# # مكان ربط باقي الصفحات لاحقاً
# # =============================================================

# async def get_mood_poems(mood: str) -> dict:
#     # TODO: مكان ربط مودل شعور اليوم
#     raise NotImplementedError

# async def generate_verse(idea: str) -> dict:
#     # TODO: مكان ربط مودل ساعدني أكتب
#     raise NotImplementedError

# async def get_time_journey(topic: str) -> dict:
#     # TODO: مكان ربط مودل رحلة عبر الزمن
#     raise NotImplementedError

# async def interpret_verses(verses: str) -> dict:
#     # TODO: مكان ربط مودل تفسير الأبيات
#     raise NotImplementedError
