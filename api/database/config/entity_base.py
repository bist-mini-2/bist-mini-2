from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy ORM 엔티티 정의를 위한 공통 베이스 클래스입니다.

    비동기 속성 로딩을 지원하는 AsyncAttrs와 선언적 매핑을 지원하는 DeclarativeBase를 상속받습니다.
    """
    pass
