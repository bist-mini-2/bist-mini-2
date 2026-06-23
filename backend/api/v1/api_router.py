from fastapi import APIRouter
from api.v1.health.endpoints import router as health_router
from api.v1.auth.endpoints import router as auth_router
from api.v1.member.endpoints import router as member_router
from api.v1.chat.endpoints import router as chat_router
from api.v1.research_gap.endpoints import router as research_gap_router
from api.v1.gems.endpoints import router as gems_router
from api.v1.notification.endpoints import router as notification_router
from api.v1.similarity_search.endpoints import router as similarity_search_router
from api.v1.defense_arena.endpoints import router as defense_arena_router

api_router = APIRouter()

# Register endpoint routers under API v1
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(member_router)
api_router.include_router(chat_router)
api_router.include_router(research_gap_router)
api_router.include_router(gems_router)
api_router.include_router(notification_router)
api_router.include_router(similarity_search_router)
api_router.include_router(defense_arena_router)
