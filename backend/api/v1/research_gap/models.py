from typing import Any, List, Optional
from pydantic import Field
from api.database.config.dto_base import BaseDTO


class AnalyzeRequest(BaseDTO):
    """분석 요청용 DTO 스키마입니다."""
    domain: str = Field(
        ...,
        description="학술 도메인 (cs, bio, 또는 astronomy)",
        examples=["cs"]
    )
    query: str = Field(
        ...,
        description="분석하고자 하는 기술/주제 키워드",
        examples=["neural network"]
    )


class TaskStatusResponse(BaseDTO):
    """비동기 배치 작업의 중간 진행도 및 상태 정보 응답용 DTO 스키마입니다."""
    task_id: str = Field(
        ...,
        description="태스크 고유 ID (UUID)",
        examples=["8c7b827e-8c88-4228-94ef-650a256a2bbd"]
    )
    domain: str = Field(
        ...,
        description="학술 도메인",
        examples=["cs"]
    )
    query: str = Field(
        ...,
        description="분석하고자 하는 기술/주제 키워드",
        examples=["neural network"]
    )
    status: str = Field(
        ...,
        description="태스크 작업 상태 (PENDING, RUNNING, COMPLETED, FAILED)",
        examples=["RUNNING"]
    )
    progress: int = Field(
        ...,
        description="배치 작업 진행률 (0 ~ 100)",
        examples=[40]
    )
    created_at: Any = Field(
        ...,
        description="태스크 생성 일시",
        examples=["2026-06-17T15:43:42"]
    )
    updated_at: Any = Field(
        ...,
        description="태스크 수정 일시",
        examples=["2026-06-17T15:44:00"]
    )


class AnalysisItem(BaseDTO):
    """핵심 요약 정보와 그에 매핑되는 논문 본문 원문(인용구)을 갖는 DTO 스키마입니다."""
    summary: str = Field(..., description="요약된 핵심 정보")
    source_quote: str = Field(..., description="요약의 근거가 된 논문 원문의 실제 인용 구절 (영문 원본)")


class PaperAnalysisResult(BaseDTO):
    """개별 논문 분석 결과를 나타내는 Pydantic Structured Output용 DTO 스키마입니다."""
    title: str = Field(..., description="논문 제목")
    arxiv_id: str = Field(..., description="ArXiv 논문 고유 ID")
    problems_solved: List[AnalysisItem] = Field(
        ...,
        max_length=2,
        description="논문에서 해결한 주요 문제 및 제안한 핵심 방법론 목록 (최대 2개)"
    )
    limitations: List[AnalysisItem] = Field(
        ...,
        max_length=2,
        description="논문에서 언급되었거나 식별된 한계점 및 향후 과제 목록 (최대 2개)"
    )
    similarity: Optional[float] = Field(None, description="유사도 스코어")



class ResearchGapMatrix(BaseDTO):
    """비동기 분석 태스크의 최종 매트릭스 및 연구 공백 리포트 정보가 담긴 DTO 스키마입니다."""
    papers: List[PaperAnalysisResult] = Field(..., description="수집/분석된 논문들의 핵심 정보 매트릭스")
    common_limitations: List[str] = Field(..., description="분석 대상 논문군 전반에 걸쳐 식별된 공통적인 한계점 목록")
    suggested_directions: List[str] = Field(..., description="식별된 한계점/연구 공백을 보완하는 구체적인 AI 추천 연구 로드맵 주제 및 방법론 목록")


class TaskResultResponse(BaseDTO):
    """비동기 배치 작업의 최종 결과 및 실패 사유 응답용 DTO 스키마입니다."""
    task_id: str = Field(
        ...,
        description="태스크 고유 ID (UUID)",
        examples=["8c7b827e-8c88-4228-94ef-650a256a2bbd"]
    )
    status: str = Field(
        ...,
        description="태스크 작업 상태 (PENDING, RUNNING, COMPLETED, FAILED)",
        examples=["COMPLETED"]
    )
    progress: int = Field(
        ...,
        description="배치 작업 진행률 (0 ~ 100)",
        examples=[100]
    )
    result: Optional[ResearchGapMatrix] = Field(
        None,
        description="분석 완료 매트릭스 및 결과 데이터 객체",
        examples=[{
            "papers": [
                {
                    "title": "Empirical Analysis of RAG Pipeline Tuning",
                    "arxiv_id": "2401.12345",
                    "problems_solved": [
                        {
                            "summary": "다중 도메인 내 최적 청크 크기가 500자임을 수치적으로 증명",
                            "source_quote": "Our experiments demonstrate that a chunk size of 500 characters preserves semantic density across multi-domain datasets."
                        }
                    ],
                    "limitations": [
                        {
                            "summary": "표, 수식 등이 포함된 멀티모달 요소 청킹 시의 정보 누락 처리 미비",
                            "source_quote": "However, the current pipeline struggles to parse dense tables and mathematical expressions without structural degradation."
                        }
                    ],
                    "similarity": 0.4567
                }
            ],
            "common_limitations": [
                "표/수식 등 구조화 데이터의 유실 문제",
                "언어별 청킹 왜곡 및 실시간 동적 청킹 제어판 부재"
            ],
            "suggested_directions": [
                "1. 구조 인지형 하이브리드 청커 설계: 표, 그래프 및 수식 객체를 별도의 노드로 분리 보존하고 메타데이터 연동 키를 삽입하는 청킹 파이프라인 개발",
                "2. 한국어 맞춤형 토큰-형태소 가변 오버랩 모델: 조사 결합 특성을 반영하여 의미 조각 분실을 방지하기 위한 동적 형태소 기반 겹침 알고리즘 연구"
            ]
        }]
    )
    error_message: Optional[str] = Field(
        None,
        description="작업 실패 시 에러 사유",
        examples=["지원되지 않는 도메인입니다. 현재는 'cs', 'bio', 'astronomy' 도메인만 분석을 지원합니다."]
    )


class TranslateRequest(BaseDTO):
    """분석 결과 번역 요청용 DTO 스키마입니다."""
    matrix: ResearchGapMatrix


class BulkDeleteRequest(BaseDTO):
    """일괄 삭제 요청용 DTO 스키마입니다."""
    task_ids: List[str] = Field(
        ...,
        description="삭제하고자 하는 태스크 고유 ID(UUID) 목록",
        examples=[["test-uuid-1", "test-uuid-2"]]
    )


