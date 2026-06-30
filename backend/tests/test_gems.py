import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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


# =====================================================================
# Gem CRUD Endpoint Tests
# =====================================================================

@patch("api.v1.gems.services.GemService.create_gem")
def test_create_gem_endpoint(mock_create):
    """Gem 생성 API가 새로운 젬을 올바르게 등록하고 응답하는지 검증합니다."""
    from api.v1.gems.entity import GemEntity
    from datetime import datetime
    mock_create.return_value = GemEntity(
        gem_id="gem-uuid-1",
        member_id="test-user",
        name="테스트 젬",
        db_sources="cs,bio",
        system_prompt="테스트 프롬프트",
        created_at=datetime.now()
    )

    payload = {
        "name": "테스트 젬",
        "db_sources": ["cs", "bio"],
        "system_prompt": "테스트 프롬프트"
    }
    response = client.post("/api/v1/gems", json=payload)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["gem_id"] == "gem-uuid-1"
    assert json_data["data"]["name"] == "테스트 젬"
    assert json_data["data"]["db_sources"] == ["cs", "bio"]
    mock_create.assert_called_once_with(
        member_id="test-user",
        name="테스트 젬",
        db_sources=["cs", "bio"],
        system_prompt="테스트 프롬프트"
    )


@patch("api.v1.gems.services.GemService.list_gems")
def test_list_gems_endpoint(mock_list):
    """사용자가 생성한 젬 목록 조회 API를 테스트합니다."""
    from api.v1.gems.entity import GemEntity
    from datetime import datetime
    mock_list.return_value = [
        GemEntity(
            gem_id="gem-uuid-1",
            member_id="test-user",
            name="테스트 젬",
            db_sources="cs",
            system_prompt="프롬프트",
            created_at=datetime.now()
        )
    ]

    response = client.get("/api/v1/gems")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["gem_id"] == "gem-uuid-1"
    mock_list.assert_called_once_with("test-user")


@patch("api.v1.gems.services.GemService.update_gem")
def test_update_gem_endpoint(mock_update):
    """젬 정보 부분 수정(update) API를 검증합니다."""
    from api.v1.gems.entity import GemEntity
    from datetime import datetime
    mock_update.return_value = GemEntity(
        gem_id="gem-uuid-1",
        member_id="test-user",
        name="수정된 젬",
        db_sources="bio",
        system_prompt="수정된 프롬프트",
        created_at=datetime.now()
    )

    payload = {
        "name": "수정된 젬",
        "db_sources": ["bio"],
        "system_prompt": "수정된 프롬프트"
    }
    response = client.put("/api/v1/gems/gem-uuid-1", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["name"] == "수정된 젬"
    mock_update.assert_called_once_with(
        member_id="test-user",
        gem_id="gem-uuid-1",
        name="수정된 젬",
        db_sources=["bio"],
        system_prompt="수정된 프롬프트"
    )


@patch("api.v1.gems.services.GemService.delete_gem")
def test_delete_gem_endpoint(mock_delete):
    """젬 삭제 API를 테스트합니다."""
    mock_delete.return_value = None

    response = client.delete("/api/v1/gems/gem-uuid-1")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert "Deleted Gem ID" in json_data["data"]["message"]
    mock_delete.assert_called_once_with("test-user", "gem-uuid-1")


# =====================================================================
# Gem Chatting Endpoint Tests
# =====================================================================

@patch("api.v1.gems.services.GemService.send_message")
def test_chat_with_gem_endpoint(mock_send):
    """젬과의 대화 질의 API를 테스트합니다."""
    mock_send.return_value = {
        "answer": "젬이 생성한 맞춤형 대답입니다.",
        "sources": [{"arxiv_id": "cs-2", "title": "CS Title 2"}]
    }

    payload = {
        "thread_id": "thread-1234",
        "message": "맞춤 질문"
    }
    response = client.post("/api/v1/gems/gem-uuid-1/chat", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["answer"] == "젬이 생성한 맞춤형 대답입니다."
    assert json_data["data"]["sources"][0]["arxiv_id"] == "cs-2"
    mock_send.assert_called_once_with(
        member_id="test-user",
        gem_id="gem-uuid-1",
        thread_id="thread-1234",
        message="맞춤 질문"
    )


@patch("api.v1.gems.services.GemService.get_messages")
def test_get_gem_messages_history_endpoint(mock_get_msgs):
    """젬 스레드 대화 이력 조회 API를 테스트합니다."""
    mock_get_msgs.return_value = [
        {"role": "user", "content": "질문"},
        {"role": "assistant", "content": "대답"}
    ]

    response = client.get("/api/v1/gems/gem-uuid-1/chat/thread-1234/messages")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert len(json_data["data"]) == 2
    mock_get_msgs.assert_called_once_with("test-user", "gem-uuid-1", "thread-1234")
