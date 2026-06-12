from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy ORM Entity 클래스를 정의할 때 사용하는 비동기 매핑 기본 클래스입니다."""
    pass
