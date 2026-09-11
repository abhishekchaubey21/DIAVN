from .health import router as health_router
from .cases import router as cases_router
from .dealers import router as dealers_router
from .invoices import router as invoices_router
from .images import router as images_router
from .pipeline import router as pipeline_router
from .risk import router as risk_router
from .verification import router as verification_router

__all__ = [
    "health_router",
    "cases_router",
    "dealers_router",
    "invoices_router",
    "images_router",
    "pipeline_router",
    "risk_router",
    "verification_router"
]
