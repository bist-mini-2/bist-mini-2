from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Boolean, func
from api.database.config.entity_base import Base


class GemEntity(Base):
    """사용자 정의 연구 비서(Gem) 메타데이터 엔티티.

    name, db_sources(RAG 필터), system_prompt를 영구 저장한다.
    실제 대화 이력은 AsyncPostgresSaver가 thread_id(gem_id + session suffix)별로 별도 저장한다.
    has_files: 사용자가 업로드한 파일의 임베딩이 pgvector에 저장되어 있는지 여부.
    """
    __tablename__ = "gem"

    gem_id: Mapped[str] = mapped_column("gem_id", String(36), primary_key=True)
    member_id: Mapped[str] = mapped_column("member_id", String(20), nullable=False)
    name: Mapped[str] = mapped_column("name", String(100), nullable=False)
    db_sources: Mapped[str] = mapped_column("db_sources", String(50), nullable=False)  # e.g. "bio,cs,astronomy"
    system_prompt: Mapped[str] = mapped_column("system_prompt", Text, nullable=False)
    has_files: Mapped[bool] = mapped_column("has_files", Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, server_default=func.now())
