from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator, Annotated
from fastapi import Depends
import logging

from api.common.config import settings

logger = logging.getLogger(__name__)

# DB 비동기 커넥션 풀(엔진) 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,  # 표준 logging 모듈로 제어하기 위해 False 설정
)

# 비동기 ORM 작업 세션 팩토리 생성
session_maker = async_sessionmaker(
    bind=engine,
    autoflush=True,
    autocommit=False
)


async def get_orm_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 종속성 주입용 비동기 ORM 세션(AsyncSession) 제너레이터입니다.

    요청별로 새로운 세션을 생성하여 제공하고, 처리가 정상 완료되면 트랜잭션을
    커밋하고 예외가 발생하면 롤백을 수행한 후 최종적으로 세션을 반납합니다.

    Yields:
        AsyncSession: 생성된 SQLAlchemy 비동기 세션 객체.

    Raises:
        Exception: 컨트롤러 또는 서비스 레이어 수행 도중 예외가 발생한 경우 롤백 후 예외를 전파합니다.
    """
    orm_session = session_maker()
    try:
        yield orm_session
        await orm_session.commit()
    except Exception as e:
        logger.error(f"Database transaction error, rolling back: {e}")
        await orm_session.rollback()
        raise
    finally:
        await orm_session.close()


# 의존성 주입을 위한 타입 별칭 정의
OrmSessionDep = Annotated[AsyncSession, Depends(get_orm_session)]
