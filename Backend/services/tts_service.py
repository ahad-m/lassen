"""
خدمة تحويل النص إلى صوت لميزة رحلة عبر الزمن عبر ElevenLabs.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"المتغير '{name}' غير موجود")
    return value


@lru_cache(maxsize=1)
def _tts_config() -> dict[str, str]:
    return {
        "api_key": _required_env("ELEVENLABS_API_KEY"),
        "voice_id": _required_env("ELEVENLABS_VOICE_ID"),
        "model_id": (os.getenv("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2").strip(),
    }


def _build_request_body(text: str, model_id: str) -> bytes:
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.35,
            "use_speaker_boost": True,
        },
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def synthesize_journey_speech(text: str) -> dict[str, str]:
    text = (text or "").strip()
    if not text:
        raise ValueError("النص المطلوب تحويله إلى صوت فارغ.")

    cfg = _tts_config()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}"
    request = urllib.request.Request(
        url=url,
        data=_build_request_body(text, cfg["model_id"]),
        method="POST",
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": cfg["api_key"],
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            audio_bytes = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"فشل ElevenLabs ({exc.code}): {body[:220]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"تعذّر الاتصال بخدمة ElevenLabs: {exc.reason}") from exc

    if not audio_bytes:
        raise RuntimeError("لم ترجع خدمة ElevenLabs أي صوت.")

    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    return {
        "audio_base64": audio_b64,
        "mime_type": "audio/mpeg",
    }