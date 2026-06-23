import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def override_auth_dependency():
    """JWT 인증을 테스트용 모의 페이로드로 자동 오버라이딩합니다."""
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}
    yield
    app.dependency_overrides.clear()


# =====================================================================
# Isolated Defense Arena Endpoint Tests
# =====================================================================

@patch("api.v1.defense_arena.services.DefenseArenaService.process_pdf_upload")
def test_upload_isolated_endpoint(mock_upload):
    """PDF 격리 업로드 API가 세션을 생성하고 올바른 DTO 형태로 응답하는지 검증합니다."""
    mock_upload.return_value = {
        "session_id": "test-session-uuid",
        "file_name": "draft.pdf",
        "chunk_count": 12
    }

    # 모의 파일 생성하여 전송
    files = {"file": ("draft.pdf", b"%PDF-1.4 mock content", "application/pdf")}
    response = client.post("/api/v1/defense-arena/upload-isolated", files=files)

    assert response.status_code == 201
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["session_id"] == "test-session-uuid"
    assert json_data["data"]["chunk_count"] == 12
    mock_upload.assert_called_once()


@patch("api.v1.defense_arena.services.DefenseArenaService.run_peer_review")
def test_academic_peer_review_endpoint(mock_review):
    """다중 에이전트 피어 리뷰 실행 API가 에이전트 평점과 심사평 보고서를 올바르게 반환하는지 검증합니다."""
    from api.v1.defense_arena.models import PeerReviewReport, AgentOpinion
    
    mock_review.return_value = PeerReviewReport(
        overall_score=85,
        opinions=[
            AgentOpinion(agent_type="methodology", score=80, feedback="Good methodology logic."),
            AgentOpinion(agent_type="novelty", score=90, feedback="High novelty."),
            AgentOpinion(agent_type="style", score=85, feedback="Polished academic tone.")
        ],
        summary="Highly recommended draft."
    )

    payload = {
        "session_id": "test-session-uuid",
        "target_journal": "IEEE Trans"
    }
    response = client.post("/api/v1/defense-arena/peer-review", data=payload)

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["overall_score"] == 85
    assert len(json_data["data"]["opinions"]) == 3
    assert json_data["data"]["opinions"][0]["agent_type"] == "methodology"
    mock_review.assert_called_once_with("test-session-uuid", "IEEE Trans", mid="test-user")


@patch("api.v1.defense_arena.services.DefenseArenaService.verify_hypothesis")
def test_verify_hypothesis_endpoint(mock_verify):
    """자기 일관성 기반 가설 검증 API가 다수결 찬반 결론 및 투표율 DTO를 정상 반환하는지 테스트합니다."""
    from api.v1.defense_arena.models import HypothesisVerificationResult, HypothesisVoteItem
    
    mock_verify.return_value = HypothesisVerificationResult(
        verdict="SUPPORT",
        support_count=2,
        refute_count=1,
        insufficient_count=0,
        consensus_ratio=0.6667,
        detailed_votes=[
            HypothesisVoteItem(vote="SUPPORT", reason="Reason A"),
            HypothesisVoteItem(vote="SUPPORT", reason="Reason B"),
            HypothesisVoteItem(vote="REFUTE", reason="Reason C")
        ],
        citations=["Citation paragraph 1", "Citation paragraph 2"]
    )

    payload = {
        "session_id": "test-session-uuid",
        "hypothesis": "RAG pipeline tuning is efficient."
    }
    response = client.post("/api/v1/defense-arena/verify-hypothesis", data=payload)

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["verdict"] == "SUPPORT"
    assert json_data["data"]["support_count"] == 2
    assert json_data["data"]["consensus_ratio"] == 0.6667
    assert len(json_data["data"]["citations"]) == 2
    mock_verify.assert_called_once_with(
        "test-session-uuid",
        "RAG pipeline tuning is efficient.",
        mid="test-user"
    )


@patch("api.v1.defense_arena.services.DefenseArenaService.process_defense_chat")
def test_defense_chat_arena_endpoint(mock_chat):
    """심사위원 모의 디펜스 채팅 API가 턴 정보, 점수, 다음 질문 피드백 DTO를 정상 반환하는지 테스트합니다."""
    from api.v1.defense_arena.models import DefenseChatResponse
    
    mock_chat.return_value = DefenseChatResponse(
        session_id="test-session-uuid",
        turn=2,
        question="What about chunk size limits?",
        score=78,
        feedback="Fair answer, but elaborate on limits.",
        is_finished=False,
        final_report=None
    )

    payload = {
        "session_id": "test-session-uuid",
        "user_response": "We handle that via dynamic thresholding."
    }
    response = client.post("/api/v1/defense-arena/defense/chat", data=payload)

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["turn"] == 2
    assert json_data["data"]["question"] == "What about chunk size limits?"
    assert json_data["data"]["score"] == 78
    assert json_data["data"]["is_finished"] is False
    mock_chat.assert_called_once_with(
        "test-session-uuid",
        "We handle that via dynamic thresholding.",
        mid="test-user"
    )
