from fastapi import APIRouter
from api.v1.health.endpoints import router as health_router
from api.v1.auth.endpoints import router as auth_router
from api.v1.member.endpoints import router as member_router

api_router = APIRouter()

# Register endpoint routers under API v1
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(member_router)

