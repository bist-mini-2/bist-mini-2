import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def override_auth_dependency():
    """테스트 시 JWT 인증 의존성을 모의 페이로드로 자동 오버라이딩합니다."""
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}
    yield
    app.dependency_overrides.clear()


@pytest.mark.anyio
@patch("api.v1.similarity_search.endpoints.common_rag_pipeline.similarity_search")
async def test_search_bio_endpoint_success(mock_similarity_search):
    """POST /api/v1/similarity-search/bio 호출 성공 시 결과 데이터를 올바르게 반환하는지 테스트합니다."""
    mock_similarity_search.return_value = [
        {
            "doc_id": "bio-1",
            "title": "Bio Title 1",
            "text_chunk": "Bio Abstract Content 1",
            "score": 0.95
        }
    ]

    response = client.post(
        "/api/v1/similarity-search/bio",
        json={"query": "genomics", "top_k": 1}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert "results" in json_data["data"]
    results = json_data["data"]["results"]
    assert len(results) == 1
    assert results[0]["doc_id"] == "bio-1"
    assert results[0]["title"] == "Bio Title 1"
    assert results[0]["text_chunk"] == "Bio Abstract Content 1"
    assert results[0]["score"] == 0.95
    mock_similarity_search.assert_called_once_with(domain="bio", query="genomics", k=1)


@pytest.mark.anyio
@patch("api.v1.similarity_search.endpoints.common_rag_pipeline.similarity_search")
async def test_search_cs_endpoint_success(mock_similarity_search):
    """POST /api/v1/similarity-search/cs 호출 성공 시 결과 데이터를 올바르게 반환하는지 테스트합니다."""
    mock_similarity_search.return_value = [
        {
            "doc_id": "cs-1",
            "title": "CS Title 1",
            "text_chunk": "CS Abstract Content 1",
            "score": 0.88
        }
    ]

    response = client.post(
        "/api/v1/similarity-search/cs",
        json={"query": "neural networks", "top_k": 1}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    results = json_data["data"]["results"]
    assert len(results) == 1
    assert results[0]["doc_id"] == "cs-1"
    mock_similarity_search.assert_called_once_with(domain="cs", query="neural networks", k=1)


@pytest.mark.anyio
@patch("api.v1.similarity_search.endpoints.common_rag_pipeline.similarity_search")
async def test_search_astronomy_endpoint_success(mock_similarity_search):
    """POST /api/v1/similarity-search/astronomy 호출 성공 시 결과 데이터를 올바르게 반환하는지 테스트합니다."""
    mock_similarity_search.return_value = [
        {
            "doc_id": "astro-1",
            "title": "Astro Title 1",
            "text_chunk": "Astro Abstract Content 1",
            "score": 0.92
        }
    ]

    response = client.post(
        "/api/v1/similarity-search/astronomy",
        json={"query": "black holes", "top_k": 1}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    results = json_data["data"]["results"]
    assert len(results) == 1
    assert results[0]["doc_id"] == "astro-1"
    mock_similarity_search.assert_called_once_with(domain="astronomy", query="black holes", k=1)


def test_search_endpoint_validation_error():
    """요청 파라미터가 유효하지 않은 경우 400 Bad Request 에러가 발생하는지 검증합니다."""
    # top_k가 0 이하일 때 validation ge=1 제한에 걸려야 함
    response = client.post(
        "/api/v1/similarity-search/bio",
        json={"query": "invalid_k", "top_k": 0}
    )
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["status"] == "error"
    assert "body" in json_data["message"]
