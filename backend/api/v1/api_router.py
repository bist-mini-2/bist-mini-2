from fastapi import APIRouter
from api.v1.health.endpoints import router as health_router
from api.v1.auth.endpoints import router as auth_router
from api.v1.member.endpoints import router as member_router
from api.v1.cs.endpoints import router as cs_router
from api.v1.astronomy.controller import router as astronomy_router
from api.v1.bio.controller import router as bio_router
from api.v1.chat.controller import router as chat_router
from api.v1.research_gap.endpoints import router as research_gap_router
from api.v1.gems.endpoints import router as gems_router

api_router = APIRouter()

# Register endpoint routers under API v1
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(member_router)
api_router.include_router(cs_router)
api_router.include_router(astronomy_router)
api_router.include_router(bio_router)
api_router.include_router(chat_router)
api_router.include_router(research_gap_router)
api_router.include_router(gems_router)

