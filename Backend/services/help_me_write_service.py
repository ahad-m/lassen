"""
خدمة ميزة "ساعدني أكتب" - جزء توليد الأبيات فقط.
مستخرجة من نوتبوك generating_using_gpt_only.ipynb
"""

from __future__ import annotations

import os
import re
import html
import json
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from openai import OpenAI
from supabase import Client, create_client

from HelpMeWrite_prompts import (
    HELP_WRITE_VALIDATE_SYSTEM_PROMPT,
    HELP_WRITE_VALIDATE_USER_PROMPT,
    HELP_WRITE_GENERATE_SYSTEM_PROMPT,
    HELP_WRITE_GENERATE_USER_PROMPT,
)

load_dotenv()

METERS = [
    "الطويل",
    "الكامل",
    "البسيط",
    "الوافر",
    "الخفيف",
    "الرجز",
    "الرمل",
    "السريع",
    "المنسرح",
    "الهزج",
    "المتقارب",
    "المتدارك",
    "المديد",
    "المضارع",
    "المقتضب",
    "المجتث",
]

METER_PATTERNS = {
    "الطويل": "فَعُولُنْ مَفَاعِيلُنْ فَعُولُنْ مَفَاعِلُنْ",
    "الكامل": "مُتَفَاعِلُنْ مُتَفَاعِلُنْ مُتَفَاعِلُنْ",
    "البسيط": "مُسْتَفْعِلُنْ فَاعِلُنْ مُسْتَفْعِلُنْ فَاعِلُنْ",
    "الوافر": "مُفَاعَلَتُنْ مُفَاعَلَتُنْ فَعُولُنْ",
    "الخفيف": "فَاعِلَاتُنْ مُسْتَفْعِلُنْ فَاعِلَاتُنْ",
    "الرجز": "مُسْتَفْعِلُنْ مُسْتَفْعِلُنْ مُسْتَفْعِلُنْ",
    "الرمل": "فَاعِلَاتُنْ فَاعِلَاتُنْ فَاعِلَاتُنْ",
    "السريع": "مُسْتَفْعِلُنْ مُسْتَفْعِلُنْ مَفْعُولَاتُ",
    "المنسرح": "مُسْتَفْعِلُنْ مَفْعُولَاتُ مُسْتَفْعِلُنْ",
    "الهزج": "مَفَاعِيلُنْ مَفَاعِيلُنْ",
    "المتقارب": "فَعُولُنْ فَعُولُنْ فَعُولُنْ فَعُولُنْ",
    "المتدارك": "فَاعِلُنْ فَاعِلُنْ فَاعِلُنْ فَاعِلُنْ",
    "المديد": "فَاعِلَاتُنْ فَاعِلُنْ فَاعِلَاتُنْ",
    "المضارع": "مَفَاعِيلُنْ فَاعِلَاتُنْ",
    "المقتضب": "مَفْعُولَاتُ مُسْتَفْعِلُنْ",
    "المجتث": "مُسْتَفْعِلُنْ فَاعِلَاتُنْ",
}


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY غير موجود في .env")
    return OpenAI(api_key=api_key)


def _model_name() -> str:
    return os.getenv("HELP_WRITE_MODEL", "gpt-4o-mini")


ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0610-\u061A\u06D6-\u06DC\u06DF-\u06E4\u06E7-\u06ED]")
ARABIC_LETTERS = re.compile(r"[\u0600-\u06FF]")
MIN_ARABIC_CHARS = 3
MATCH_INPUT_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")

EMBED_MODEL = os.getenv("WRITE_COMPLETE_EMBED_MODEL", "text-embedding-3-large")
EMBED_DIM = int(os.getenv("WRITE_COMPLETE_EMBED_DIM", "768"))
MATCH_THRESHOLD = float(os.getenv("WRITE_COMPLETE_MATCH_THRESHOLD", "0.87"))
LOOSE_MATCH_THRESHOLD = float(os.getenv("WRITE_COMPLETE_LOOSE_MATCH_THRESHOLD", "0.60"))
MIN_ALLOWED_SIMILARITY = float(os.getenv("WRITE_COMPLETE_MIN_SIMILARITY", "0.85"))
MATCH_COUNT = int(os.getenv("WRITE_COMPLETE_MATCH_COUNT", "24"))
TOP_K_CANDIDATES = int(os.getenv("WRITE_COMPLETE_TOP_K", "3"))
MAX_SEARCH_QUERIES = int(os.getenv("WRITE_COMPLETE_MAX_SEARCH_QUERIES", "4"))
ALDIWAN_FALLBACK_ENABLED = os.getenv("WRITE_COMPLETE_ENABLE_ALDIWAN_FALLBACK", "true").lower() == "true"
ALDIWAN_TOP_K = int(os.getenv("WRITE_COMPLETE_ALDIWAN_TOP_K", "2"))
ALDIWAN_MIN_SCORE = float(os.getenv("WRITE_COMPLETE_ALDIWAN_MIN_SCORE", "0.88"))
ALDIWAN_TIMEOUT_SEC = float(os.getenv("WRITE_COMPLETE_ALDIWAN_TIMEOUT_SEC", "12"))
ALDIWAN_MAX_RESULTS = int(os.getenv("WRITE_COMPLETE_ALDIWAN_MAX_RESULTS", "5"))
ALDIWAN_POEM_URL_PATTERN = re.compile(r"https?://(?:www\.)?aldiwan\.net/poem\d+\.html")
ALDIWAN_REQUIRE_EXACT_MATCH = os.getenv("WRITE_COMPLETE_ALDIWAN_REQUIRE_EXACT_MATCH", "true").lower() == "true"
ALDIWAN_MIN_EXACT_CHARS = int(os.getenv("WRITE_COMPLETE_ALDIWAN_MIN_EXACT_CHARS", "8"))

RPC_MATCH_VERSES = os.getenv("WRITE_COMPLETE_RPC_MATCH", "match_verses")
RPC_GET_FULL_POEM = os.getenv("WRITE_COMPLETE_RPC_FULL_POEM", "get_full_poem")

COL_VERSE_DISPLAY = os.getenv("WRITE_COMPLETE_COL_VERSE", "verse")
COL_POEM_ID = os.getenv("WRITE_COMPLETE_COL_POEM_ID", "poem_id")
COL_POET = os.getenv("WRITE_COMPLETE_COL_POET", "poet_name")
COL_METER = os.getenv("WRITE_COMPLETE_COL_METER", "poem_meter")
COL_ERA = os.getenv("WRITE_COMPLETE_COL_ERA", "era")


@lru_cache(maxsize=1)
def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL أو SUPABASE_KEY غير موجود في .env")
    return create_client(supabase_url, supabase_key)


def strip_diacritics(text: str) -> str:
    return ARABIC_DIACRITICS.sub("", (text or "")).strip()


def normalize_for_matching(text: str) -> str:
    """
    نفس normalization المستخدم لبناء verse_normalized في قاعدة البيانات.
    """
    normalized = str(text or "")
    normalized = normalized.replace("ى", "ي")
    normalized = normalized.replace("ة", "ه")
    normalized = normalized.replace("إ", "ا")
    normalized = normalized.replace("أ", "ا")
    normalized = normalized.replace("آ", "ا")
    normalized = normalized.replace("ٱ", "ا")
    normalized = normalized.replace("ـ", "")
    normalized = MATCH_INPUT_DIACRITICS.sub("", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _normalized_input_lines(text: str) -> set[str]:
    lines: set[str] = set()
    for raw_line in re.split(r"[\r\n]+", text or ""):
        cleaned = normalize_for_matching(raw_line)
        if cleaned:
            lines.add(cleaned)
    if lines:
        return lines
    one_line = normalize_for_matching(text)
    return {one_line} if one_line else set()


def _safe_text(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _call_tavily_search_aldiwan(query_text: str) -> list[dict[str, Any]]:
    api_key = (os.getenv("TAVILY_API_KEY") or "").strip()
    if not api_key:
        return []

    payload = {
        "api_key": api_key,
        "query": f"site:aldiwan.net/poem {query_text}",
        "max_results": max(1, ALDIWAN_MAX_RESULTS),
        "include_raw_content": False,
        "include_answer": False,
        "search_depth": "basic",
        "include_domains": ["aldiwan.net"],
    }
    req = Request(
        url="https://api.tavily.com/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=ALDIWAN_TIMEOUT_SEC) as response:
            raw = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []

    results = parsed.get("results")
    return results if isinstance(results, list) else []


def _extract_aldiwan_poem_urls(results: list[dict[str, Any]]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for item in results:
        if not isinstance(item, dict):
            continue
        candidate_url = _safe_text(item.get("url"), "")
        match = ALDIWAN_POEM_URL_PATTERN.search(candidate_url)
        if not match:
            continue
        poem_url = match.group(0)
        if poem_url in seen:
            continue
        seen.add(poem_url)
        urls.append(poem_url)
    return urls


def _extract_plain_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment or "")
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _fetch_aldiwan_poem(poem_url: str) -> dict[str, Any] | None:
    req = Request(
        url=poem_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LassenBot/1.0)"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=ALDIWAN_TIMEOUT_SEC) as response:
            page_html = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

    content_match = re.search(
        r'id="poem_content"[^>]*>(.*?)<div class="header-center">',
        page_html,
        flags=re.S,
    )
    if not content_match:
        return None

    content_html = content_match.group(1)
    verse_chunks = re.findall(r"<h3[^>]*>(.*?)</h3>", content_html, flags=re.S)
    verses: list[str] = []
    seen_norm: set[str] = set()
    for chunk in verse_chunks:
        verse_text = _extract_plain_text(chunk)
        if len(ARABIC_LETTERS.findall(verse_text)) < 4:
            continue
        norm = normalize_for_matching(verse_text)
        if not norm or norm in seen_norm:
            continue
        seen_norm.add(norm)
        verses.append(verse_text)

    if not verses:
        return None

    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', page_html)
    title = _safe_text(_extract_plain_text(title_match.group(1) if title_match else ""), "")
    poet_match = re.search(r'<meta name="author" content="([^"]+)"', page_html)
    poet = _safe_text(_extract_plain_text(poet_match.group(1) if poet_match else ""), "مجهول")

    return {
        "url": poem_url,
        "title": title,
        "poet": poet or "مجهول الهوية",
        "verses": verses,
    }


def _score_aldiwan_candidate(user_input: str, poem_verses: list[str]) -> float:
    input_lines = _normalized_input_lines(user_input)
    if not input_lines or not poem_verses:
        return 0.0

    best_score = 0.0
    for verse in poem_verses:
        verse_norm = normalize_for_matching(verse)
        if not verse_norm:
            continue
        for line in input_lines:
            if not line:
                continue
            if line in verse_norm or verse_norm in line:
                best_score = max(best_score, 1.0)
                continue
            ratio = SequenceMatcher(a=line, b=verse_norm).ratio()
            best_score = max(best_score, ratio)

    return round(max(0.0, min(1.0, best_score)), 4)


def _has_exact_aldiwan_match(user_input: str, poem_verses: list[str]) -> bool:
    input_lines = _normalized_input_lines(user_input)
    if not input_lines or not poem_verses:
        return False

    min_chars = max(4, ALDIWAN_MIN_EXACT_CHARS)
    strong_lines = [line for line in input_lines if len(ARABIC_LETTERS.findall(line)) >= min_chars]
    if not strong_lines:
        return False

    normalized_verses = [normalize_for_matching(v) for v in poem_verses]
    normalized_verses = [v for v in normalized_verses if v]
    if not normalized_verses:
        return False

    for line in strong_lines:
        if any((line in verse) or (verse in line) for verse in normalized_verses):
            return True
    return False


def find_poem_candidates_on_aldiwan(user_input: str, top_k: int = ALDIWAN_TOP_K) -> list[dict[str, Any]]:
    if not ALDIWAN_FALLBACK_ENABLED:
        return []

    queries = _split_search_queries(user_input)
    if not queries:
        return []

    discovered_urls: list[str] = []
    seen_urls: set[str] = set()
    for query in queries:
        results = _call_tavily_search_aldiwan(query)
        for poem_url in _extract_aldiwan_poem_urls(results):
            if poem_url in seen_urls:
                continue
            seen_urls.add(poem_url)
            discovered_urls.append(poem_url)
        if len(discovered_urls) >= max(4, top_k * 3):
            break

    if not discovered_urls:
        return []

    ranked: list[dict[str, Any]] = []
    for poem_url in discovered_urls:
        poem_data = _fetch_aldiwan_poem(poem_url)
        if not poem_data:
            continue
        has_exact_match = _has_exact_aldiwan_match(user_input, poem_data["verses"])
        if ALDIWAN_REQUIRE_EXACT_MATCH and not has_exact_match:
            continue
        score = _score_aldiwan_candidate(user_input, poem_data["verses"])
        if score < max(0.0, min(1.0, ALDIWAN_MIN_SCORE)):
            continue
        ranked.append(
            {
                "poem_url": poem_data["url"],
                "poem_title": poem_data["title"],
                "poet": poem_data["poet"],
                "similarity": score,
                "verses": poem_data["verses"],
            }
        )

    ranked.sort(key=lambda item: float(item.get("similarity") or 0.0), reverse=True)
    final_candidates: list[dict[str, Any]] = []
    input_lines = _normalized_input_lines(user_input)
    for idx, item in enumerate(ranked[: max(1, top_k)], start=1):
        poem_verses = []
        for verse_idx, verse in enumerate(item["verses"], start=1):
            verse_norm = normalize_for_matching(verse)
            is_match = verse_norm in input_lines or any(
                verse_norm and (verse_norm in user_line or user_line in verse_norm)
                for user_line in input_lines
            )
            poem_verses.append(
                {
                    "verse_index": verse_idx,
                    "verse": verse,
                    "is_input_match": is_match,
                }
            )

        final_candidates.append(
            {
                "rank": idx,
                "poem_verses": poem_verses,
                "meta": {
                    "poet": item.get("poet") or "مجهول",
                    "meter": "-",
                    "era": "-",
                    "similarity": float(item.get("similarity") or 0.0),
                },
                "matched_verse": poem_verses[0]["verse"] if poem_verses else None,
                "source": "web",
                "source_label": "الديوان",
            }
        )

    return final_candidates


def validate_complete_input(text: str) -> tuple[bool, str]:
    if not text or not text.strip():
        return False, "الرجاء إدخال شطر او بيت شعر."

    if len(text) > 2000:
        return False, "النص طويل جدًا. الرجاء تقليل المدخل قليلًا."

    arabic_chars = ARABIC_LETTERS.findall(normalize_for_matching(text))
    if not arabic_chars:
        return False, "النص غير مفهوم. الرجاء إدخال بيت شعر عربي."

    if len(arabic_chars) < MIN_ARABIC_CHARS:
        return False, "النص قصير جدًا. الرجاء إدخال شطر او بيت شعر كامل."

    text_no_spaces = re.sub(r"\s+", "", text)
    if text_no_spaces and (len(arabic_chars) / len(text_no_spaces) < 0.4):
        return False, "النص بلغة مختلفة، الرجاء كتابة نص عربي."

    return True, ""


def get_embedding(text: str) -> list[float]:
    response = _get_openai_client().embeddings.create(
        model=EMBED_MODEL,
        input=text,
        dimensions=EMBED_DIM,
    )
    return response.data[0].embedding


def _extract_unique_poem_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_poem: dict[str, dict[str, Any]] = {}
    for row in rows:
        poem_id_raw = row.get(COL_POEM_ID)
        poem_id = str(poem_id_raw).strip() if poem_id_raw is not None else ""
        if not poem_id:
            continue

        similarity_raw = row.get("similarity", 0)
        try:
            similarity = float(similarity_raw or 0)
        except (TypeError, ValueError):
            similarity = 0.0

        candidate = {
            "verse": _safe_text(row.get(COL_VERSE_DISPLAY), ""),
            "poem_id": poem_id,
            "poet": _safe_text(row.get(COL_POET), "مجهول"),
            "meter": _safe_text(row.get(COL_METER), "-"),
            "era": _safe_text(row.get(COL_ERA), "-"),
            "similarity": round(similarity, 4),
        }
        existing = best_by_poem.get(poem_id)
        if not existing or candidate["similarity"] > existing["similarity"]:
            best_by_poem[poem_id] = candidate

    return sorted(best_by_poem.values(), key=lambda item: item["similarity"], reverse=True)


def _split_search_queries(user_input: str) -> list[str]:
    """
    يدعم إدخال بيت/بيتين/نص أطول:
    - يجرّب النص كاملًا.
    - يجرّب كل سطر على حدة (حتى حد أقصى) لزيادة مرونة المطابقة.
    """
    normalized_full = normalize_for_matching(user_input)
    if not normalized_full:
        return []

    lines = [normalize_for_matching(line) for line in re.split(r"[\r\n]+", user_input or "")]
    lines = [line for line in lines if line]

    queries: list[str] = [normalized_full]
    for line in lines:
        if line not in queries:
            queries.append(line)
        if len(queries) >= max(1, MAX_SEARCH_QUERIES):
            break

    return queries


def _rpc_match_rows(query_text: str, match_count: int) -> list[dict[str, Any]]:
    query_embedding = get_embedding(query_text)
    response = _get_supabase_client().rpc(
        RPC_MATCH_VERSES,
        {"query_embedding": query_embedding, "match_count": match_count},
    ).execute()
    return response.data or []


def find_poem_candidates_in_db(verse: str, top_k: int = TOP_K_CANDIDATES) -> list[dict[str, Any]]:
    query_texts = _split_search_queries(verse)
    if not query_texts:
        return []

    all_rows: list[dict[str, Any]] = []
    match_count = max(MATCH_COUNT, top_k)
    for query_text in query_texts:
        all_rows.extend(_rpc_match_rows(query_text, match_count=match_count))

    if not all_rows:
        return []

    unique_poems = _extract_unique_poem_candidates(all_rows)
    if not unique_poems:
        return []

    min_similarity = max(0.0, min(1.0, MIN_ALLOWED_SIMILARITY))
    strict_threshold = max(MATCH_THRESHOLD, min_similarity)
    fallback_threshold = max(LOOSE_MATCH_THRESHOLD, min_similarity)

    strict = [item for item in unique_poems if item["similarity"] >= strict_threshold]
    if len(strict) >= top_k:
        return strict[:top_k]

    relaxed = [item for item in unique_poems if item["similarity"] >= fallback_threshold]
    return relaxed[:top_k]


def get_full_poem(poem_id: str) -> list[dict[str, Any]]:
    response = _get_supabase_client().rpc(
        RPC_GET_FULL_POEM,
        {"p_poem_id": str(poem_id)},
    ).execute()
    return response.data or []


def _build_poem_verses(poem_verses_rows: list[dict[str, Any]], input_lines: set[str]) -> list[dict[str, Any]]:
    poem_verses_rows_sorted = sorted(
        poem_verses_rows,
        key=lambda item: int(item.get("verse_index", 10**9)),
    )
    poem_verses: list[dict[str, Any]] = []
    for i, row in enumerate(poem_verses_rows_sorted, start=1):
        verse_text = (row.get("verse_text") or row.get("verse") or "").strip()
        if not verse_text:
            continue
        verse_index_raw = row.get("verse_index", i)
        try:
            verse_index = int(verse_index_raw)
        except Exception:
            verse_index = i

        verse_normalized = normalize_for_matching(verse_text)
        is_match = verse_normalized in input_lines
        if not is_match:
            is_match = any(
                verse_normalized and (verse_normalized in user_line or user_line in verse_normalized)
                for user_line in input_lines
            )

        poem_verses.append(
            {
                "verse_index": verse_index,
                "verse": verse_text,
                "is_input_match": is_match,
            }
        )
    return poem_verses


def help_me_write_complete_api_response(user_input: str) -> dict[str, Any]:
    is_valid, error_msg = validate_complete_input(user_input)
    if not is_valid:
        return {
            "success": False,
            "found": False,
            "poem_verses": [],
            "meta": {},
            "alternatives": [],
            "message": error_msg,
        }

    try:
        matched_candidates = find_poem_candidates_in_db(
            user_input.strip(),
            top_k=max(1, TOP_K_CANDIDATES),
        )
    except Exception as e:
        return {
            "success": False,
            "found": False,
            "poem_verses": [],
            "meta": {},
            "alternatives": [],
            "message": f"خطأ في البحث: {str(e)}",
        }

    if not matched_candidates:
        aldiwan_candidates = find_poem_candidates_on_aldiwan(
            user_input.strip(),
            top_k=max(1, ALDIWAN_TOP_K),
        )
        if aldiwan_candidates:
            primary = aldiwan_candidates[0]
            return {
                "success": True,
                "found": True,
                "poem_verses": primary.get("poem_verses", []),
                "meta": primary.get("meta", {}),
                "alternatives": aldiwan_candidates,
                "current_index": 0,
                "total_candidates": len(aldiwan_candidates),
                "message": "تم العثور على نتيجة من الديوان.",
            }

        return {
            "success": True,
            "found": False,
            "poem_verses": [],
            "meta": {},
            "alternatives": [],
            "message": "عذراً، لم نتمكن من العثور على القصيدة",
        }

    input_lines = _normalized_input_lines(user_input.strip())
    alternatives: list[dict[str, Any]] = []
    warnings: list[str] = []

    for idx, matched_verse in enumerate(matched_candidates, start=1):
        try:
            poem_verses_rows = get_full_poem(matched_verse["poem_id"])
        except Exception as e:
            warnings.append(f"تعذّر جلب القصيدة رقم {idx}: {str(e)}")
            poem_verses_rows = []

        poem_verses = _build_poem_verses(poem_verses_rows, input_lines)
        if not poem_verses:
            poem_verses = [
                {
                    "verse_index": 1,
                    "verse": matched_verse["verse"],
                    "is_input_match": True,
                }
            ]

        alternatives.append(
            {
                "rank": idx,
                "poem_verses": poem_verses,
                "meta": {
                    "poet": matched_verse.get("poet") or "مجهول",
                    "meter": matched_verse.get("meter") or "-",
                    "era": matched_verse.get("era") or "-",
                    "similarity": float(matched_verse.get("similarity") or 0.0),
                },
                "matched_verse": matched_verse.get("verse"),
                "source": "database",
                "source_label": "قاعدة البيانات",
            }
        )

    if not alternatives:
        return {
            "success": True,
            "found": False,
            "poem_verses": [],
            "meta": {},
            "alternatives": [],
            "message": "تعذّر العثور على قصائد قريبة.",
        }

    primary = alternatives[0]

    return {
        "success": True,
        "found": True,
        "poem_verses": primary["poem_verses"],
        "meta": primary["meta"],
        "alternatives": alternatives,
        "current_index": 0,
        "total_candidates": len(alternatives),
        "message": " | ".join(warnings) if warnings else None,
    }


def validate_idea(idea_text: str) -> tuple[bool, str]:
    """
    تحقق ثنائي الطبقات:
    1) قواعد سريعة محلية
    2) تحقق دلالي عبر GPT (YES/NO)
    """
    idea_clean = (idea_text or "").strip()

    # layer 1 - local rules
    if not idea_clean:
        return False, "الرجاء كتابة فكرة للبدء."

    if len(idea_clean) < 3:
        return False, "الرجاء كتابة فكرة أوضح."

    arabic_chars = [c for c in idea_clean if "\u0600" <= c <= "\u06FF"]

    if len(arabic_chars) < 2:
        return False, "الرجاء كتابة فكرتك باللغة العربية."

    if len(arabic_chars) / max(1, len(idea_clean)) < 0.3:
        return False, "لم نفهم فكرتك — الرجاء كتابة جملة عربية واضحة."

    # layer 2 - semantic check with GPT
    response = _get_openai_client().chat.completions.create(
        model=_model_name(),
        messages=[
            {"role": "system", "content": HELP_WRITE_VALIDATE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": HELP_WRITE_VALIDATE_USER_PROMPT.format(idea_text=idea_clean),
            },
        ],
        temperature=0,
        max_tokens=5,
    )

    answer = (response.choices[0].message.content or "").strip().upper()
    if "YES" not in answer:
        return False, "ما فهمنا فكرتك — الرجاء كتابة جملة واضحة."

    return True, idea_clean


def generate_verses(idea_text: str, meter_name: str, num_verses: int = 4) -> dict[str, Any]:
    """
    توليد أبيات شعرية بالفصحى على بحر محدد.
    """
    pattern = METER_PATTERNS.get(meter_name, "")
    pattern_line = f"Taf'ila pattern: {pattern}" if pattern else ""

    prompt = HELP_WRITE_GENERATE_USER_PROMPT.format(
        idea_text=idea_text,
        meter_name=meter_name,
        pattern_line=pattern_line,
        num_verses=num_verses,
    )

    response = _get_openai_client().chat.completions.create(
        model=_model_name(),
        messages=[
            {"role": "system", "content": HELP_WRITE_GENERATE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.75,
    )

    raw_output = (response.choices[0].message.content or "").strip()
    verses = [
        line.strip()
        for line in raw_output.split("\n")
        if line.strip() and len(line.strip()) > 10
    ]

    return {
        "success": True,
        "verses": verses[:num_verses],
        "meter": meter_name,
    }


def help_me_write_generate_api_response(idea_text: str, meter_num: int = 1, num_verses: int = 4) -> dict[str, Any]:
    """
    الاستجابة الجاهزة للـ API لميزة ساعدني أكتب (توليد فقط).
    """
    if not 1 <= meter_num <= len(METERS):
        return {"success": False, "message": f"meter_num must be 1–{len(METERS)}"}

    meter_name = METERS[meter_num - 1]

    is_valid, result = validate_idea(idea_text)
    if not is_valid:
        return {"success": False, "message": result}

    generated = generate_verses(result, meter_name, num_verses)
    return {
        "success": True,
        "meter": generated["meter"],
        "verses": generated["verses"],
        "message": None,
    }


# اسم توافقي مختصر للاستخدام في main.py
def generate_poetry_response(idea: str, meter_num: int = 1, num_verses: int = 4) -> dict[str, Any]:
    return help_me_write_generate_api_response(
        idea_text=idea,
        meter_num=meter_num,
        num_verses=num_verses,
    )


def complete_poem_response(verse: str) -> dict[str, Any]:
    return help_me_write_complete_api_response(verse)