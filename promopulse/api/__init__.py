from fastapi import APIRouter

from .health import router as health_router
from .users import router as users_router

api_router = APIRouter()

# Register sub-routers here
api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(users_router, prefix="", tags=["users"])
