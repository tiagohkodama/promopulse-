from fastapi import APIRouter

from promopulse.core.config import get_settings

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check():
    """
    Basic health check endpoint.

    Returns static OK + app metadata.
    Later this can be extended to check DB, queues, etc.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }
