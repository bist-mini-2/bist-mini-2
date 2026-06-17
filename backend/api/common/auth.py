import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, TypedDict
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from api.common.config import settings

logger = logging.getLogger(__name__)

# OAuth2PasswordBearer configures the Swagger UI login modal.
# It points to the token issuance URL (/api/v1/auth/login).
_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


def create_token(mid: str, mrole: str) -> str:
    """지정된 사용자 ID와 역할(권한)에 대한 JWT 토큰을 생성합니다.

    Args:
        mid (str): 사용자의 식별자 ID.
        mrole (str): 사용자의 역할(권한) 정보.

    Returns:
        str: 암호화된 JWT 토큰 문자열.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": mid,
        "mrole": mrole,
        "iat": now.timestamp(),
        "exp": int((now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
    }
    jwt_str = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return jwt_str


def get_payload(token: str) -> dict:
    """JWT 토큰을 디코딩하고 토큰의 유효성을 검증하여 페이로드를 획득합니다.

    Args:
        token (str): 검증 및 디코딩할 JWT 토큰 문자열.

    Returns:
        dict: 디코딩에 성공한 토큰의 페이로드 딕셔너리 정보.

    Raises:
        jwt.MissingRequiredClaimError: 페이로드에 필수 클레임인 'sub'이 없는 경우 발생합니다.
        HTTPException: 토큰 서명이 만료되었거나 부적절할 경우 401 Unauthorized 에러를 발생시킵니다.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if "sub" not in payload:
            raise jwt.MissingRequiredClaimError("sub")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature has expired"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


class UserPayload(TypedDict):
    """검증된 JWT 토큰 페이로드 데이터 스키마입니다."""
    sub: str
    mrole: str


async def verify_access_token(
    request: Request,
    access_token: Annotated[str | None, Depends(_oauth2_scheme)] = None
) -> UserPayload:
    """FastAPI 종속성 주입용 함수로, 요청 헤더 또는 쿼리 파라미터에서 토큰을 추출하여 검증합니다.

    Args:
        request (Request): FastAPI 요청 객체.
        access_token (str | None): OAuth2 스키마를 통해 추출된 액세스 토큰 문자열.

    Returns:
        UserPayload: 검증이 완료된 액세스 토큰의 페이로드 데이터.

    Raises:
        HTTPException: 토큰이 누락되었거나 유효하지 않을 때 401 Unauthorized 에러를 발생시킵니다.
    """
    # Attempt to extract from query parameters if not present in Authorization header
    if not access_token:
        access_token = request.query_params.get("accessToken")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Token is missing"
        )

    payload = get_payload(access_token)
    logger.info(f"Verified JWT payload: {payload}")
    return {
        "sub": str(payload.get("sub", "")),
        "mrole": str(payload.get("mrole", ""))
    }


def require_roles(roles: list[str]):
    """지정된 역할 목록에 기반하여 접근을 허용하는 FastAPI 종속성 빌더 함수입니다.

    Args:
        roles (list[str]): 해당 엔드포인트에 접근이 허용된 역할 권한 목록.

    Returns:
        Callable: JWT 토큰의 권한(mrole) 정보가 허용 목록에 포함되는지 검증하는 비동기 함수.
    """
    async def check_roles(payload: Annotated[UserPayload, Depends(verify_access_token)]) -> UserPayload:
        user_role = payload.get("mrole")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {roles}, current role: {user_role}"
            )
        return payload
    return check_roles


# Common dependency aliases
LoginCheckDep = Annotated[UserPayload, Depends(verify_access_token)]
AdminCheckDep = Annotated[UserPayload, Depends(require_roles(["ROLE_ADMIN"]))]
