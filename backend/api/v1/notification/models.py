from datetime import datetime
from typing import Optional, List
from pydantic import Field
from api.database.config.dto_base import BaseDTO


class NotificationDTO(BaseDTO):
    """알림 정보 DTO 스키마입니다."""
    id: str = Field(
        ..., 
        description="알림 고유 식별자 (UUID)", 
        examples=["notif-9c7b827e-8c88-4228"]
    )
    mid: str = Field(
        ..., 
        description="알림 수신자 회원 ID", 
        examples=["testuser"]
    )
    title: str = Field(
        ..., 
        description="알림 요약 제목", 
        examples=["배치 분석 완료 알림"]
    )
    message: str = Field(
        ..., 
        description="알림 세부 정보 메시지 내용", 
        examples=["의뢰하신 'neural network' 키워드에 대한 비교 분석이 성공적으로 종료되었습니다."]
    )
    type: str = Field(
        ..., 
        description="알림 스타일 분류 타입 (info, success, danger, warning)", 
        examples=["success"]
    )
    task_id: Optional[str] = Field(
        None, 
        description="비동기 배치 분석 작업과 관련된 태스크 ID", 
        examples=["task-8c7b827e-8c88-4228"]
    )
    read: bool = Field(
        ..., 
        description="알림 읽음 여부 상태", 
        examples=[False]
    )
    created_at: datetime = Field(
        ..., 
        description="알림 생성 일시", 
        examples=["2026-06-23T11:22:00"]
    )


class NotificationListResponse(BaseDTO):
    """알림 목록 조회 응답용 DTO 스키마입니다."""
    notifications: List[NotificationDTO] = Field(
        ..., 
        description="도달한 전체 알림 목록 리스트"
    )
