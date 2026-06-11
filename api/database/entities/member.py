from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean

from api.database.config.entity_base import Base


class MemberEntity(Base):
    """회원(Member) 정보를 나타내는 SQLAlchemy ORM Entity 클래스입니다.

    이 클래스는 데이터베이스의 `member` 테이블과 매핑되며,
    회원의 계정 ID, 이름, 비밀번호, 이메일, 활성화 여부 및 역할을 관리합니다.

    Attributes:
        mid (str): 회원 아이디 (Primary Key, 최대 20자)
        mname (str): 회원 이름 (최대 20자)
        mpassword (str): 암호화된 비밀번호 (최대 255자)
        memail (str): 이메일 주소 (최대 255자, 고유값)
        menabled (bool): 계정 활성화 여부 (기본값: True)
        mrole (str): 회원 역할/권한 (예: ROLE_USER, ROLE_ADMIN, 최대 20자)
    """
    __tablename__ = "member"

    mid: Mapped[str] = mapped_column("mid", String(20), primary_key=True)
    mname: Mapped[str] = mapped_column("mname", String(20), nullable=False)
    mpassword: Mapped[str] = mapped_column("mpassword", String(255), nullable=False)
    memail: Mapped[str] = mapped_column("memail", String(255), unique=True, nullable=False)
    menabled: Mapped[bool] = mapped_column("menabled", Boolean, default=True, nullable=False)
    mrole: Mapped[str] = mapped_column("mrole", String(20), nullable=False)
