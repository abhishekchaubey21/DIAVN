"""
Database connection and Supabase client configuration module.
In Phase 1, provides environment-grounded placeholders for database sessions and client init.
"""

from typing import Optional
from app.core.config import settings

def get_supabase_client():
    """
    Returns configured Supabase client if keys are present.
    Uses free tier Supabase project configuration.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        return None
    # In later phases, initialize supabase-py client
    return None

def get_db():
    """
    Dependency generator for PostgreSQL sessions (SQLAlchemy/asyncpg in later phases).
    """
    yield None
