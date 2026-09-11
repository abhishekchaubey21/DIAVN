import logging
from typing import Optional
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

_gemini_client: Optional[genai.Client] = None


def get_gemini_client() -> Optional[genai.Client]:
    """
    Initializes and returns the official Google GenAI client (Free Tier).
    Returns None if GEMINI_API_KEY is not configured.
    """
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client

    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY is not configured. Invoice extraction will operate in graceful fallback mode.")
        return None

    try:
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Initialized Google GenAI client for Gemini Free Tier.")
        return _gemini_client
    except Exception as e:
        logger.warning(f"Failed to initialize Google GenAI client: {e}")
        return None
