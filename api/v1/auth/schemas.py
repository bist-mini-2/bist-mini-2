from api.database.config.dto_base import BaseDTO, SuccessResponse


class TokenResponse(BaseDTO):
    """로그인 성공 시 반환되는 액세스 토큰 정보 스키마입니다.

    Attributes:
        access_token (str): 발급된 JWT 액세스 토큰.
        token_type (str): 토큰 타입 (기본값: bearer).
        username (str): 사용자 이름.
        role (str): 사용자 권한.
    """
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class TokenResponseWrapper(SuccessResponse):
    """토큰 응답 성공 공통 래퍼 스키마입니다.

    Attributes:
        data (TokenResponse): 로그인 성공 시 반환되는 액세스 토큰 본문 데이터.
    """
    data: TokenResponse


class UserInfoResponse(BaseDTO):
    """현재 로그인한 사용자의 정보를 반환하는 스키마입니다.

    Attributes:
        username (str): 사용자 이름.
        role (str): 사용자 권한.
    """
    username: str
    role: str


class UserInfoResponseWrapper(SuccessResponse):
    """사용자 정보 성공 공통 래퍼 스키마입니다.

    Attributes:
        data (UserInfoResponse): 현재 로그인한 사용자의 정보 본문 데이터.
    """
    data: UserInfoResponse


class MemberJoinRequest(BaseDTO):
    """회원가입 요청 데이터를 담는 스키마입니다.

    Attributes:
        mid (str): 회원가입 아이디.
        mname (str): 회원 이름.
        mpassword (str): 회원 비밀번호.
        memail (str): 회원 이메일 주소.
    """
    mid: str
    mname: str
    mpassword: str
    memail: str


class MemberJoinResponse(BaseDTO):
    """회원가입 완료 시 반환될 정보를 담는 스키마입니다.

    Attributes:
        mid (str): 가입된 회원 아이디.
        mname (str): 가입된 회원 이름.
        memail (str): 가입된 회원 이메일 주소.
        menabled (bool): 회원 활성화 상태.
        mrole (str): 회원 권한/역할.
    """
    mid: str
    mname: str
    memail: str
    menabled: bool
    mrole: str


class MemberJoinResponseWrapper(SuccessResponse):
    """회원가입 성공 공통 래퍼 스키마입니다.

    Attributes:
        data (MemberJoinResponse): 가입 완료된 회원 정보 본문 데이터.
    """
    data: MemberJoinResponse
