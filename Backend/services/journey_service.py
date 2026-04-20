"""
خدمة رحلة عبر الزمن:
- تسحب قصيدة واحدة لكل عصر من Supabase حسب الموضوع المختار.
- تعيد الأبيات مرتبة عبر verse_index.
- تستدعي LLM لتحليل التشابه والاختلاف الجوهري بين العصور.
"""

from __future__ import annotations

import json
import os
import random
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from JourneyThroughTime_prompts import (
    JOURNEY_SUMMARY_SYSTEM_PROMPT,
    JOURNEY_SUMMARY_USER_PROMPT,
)
from services.supabase_client import get_supabase_client

load_dotenv()

GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY غير موجود في .env")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


TARGET_ERAS = [
    ("jahili", "العصر الجاهلي"),
    ("abbasi", "العصر العباسي"),
    ("modern", "العصر الحديث"),
]

THEME_MAP: dict[str, list[str]] = {
    "غزل": ["قصيدة غزل"],
    "عتاب": ["قصيدة عتاب"],
    "حزينه": ["قصيدة حزينه"],
    "هجاء": ["قصيدة هجاء"],
    "شوق": ["قصيدة شوق"],
    "فراق": ["قصيدة فراق"],
    "مدح": ["قصيدة مدح"],
    "رومنسيه": ["قصيدة رومنسيه"],
}


def _normalize_theme(theme: str) -> str:
    t = (theme or "").strip()
    alias = {
        "حزن": "حزينه",
        "الحزن": "حزينه",
        "حزين": "حزينه",
        "الحزينه": "حزينه",
        "الغزل": "غزل",
        "العتاب": "عتاب",
        "عتب": "عتاب",
        "المدح": "مدح",
        "المدح": "مدح",
        "الهجاء": "هجاء",
        "الشوق": "شوق",
        "الفراق": "فراق",
        "الرومنسية": "رومنسيه",
        "الرومانسية": "رومنسيه",
        "رومانسية": "رومنسيه",
    }
    return alias.get(t, t)


def _safe_text(value: Any, default: str = "غير معروف") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _group_rows_by_poem(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        poem_id = row.get("poem_id")
        if not poem_id:
            continue
        grouped.setdefault(poem_id, []).append(row)

    for poem_id in grouped:
        grouped[poem_id].sort(key=lambda r: r.get("verse_index") or 0)

    return grouped


def _build_era_entry(poem_rows: list[dict[str, Any]], fallback_used: bool) -> dict[str, Any]:
    first = poem_rows[0] if poem_rows else {}
    verses = []
    for r in poem_rows:
        v = _safe_text(r.get("verse"), "")
        if v:
            verses.append(v)

    preview = verses[0] if verses else "لا تتوفر أبيات في هذه القصيدة."

    return {
        "poem_id": first.get("poem_id"),
        "poem_title": _safe_text(first.get("poem_title"), "بدون عنوان"),
        "poet_name": _safe_text(first.get("poet_name"), "شاعر غير معروف"),
        "poem_meter": _safe_text(first.get("poem_meter"), "غير محدد"),
        "poem_theme": _safe_text(first.get("poem_theme"), "غير مصنف"),
        "verses": verses[:8],
        "cinematic_note": f"يبدأ المشهد بهذا البيت: «{preview}»",
        "fallback_used": fallback_used,
    }


def _pick_random_poem(
    grouped_poems: dict[str, list[dict[str, Any]]],
    excluded_poem_ids: set[str],
) -> list[dict[str, Any]] | None:
    if not grouped_poems:
        return None

    available_ids = [pid for pid in grouped_poems.keys() if pid not in excluded_poem_ids]
    if not available_ids:
        available_ids = list(grouped_poems.keys())

    poem_id = random.choice(available_ids)
    return grouped_poems[poem_id]


def _pick_poem_for_era(
    era_label: str,
    theme_labels: list[str],
    excluded_poem_ids: set[str] | None = None,
) -> tuple[dict[str, Any] | None, bool]:
    """
    يحاول أولًا بعصر + موضوع.
    إذا لم يجد، يسقط شرط الموضوع ويجلب قصيدة من نفس العصر.
    """
    supabase = get_supabase_client()
    base_select = "poem_id, verse_index, verse, poem_title, poet_name, poet_era, poem_meter, poem_theme"

    excluded_poem_ids = excluded_poem_ids or set()

    # 1) عصر + موضوع
    strict_rows = (
        supabase.table("poetry_verses")
        .select(base_select)
        .eq("poet_era", era_label)
        .in_("poem_theme", theme_labels)
        .order("poem_id")
        .order("verse_index")
        .limit(2500)
        .execute()
        .data
        or []
    )

    grouped_strict = _group_rows_by_poem(strict_rows)
    poem_rows = _pick_random_poem(grouped_strict, excluded_poem_ids)
    if poem_rows:
        return _build_era_entry(poem_rows, fallback_used=False), False

    # 2) fallback: عصر فقط
    fallback_rows = (
        supabase.table("poetry_verses")
        .select(base_select)
        .eq("poet_era", era_label)
        .order("poem_id")
        .order("verse_index")
        .limit(2500)
        .execute()
        .data
        or []
    )

    grouped_fallback = _group_rows_by_poem(fallback_rows)
    poem_rows = _pick_random_poem(grouped_fallback, excluded_poem_ids)
    if poem_rows:
        return _build_era_entry(poem_rows, fallback_used=True), True

    return None, False


async def _analyze_journey(theme: str, eras_payload: list[dict[str, Any]]) -> dict[str, Any]:
    eras_for_llm: list[dict[str, Any]] = []
    for era in eras_payload:
        eras_for_llm.append(
            {
                "era_label": era.get("era_label"),
                "poet_name": era.get("poet_name"),
                "poem_title": era.get("poem_title"),
                "poem_theme": era.get("poem_theme"),
                "verses": era.get("verses", []),
            }
        )

    user_msg = JOURNEY_SUMMARY_USER_PROMPT.format(
        theme=theme,
        eras_block=json.dumps(eras_for_llm, ensure_ascii=False, indent=2),
    )

    response = await _get_client().chat.completions.create(
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

    if not isinstance(result.get("similarities"), list):
        result["similarities"] = []
    result["core_difference"] = str(result.get("core_difference", "")).strip()
    result["final_line"] = str(result.get("final_line", "")).strip() or "هذه نهاية الرحلة عبر الزمن."

    return result


async def build_time_journey(theme: str, exclude_poem_ids: list[str] | None = None) -> dict[str, Any]:
    normalized_theme = _normalize_theme(theme)
    theme_labels = THEME_MAP.get(normalized_theme)
    if not theme_labels:
        raise ValueError("الموضوع غير مدعوم. المواضيع المتاحة: غزل، عتاب، حزينه، هجاء، شوق، فراق، مدح، رومنسيه.")

    excluded_poem_ids = {str(pid) for pid in (exclude_poem_ids or []) if str(pid).strip()}

    eras_result: list[dict[str, Any]] = []
    warnings: list[str] = []

    for era_key, era_label in TARGET_ERAS:
        era_poem, used_fallback = _pick_poem_for_era(era_label, theme_labels, excluded_poem_ids)

        if not era_poem:
            warnings.append(f"لم نجد قصيدة متاحة في {era_label}.")
            eras_result.append(
                {
                    "era_key": era_key,
                    "era_label": era_label,
                    "poem_id": None,
                    "poem_title": "لا توجد بيانات",
                    "poet_name": "غير متوفر",
                    "poem_meter": "غير متوفر",
                    "poem_theme": "غير متوفر",
                    "verses": ["تعذر العثور على قصيدة لهذا العصر."],
                    "cinematic_note": "هذا المشهد فارغ بسبب نقص البيانات.",
                    "fallback_used": False,
                }
            )
            continue

        if used_fallback:
            warnings.append(
                f"في {era_label} لم نجد قصيدة مصنفة مباشرة تحت '{normalized_theme}'، "
                "فعرضنا قصيدة من نفس العصر كبديل."
            )

        eras_result.append(
            {
                "era_key": era_key,
                "era_label": era_label,
                **era_poem,
            }
        )

    summary = await _analyze_journey(normalized_theme, eras_result)

    return {
        "status": "ok",
        "selected_theme": normalized_theme,
        "intro_line": f"الآن نبدأ رحلة عبر الزمن لرؤية التعبير عن {normalized_theme} عبر العصور.",
        "eras": eras_result,
        "summary": summary,
        "warnings": warnings,
    }
    