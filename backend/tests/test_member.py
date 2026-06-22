import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def override_auth_dependencies():
    """테스트 시 JWT 인증 의존성을 모의 페이로드로 자동 오버라이딩합니다."""
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}
    yield
    app.dependency_overrides.clear()



# =====================================================================
# 1. Member Endpoint Tests
# =====================================================================

@patch("api.v1.member.services.MemberService.join")
def test_member_join_endpoint(mock_join):
    """회원가입 API가 정상적으로 작동하고 201 상태코드를 반환하는지 테스트합니다."""
    from api.v1.member.entity import MemberEntity
    mock_join.return_value = MemberEntity(
        mid="new-user",
        mname="홍길동",
        mpassword="hashed-password",
        memail="new@uni.edu",
        menabled=True,
        mrole="ROLE_USER"
    )

    payload = {
        "mid": "new-user",
        "mname": "홍길동",
        "mpassword": "password123",
        "memail": "new@uni.edu",
        "mrole": "ROLE_USER"
    }
    response = client.post("/api/v1/member/join", json=payload)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["mid"] == "new-user"
    assert json_data["data"]["mname"] == "홍길동"
    mock_join.assert_called_once()


@patch("api.v1.member.services.MemberService.read")
def test_member_info_endpoint(mock_read):
    """현재 사용자 정보 조회 API를 테스트합니다."""
    from api.v1.member.entity import MemberEntity
    mock_read.return_value = MemberEntity(
        mid="test-user",
        mname="테스터",
        mpassword="hashed-password",
        memail="test@uni.edu",
        menabled=True,
        mrole="ROLE_USER"
    )

    response = client.get("/api/v1/member/info")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["mid"] == "test-user"
    assert json_data["data"]["memail"] == "test@uni.edu"
    mock_read.assert_called_once_with("test-user")


@patch("api.v1.member.services.MemberService.modify")
def test_member_modify_endpoint(mock_modify):
    """회원 정보 수정 API를 테스트합니다."""
    from api.v1.member.entity import MemberEntity
    mock_modify.return_value = MemberEntity(
        mid="test-user",
        mname="테스터수정",
        mpassword="hashed-password-2",
        memail="test_modify@uni.edu",
        menabled=True,
        mrole="ROLE_USER"
    )

    payload = {
        "mname": "테스터수정",
        "mpassword": "newpassword123",
        "memail": "test_modify@uni.edu"
    }
    response = client.put("/api/v1/member/modify", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["mname"] == "테스터수정"
    assert json_data["data"]["memail"] == "test_modify@uni.edu"
    mock_modify.assert_called_once()


@patch("api.v1.member.services.MemberService.delete")
def test_member_delete_endpoint_by_admin(mock_delete):
    """관리자 권한으로 특정 회원 삭제 API를 테스트합니다."""
    mock_delete.return_value = None
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "admin-user", "mrole": "ROLE_ADMIN"}
    try:
        response = client.delete("/api/v1/member/delete/delete-target-user")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "success"
        assert "삭제된 회원의 아이디" in json_data["data"]["message"]
        mock_delete.assert_called_once_with("delete-target-user")
    finally:
        app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}


# =====================================================================
# 2. Authentication (Auth) Endpoint Tests
# =====================================================================

@patch("api.v1.auth.services.AuthService.login")
def test_auth_login_endpoint(mock_login):
    """OAuth2 호환 로그인 토큰 발급 API를 테스트합니다."""
    mock_login.return_value = {
        "access_token": "mocked-jwt-token",
        "token_type": "bearer",
        "username": "test-user",
        "role": "ROLE_USER"
    }

    # OAuth2 Password Form 형식 (x-www-form-urlencoded)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test-user", "password": "password123"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["access_token"] == "mocked-jwt-token"
    assert json_data["token_type"] == "bearer"
    assert json_data["username"] == "test-user"
    assert json_data["role"] == "ROLE_USER"
    mock_login.assert_called_once_with("test-user", "password123")



def test_auth_me_endpoint():
    """현재 토큰 소유자의 정보 조회 API를 테스트합니다."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["username"] == "test-user"
    assert json_data["data"]["role"] == "ROLE_USER"


def test_auth_admin_only_endpoint_success():
    """관리자 권한으로 관리자 전용 리소스 조회를 테스트합니다."""
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "admin-user", "mrole": "ROLE_ADMIN"}
    try:
        response = client.get("/api/v1/auth/admin-only")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "success"
        assert "Hello Admin 'admin-user'!" in json_data["data"]["message"]
    finally:
        app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}

