from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "DIAVN Backend"
    API_V1_STR: str = "/api/v1"
    
    # Supabase / PostgreSQL Database settings (Free Tier)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # Supabase Storage configuration
    SUPABASE_INVOICE_BUCKET: str = "invoices"
    SUPABASE_INSTALLATION_IMAGES_BUCKET: str = "installation-images"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB upload limit
    
    # Phase 4 Imaging Forensics Parameters
    MAX_INSTALLATION_DISTANCE_KM: float = 1.0  # Max distance from claimed location (km)
    PHASH_NEAR_MATCH_THRESHOLD: int = 6        # Conservative Hamming distance threshold for 64-bit pHash
    
    # Phase 5 Deep Visual Feature Embedding Parameters
    EMBEDDING_MODEL_NAME: str = "resnet18"
    EMBEDDING_DIMENSION: int = 512
    EMBEDDING_SIMILARITY_THRESHOLD: float = 0.85  # Configurable provisional threshold
    EMBEDDING_TOP_K: int = 5
    
    # Gemini AI settings (Free Tier Only)
    # Recommended free-tier models: 'gemini-2.5-flash' or 'gemini-1.5-flash'
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Phase 9 Alerts & Workflow Automation Parameters
    DIAVN_WEBHOOK_SECRET: str = "diavn-default-shared-secret-for-n8n-auth"
    N8N_WEBHOOK_URL: Optional[str] = "http://localhost:5678/webhook/diavn-events"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    WORKFLOW_DISPATCH_ENABLED: bool = True
    WORKFLOW_MAX_RETRIES: int = 3
    WORKFLOW_POLL_INTERVAL_SEC: float = 5.0

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
