"""
عميل Supabase مشترك لخدمات الباك إند.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_supabase_client():
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError(
            "حزمة supabase غير مثبتة. ثبّت الحزمة: pip install supabase"
        ) from exc

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "إعدادات Supabase ناقصة. تأكد من وجود SUPABASE_URL و "
            "SUPABASE_SERVICE_ROLE_KEY (أو SUPABASE_KEY / SUPABASE_ANON_KEY)."
        )

    return create_client(supabase_url, supabase_key)