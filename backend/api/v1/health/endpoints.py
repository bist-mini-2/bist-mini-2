import time
from fastapi import APIRouter
from api.common.config import settings
from api.database.config.dto_base import SuccessResponse

router = APIRouter(prefix="/system", tags=["System"])

# Simple uptime counter reference
START_TIME = time.time()


@router.get("/health", response_model=SuccessResponse, summary="Perform API health check")
async def health_check():
    """FastAPI 서버의 상태와 가동 시간(uptime) 및 기본 설정을 조회하여 헬스체크를 수행합니다."""
    uptime = time.time() - START_TIME
    return SuccessResponse(
        data={
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "environment": settings.ENV,
            "uptime_seconds": round(uptime, 2),
            "debug_mode": settings.DEBUG,
            "version": "1.0.0"
        }
    )
