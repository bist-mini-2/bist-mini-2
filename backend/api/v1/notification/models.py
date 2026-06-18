from datetime import datetime
from typing import Optional, List
from pydantic import Field
from api.database.config.dto_base import BaseDTO


class NotificationDTO(BaseDTO):
    """알림 정보 DTO 스키마입니다."""
    id: str = Field(..., description="알림 고유 ID")
    mid: str = Field(..., description="사용자 ID")
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 내용")
    type: str = Field(..., description="알림 타입 (info, success, danger, warning)")
    task_id: Optional[str] = Field(None, description="연관 태스크 ID")
    read: bool = Field(..., description="읽음 여부")
    created_at: datetime = Field(..., description="생성 일시")


class NotificationListResponse(BaseDTO):
    """알림 목록 조회 응답용 DTO 스키마입니다."""
    notifications: List[NotificationDTO]
