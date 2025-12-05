from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from promopulse.api import api_router
from promopulse.core.config import get_settings
from promopulse.core.logging import setup_logging


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context for startup/shutdown.

    This is where we'll later:
    - Initialize DB connections
    - Initialize queues/workers
    - Warm up caches, etc.
    """
    setup_logging()
    settings = get_settings()
    logger.info("Application starting up", extra={"correlation_id": "-"})

    # Startup logic here
    yield
    # Shutdown logic here

    logger.info("Application shutting down", extra={"correlation_id": "-"})


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
    )

    # Mount API routers
    app.include_router(api_router)

    return app


app = create_app()
