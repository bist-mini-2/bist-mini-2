from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, Integer, func, ForeignKey
from pgvector.sqlalchemy import Vector
from api.database.config.entity_base import Base


class DefenseArenaSessionEntity(Base):
    """보안 격리 샌드박스 세션 엔티티.

    사용자가 PDF 문서를 임시 업로드했을 때 세션을 생성하며,
    30분간 미활동 시 자동 소거(Wipe Out) 데몬에 의해 CASCADE 삭제 처리됩니다.
    """
    __tablename__ = "defense_arena_session"

    session_id: Mapped[str] = mapped_column("session_id", String(36), primary_key=True)
    member_id: Mapped[str] = mapped_column("member_id", String(20), nullable=False)
    file_name: Mapped[str] = mapped_column("file_name", String(255), nullable=False)
    file_path: Mapped[str] = mapped_column("file_path", String(500), nullable=False)
    chunk_count: Mapped[int] = mapped_column("chunk_count", Integer, default=0)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    # CASCADE ON DELETE
    defense_histories: Mapped[list["DefenseHistoryEntity"]] = relationship(
        "DefenseHistoryEntity",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    chunks: Mapped[list["DefenseArenaChunkEntity"]] = relationship(
        "DefenseArenaChunkEntity",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class DefenseArenaChunkEntity(Base):
    """임시 업로드된 PDF의 분할 텍스트 및 pgvector 임베딩 엔티티.

    3072차원의 text-embedding-3-large 벡터 데이터가 적재되며,
    DefenseArenaSessionEntity가 삭제되면 Cascade Delete 됩니다.
    """
    __tablename__ = "defense_arena_chunk"

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column("session_id", String(36), ForeignKey("defense_arena_session.session_id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column("chunk_index", Integer, nullable=False)
    text_chunk: Mapped[str] = mapped_column("text_chunk", Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column("embedding", Vector(3072), nullable=False)

    session: Mapped["DefenseArenaSessionEntity"] = relationship("DefenseArenaSessionEntity", back_populates="chunks")


class DefenseHistoryEntity(Base):
    """심사위원 에이전트와 나눈 모의 디펜스 채팅 이력 엔티티."""
    __tablename__ = "defense_history"

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column("session_id", String(36), ForeignKey("defense_arena_session.session_id", ondelete="CASCADE"), nullable=False)
    turn: Mapped[int] = mapped_column("turn", Integer, nullable=False)
    question: Mapped[str] = mapped_column("question", Text, nullable=False)
    answer: Mapped[str] = mapped_column("answer", Text, nullable=True)  # 심사위원이 첫 질문을 던질 때는 사용자의 답변이 아직 없음
    score: Mapped[int] = mapped_column("score", Integer, nullable=True)     # 사용자가 답변했을 때의 채점 점수
    feedback: Mapped[str] = mapped_column("feedback", Text, nullable=True)  # 사용자가 답변했을 때의 채점 피드백
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, server_default=func.now())

    session: Mapped["DefenseArenaSessionEntity"] = relationship("DefenseArenaSessionEntity", back_populates="defense_histories")
