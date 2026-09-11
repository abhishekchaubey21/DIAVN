import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.security import RateLimitMiddleware
from app.api.health import router as health_router
from app.api.cases import router as cases_router
from app.api.dealers import router as dealers_router
from app.api.invoices import router as invoices_router
from app.api.images import router as images_router
from app.api.pipeline import router as pipeline_router
from app.api.risk import router as risk_router
from app.api.verification import router as verification_router
from app.api.relationships import router as relationships_router
from app.api.workflow import router as workflow_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Dealer Integrity & Asset Verification Network (DIAVN) - Backend API Foundation (Security Hardened)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 1. Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# 2. Strict CORS Configuration (Explicit Whitelist, no wildcard with credentials)
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if settings.FRONTEND_BASE_URL and settings.FRONTEND_BASE_URL not in allowed_origins:
    allowed_origins.append(settings.FRONTEND_BASE_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 3. Security Response Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# 4. Global Exception Masking (Zero Stack Trace Leakage)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status_code": exc.status_code}
        )
    logger.error(f"Unhandled server exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred during request processing. Details have been logged securely."
        }
    )

# Include required top-level endpoints
app.include_router(health_router)
app.include_router(cases_router)
app.include_router(dealers_router)
app.include_router(invoices_router)
app.include_router(images_router)
app.include_router(pipeline_router)
app.include_router(risk_router)
app.include_router(verification_router)
app.include_router(relationships_router)
app.include_router(workflow_router)

# Also expose under /api/v1 prefix for clean API versioning
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(dealers_router, prefix=settings.API_V1_STR)
app.include_router(invoices_router, prefix=settings.API_V1_STR)
app.include_router(images_router, prefix=settings.API_V1_STR)
app.include_router(pipeline_router, prefix=settings.API_V1_STR)
app.include_router(risk_router, prefix=settings.API_V1_STR)
app.include_router(verification_router, prefix=settings.API_V1_STR)
app.include_router(relationships_router, prefix=settings.API_V1_STR)
app.include_router(workflow_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "service": "diavn-backend",
        "version": "0.1.0",
        "status": "online",
        "docs": "/docs"
    }
