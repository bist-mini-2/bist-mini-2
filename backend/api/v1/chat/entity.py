from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func
from api.database.config.entity_base import Base


class ChatSessionEntity(Base):
    """채팅방(세션) 메타데이터 엔티티.

    방의 소유자와 제목 등 메타데이터만 관리하며,
    방 안의 실제 대화 내용은 AsyncPostgresSaver가 thread_id(=session_id)별로 별도 저장한다.
    """
    __tablename__ = "chat_session"

    session_id: Mapped[str] = mapped_column("session_id", String(36), primary_key=True)  # UUID
    member_id: Mapped[str] = mapped_column("member_id", String(20), nullable=False)       # 소유자(mid)
    title: Mapped[str] = mapped_column("title", String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, server_default=func.now())
