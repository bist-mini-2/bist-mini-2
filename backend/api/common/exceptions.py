class MemberNotFoundError(Exception):
    """회원을 찾을 수 없을 때 발생하는 예외입니다."""
    def __init__(self, message: str, error_code: str = "MEMBER_NOT_FOUND"):
        self.error_code = error_code
        super().__init__(message)


class InvalidPasswordError(Exception):
    """비밀번호 검증에 실패했을 때 발생하는 예외입니다."""
    def __init__(self, message: str, error_code: str = "INVALID_PASSWORD"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class BusinessException(Exception):
    """일반적인 비즈니스 로직 처리 에러가 발생했을 때 호출되는 예외입니다."""
    def __init__(self, message: str = "", error_code: str = "BUSINESS_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TaskNotFoundError(Exception):
    """요청한 분석 배치 태스크를 찾을 수 없을 때 발생하는 예외입니다."""
    def __init__(self, message: str, error_code: str = "TASK_NOT_FOUND"):
        self.error_code = error_code
        super().__init__(message)

