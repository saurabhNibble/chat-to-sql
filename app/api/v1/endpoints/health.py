from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.db.connection import ping_database
from app.models.query import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service & Database Health Probe",
    description="Check the liveness and readiness of the service and its underlying PostgreSQL connection.",
    responses={
        status.HTTP_200_OK: {"description": "Service and database healthy"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unreachable"},
    },
)
def check_health():
    is_healthy = ping_database()
    if not is_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL database is currently unreachable.",
        )

    return HealthResponse(
        status="ok",
        database="connected",
        version=settings.VERSION,
    )
