import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Returns standard Supabase client with anon key.
    Returns None if credentials are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.info("Supabase URL / ANON_KEY not configured. Database/Storage operating in local fallback mode.")
        return None

    try:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        return _supabase_client
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase client: {e}")
        return None


def get_supabase_admin_client() -> Optional[Client]:
    """
    Returns backend-only Supabase client with service_role key.
    Used exclusively in backend for private storage bucket operations and admin actions.
    NEVER exposed to frontend.
    """
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.info("Supabase SERVICE_ROLE_KEY not configured. Private storage operating in local fallback mode.")
        return None

    try:
        _supabase_admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        return _supabase_admin_client
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase admin client: {e}")
        return None
