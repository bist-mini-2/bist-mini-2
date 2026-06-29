from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer, ForeignKey, func
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

class ChatSourceEntity(Base):
    """채팅 답변의 참고 논문(출처) 엔티티.

    어느 방(session_id)의 몇 번째 메시지(message_index)에 대한 출처인지 기록한다.
    방이 삭제되면 ON DELETE CASCADE로 함께 삭제된다.
    """
    __tablename__ = "chat_source"

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        "session_id",
        String(36),
        ForeignKey("chat_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    message_index: Mapped[int] = mapped_column("message_index", Integer, nullable=False)
    arxiv_id: Mapped[str] = mapped_column("arxiv_id", String(50), nullable=False)
    title: Mapped[str] = mapped_column("title", String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column("summary", String(500), nullable=True)  
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, server_default=func.now())


class ChatWebSourceEntity(Base):
    """채팅 답변의 참고 웹페이지(출처) 엔티티.

    어느 방(session_id)의 몇 번째 메시지(message_index)에 대한 웹 출처인지 기록한다.
    방이 삭제되면 ON DELETE CASCADE로 함께 삭제된다.
    """
    __tablename__ = "chat_web_source"

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        "session_id",
        String(36),
        ForeignKey("chat_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    message_index: Mapped[int] = mapped_column("message_index", Integer, nullable=False)
    url: Mapped[str] = mapped_column("url", String(1000), nullable=False)
    title: Mapped[str] = mapped_column("title", String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column("summary", String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, server_default=func.now())


class ChatSuggestionEntity(Base):
    """채팅 답변 뒤에 따라붙는 추천 후속 질문 엔티티.

    어느 방(session_id)의 몇 번째 메시지(message_index)에 대한 추천 질문인지 기록한다.
    방이 삭제되면 ON DELETE CASCADE로 함께 삭제된다.
    """
    __tablename__ = "chat_suggestion"

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        "session_id",
        String(36),
        ForeignKey("chat_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    message_index: Mapped[int] = mapped_column("message_index", Integer, nullable=False)
    question: Mapped[str] = mapped_column("question", String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, server_default=func.now())