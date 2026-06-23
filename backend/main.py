import asyncio
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
    
    # Uvicorn 핫리로드 시 SSE 커넥션 교착(hang) 방지를 위한 시그널 핸들러 체이닝
    import signal
    from api.v1.notification.notifier import notification_broadcaster
    
    original_sigint = signal.getsignal(signal.SIGINT)
    original_sigterm = signal.getsignal(signal.SIGTERM)
    
    def custom_signal_handler(signum, frame):
        logging.getLogger("uvicorn").info(f"Signal {signum} caught. Closing notification broadcaster immediately...")
        try:
            notification_broadcaster.close()
        except Exception:
            pass
        if signum == signal.SIGINT and callable(original_sigint):
            original_sigint(signum, frame)
        elif signum == signal.SIGTERM and callable(original_sigterm):
            original_sigterm(signum, frame)
            
    try:
        signal.signal(signal.SIGINT, custom_signal_handler)
        signal.signal(signal.SIGTERM, custom_signal_handler)
    except ValueError:
        # 메인 스레드가 아닐 경우 대비
        pass
    
    # 데이터베이스 테이블 자동 생성
    from api.database.config.entity_base import Base
    from api.database.config.dbsession import engine
    from api.v1.member.entity import MemberEntity
    from api.v1.research_gap.entity import ResearchGapTaskEntity
    from api.v1.chat.entity import ChatSessionEntity
    from api.v1.gems.entity import GemEntity
    from api.v1.notification.entity import NotificationEntity
    from api.v1.defense_arena.entity import DefenseArenaSessionEntity, DefenseArenaChunkEntity, DefenseHistoryEntity
    
    try:
        async with engine.begin() as conn:
            # PostgreSQL인 경우 pgvector 익스텐션 자동 활성화
            if "postgresql" in settings.DATABASE_URL:
                from sqlalchemy import text
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await conn.execute(text("ALTER TABLE research_gap_task ADD COLUMN IF NOT EXISTS translated_result JSON;"))
            await conn.run_sync(Base.metadata.create_all)
        logging.getLogger("uvicorn").info("Database tables initialized successfully.")
    except Exception as e:
        logging.getLogger("uvicorn").error(f"Database initialization deferred (server offline?): {e}")

    # 30분 미활동 보안 세션 소거 백그라운드 데몬 기동
    async def cleanup_daemon():
        while True:
            try:
                await asyncio.sleep(60) # 1분마다 주기적 스캔
                from api.v1.defense_arena.services import DefenseArenaService
                from api.v1.defense_arena.dao import DefenseArenaDao
                from api.database.config.dbsession import session_maker
                async with session_maker() as session:
                    dao = DefenseArenaDao(session)
                    service = DefenseArenaService(dao)
                    await service.wipe_out_expired_sessions(expire_minutes=30)
                    await session.commit()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.getLogger("uvicorn").error(f"Error in cleanup_daemon: {e}")

    cleanup_task = asyncio.create_task(cleanup_daemon())
        
    yield
    logging.getLogger("uvicorn").info("Application Shutting Down...")
    cleanup_task.cancel()
    
    try:
        from api.v1.notification.notifier import notification_broadcaster
        notification_broadcaster.close()
    except Exception as e:
        logging.getLogger("uvicorn").error(f"Error closing notification broadcaster: {e}")
    await engine.dispose()
    
    # 미종료된 asyncio 백그라운드 태스크들을 강제 취소하여 uvicorn 리로드 대기 현상을 완전히 방지
    try:
        current_task = asyncio.current_task()
        pending_tasks = [t for t in asyncio.all_tasks() if t is not current_task and t is not cleanup_task]
        if pending_tasks:
            logging.getLogger("uvicorn").info(f"Cancelling {len(pending_tasks)} pending background tasks...")
            for task in pending_tasks:
                task.cancel()
            # CancelledError가 전파될 때까지 대기
            await asyncio.gather(*pending_tasks, return_exceptions=True)
    except Exception as e:
        logging.getLogger("uvicorn").error(f"Error cancelling pending tasks: {e}")

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
    from api.v1.health.endpoints import get_dashboard_context
    context = await get_dashboard_context(request)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

# ============================================
# Local Development Execution Entry
# ============================================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        timeout_graceful_shutdown=2
    )
