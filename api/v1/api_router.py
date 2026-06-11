from fastapi import APIRouter
from api.v1.endpoints import health
from api.v1.auth.endpoints import router as auth_router

api_router = APIRouter()

# Register endpoint routers under API v1
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth_router)


