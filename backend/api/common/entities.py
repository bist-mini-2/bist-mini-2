from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Boolean, func
from api.database.config.entity_base import Base


class PaperFullTextCacheEntity(Base):
    """논문 본문 텍스트 캐싱을 위한 데이터베이스 매핑 엔티티.

    온디맨드로 크롤링 및 파싱한 논문 본문 데이터를 영구 보관하여 재사용할 수 있도록 한다.
    """
    __tablename__ = "paper_full_text_cache"

    paper_id: Mapped[str] = mapped_column("paper_id", String(50), primary_key=True)
    title: Mapped[str | None] = mapped_column("title", String(255), nullable=True)
    full_text: Mapped[str] = mapped_column("full_text", Text, nullable=False)
    domain: Mapped[str] = mapped_column("domain", String(50), nullable=False)  # e.g., 'bio', 'cs', 'astronomy'
    source: Mapped[str] = mapped_column("source", String(50), nullable=False)  # e.g., 'arxiv', 'europepmc'
    is_vectorized: Mapped[bool] = mapped_column(
        "is_vectorized", Boolean, server_default="false", default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, server_default=func.now(), nullable=False
    )
