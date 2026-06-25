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
# Chat Session Endpoint Tests
# =====================================================================

@patch("api.v1.chat.services.ChatService.create_session")
def test_create_session_endpoint(mock_create):
    """채팅 세션 생성 API가 정상적으로 세션을 생성하는지 검증합니다."""
    from api.v1.chat.entity import ChatSessionEntity
    from datetime import datetime
    mock_create.return_value = ChatSessionEntity(
        session_id="test-session-uuid",
        member_id="test-user",
        title="새로운 채팅방",
        created_at=datetime.now()
    )

    response = client.post(
        "/api/v1/chat/sessions",
        json={"title": "새로운 채팅방"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["session_id"] == "test-session-uuid"
    assert json_data["data"]["title"] == "새로운 채팅방"
    mock_create.assert_called_once_with("test-user", "새로운 채팅방")


@patch("api.v1.chat.services.ChatService.list_sessions")
def test_list_sessions_endpoint(mock_list):
    """사용자의 채팅 세션 목록 조회 API를 테스트합니다."""
    from api.v1.chat.entity import ChatSessionEntity
    from datetime import datetime
    mock_list.return_value = [
        ChatSessionEntity(
            session_id="session-1",
            member_id="test-user",
            title="방 1",
            created_at=datetime.now()
        )
    ]

    response = client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["session_id"] == "session-1"
    mock_list.assert_called_once_with("test-user")


@patch("api.v1.chat.services.ChatService.delete_session")
def test_delete_session_endpoint(mock_delete):
    """채팅 세션 삭제 API를 테스트합니다."""
    mock_delete.return_value = None

    response = client.delete("/api/v1/chat/sessions/session-1")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert "삭제된 채팅방" in json_data["data"]["message"]
    mock_delete.assert_called_once_with("test-user", "session-1")


@patch("api.v1.chat.services.ChatService.rename_session")
def test_rename_session_endpoint(mock_rename):
    """채팅 세션 제목 변경 API를 테스트합니다."""
    from api.v1.chat.entity import ChatSessionEntity
    from datetime import datetime
    mock_rename.return_value = ChatSessionEntity(
        session_id="session-1",
        member_id="test-user",
        title="변경된 방 이름",
        created_at=datetime.now()
    )

    response = client.patch(
        "/api/v1/chat/sessions/session-1",
        json={"title": "변경된 방 이름"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["title"] == "변경된 방 이름"
    mock_rename.assert_called_once_with("test-user", "session-1", "변경된 방 이름")


@patch("api.v1.chat.services.ChatService.generate_and_set_title")
def test_generate_title_endpoint(mock_gen_title):
    """첫 질문 기반 채팅 제목 자동 생성 API를 테스트합니다."""
    mock_gen_title.return_value = "자동 생성된 제목"

    response = client.post(
        "/api/v1/chat/sessions/session-1/generate-title",
        json={"message": "첫 질문"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["title"] == "자동 생성된 제목"
    mock_gen_title.assert_called_once_with("test-user", "session-1", "첫 질문")


# =====================================================================
# Chat Message Send and History Endpoint Tests
# =====================================================================

@patch("api.v1.chat.services.ChatService.send_message")
def test_send_message_endpoint(mock_send):
    """비스트리밍 메시지 전송 API를 검증합니다."""
    mock_send.return_value = {
        "answer": "질문에 대한 대답입니다[1].",
        "sources": [{"arxiv_id": "cs-1", "title": "CS Title 1"}]
    }

    response = client.post(
        "/api/v1/chat/sessions/session-1/messages",
        json={"message": "질문"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["answer"] == "질문에 대한 대답입니다[1]."
    assert json_data["data"]["sources"][0]["arxiv_id"] == "cs-1"
    mock_send.assert_called_once_with("test-user", "session-1", "질문")


@patch("api.v1.chat.services.ChatService.send_message_stream")
def test_send_message_stream_endpoint(mock_send_stream):
    """스트리밍 메시지 전송 API를 검증합니다."""
    async def mock_generator(*args, **kwargs):
        yield "안"
        yield "녕"
        yield "하"
        yield "세"
        yield "요"

    mock_send_stream.return_value = mock_generator()

    response = client.post(
        "/api/v1/chat/sessions/session-1/messages/stream",
        json={"message": "인사"}
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/plain")
    assert response.text == "안녕하세요"
    mock_send_stream.assert_called_once_with("test-user", "session-1", "인사")


@patch("api.v1.chat.services.ChatService.get_messages")
def test_get_messages_history_endpoint(mock_history):
    """대화 내역 조회 API를 검증합니다."""
    from datetime import datetime
    mock_history.return_value = [
        {
            "role": "user",
            "content": "질문",
            "created_at": datetime.now(),
            "sources": []
        },
        {
            "role": "assistant",
            "content": "대답[1]",
            "created_at": datetime.now(),
            "sources": [{"arxiv_id": "cs-1", "title": "CS Title 1"}]
        }
    ]

    response = client.get("/api/v1/chat/sessions/session-1/messages")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert len(json_data["data"]) == 2
    assert json_data["data"][0]["role"] == "user"
    assert json_data["data"][1]["role"] == "assistant"
    assert json_data["data"][1]["sources"][0]["arxiv_id"] == "cs-1"
    mock_history.assert_called_once_with("test-user", "session-1")
