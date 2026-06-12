from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator, Annotated
from fastapi import Depends
from api.common.config import settings

# DB 커넥션 풀(비동기 데이터베이스 엔진) 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False
)

# ORM 작업 세션 생성
session_maker = async_sessionmaker(
    bind=engine,
    autoflush=True,
    autocommit=False
)


async def get_orm_session() -> AsyncGenerator[AsyncSession, None]:
    """ORM 작업 세션(AsyncSession)을 제공하는 비동기 제너레이터입니다.
    
    FastAPI Depends를 통해 매 요청마다 주입받아 사용하며, 
    정상 작동 시 commit을, 예외 발생 시 rollback을 일괄 수행하고 세션을 닫습니다.
    """
    orm_session = session_maker()
    try:
        yield orm_session
        await orm_session.commit()
    except Exception:
        await orm_session.rollback()
        raise
    finally:
        await orm_session.close()

# 의존성 주입을 위한 타입 에일리어스 정의
OrmSessionDep = Annotated[AsyncSession, Depends(get_orm_session)]
