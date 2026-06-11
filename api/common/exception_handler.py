import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def register_exception_handler(app: FastAPI):
    """전역 예외 처리기를 등록하여 일관된 에러 응답 규격을 유지합니다.

    Args:
        app (FastAPI): 예외 처리기를 등록할 FastAPI 애플리케이션 인스턴스.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """HTTP 예외 발생 시 호출되며, 공통 에러 규격에 맞는 응답을 반환합니다.

        Args:
            request (Request): HTTP 요청 객체.
            exc (StarletteHTTPException): 발생한 HTTP 예외 객체.

        Returns:
            JSONResponse: 'status': 'error', 'message': 에러 내용 구조의 JSON 응답.
        """
        logger.error(f"HTTPException: {exc.detail} (status_code={exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Pydantic 유효성 검사 실패 시 호출되며, 공통 에러 규격에 맞는 400 응답을 반환합니다.

        Args:
            request (Request): HTTP 요청 객체.
            exc (RequestValidationError): 발생한 유효성 검사 예외 객체.

        Returns:
            JSONResponse: 'status': 'error', 'message': 상세 유효성 검사 에러 내용 구조의 JSON 응답.
        """
        logger.error(f"RequestValidationError: {exc.errors()}")
        error_messages = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error.get("loc", []))
            msg = error.get("msg", "Unknown error")
            error_messages.append(f"[{loc}]: {msg}")
        
        detail_msg = " / ".join(error_messages) if error_messages else "Request validation failed"
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "message": detail_msg
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """처리되지 않은 전역 런타임 예외 발생 시 호출되며, 500 에러를 반환합니다.

        Args:
            request (Request): HTTP 요청 객체.
            exc (Exception): 발생한 일반 예외 객체.

        Returns:
            JSONResponse: 'status': 'error', 'message': 시스템 오류 메시지 구조의 JSON 응답.
        """
        logger.exception(f"Unhandled Exception occurred: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Internal Server Error"
            }
        )


