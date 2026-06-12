from typing import Any
from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """프로젝트 내부의 모든 Pydantic DTO가 상속받는 공통 베이스 클래스입니다.

    Attributes:
        model_config (ConfigDict): Pydantic 모델 설정. ORM 객체 속성을 DTO로 자동 매핑(from_attributes=True)하도록 지원합니다.
    """
    model_config = ConfigDict(
        from_attributes=True
    )


class SuccessResponse(BaseDTO):
    """성공 시 반환되는 전역 공통 응답 규격입니다.

    Attributes:
        status (str): 성공 상태 표시 (기본값: success).
        data (Any): 실제 응답 데이터 본문.
    """
    status: str = "success"
    data: Any


class ErrorResponse(BaseDTO):
    """실패 시 반환되는 전역 공통 응답 규격입니다.

    Attributes:
        status (str): 실패 상태 표시 (기본값: error).
        message (str): 실패 원인에 대한 에러 메시지.
    """
    status: str = "error"
    message: str

