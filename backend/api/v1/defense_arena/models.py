from typing import List, Optional, Any
from pydantic import Field
from api.database.config.dto_base import BaseDTO


class UploadResponse(BaseDTO):
    """보안 격리 업로드 성공 응답 DTO."""
    session_id: str = Field(..., description="보안 샌드박스 세션 ID (UUID)")
    file_name: str = Field(..., description="업로드 완료된 파일명")
    chunk_count: int = Field(..., description="파싱 및 청킹된 총 텍스트 조각 수")


class AgentOpinion(BaseDTO):
    """피어리뷰 3대 에이전트 개별 평가 의견 DTO."""
    agent_type: str = Field(..., description="에이전트 구분 (methodology: 방법론, novelty: 신규성, style: 학술문체)")
    score: int = Field(..., ge=0, le=100, description="에이전트별 평가 점수 (0~100)")
    feedback: str = Field(..., description="에이전트별 구체적인 비평 및 보완책 제안")


class PeerReviewReport(BaseDTO):
    """3대 에이전트의 종합 피어리뷰 보고서 DTO."""
    overall_score: int = Field(..., ge=0, le=100, description="종합 종합 점수 (0~100)")
    opinions: List[AgentOpinion] = Field(..., description="3대 에이전트별 상세 리뷰 리스트")
    summary: str = Field(..., description="종합 심사평 요약 및 핵심 권고사항")


class HypothesisRequest(BaseDTO):
    """가설 검증 요청 DTO."""
    hypothesis: str = Field(..., description="검증받고자 하는 연구 가설 텍스트", min_length=5)


class HypothesisVoteItem(BaseDTO):
    """자기 일관성(Self-Consistency) 개별 투표 항목 DTO."""
    vote: str = Field(..., description="개별 투표 결론 (SUPPORT, REFUTE, INSUFFICIENT_EVIDENCE)")
    reason: str = Field(..., description="투표 결론을 뒷받침하는 구체적인 근거 및 논리")


class HypothesisVerificationResult(BaseDTO):
    """가설 검증의 최종 합의 결과 DTO."""
    verdict: str = Field(..., description="최종 다수결 결론 (SUPPORT, REFUTE, INSUFFICIENT_EVIDENCE)")
    support_count: int = Field(..., description="SUPPORT 투표 개수")
    refute_count: int = Field(..., description="REFUTE 투표 개수")
    insufficient_count: int = Field(..., description="INSUFFICIENT_EVIDENCE 투표 개수")
    consensus_ratio: float = Field(..., description="의견 합의율 (0.0 ~ 1.0)")
    detailed_votes: List[HypothesisVoteItem] = Field(..., description="독립 시행 N회의 상세 투표 리스트")
    citations: List[str] = Field(..., description="검증의 근거로 인용된 문서 내 핵심 문장/청크 목록")


class DefenseChatRequest(BaseDTO):
    """디펜스 아레나 답변 제출 요청 DTO."""
    user_response: str = Field(..., description="심사위원의 압박 질문에 대한 사용자의 반론/답변 텍스트", min_length=2)


class DefenseChatResponse(BaseDTO):
    """디펜스 아레나 심사위원 응답 DTO."""
    session_id: str = Field(..., description="세션 ID")
    turn: int = Field(..., description="현재 대화 진행 턴수")
    question: str = Field(..., description="심사위원이 던지는 새로운 (또는 다음) 압박 질문")
    score: Optional[int] = Field(None, ge=0, le=100, description="방금 제출한 사용자의 답변에 대한 획득 점수 (첫 턴의 경우 null)")
    feedback: Optional[str] = Field(None, description="방금 제출한 사용자의 답변에 대한 심사위원의 크리틱 피드백 (첫 턴의 경우 null)")
    is_finished: bool = Field(..., description="디펜스 세션 종료 여부 (보통 3~5턴 완료 시 True)")
    final_report: Optional[str] = Field(None, description="세션 종료 시 산출되는 종합 스코어카드 및 모의 디펜스 최종 평가서")


class ScoreDTO(BaseDTO):
    """답변에 대한 실시간 채점 및 크리틱 피드백 DTO."""
    score: int = Field(..., ge=0, le=100, description="답변에 대한 논리적 방어 점수")
    feedback: str = Field(..., description="촌철살인 평가 피드백 및 논리 보충 조언")

