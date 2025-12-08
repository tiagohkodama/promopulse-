from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from sqlalchemy import text

from promopulse.api import api_router
from promopulse.core.config import get_settings
from promopulse.core.logging import setup_logging
from promopulse.db import get_engine

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

    # Optional: DB connectivity sanity check
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info(
            "Database connectivity check succeeded",
            extra={"correlation_id": "-"},
        )
    except Exception:
        logger.exception(
            "Database connectivity check failed",
            extra={"correlation_id": "-"},
        )
        # Optionally: raise here to hard-fail startup

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
