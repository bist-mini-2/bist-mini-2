import logging
import uvicorn
import colorlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from api.common.config import settings
from api.common.exception_handler import register_exception_handler
from api.v1.api_router import api_router


class NoCacheStaticFiles(StaticFiles):
    """캐시 방지 헤더가 주입된 커스텀 StaticFiles 서브클래스입니다."""

    def file_response(self, *args, **kwargs) -> Response:
        """정적 파일 반환 시 캐시를 사용하지 않도록 헤더를 주입합니다.

        Args:
            *args: 부모 메서드에 전달될 위치 인자.
            **kwargs: 부모 메서드에 전달될 키워드 인자.

        Returns:
            Response: 캐시 방지 헤더가 추가된 HTTP 응답 객체.
        """
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


# ============================================
# Application Lifespan (Startup & Shutdown)
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn").info("Application Starting Up...")
    
    # 데이터베이스 테이블 자동 생성
    from api.database.config.entity_base import Base
    from api.database.config.dbsession import engine
    from api.v1.member.entity import MemberEntity
    
    async with engine.begin() as conn:
        # PostgreSQL인 경우 pgvector 익스텐션 자동 활성화
        if "postgresql" in settings.DATABASE_URL:
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    logging.getLogger("uvicorn").info("Application Shutting Down...")
    await engine.dispose()

# ============================================
# FastAPI Application Initialization
# ============================================
app = FastAPI(
    title=settings.APP_NAME,
    description="Basic FastAPI backend template designed with clean architecture.",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)


# ============================================
# Global Middleware (Cache Control)
# ============================================
@app.middleware("http")
async def add_cache_control_header(request: Request, call_next) -> Response:
    """모든 동적 API 요청에 캐시 방지 헤더를 강제 주입합니다.

    Args:
        request (Request): HTTP 요청 객체.
        call_next (Callable): 다음 미들웨어 또는 핸들러를 호출하는 콜백.

    Returns:
        Response: 캐시 방지 헤더가 적용된 HTTP 응답 객체.
    """
    response = await call_next(request)
    if request.url.path.startswith(settings.API_V1_STR):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ============================================
# Register global exception handlers
# ============================================
register_exception_handler(app)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production: allow only specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Static Files & Templates Mounting
# ============================================
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static assets directory with caching disabled
app.mount("/static", NoCacheStaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Initialize Jinja2 Templates engine
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ============================================
# Custom Color Logging Configuration
# ============================================
# Setup cleaner, colorized log stream outputs for console debugging
logger = logging.getLogger()
logger.handlers.clear()

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)-8s%(reset)s:     '
    '%(cyan)s%(name)s%(reset)s.%(yellow)s%(funcName)s()%(reset)s: '
    '%(green)s%(message)s%(reset)s',
    log_colors={
        'DEBUG': 'white',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
))
logger.addHandler(handler)
logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# ============================================
# API Routers Mounting
# ============================================
app.include_router(api_router, prefix=settings.API_V1_STR)

# ============================================
# HTML Dashboard Welcome Page Route
# ============================================
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    logging.getLogger(__name__).info("Root welcome portal page requested.")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.APP_NAME}
    )

# ============================================
# Local Development Execution Entry
# ============================================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
