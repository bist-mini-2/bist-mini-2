from typing import Any, List, Optional
from pydantic import Field
from api.database.config.dto_base import BaseDTO


class AnalyzeRequest(BaseDTO):
    """분석 요청용 DTO 스키마입니다."""
    domain: str = Field(..., description="학술 도메인 (cs 또는 bio)")
    query: str = Field(..., description="분석하고자 하는 기술/주제 키워드")


class TaskStatusResponse(BaseDTO):
    """비동기 배치 작업의 중간 진행도 및 상태 정보 응답용 DTO 스키마입니다."""
    task_id: str
    domain: str
    query: str
    status: str
    progress: int
    created_at: Any
    updated_at: Any


class TaskResultResponse(BaseDTO):
    """비동기 배치 작업의 최종 결과 및 실패 사유 응답용 DTO 스키마입니다."""
    task_id: str
    status: str
    progress: int
    result: Optional[Any] = None
    error_message: Optional[str] = None


class PaperAnalysisResult(BaseDTO):
    """개별 논문 분석 결과를 나타내는 Pydantic Structured Output용 DTO 스키마입니다."""
    title: str = Field(..., description="논문 제목")
    arxiv_id: str = Field(..., description="ArXiv 논문 고유 ID")
    problems_solved: List[str] = Field(..., description="논문에서 해결한 주요 문제 및 제안한 핵심 방법론 목록")
    limitations: List[str] = Field(..., description="논문에서 언급되었거나 식별된 한계점 및 향후 과제 목록")


class ResearchGapMatrix(BaseDTO):
    """비동기 분석 태스크의 최종 매트릭스 및 연구 공백 리포트 정보가 담긴 DTO 스키마입니다."""
    papers: List[PaperAnalysisResult] = Field(..., description="수집/분석된 논문들의 핵심 정보 매트릭스")
    common_limitations: List[str] = Field(..., description="분석 대상 논문군 전반에 걸쳐 식별된 공통적인 한계점 목록")
    suggested_directions: List[str] = Field(..., description="식별된 한계점/연구 공백을 보완하는 구체적인 AI 추천 연구 로드맵 주제 및 방법론 목록")
