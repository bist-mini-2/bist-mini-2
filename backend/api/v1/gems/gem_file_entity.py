from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from api.database.config.entity_base import Base


class GemFileEntity(Base):
    """Gem에 업로드된 파일의 메타데이터 엔티티.

    pgvector에 임베딩이 저장된 파일의 원본 이름, 청크 수 등을 추적한다.
    gem 삭제 시 CASCADE로 자동 삭제된다.
    """
    __tablename__ = "gem_file"

    file_id: Mapped[str] = mapped_column("file_id", String(36), primary_key=True)
    gem_id: Mapped[str] = mapped_column(
        "gem_id",
        String(36),
        ForeignKey("gem.gem_id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column("filename", String(255), nullable=False)
    chunk_count: Mapped[int] = mapped_column("chunk_count", Integer, nullable=False, default=0)
    uploaded_at: Mapped[datetime] = mapped_column("uploaded_at", DateTime, server_default=func.now())
