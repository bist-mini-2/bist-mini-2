from sqlalchemy import String, Text, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from api.database.config.entity_base import Base


class ResearchGapTaskEntity(Base):
    """비동기 배치 분석 작업의 수명 주기 및 상태 정보를 저장하는 테이블입니다."""
    
    __tablename__ = "research_gap_task"

    task_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    mid: Mapped[str] = mapped_column(String(20), ForeignKey("member.mid"), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)           # 0 to 100
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)                    # JSON format analysis report
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)               # Error message in case of failure
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
