# ⚙️ 백엔드 개발 및 공통 코드 컨벤션 (Backend Development & Coding Conventions)

본 문서는 **'논문 AI 에이전트 채팅 플랫폼 (Paper Agent Chat Platform)'** 백엔드 아키텍처의 일관된 코드 품질과 유기적 연동을 위해 모든 개발팀원이 준수해야 하는 공통 코드 컨벤션 가이드라인입니다.

강의자료 및 노션 가이드라인 문서(`docs/notion/*.md`)의 설계 규격을 철저히 분석 및 병합하여 정의되었습니다.

---

## 📂 목차
1. [API 응답 및 전역 예외 처리 규격](#1-api-응답-및-전역-예외-처리-규격)
2. [FastAPI Annotated 기반 의존성 주입](#2-fastapi-annotated-기반-의존성-주입)
3. [Pydantic DTO 전역 설정 (Custom Base Class 패턴)](#3-pydantic-dto-전역-설정-custom-base-class-패턴)
4. [SQLAlchemy AsyncSession 연동 및 MissingGreenlet 에러 방지 규칙](#4-sqlalchemy-asyncsession-연동-및-missinggreenlet-에러-방지-규칙)
5. [LangChain Structured Output 타입 검증 컨벤션](#5-langchain-structured-output-타입-검증-컨벤션)
6. [StreamingResponse 및 제너레이터 구현 규칙](#6-streamingresponse-및-제너레이터-구현-규칙)
7. [LLM 및 에이전트 로깅 콜백 통일](#7-llm-및-에이전트-로깅-콜백-통일)
8. [에이전트 공유 상태 (Shared State) 설계 컨벤션](#8-에이전트-공유-상태-shared-state-설계-컨벤션)
9. [FastAPI 앱 수명 주기(Lifespan) 및 CORS 설정](#9-fastapi-앱-수명-주기lifespan-및-cors-설정)
10. [환경 변수 및 보안 규칙](#10-환경-변수-및-보안-규칙)
11. [파이썬 모듈 캐싱 기반 싱글톤(Singleton) 설계 규칙](#11-파이썬-모듈-캐싱-기반-싱글톤singleton-설계-규칙)
12. [표준 Docstring 및 문서화 가이드](#12-표준-docstring-및-문서화-가이드)

---

## 1. API 응답 및 전역 예외 처리 규격

*   **일관된 응답 구조**: 모든 HTTP API 응답은 프론트엔드가 파싱하기 쉽도록 일관된 JSON 래퍼 구조를 따릅니다.
    *   **성공 시 (HTTP 200/201)**: `{ "status": "success", "data": ... }`
    *   **실패 시 (HTTP 4xx/5xx)**: `{ "status": "error", "message": "에러 설명 내용" }`
*   **전역 예외 처리기**: HTTP 예외, 유효성 검사 예외(ValidationError), 데이터베이스 예외가 발생할 경우 FastAPI 전역 미들웨어를 통해 예외 정보를 감싸 에러 규격에 맞춰 클라이언트에 반환합니다.
*   **HTTP 상태 코드 매핑 규칙**:
    *   `200 OK`: 일반 조회 및 성공적인 비즈니스 로직 수행 완료 시.
    *   `201 Created`: 신규 리소스(데이터베이스 레코드, 영구 파일 등)가 성공적으로 영구 적재되었을 때.
    *   `400 Bad Request`: 파라미터 유효성 검증 실패(Pydantic ValidationError) 및 비즈니스 조건 미충족 시.
    *   `401 Unauthorized`: 인증 토큰 부재 및 유효하지 않은 인증 시도 시.
    *   `403 Forbidden`: 인가되지 않은 권한으로 자원 접근 시.
    *   `404 Not Found`: 존재하지 않는 Thread ID, 파일 경로, API 라우트 요청 시.
    *   `500 Internal Server Error`: 처리되지 않은 미상의 백엔드 서버 런타임 오류 발생 시.
*   **동적 API HTTP 캐싱 방지 정책**:
    *   에이전트 답변 및 실시간 대화 상태는 프론트엔드나 클라이언트 및 CDN 단에서 캐싱되어서는 안 됩니다.
    *   모든 동적 대화/RAG API 응답 헤더에 아래의 **캐시 방지 헤더**를 강제로 주입합니다:
        `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`

---

## 2. FastAPI Annotated 기반 의존성 주입 (Dependency Injection)

*   **Annotated 공식 적용**: IDE 자동 완성 및 정적 분석기(Pyright) 지원 극대화를 위해 매개변수 선언 시 `typing.Annotated` 방식을 필수 사용합니다.
    *   *기존 방식 금지*: `q: str = Query(None)`
    *   *컨벤션 준수*: `q: Annotated[str, Query()] = None`
*   **공통 타입 Alias 정의 및 재사용**: 여러 라우터에서 공통으로 주입받을 의존성은 `api/dependencies.py` 파일에 사전 타입 선언 후 임포트하여 사용합니다.
    *   예: `DbSession = Annotated[AsyncSession, Depends(get_db)]`
    *   예: `CurrentUser = Annotated[User, Depends(get_current_user)]`
*   **의존성 캐시를 활용한 2단계 보안 검증 패턴**:
    *   FastAPI의 `Depends` 캐싱 매커니즘(`use_cache=True`)을 이용하여 중복 JWT 디코딩 연산을 회피합니다.
    *   **1단계 (APIRouter 수준)**: `dependencies=[Depends(verify_access_token)]`를 명시하여 토큰 유무를 일괄 강제 및 최초 검증된 유저 정보 데이터를 캐시에 적재합니다.
    *   **2단계 (컨트롤러 수준)**: 실제 핸들러 인자에서 `payload: LoginCheckDep` 형태로 주입받아 캐싱된 값을 중복 디코딩 없이 즉시 획득합니다.

---

## 3. Pydantic DTO 전역 설정 (Custom Base Class 패턴)

*   **BaseDTO 상속**: 중복 코드 최소화 및 설정을 위해 프로젝트의 모든 Pydantic 모델은 `BaseModel`이 아닌 공통 커스텀 베이스인 `BaseDTO`를 상속합니다.
*   **BaseDTO 정의 사양** (`api/database/config/dto_base.py`):
    ```python
    from pydantic import BaseModel, ConfigDict
    
    class BaseDTO(BaseModel):
        model_config = ConfigDict(
            from_attributes=True  # ORM/Entity 속성 기반 DTO 자동 변환 허용 (model_validate)
        )
    ```

---

## 4. SQLAlchemy AsyncSession 연동 및 MissingGreenlet 에러 방지 규칙

*   **Lazy Loading 전면 금지**: 비동기 컨텍스트(Pydantic 직렬화 등) 내에서 동기식 속성 접근 시 발생하는 `MissingGreenlet` 에러 방지를 위해, 조회하지 않은 관계 필드의 암묵적 지연 로딩을 원천 금지합니다.
*   **비동기 드라이버 사용**: PostgreSQL 연결 시 `asyncpg` 드라이버를 기반으로 동작하는 `create_async_engine`을 강제 설정합니다.
*   **해결책 A (프로젝션 직접 조회 - 권장)**: 데이터 가중이 필요 없는 단순 조회 API는 필요한 컬럼만 `select` 인자로 명시하여 `.mappings().all()`을 통해 `RowMapping` 딕셔너리 형태로 데이터를 반환하여 Pydantic `model_validate`를 수행합니다.
*   **해결책 B (Eager Loading 명시)**: ORM 엔티티 조회가 불가피할 경우, 조회 시점에 모든 연관 응답 필드를 `load_only`에 포함하거나 관계 속성에 대해 `selectinload()` 설정을 명시해야 합니다.
*   **비동기 트랜잭션 (Flush vs Commit) 수명 주기**:
    *   비동기 쿼리 실행 후 PK(기본 키) 값 획득이나 중간 제약 조건 유효성 검증이 필요할 때는 데이터베이스에 즉각 쓰기 처리를 밀어넣기 위해 `db.flush()`를 실행합니다.
    *   트랜잭션의 물리적 반영 및 락(Lock) 해제를 위한 최종 동기화 완료 지점에서만 `db.commit()`을 수행하여 비동기 커넥션 풀을 효율적으로 관리하고 데이터 무결성을 보장합니다.

---

## 5. LangChain Structured Output 타입 검증 컨벤션

*   **`isinstance` 타입 가드 (Type Guard) 적용**: `with_structured_output` API의 모호한 반환 타입 힌트(`Runnable[Any, BaseModel | dict]`)로 인한 Pyright 경고를 방지하고 런타임 안정성을 보장하기 위해 **타입 가드를 이용한 명시적 검증**을 준수합니다.
    ```python
    result = await structured_chat.ainvoke(content)
    if not isinstance(result, TargetDTO):
        raise TypeError(f"Expected TargetDTO, got {type(result)}")
    return result
    ```

---

## 6. StreamingResponse 및 제너레이터 구현 규칙

*   **문자열 검증 강제**: FastAPI의 `StreamingResponse`는 `AsyncIterable[str | bytes]`만 수용합니다. LangChain의 `BaseMessageChunk.content`가 복합 리스트 타입으로 추론되어 생기는 Pyright 오류를 막기 위해 명시적으로 `str` 타입 가드를 적용하여 `yield`합니다.
    ```python
    async for chunk in chat.astream(messages):
        content = chunk.content
        if isinstance(content, str) and content:
            yield content
    ```
*   **비동기 제너레이터 `send()` 호출 제한 및 프라이밍**:
    *   비동기 스트리밍 호출 시, 한 반복 주기 내에서 `next()`와 `.send()`를 혼용하여 발생하는 원치 않는 `None` 값의 이중 주입 이슈를 원천 차단합니다.
    *   제너레이터로 양방향 값을 주입받는 경우, 루프 시작 전 최초 1회만 `next(generator)` 또는 `await generator.__anext__()`를 호출하여 **프라이밍(Priming)**한 후, 본 루프 내에서는 오직 `send(값)`만 호출하여 제너레이터를 안전하게 작동시킵니다.
*   **파일 다운로드 API 규격**:
    *   문서 다운로드 및 에셋 반환의 경우 서버 메모리 오버헤드를 회피하기 위해 `StreamingResponse`가 아닌 `FileResponse` 사용을 최우선 권장합니다.
    *   브라우저의 불필요한 자동 인라인 다운로드나 렌더링 오작동을 차단하기 위해 `Content-Disposition: attachment; filename="..."` 헤더를 명시적으로 세팅하여 반환합니다.

---

## 7. LLM 및 에이전트 로깅 콜백 통일

*   디버깅과 API 비용 파악을 용이하게 하기 위해, LLM 요청 프롬프트와 반환된 답변 메시지를 표준 규격으로 콘솔 및 파일에 기록하는 **커스텀 로깅 콜백 핸들러(Custom Logging Callback)**를 전역적으로 정의하여 주입합니다.
*   백엔드 로그 출력 시 가독성을 높이기 위해 `colorlog` 라이브러리를 활용해 레벨별로 일관된 색상 포맷팅을 적용합니다.
*   **SQLAlchemy 쿼리 로깅 연동**:
    *   SQL 실행 시 생성되는 로깅 데이터는 별도 print문이나 stdout이 아닌 파이썬 표준 `logging` 모듈로 통합 연동합니다.
    *   `logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)` 설정을 백엔드 기동 로깅 핸들러에 통합하여 SQL 포맷에 맞춰 에이전트 로그와 함께 하나의 통합 파일/콘솔 스트림으로 관리합니다.

---

## 8. 에이전트 공유 상태 (Shared State) 설계 컨벤션

*   LangGraph 오케스트레이션 노드(질문 분석, 로컬 RAG, 외부 브라우징 등) 간 데이터 공유를 위해 사용하는 `Shared State`는 단일 Pydantic 스키마 구조로 프로젝트 루트에 공통 정의합니다.
*   에이전트 노드는 해당 스키마에 정의된 지정 Key-Value 속성만을 활용해 상태를 조회 및 비동기 업데이트해야 합니다.

---

## 9. FastAPI 앱 수명 주기(Lifespan) 및 CORS 설정

*   데이터베이스 연결 풀(`Connection Pool`)은 서버 시작 시 오픈하고, 종료 시 세션을 완전히 회수하도록 FastAPI **수명 주기(`lifespan`) 핸들러**로 관리합니다.
*   Next.js 프론트엔드 도메인에 대한 접근을 지원하기 위해 공통 CORS 미들웨어를 정의하고 허용 도메인은 환경 변수를 통해 제어합니다.

---

## 10. 환경 변수 및 보안 규칙

*   **환경 변수 관리**: API 키(OpenAI, Tavily 등) 및 DB 접속 URL은 소스 코드에 절대 직접 기재하지 않으며, `.env` 파일과 `Pydantic-Settings`를 통해 주입되도록 강제합니다.
*   **로컬 파일 도구 보안**: 로컬 파일 시스템을 조작하는 도구를 구현/사용할 때는 루트 디렉토리 밖으로 탈출할 수 없도록 상대 경로(`..`) 입력 유무를 엄격하게 검증하는 차단 로직을 포함합니다.
*   **도구(Tool) 개발 보안 및 실행 제어**: 외부 API 인증 정보 등 민감한 값은 LLM에 노출하지 않도록 `context_schema`를 통해 백엔드 내부로만 전달하며, 요약 없이 즉각 응답이 필요한 데이터 도구는 `return_direct=True` 속성을 강제합니다.

---

## 11. 파이썬 모듈 캐싱 기반 싱글톤(Singleton) 설계 규칙

*   데이터베이스 접속 엔진 인스턴스, 환경 설정(`Settings`), 외부 API 통합 클라이언트 등 시스템 전반에 걸쳐 유일해야 하는 자원은 파이썬 자체의 **모듈 임포트 캐싱(`sys.modules`) 메커니즘**을 적극 활용하여 싱글톤 패턴으로 구현합니다.
*   클래스 생성자에 괄호를 붙여 매번 객체를 다중 인스턴스로 생성하는 행위를 금지하며, 해당 모듈 파일 내에서 미리 생성해 둔 전역 변수를 `from module import instance`로 불러와 사용하게 함으로써 자원 낭비 및 객체 상태 충돌을 원천 차단합니다.

---

## 12. 표준 Docstring 및 문서화 가이드

*   모든 모듈, 함수 및 클래스에는 파이썬 표준 **Google 스타일 Docstring 포맷**을 필수로 기술하여 협업 시 가독성을 최대화합니다.
*   Sphinx를 활용해 프로젝트 아키텍처 문서를 코드 기반으로 자동 생성할 수 있도록, docstring 내부에 매개변수의 타입, 설명, 반환 값 및 발생 가능 예외(`Raises`)를 다음과 같이 표준 형태로 명세합니다:
    ```python
    def perform_similarity_search(query_vector: list[float], limit: int = 5) -> list[dict]:
        """Perform similarity search on the pgvector database.
        
        Args:
            query_vector (list[float]): The embedded query vector to compare.
            limit (int): The maximum number of relevant passages to retrieve. Default is 5.
            
        Returns:
            list[dict]: A list of mapped dictionaries containing document content and similarity score.
            
        Raises:
            DatabaseConnectionError: If the connection pool to the database is unavailable.
        """
    ```
