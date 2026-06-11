import time
from fastapi import APIRouter
from api.common.config import settings
from api.database.config.dto_base import SuccessResponse

router = APIRouter()

# Simple uptime counter reference
START_TIME = time.time()


@router.get("/health", response_model=SuccessResponse, summary="Perform API health check")
async def health_check():
    """FastAPI 서버의 상태와 가동 시간(uptime) 및 기본 설정을 조회하여 헬스체크를 수행합니다.

    Returns:
        SuccessResponse: 성공 상태값 및 애플리케이션 이름, 가동 시간, 디버그 모드 상태, 버전 정보 등이 담긴 DTO.
    """
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

