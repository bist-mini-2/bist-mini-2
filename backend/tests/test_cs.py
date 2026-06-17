import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app

from api.v1.cs.services import CsService

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


# =====================================================================
# 1. API Endpoints Test Cases (FastAPI Routing & DTO Validation)
# =====================================================================

@patch("api.v1.cs.services.CsService.search_similar_papers")
def test_similarity_search_cs_endpoint(mock_search_papers):
    """유사도 검색 API가 정상 응답 구조를 반환하는지 테스트합니다."""
    mock_search_papers.return_value = [
        {
            "doc_id": "2406.12345",
            "title": "Test Neural Evolutionary Dynamics",
            "text_chunk": "This is a mocked paper abstract chunk about neural dynamics.",
            "score": 0.95
        }
    ]

    # API 요청
    payload = {"query": "neural network training", "top_k": 3}
    response = client.post("/api/v1/similarity-search/cs", json=payload)

    # 검증
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert "data" in json_data
    assert len(json_data["data"]["results"]) == 1
    assert json_data["data"]["results"][0]["doc_id"] == "2406.12345"
    assert json_data["data"]["results"][0]["score"] == 0.95
    mock_search_papers.assert_called_once_with("neural network training", 3)


def test_similarity_search_cs_validation_error():
    """유효하지 않은 파라미터(예: top_k 범위 초과) 전송 시 Validation Error가 발생하는지 테스트합니다."""
    # top_k가 10 초과인 잘못된 요청
    payload = {"query": "neural network training", "top_k": 99}
    response = client.post("/api/v1/similarity-search/cs", json=payload)

    # 검증 (FastAPI validation error는 프로젝트 예외 처리기에 의해 400 Bad Request를 반환)
    assert response.status_code == 400


@patch("api.v1.cs.services.CsService.answer_question_with_rag")
def test_ask_cs_rag_endpoint(mock_ask_rag):
    """RAG 기반 질의응답 API가 정상 응답 구조를 반환하는지 테스트합니다."""
    mock_ask_rag.return_value = {
        "answer": "모킹된 답변 결과입니다.",
        "sources": [
            {
                "doc_id": "2406.12345",
                "title": "Test Neural Evolutionary Dynamics",
                "text_chunk": "This is a mocked paper abstract chunk.",
                "score": 0.95
            }
        ]
    }

    # API 요청
    payload = {"query": "How do networks train?", "top_k": 2, "llm_model": "gpt-4o-mini"}
    response = client.post("/api/v1/similarity-search/cs/ask", json=payload)

    # 검증
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["answer"] == "모킹된 답변 결과입니다."
    assert len(json_data["data"]["sources"]) == 1
    mock_ask_rag.assert_called_once_with(
        query="How do networks train?",
        top_k=2,
        llm_model="gpt-4o-mini"
    )


@patch("api.v1.cs.services.CsService.run_agent_with_rag_tool")
def test_ask_cs_agent_endpoint(mock_run_agent):
    """에이전트 API가 정상 응답 구조를 반환하는지 테스트합니다."""
    # Mock 응답 데이터 설정 (dict 반환)
    mock_run_agent.return_value = {
        "answer": "에이전트의 최종 모킹된 추론 결과입니다.",
        "sources": [
            {
                "doc_id": "2406.12345",
                "title": "Test Paper",
                "text_chunk": "Content text...",
                "score": 0.95
            }
        ],
        "tool_calls": [
            {
                "name": "search_cs_papers",
                "args": {"search_query": "agent search"},
                "id": "call_abc123"
            }
        ]
    }

    # API 요청
    payload = {"query": "Explain agent reasoning.", "llm_model": "gpt-4o-mini"}
    response = client.post("/api/v1/similarity-search/cs/agent", json=payload)

    # 검증
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["answer"] == "에이전트의 최종 모킹된 추론 결과입니다."
    assert len(json_data["data"]["sources"]) == 1
    assert json_data["data"]["sources"][0]["doc_id"] == "2406.12345"
    assert len(json_data["data"]["tool_calls"]) == 1
    assert json_data["data"]["tool_calls"][0]["name"] == "search_cs_papers"
    mock_run_agent.assert_called_once_with(
        query="Explain agent reasoning.",
        llm_model="gpt-4o-mini"
    )


# =====================================================================
# 2. Service Layer Unit Test Case (CsService & CsDao Orchestration)
# =====================================================================

@pytest.mark.anyio
async def test_cs_service_business_logic():
    """CsService.search_similar_papers가 임베딩과 DAO를 올바르게 호출하는지 단위 테스트합니다."""
    mock_dao = MagicMock()
    mock_dao.select_similar_chunks = AsyncMock(
        return_value=[
            {
                "doc_id": "doc-101",
                "title": "Title A",
                "text_chunk": "Chunk text content",
                "score": 0.88
            }
        ]
    )

    # 임베딩 헬퍼 모킹
    with patch("api.v1.cs.services.embedding_helper") as mock_embed_helper:
        # 3072차원 가상 임베딩 벡터 반환 설정
        mock_vector = [0.1] * 3072
        mock_embed_helper.encode.return_value = mock_vector

        # CsService 인스턴스화 및 테스트 함수 실행
        cs_service = CsService(cs_dao=mock_dao)
        response = await cs_service.search_similar_papers(query="search query", top_k=5)

        # 검증
        mock_embed_helper.encode.assert_called_once_with("search query")
        mock_dao.select_similar_chunks.assert_called_once_with(mock_vector, 5)
        
        assert len(response) == 1
        result = response[0]
        assert result["doc_id"] == "doc-101"
        assert result["title"] == "Title A"
        assert result["text_chunk"] == "Chunk text content"
        assert result["score"] == 0.88


@pytest.mark.anyio
async def test_cs_service_invalid_model_error():
    """지원되지 않는 모델명 요청 시 BusinessException 예외가 올바르게 슬로우되는지 테스트합니다."""
    from api.common.exceptions import BusinessException
    mock_dao = MagicMock()
    cs_service = CsService(cs_dao=mock_dao)

    with pytest.raises(BusinessException) as exc_info:
        await cs_service.answer_question_with_rag(query="test", top_k=3, llm_model="unsupported-model")
    assert "지원하지 않는 LLM 모델입니다" in str(exc_info.value)

    with pytest.raises(BusinessException) as exc_info:
        await cs_service.run_agent_with_rag_tool(query="test", llm_model="unsupported-model")
    assert "지원하지 않는 LLM 모델입니다" in str(exc_info.value)


def test_similarity_search_cs_empty_query_validation_error():
    """빈 쿼리 전송 시 Validation Error가 발생하는지 테스트합니다."""
    payload = {"query": "", "top_k": 3}
    response = client.post("/api/v1/similarity-search/cs", json=payload)
    assert response.status_code == 400
    assert response.json()["status"] == "error"

