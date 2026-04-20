# يستقبل الطلبات من الفرونت
# يحدد أي endpoint انطلب
# ينادي الخدمة المناسبة
# يرجع JSON




# =============================================================
# main.py — FastAPI
# تشغيل: uvicorn main:app --reload --port 8000
# =============================================================

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from schemas import (
    TreasuresRequest, TreasuresResponse, SiwarInfo,
    MoodRequest, MoodResponse, PoemEntry,
)
from services.siwar_service import get_siwar_definition
from services.ai_service import explain_word, get_mood_poems
from services.poetry_retriever import get_poems_for_mood, get_db_stats

load_dotenv()

app = FastAPI(title="بيت القصيد API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── فحص الصحة ─────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "✅ يعمل"}

@app.get("/health")
async def health():
    return {
        "openai":   "✅" if os.getenv("OPENAI_API_KEY") else "❌ مفقود",
        "siwar":    "✅" if os.getenv("SIWAR_API_KEY")  else "❌ مفقود",
        "poems_db": get_db_stats(),
    }


# =============================================================
# 🔌 كنوز الكلمات — POST /api/treasures/explain
# =============================================================

@app.post("/api/treasures/explain", response_model=TreasuresResponse)
async def explain_arabic_word(req: TreasuresRequest):
    siwar = await get_siwar_definition(req.word)
    try:
        gpt_result = await explain_word(
            word=req.word,
            siwar_result=siwar,
            verse=req.verse,
            is_followup=req.is_followup,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ GPT: {str(e)}")

    return TreasuresResponse(
        word          = req.word,
        meaning       = gpt_result.get("meaning", ""),
        poetic_usage  = gpt_result.get("poetic_usage", ""),
        symbolism     = gpt_result.get("symbolism", ""),
        example_verse = gpt_result.get("example_verse", ""),
        simple_tip    = gpt_result.get("simple_tip", ""),
        confidence    = gpt_result.get("confidence", "medium"),
        siwar         = SiwarInfo(**siwar),
        verse         = req.verse,
    )


# =============================================================
# 🔌 مزاج اليوم — POST /api/mood/poems
# =============================================================

@app.post("/api/mood/poems", response_model=MoodResponse)
async def mood_poems(req: MoodRequest):
    """
    1. يكتشف التصنيف من مشاعر المستخدم
    2. يجلب أبياتاً من poems_db.json المحلي
    3. يرسل لـ GPT ليختار ويشرح
    4. يُرجع النتيجة
    """

    # الخطوة 1+2: جلب الأبيات من الداتاست المحلي
    try:
        category, poems = get_poems_for_mood(req.user_input, count=20)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # الخطوة 3: GPT يختار ويشرح
    try:
        result = await get_mood_poems(req.user_input, category, poems)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ GPT: {str(e)}")

    # الخطوة 4: بناء الرد
    poem_entries = [
        PoemEntry(
            verse       = p.get("verse", ""),
            poet        = p.get("poet", "مجهول"),
            explanation = p.get("explanation", ""),
        )
        for p in result.get("poems", [])
    ]

    return MoodResponse(
        feeling_detected  = result.get("feeling_detected", ""),
        feeling_intensity = result.get("feeling_intensity", ""),
        category_used     = result.get("category_used", category),
        opening_line      = result.get("opening_line", ""),
        poems             = poem_entries,
        closing_line      = result.get("closing_line", ""),
    )


# =============================================================
# TODO: باقي الصفحات
# =============================================================
# @app.post("/api/write/generate")
# @app.post("/api/journey/explore")
# @app.post("/api/interpret/verses")














# # =============================================================
# # main.py — FastAPI entry point
# # تشغيل: uvicorn main:app --reload --port 8000
# # توثيق: http://localhost:8000/docs
# # =============================================================

# import os
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv

# from schemas import TreasuresRequest, TreasuresResponse, SiwarInfo
# from services.siwar_service import get_siwar_definition
# from services.ai_service import explain_word

# load_dotenv()

# app = FastAPI(title="بيت القصيد API", version="1.0.0")

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["http://localhost:5173", "http://localhost:5174",
# #                    "http://localhost:3000", "http://127.0.0.1:5173"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # مؤقتاً للتطوير
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ── فحص الصحة ─────────────────────────────────────────────────
# @app.get("/")
# async def root():
#     return {"status": "✅ يعمل"}


# @app.get("/health")
# async def health():
#     return {
#         "openai": "✅" if os.getenv("OPENAI_API_KEY") else "❌ مفقود",
#         "siwar":  "✅" if os.getenv("SIWAR_API_KEY")  else "❌ مفقود",
#     }


# # =============================================================
# # 🔌 كنوز الكلمات — POST /api/treasures/explain
# # =============================================================
# @app.post("/api/treasures/explain", response_model=TreasuresResponse)
# async def explain_arabic_word(req: TreasuresRequest):
#     """
#     1. يسأل معجم سوار
#     2. يبني البرومت
#     3. يرسل لـ GPT
#     4. يُرجع النتيجة للفرونت
#     """
#     # الخطوة 1: معجم سوار
#     siwar = await get_siwar_definition(req.word)

#     # الخطوة 2+3: GPT
#     try:
#         gpt_result = await explain_word(
#             word=req.word,
#             siwar_result=siwar,
#             verse=req.verse,
#             is_followup=req.is_followup,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"خطأ GPT: {str(e)}")

#     # الخطوة 4: رد منظم
#     return TreasuresResponse(
#         word          = req.word,
#         meaning       = gpt_result.get("meaning", ""),
#         poetic_usage  = gpt_result.get("poetic_usage", ""),
#         symbolism     = gpt_result.get("symbolism", ""),
#         example_verse = gpt_result.get("example_verse", ""),
#         simple_tip    = gpt_result.get("simple_tip", ""),
#         confidence    = gpt_result.get("confidence", "medium"),
#         siwar         = SiwarInfo(**siwar),
#         verse         = req.verse,
#     )


# # =============================================================
# # Endpoints الصفحات الأخرى (لاحقاً)
# # =============================================================
# # TODO: POST /api/mood/poems
# # TODO: POST /api/write/generate
# # TODO: POST /api/journey/explore
# # TODO: POST /api/interpret/verses