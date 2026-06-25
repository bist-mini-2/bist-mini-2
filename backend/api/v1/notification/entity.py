from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from api.database.config.entity_base import Base


class NotificationEntity(Base):
    """실시간 및 오프라인 누적 알림 정보를 저장하는 테이블입니다."""
    
    __tablename__ = "notification"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    mid: Mapped[str] = mapped_column(String(20), ForeignKey("member.mid"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="info")  # info, success, danger, warning
    task_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
