# Bist Mini 2 - Backend Code Methods & Class Specification

본 문서는 `Bist Mini 2` 백엔드 프로젝트의 전체 파이썬 소스 코드에 대하여 파일별로 정의된 모든 클래스(Classes)와 개별 함수/메소드(Methods/Functions)를 분석하여 해당 역할, 매개변수(Parameters), 반환값(Returns) 및 예외 처리(Exceptions) 등을 상세히 명세합니다.

---

## 📂 백엔드 전체 파일 구조 및 개요
백엔드는 **FastAPI** 프레임워크를 기반으로 하며, 비즈니스 관심사를 명확히 격리하기 위해 **Controller(Endpoint) - Service - DAO - Entity(SQLAlchemy ORM)** 구조로 설계된 레이어드 아키텍처를 채택하고 있습니다. 

```
backend/
├── main.py (FastAPI App Entry & Lifecycle)
└── api/
    ├── common/ (설정, 인증, 공통 RAG 파이프라인, 전역 예외 처리)
    ├── database/ (비동기 DB 세션 설정 및 공통 DTO/Entity 매핑 클래스)
    └── v1/ (API 버전 1 라우터 및 각 기능 도메인 폴더)
        ├── api_router.py (v1 라우터 통합 허브)
        ├── health/ (시스템 헬스체크 및 개발자 포털 대시보드)
        ├── auth/ (사용자 인증 및 로그인 토큰 발급)
        ├── member/ (사용자 관리 및 회원 가입/수정/탈퇴)
        ├── chat/ (LangGraph RAG 기반의 챗봇 대화 세션 관리)
        ├── gems/ (사용자 정의 커스텀 연구 RAG 에이전트 공간)
        ├── notification/ (SSE 기반의 비동기 알림 통합 브로드캐스터)
        ├── research_gap/ (비동기 문헌 분석, 매트릭스 도출, 공백 분석, AI 추천 로드맵)
        └── similarity_search/ (도메인별 RAG 유사 논문 순수 검색 API)
```

---

## 1. ⚙️ 공통 엔트리포인트 및 공통 인프라 (Common Modules)

### 📄 [main.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/main.py)
애플리케이션 구동 및 Lifespan(Startup/Shutdown) 이벤트, 전역 CORS 및 캐싱 방지 미들웨어, 정적 파일 마운팅, 로그 포맷 설정을 제어하는 중심 진입점 파일입니다.

#### 1) 클래스
*   **`NoCacheStaticFiles(StaticFiles)`**: `FastAPI` 정적 파일을 전달할 때 브라우저 캐싱을 완전히 강제 차단하기 위한 커스텀 정적 파일 클래스입니다.
    *   `file_response(self, *args, **kwargs) -> Response`: 부모 메서드 호출 결과인 파일 응답 객체에 `Cache-Control: no-cache, no-store, must-revalidate`, `Pragma: no-cache`, `Expires: 0` 헤더를 주입하여 반환합니다.

#### 2) 함수 및 데코레이터
*   **`@asynccontextmanager lifespan(app: FastAPI)`**: 애플리케이션 시작(Startup) 및 종료(Shutdown) 수명 주기 동안 비동기 인프라를 연결하고 관리하는 전역 이벤트 관리용 데코레이터 함수입니다.
    *   **내부 함수 `custom_signal_handler(signum, frame)`**: Uvicorn 리로드 동작 시 SSE 커넥션 교착(hang)이 일어나는 현상을 방지하고자 `SIGINT`/`SIGTERM` 발생 시 즉각 알림 브로드캐스터 리소스를 닫는 시그널 핸들러입니다.
    *   **내부 비동기 함수 `cleanup_daemon()`**: 1분 스캔 주기로 DB 백그라운드 스레드를 동작시켜, 30분 이상 상호작용이 멈춘 만료된 보안 샌드박스 임시 세션을 소거(`wipe_out_expired_sessions`)하는 백그라운드 데몬입니다.
    *   **Startup 액션**: pgvector 데이터베이스 익스텐션 활성화, 테이블 스키마 자동 동기화(create_all), `cleanup_daemon` 태스크 실행.
    *   **Shutdown 액션**: `cleanup_daemon` 취소, 알림 브로드캐스터 강제 해제, 비동기 엔진 풀 반환(`engine.dispose`), 미종료 백그라운드 asyncio 태스크 일괄 취소 처리.
*   **`@app.middleware("http") add_cache_control_header(request: Request, call_next) -> Response`**: v1 API 요청(`settings.API_V1_STR`로 시작하는 경로)에 대하여 캐시 무효화 응답 헤더(`Cache-Control: no-store, no-cache...`)를 주입하는 전역 HTTP 미들웨어 함수입니다.
*   **`@app.get("/") home(request: Request) -> templates.TemplateResponse`**: 루트 경로 접근 시 Bist 개발자 포털 웰컴 대시보드 화면(`index.html`)을 렌더링하여 서빙하는 홈 라우터입니다.

---

### 📄 [api/common/auth.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/auth.py)
JWT(JSON Web Token) 생성 및 디코딩, 사용자 권한 및 역할을 검사하는 FastAPI 종속성 주입 및 인증 유틸리티 파일입니다.

#### 1) 클래스 및 타입 정의
*   **`UserPayload(TypedDict)`**: JWT 토큰 페이로드 데이터 스키마입니다.
    *   `sub: str` (사용자 계정 ID), `mrole: str` (사용자 권한/역할)

#### 2) 함수 및 의존성 주입 정의
*   **`create_token(mid: str, mrole: str) -> str`**: 지정된 사용자 식별자 ID와 역할명을 포함하여 JWT 액세스 토큰을 발급하는 암호화 생성 함수입니다.
    *   **Parameters**: `mid` (회원 ID), `mrole` (회원 역할)
    *   **Returns**: HS256 알고리즘 및 비밀 키로 서명된 만료 기간(24시간)이 설정된 JWT 스트링.
*   **`get_payload(token: str) -> dict`**: JWT 토큰의 서명을 검증하고 디코딩하여 페이로드 딕셔너리를 반환합니다.
    *   **Parameters**: `token` (검증 및 복호화할 토큰 스트링)
    *   **Raises**: `jwt.ExpiredSignatureError` (만료된 경우 401 에러), `jwt.MissingRequiredClaimError` (필수 claim 'sub' 누락), `HTTPException` (기타 유효하지 않은 서명 시 401 에러)
*   **`async def verify_access_token(request: Request, access_token: Annotated[str | None, Depends(_oauth2_scheme)] = None) -> UserPayload`**: 요청 헤더(`Authorization: Bearer <token>`) 또는 쿼리 파라미터(`?accessToken=<token>`)로부터 토큰을 추출하여 검증을 거친 후 페이로드를 제공하는 FastAPI 공통 종속성 함수입니다.
    *   **Parameters**: `request` (HTTP Request 객체), `access_token` (추출된 토큰)
    *   **Returns**: 검증 성공한 사용자 ID와 역할 딕셔너리(`UserPayload`).
    *   **Raises**: `HTTPException` (토큰 누락 및 비정상 서명 시 401 Unauthorized 에러)
*   **`require_roles(roles: list[str])`**: 특정 역할(예: `ROLE_ADMIN`)을 지닌 인증된 회원만 해당 API 컨트롤러에 진입할 수 있도록 인가 검사를 가로채는 클로저 형태의 종속성 빌더 함수입니다.
    *   **Parameters**: `roles` (진입이 허용되는 권한 리스트)
    *   **Returns**: `verify_access_token`이 제공한 `UserPayload` 중 사용자의 `mrole` 값을 체크하여 예외를 발생시키거나 페이로드를 통과시켜주는 비동기 검사 함수(`check_roles`).
    *   **Raises**: `HTTPException` (접근 권한 부족 시 403 Forbidden 에러)
*   **`LoginCheckDep` & `AdminCheckDep`**: 비즈니스 컨트롤러에서 각각 일반 로그인 인증 및 어드민 전역 권한 체크를 어노테이션 형태로 쉽게 주입받기 위한 Annotated 타입 에일리어스 정보입니다.

---

### 📄 [api/common/config.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/config.py)
Pydantic `BaseSettings`를 활용하여 `.env` 환경 변수를 파싱하고, 시스템 설정 정보(애플리케이션 설정, JWT 보안키, 데이터베이스 접속 주소, OpenAI API Key 등)를 전역 싱글톤으로 제공합니다.

#### 1) 클래스
*   **`Settings(BaseSettings)`**: 애플리케이션 기동 시 실행 환경에 맞춰 필요한 환경 매개변수를 바인딩하는 설정 모델입니다.
    *   `model_config`: `.env` 파일을 로드하고 정의되지 않은 불필요 필드를 무시(`ignore`)하는 Pydantic 설정 메타데이터 객체입니다.
    *   `PGVECTOR_URL` (Property): 비동기 psycopg3 연동을 위해 `DATABASE_URL` 내의 드라이버 명칭(`postgresql+asyncpg://`)을 `postgresql+psycopg_async://`로 문자열 교체하여 반환하는 프로퍼티 메서드입니다.

---

### 📄 [api/common/exceptions.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/exceptions.py)
애플리케이션 전반에서 비즈니스 로직 예외 상황을 도메인별로 세분화하여 처리하고 발생시키기 위한 커스텀 예외 클래스 세트입니다.

#### 1) 클래스
*   **`MemberNotFoundError(Exception)`**: 요청한 사용자 정보(mid)가 존재하지 않을 때 호출되는 404용 예외입니다. (기본 에러 코드: `MEMBER_NOT_FOUND`)
*   **`InvalidPasswordError(Exception)`**: 회원 자격 증명 검증(로그인) 도중 비밀번호가 틀렸을 때 발생하는 401용 예외입니다. (기본 에러 코드: `INVALID_PASSWORD`)
*   **`BusinessException(Exception)`**: 데이터 중복, 유효성 위반 등 일반적인 비즈니스 규칙 위반 상황 시 400 응답을 트리거하기 위해 던지는 기반 예외입니다. (기본 에러 코드: `BUSINESS_ERROR`)
*   **`TaskNotFoundError(Exception)`**: 백그라운드 연구 공백 배치 작업 조회 시 매칭되는 UUID 태스크를 찾을 수 없을 때 발생하는 404용 예외입니다. (기본 에러 코드: `TASK_NOT_FOUND`)

---

### 📄 [api/common/exception_handler.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/exception_handler.py)
FastAPI 앱 내에서 발생하는 모든 표준 HTTP 예외, 입력값 검증 에러 및 개발자 커스텀 예외를 수신하여 동일한 형식의 에러 JSON 포맷(`{ "status": "error", "message": "원인 설명" }`)으로 가공하여 반환하도록 전역 핸들러들을 등록합니다.

#### 1) 함수 및 내부 예외 핸들러
*   **`register_exception_handler(app: FastAPI)`**: FastAPI 인스턴스를 전달받아 전역 미들웨어성 예외 처리기 루틴을 오버라이딩하여 연동해 둡니다.
    *   `http_exception_handler(...)`: `StarletteHTTPException` 감증용 핸들러. HTTP 상태 코드를 유지한 채 에러 메세지를 래핑합니다.
    *   `validation_exception_handler(...)`: Pydantic 구조 유효성 검사 실패(`RequestValidationError`) 핸들러. 실패가 발생한 위치(`loc`)와 발생 이유(`msg`)를 `" -> "` 및 `" / "`로 결합하여 400 Bad Request 에러로 치환합니다.
    *   `member_not_found_handler(...)`: `MemberNotFoundError` 발생 시 404 JSONResponse 변환.
    *   `task_not_found_handler(...)`: `TaskNotFoundError` 발생 시 404 JSONResponse 변환.
    *   `invalid_password_handler(...)`: `InvalidPasswordError` 발생 시 401 JSONResponse 변환.
    *   `business_exception_handler(...)`: `BusinessException` 발생 시 400 JSONResponse 변환.
    *   `general_exception_handler(...)`: 그 외 시스템이 수집하지 못한 전역 런타임 오류 핸들러. 로깅에 상세 스택트레이스를 인쇄(logger.exception)하고 클라이언트에는 보안상 상세 내용을 숨긴 채 `500 Internal Server Error` 응답을 처리합니다.

---

### 📄 [api/common/rag_pipeline.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/rag_pipeline.py)
3대 학술 도메인(생명공학 q-bio.GN, 컴퓨터과학 cs.NE, 천문학 astro-ph.EP)의 공통 pgvector 임베딩 검색 엔진 기능 및 LangGraph 다중 에이전트 구조에 물려줄 결합용 @tool 함수들을 관리하는 RAG의 코어 인터페이스 모듈입니다.

#### 1) 클래스
*   **`CommonRagPipeline`**: pgvector 비동기 드라이버를 통해 데이터베이스에 보존된 각 컬렉션 영역에서 코사인 유사도 벡터 계산을 대행하는 서비스 아키텍처 클래스입니다.
    *   `__init__(self) -> None`: 로거 및 지연 인스턴스 참조 변수를 초기화합니다.
    *   `get_embeddings(self)`: 임베딩 생성 모델 인스턴스(`OpenAIEmbeddings`)를 최초 필요 시점(Lazy Loading)에 `init_embeddings` 호출로 확보 및 보관하여 반환합니다. (기본 모델: `text-embedding-3-large`)
    *   `async def similarity_search(self, domain: str, query: str, k: int = 3) -> List[Dict[str, Any]]`: 지정한 도메인 컬렉션명을 기준으로 입력 쿼리에 대한 벡터 코사인 유사성 문장을 상위 k개 추출합니다.
        *   **Parameters**: `domain` (검색 영역), `query` (질의 구문), `k` (반환 개수)
        *   **Returns**: 유사 문서 리스트. 각 딕셔너리는 `doc_id` (arxiv_id), `title` (논문명), `text_chunk` (추출 구절), `score` (1.0 - Cosine Distance 점수) 포맷을 가집니다.
        *   **Raises**: `ValueError` (지원하지 않는 도메인인 경우 예외 발생)

#### 2) LangGraph 바인딩용 RAG 도구 (Tools) 함수
*   **`@tool async def search_bio_papers(query: str, runtime: ToolRuntime, k: int = 3) -> Command`**: 생명공학/유전체학(q-bio.GN) 논문 RAG 검색용 LangGraph 전용 도구 함수입니다.
    *   **Parameters**: `query` (영문 검색어), `runtime` (툴 실행 컨텍스트), `k` (추출 개수)
    *   **Returns**: 유사 논문 텍스트 라인 결과 조각을 담은 `ToolMessage` 객체 및 `sources` 출처 정보를 업데이트 시킬 흐름 제어 `Command` 객체.
*   **`@tool async def search_cs_papers(query: str, runtime: ToolRuntime, k: int = 3) -> Command`**: 컴퓨터 과학(cs.NE) 신경망 및 머신러닝 논문 RAG 검색용 툴 함수입니다. (동작 및 반환 규격은 bio 툴과 동일)
*   **`@tool async def search_astronomy_papers(query: str, runtime: ToolRuntime, k: int = 3) -> Command`**: 천체물리학(astro-ph.EP) 논문 RAG 검색용 툴 함수입니다. (동작 및 반환 규격은 bio 툴과 동일)

---

## 2. 🗄️ 데이터베이스 및 자격증명 공통 설정 (Database Configuration)

### 📄 [api/database/config/dbsession.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/database/config/dbsession.py)
SQLAlchemy 비동기 엔진 및 세션 메이커를 선언하고, FastAPI 라우터 생명주기에 동기화되어 DB 커넥션 트랜잭션의 커밋과 롤백을 제어하는 세션 생성 제너레이터를 구성합니다.

#### 1) 함수 및 의존성 주입 정의
*   **`async def get_orm_session() -> AsyncGenerator[AsyncSession, None]`**: 데이터베이스 비동기 세션을 매 요청마다 분할해서 생성해 주는 제너레이터 함수입니다.
    *   **Yields**: `AsyncSession` 인스턴스.
    *   **로직**: 세션을 열어 요청 처리를 위해 yield한 뒤, 오류 없이 처리가 완료되면 트랜잭션 커밋(`await orm_session.commit()`)을 자동 실행합니다. 도중 런타임 예외가 던져진 경우에는 롤백(`await orm_session.rollback()`)을 명시 실행하고 최종적으로 자원을 차단(`await orm_session.close()`)합니다.
*   **`OrmSessionDep`**: `get_orm_session` 제너레이터를 FastAPI 컨트롤러 파라미터로 Annotated Depends 주입하기 위해 매핑해 둔 전역 타입 Alias입니다.

---

### 📄 [api/database/config/entity_base.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/database/config/entity_base.py)
SQLAlchemy 기반의 비동기 ORM 테이블 정의 시 사용하는 다중 상속 매핑 기반 클래스(`Base`) 파일입니다.

#### 1) 클래스
*   **`Base(AsyncAttrs, DeclarativeBase)`**: 비동기 필드 접근 지원(`AsyncAttrs`) 및 ORM 매핑 메타데이터 관리를 결합한 공통 Entity 기반 추상 부모 클래스입니다.

---

### 📄 [api/database/config/psycopg_pool.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/database/config/psycopg_pool.py)
LangGraph 프레임워크의 영구 저장소 체크포인터인 `AsyncPostgresSaver`가 내부적으로 요구하는 비동기 psycopg3 데이터베이스 풀 객체(`psycopg_pool`)를 생성합니다.

#### 1) 전역 객체
*   **`psycopg_pool`**: `AsyncConnectionPool` 인스턴스. `DATABASE_URL` 내의 드라이버 지시어를 psycopg3 통신 스키마(`postgresql://`)로 포매팅하여 풀을 비활성(`open=False`) 형태로 바인딩해 두고, 개별 에이전트 인스턴스 가동 시점이나 애플리케이션 실행 단계에서 지연 오픈할 수 있도록 싱글톤 형태로 제공합니다.

---

### 📄 [api/database/config/dto_base.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/database/config/dto_base.py)
FastAPI 입출력 자격 증명을 위한 Pydantic DTO의 최상위 부모 규격 및 성공/실패 시 전송할 전역 API 공통 JSON 응답 구조를 정의합니다.

#### 1) 클래스
*   **`BaseDTO(BaseModel)`**: 프로젝트 내 모든 Pydantic 모델의 기반 클래스입니다.
    *   `model_config`: `ConfigDict(from_attributes=True)` 설정을 상속함으로써, SQLAlchemy ORM 객체의 속성을 Pydantic DTO 필드로 자동 파싱 및 바인딩(`model_validate`) 가능하도록 합니다.
*   **`SuccessResponse(BaseDTO)`**: 모든 정상 처리 요청 반환 시 주입하는 최상단 응답 래퍼 DTO 클래스입니다.
    *   `status: str = "success"`, `data: Any` (실제 반환할 가치 데이터 본문)
*   **`ErrorResponse(BaseDTO)`**: 비즈니스 및 시스템 장애 시 반환하는 실패 응답 구조 DTO 클래스입니다.
    *   `status: str = "error"`, `message: str` (구체적인 오류 문구 내용)

---

## 3. 🌐 라우터 분기 통합 허브 (v1 API Router Hub)

### 📄 [api/v1/api_router.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/api_router.py)
v1 하위에 설계된 9대 기능성 도메인의 API 모듈 라우터 인스턴스를 하나로 취합하여 상위 FastAPI 인스턴스에 탑재할 수 있도록 브릿지 역할을 수행하는 라우터 레지스트리 허브 파일입니다.

#### 1) 전역 객체
*   **`api_router`**: `APIRouter` 인스턴스. `health`, `auth`, `member`, `chat`, `research_gap`, `gems`, `notification`, `similarity_search`, `defense_arena`의 개별 router 파일들을 `include_router`하여 통합 v1 하위 경로 구조를 정비합니다.

---

## 4. 🏥 시스템 상태 및 포털 렌더링 도메인 (Health Domain)

### 📄 [api/v1/health/endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/health/endpoints.py)
시스템 기본 기동 정보를 점검하는 API 및 개발환경 분석 도구인 통합 개발자 포털 대시보드(Bist DevPortal)의 렌더링 메타데이터 컨텍스트를 다이내믹 빌드하는 제어 파일입니다.

#### 1) 함수 및 라우터
*   **`@router.get("/health") async def health_check() -> SuccessResponse`**: 백엔드 인스턴스의 기본적인 생존 여부 및 설정 상태, 누적 가동 시간(Uptime) 정보를 반환합니다.
*   **`async def get_dashboard_context(request: Request) -> dict`**: Bist DevPortal 내에 가시화할 시스템 상태 일괄 보고서용 사전 데이터를 실시간 구성합니다.
    *   **Parameters**: `request` (HTTP Request 객체)
    *   **Returns**: 아래의 대시보드 세부 컴포넌트 정보가 담긴 대규모 딕셔너리 정보.
        *   **Overview**: Uptime 포맷 변경 텍스트, 데이터베이스 연결 유무, OpenAI Key 로드 유무.
        *   **API & Test Map**: FastAPI 내부 등록 라우트를 파싱하여 주입 의존성 기반 JWT 검증 유무 판별 및 연동될 파이썬 유닛 테스트 파일 매핑 확인.
        *   **Next.js Router Map**: 프론트엔드(`frontend/src/app`) 폴더를 순회하여 `page.js` 위치 파악 및 Jest 테스트 파일 실존 여부 결합.
        *   **Settings & Config**: DB 주소, 토큰 암호키 등 패스워드가 포함될 필드를 정규식 마스킹(`***`)으로 필터링 처리한 환경 변수 리스트.
        *   **Git Changelog**: Subprocess로 git log 명령어를 실행하여 최근 20개의 프로젝트 커밋 내역(해시, 작성자, 시간, 제목) 추출.
        *   **Database ERD (reflection)**: SQLAlchemy `inspect`를 호출해 데이터베이스 내 전체 스키마 정보를 동적으로 읽어 외래키 관계를 파악하고, 웹 화면 렌더링용 **Mermaid ERD 다이어그램 텍스트** 코드를 실시간 합성.
*   **`@router.get("/erd") async def get_erd(request: Request)`**: 구식 ERD 경로 진입 시 새 포털의 ERD 탭(`/#db-erd`)으로 리다이렉션 처리합니다.
*   **`@router.get("/dashboard") async def get_dashboard(request: Request)`**: 구식 대시보드 진입 시 루트 포털('/')로 리다이렉션 처리합니다.

---

## 5. 🔑 인증 및 토큰 발급 도메인 (Auth Domain)

### 📄 [api/v1/auth/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/auth/services.py)
로그인을 시도하는 사용자의 계정 및 비밀번호 검증과 이를 통한 토큰 발행 비즈니스 로직을 처리합니다.

#### 1) 클래스
*   **`AuthService`**: 인증 트랜잭션을 지휘하는 비즈니스 레이어 서비스 클래스입니다.
    *   `__init__(self, member_service: MemberServiceDep) -> None`: `MemberService` 의존성을 주입받아 초기화합니다.
    *   `async def login(self, username: str, password: str) -> dict`: 사용자의 자격 증명을 가려 JWT 액세스 토큰 명세를 발급합니다.
        *   **Parameters**: `username` (계정 ID), `password` (비밀번호)
        *   **Returns**: `access_token`, `token_type` (bearer), `username`, `role` 정보를 지닌 JSON용 딕셔너리 객체.

---

### 📄 [api/v1/auth/models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/auth/models.py)
인증 관련 엔드포인트에서 입출력할 Pydantic DTO 명세 파일입니다.

#### 1) 클래스
*   **`TokenResponse(BaseDTO)`**: 로그인 성공 시 최종 반환할 토큰 래퍼 정보 구조입니다.
    *   `access_token: str`, `token_type: str = "bearer"`, `username: str`, `role: str`
*   **`UserInfoResponse(BaseDTO)`**: 내 정보 가져오기(`/auth/me`) 시 응답할 유저 메타 구조입니다.
    *   `username: str`, `role: str`

---

### 📄 [api/v1/auth/endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/auth/endpoints.py)
OAuth2 및 사용자 인증 관련 엔드포인트를 노출하는 컨트롤러 게이트웨이 파일입니다.

#### 1) 함수 및 라우터
*   **`@router.post("/login") async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], auth_service: AuthServiceDep) -> TokenResponse`**: Swagger UI 자물쇠(`Authorize`) 인증 연동 및 클라이언트 로그인을 지원하기 위해 평문 토큰 객체를 반환하는 OAuth2 엔드포인트입니다.
*   **`@router.get("/me") async def get_me(payload: LoginCheckDep) -> SuccessResponse`**: JWT 토큰을 판독하여 현재 인증된 사용자의 정보(`UserInfoResponse`)를 공통 응답 규격에 주입해 가져옵니다.
*   **`@router.get("/admin-only") async def admin_only(payload: AdminCheckDep) -> SuccessResponse`**: 어드민 역할 권한을 지닌 사용자만 응답을 획득할 수 있도록 허용하는 테스트 게이트웨이입니다.

---

## 6. 👤 사용자 및 프로필 도메인 (Member Domain)

### 📄 [api/v1/member/entity.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/member/entity.py)
데이터베이스 `member` 테이블에 영속화 매핑되어 사용자의 고유 식별자, 해시 비밀번호, 역할, 이메일, 활성화 여부 컬럼 정보를 보관하는 SQLAlchemy 테이블 엔티티 클래스 정의 파일입니다.

#### 1) 클래스
*   **`MemberEntity(Base)`**: `member` 테이블 매핑 클래스입니다.
    *   **Fields**: `mid` (String(20), PK), `mname` (String(20)), `mpassword` (String(255)), `memail` (String(255), Unique), `menabled` (Boolean), `mrole` (String(20)).

---

### 📄 [api/v1/member/models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/member/models.py)
회원 가입 및 수정 단계에서 입력 수치 및 포맷(이메일 검증, 아이디 패스워드 최소 길이)을 필터링하고 결과를 리턴할 Pydantic DTO 명세입니다.

#### 1) 클래스
*   **`MemberJoinRequest(BaseDTO)`**: 회원 가입 시 필드 제한 검증용 DTO (mid 5~20자, memail EmailStr 포맷 등).
*   **`MemberJoinResponse(BaseDTO)`**: 비밀번호 해시 데이터를 가리고 결과를 알리는 응답 DTO.
*   **`MemberInfoResponse(BaseDTO)`**: 사용자 정보 상세 조회용 DTO.
*   **`MemberModifyRequest(BaseDTO)`**: 수정 요청 DTO. 부분 변경을 지원하기 위해 선택형(Optional)으로 필드가 정의되어 있습니다.
*   **`MemberModifyResponse(BaseDTO)`**: 비밀번호를 암무적으로 배제한 정보 변경 결과 반환 DTO.

---

### 📄 [api/v1/member/dao.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/member/dao.py)
`member` 테이블에 대하여 ORM 문법을 적용해 실제 생성, 수정, 상세 조회, 삭제(CRUD) SQL을 날리는 비즈니스 데이터 액세스 클래스입니다.

#### 1) 클래스
*   **`MemberDao`**: 회원 DB 물리 처리를 총괄하는 DAO 클래스입니다.
    *   `__init__(self, orm_session: OrmSessionDep)`: 데이터베이스 세션을 주입받아 초기화합니다.
    *   `async def insert(self, member_entity: MemberEntity) -> MemberEntity`: 회원 엔티티 객체를 추가하고 동기화(flush, refresh)를 수행합니다.
    *   `async def update(self, member_entity: MemberEntity) -> MemberEntity`: 특정 ID 회원을 조회한 뒤, 전달된 갱신값(비밀번호, 이메일, 활성화)만 덮어씌워 flush를 수행합니다.
        *   **Raises**: `BusinessException` (DB에 수정 대상이 존재하지 않을 시 예외)
    *   `async def delete(self, mid: str)`: 회원을 테이블에서 삭제하는 Raw SQL DELETE를 전송합니다.
    *   `async def select_by_mid(self, mid: str) -> MemberEntity | None`: 회원 ID를 기본키 조건으로 삼아 매칭되는 정보를 단건 조회합니다.

---

### 📄 [api/v1/member/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/member/services.py)
회원가입 중복 체크, 패스워드 단방향 해싱 암호화(bcrypt), 로그인 자격 증명 검증 등 실질적인 회원 비즈니스 로직을 집행합니다.

#### 1) 클래스
*   **`MemberService`**: 회원 업무 비즈니스 서비스 클래스입니다.
    *   `__init__(self, member_dao: MemberDaoDep) -> None`: 회원 관리용 DAO를 주입받습니다.
    *   `async def join(self, member_entity: MemberEntity) -> MemberEntity`: 아이디 중복 유무를 파악하고 입력된 평문 패스워드를 bcrypt 솔트 암호화 해시 값으로 치환하여 DB에 영구 등록합니다.
        *   **Raises**: `BusinessException` (이미 가입된 mid인 경우 ID 중복 예외 발생)
    *   `async def authenticate(self, mid: str, password: str) -> MemberEntity`: 아이디가 존재하는지 가리고 bcrypt 대조 검사(`checkpw`)를 거쳐 인증 여부를 확인합니다.
        *   **Raises**: `MemberNotFoundError` (가입되지 않은 경우), `InvalidPasswordError` (비밀번호 불일치 시)
    *   `async def read(self, mid: str) -> MemberEntity | None`: 특정 ID에 연동되는 프로필 데이터를 읽습니다.
    *   `async def modify(self, member_entity: MemberEntity) -> MemberEntity`: 회원 수정을 보조하되 비밀번호가 교체된 경우 해싱 처리를 거친 후 DAO 수정을 호출합니다.
    *   `async def delete(self, mid: str)`: 회원 영구 삭제 작업을 수행합니다.

---

### 📄 [api/v1/member/endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/member/endpoints.py)
회원 가입, 조회, 정보 갱신 및 관리자의 강제 탈퇴 명령을 수신하는 컨트롤러 파일입니다.

#### 1) 함수 및 라우터
*   **`@router.post("/join") async def join(...) -> SuccessResponse`**: 회원가입 요청 DTO를 받아 가입을 실행하고 `201 Created` 헤더와 회원 정보를 반환합니다.
*   **`@router.get("/info") async def info(...) -> SuccessResponse`**: 로그인 회원 본인의 상세 마이프로필 정보를 꺼냅니다.
*   **`@router.put("/modify") async def update(...) -> SuccessResponse`**: 변경을 요청받은 필드값에 대해 내 회원 정보를 변경 적용합니다.
*   **`@router.delete("/delete/{mid}") async def delete(...) -> SuccessResponse`**: 어드민 권한 검사 통과 시 특정 회원을 강제로 추방 탈퇴 조치합니다.

---

## 7. 💬 챗봇 RAG 및 대화 내역 도메인 (Chat Domain)

### 📄 [api/v1/chat/entity.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/entity.py)
채팅방의 생성 메타데이터 테이블 및 챗봇이 유사 문헌을 근거로 제시했을 때 참고한 논문 출처들을 기록해 두는 테이블의 엔티티 정의 파일입니다.

#### 1) 클래스
*   **`ChatSessionEntity(Base)`**: `chat_session` 테이블 매핑 클래스입니다. 방 생성 UUID 식별자와 개설 주인을 판별합니다.
*   **`ChatSourceEntity(Base)`**: `chat_source` 테이블 매핑 클래스입니다. 특정 방(session_id)의 몇 번째 대화(message_index)에 어떤 arXiv ID와 요약 논문이 활용되었는지 기록하며, 부모 세션이 소거되면 ON DELETE CASCADE 구조로 자동 연쇄 제거됩니다.

---

### 📄 [api/v1/chat/models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/models.py)
채팅방 생성, 제목 변경, 대화 메시지 의뢰 및 참고 논문과 히스토리 내역 정보를 주고받기 위한 Pydantic DTO 포맷 파일입니다.

#### 1) 클래스
*   **`ChatSessionCreateRequest` & `ChatSessionUpdateRequest`**: 대화방 타이틀 생성 및 수정용 DTO.
*   **`ChatSessionResponse`**: 대화방 단건 정보 응답 DTO.
*   **`ChatMessageRequest`**: 유저 RAG 질문 텍스트 전송용 DTO.
*   **`ChatMessageResponse`**: AI 답변 마크다운 텍스트와 참고 문헌 리스트(arxiv_id, title, summary)를 담는 DTO.
*   **`ChatHistoryItem`**: 누적 히스토리 반환용 DTO. 발화 주체(user/assistant)와 대화 본문 및 결합된 출처 리스트로 이루어집니다.
*   **응답 래퍼 DTO**: `ChatSessionListResponseWrapper`, `ChatSessionResponseWrapper`, `ChatMessageResponseWrapper`, `ChatHistoryResponseWrapper`.

---

### 📄 [api/v1/chat/dao.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/dao.py)
대화방 메타데이터 생성/목록/삭제/수정 쿼리 집행 및 AI RAG 답변에 근거가 되었던 출처 논문 리스트의 일괄 데이터 적재 작업을 처리하는 DAO 클래스 파일입니다.

#### 1) 클래스
*   **`ChatSessionDao`**: 대화 정보 DB 처리를 대행합니다.
    *   `__init__(self, orm_session: OrmSessionDep)`: 세션을 바인딩합니다.
    *   `async def insert(self, chat_session_entity: ChatSessionEntity) -> ChatSessionEntity`: 대화방 메타 데이터를 삽입합니다.
    *   `async def select_by_member(self, member_id: str) -> list[ChatSessionEntity]`: 회원 ID에 종속된 활성 대화방을 최신 일자순으로 가져옵니다.
    *   `async def select_by_id(self, session_id: str) -> ChatSessionEntity | None`: 세션 식별자로 단건의 방 정보를 획득합니다.
    *   `async def delete(self, session_id: str)`: 특정 대화방을 DB에서 강제 삭제합니다.
    *   `async def update_title(self, session_id: str, title: str) -> None`: 대화방 타이틀을 새 이름으로 갱신합니다.
    *   `async def insert_sources(self, session_id: str, message_index: int, sources: list[dict]) -> None`: 생성된 챗봇 응답의 근거 논문들을 `ChatSourceEntity`로 일괄 매핑하여 DB에 밀어 넣습니다.
    *   `async def select_sources_by_session(self, session_id: str) -> list[ChatSourceEntity]`: 특정 세션방 내에 결합된 모든 참고 출처 데이터를 대화 순서대로 정렬해 가져옵니다.
    *   `async def commit(self) -> None`: StreamingResponse 동작 시 트랜잭션 자동 종료 시점의 혼선 방지를 위해 DB commit 명령을 명시 실행해 줍니다.

---

### 📄 [api/v1/chat/chat_agent.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/chat_agent.py)
LangChain/LangGraph와 pgvector saver를 결합하여 사용자 대화 히스토리를 영구 복원/저장하고, 질문의 기술 맥락을 가려 적확한 논문 검색 툴을 가동해 RAG 종합 답변을 출처와 함께 뽑아내는 RAG 에이전트 클래스 파일입니다.

#### 1) 클래스
*   **`BioAgentState(TypedDict)`**: LangGraph 내부 흐름용 상태 딕셔너리 스키마. (messages 내역, sources 출처 정보 적재)
*   **`BioPaperRef(BaseModel)` & `BioAnswer(BaseModel)`**: gpt-4o-mini LLM이 최종 답변 도출 시 준수하도록 제어하는 RAG 답변 및 인용 논문 구조화 DTO 규격입니다.
*   **`ChatAgent`**: 실질적인 LLM RAG 호출 및 대화 복제 처리를 캡슐화한 코어 에이전트 클래스입니다.
    *   `__init__(self, model: str = "openai:gpt-4o-mini")`: RAG 시스템용 전문가 시스템 지침과 스트리밍 전용 무참조 안내 지침을 생성해 둡니다.
    *   `async def _initialize(self) -> None`: 비동기 동시성 Lock 제어로 스레드 세이프하게 psycopg 풀을 개방한 후, `AsyncPostgresSaver` 및 RAG 검색 도구 3종(`search_bio_papers`, `search_astronomy_papers`, `search_cs_papers`)과 `BioAnswer` 포맷을 결합한 **RAG Agent 인스턴스를 지연 생성 및 마운팅**합니다.
    *   `async def run(self, message: str, conversation_id: str) -> dict`: thread_id로 누적되어 저장된 이전 대화기록을 복구한 뒤, 질문에 해당하는 구조화 설명과 출처 리스트를 획득하여 반환합니다.
    *   `async def run_stream(self, message: str, conversation_id: str) -> AsyncGenerator[str, None]`: 실시간 화면 출력을 위해 JSON 구조화 포맷을 배제하고 토큰별 캐릭터 문자 조각을 yield 송출해주는 비동기 스트리밍 제너레이터 함수입니다.
    *   `async def get_latest_sources(self, conversation_id: str) -> list[dict]`: 스트리밍 도구 실행 과정 도중 Saver 상태에 누적되었던 실질 문헌 출처를 최종 중복 제거하여 가져옵니다.
    *   `async def get_history(self, conversation_id: str) -> list[dict]`: 누적 데이터 중 도구 호출 및 시스템 지시어를 빼고 유저와 에이전트 간의 실질적인 human/ai 문자열 발화 이력만 필터링하여 가져옵니다.
    *   `async def clear_history(self, conversation_id: str) -> None`: 세션 종료나 방 소거 요청 시 Saver 에 저장된 백그라운드 챗 히스토리 테이블 데이터를 삭제합니다.
    *   `async def generate_title(self, question: str) -> str`: 사용자의 첫 챗 문맥을 LLM을 직통 호출(`ainvoke`)하여 6~20자 내외의 깔끔한 한글 대화방 제목으로 요약 빌드해 줍니다.

---

### 📄 [api/v1/chat/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/services.py)
대화 세션 개설/목록/삭제 비즈니스 행위 제어 및 RAG 질의에 대한 일반 답변 처리, 그리고 스트리밍 반환 후 백그라운드 출처 DB 연계 마운팅을 지휘하는 비즈니스 레이어 서비스 파일입니다.

#### 1) 클래스
*   **`ChatService`**: 대화 업무 비즈니스 서비스 클래스입니다.
    *   `__init__(self, chat_session_dao: ChatSessionDaoDep, chat_agent: ChatAgentDep)`: DAO와 AI RAG 에이전트를 주입받습니다.
    *   `async def create_session(self, member_id: str, title: str) -> ChatSessionEntity`: 고유 UUID로 세션방 식별자를 발급하여 신규 대화 메타데이터를 개설합니다.
    *   `async def list_sessions(self, member_id: str) -> list[ChatSessionEntity]`: 유저가 소유권을 쥔 활성 방 목록을 조회합니다.
    *   `async def _get_owned_session(self, member_id: str, session_id: str) -> ChatSessionEntity`: 방 식별자로 조회 후, 요청 회원이 해당 방의 소유자(member_id 대조)가 맞는지 유효성 인가 검사를 보조하는 내부 헬퍼 메서드입니다.
        *   **Raises**: `BusinessException` (미존재 세션이거나 소유권이 없는 경우 접근 제한 예외)
    *   `async def delete_session(self, member_id: str, session_id: str) -> None`: 소유자 확인 후 방 메타 삭제 및 에이전트 내에 격리 누적되었던 Saver 대화 스레드 전체를 파쇄합니다.
    *   `async def rename_session(self, member_id: str, session_id: str, title: str) -> ChatSessionEntity`: 대화방 타이틀을 재설정합니다.
    *   `async def generate_and_set_title(self, member_id: str, session_id: str, question: str) -> str`: 첫 대화의 주제를 분석해 AI 추천 제목을 생성하고 이를 대화 세션에 갱신 적용합니다.
    *   `async def send_message(self, member_id: str, session_id: str, message: str) -> dict`: 대화방에 메시지를 주입해 RAG 에이전트 답변을 도출하고, 검출에 동원되었던 출처 데이터를 DB(`chat_source`)에 인덱스 순서와 연계해 저장한 뒤 결과를 제공합니다.
    *   `async def send_message_stream(self, member_id: str, session_id: str, message: str) -> AsyncGenerator[str, None]`: 실시간 답변 스트림 조각을 yield하여 방출하고, **스트리밍 루프가 무사 완료되는 종결 지점에서 백그라운드 형태로 최신 출처들을 가져와 DB에 누적 영구 보관**한 뒤 커밋합니다.
    *   `async def get_messages(self, member_id: str, session_id: str) -> list[dict]`: 이력 조회 시 에이전트 히스토리에 기록된 메시지 턴에 맞춰 DB에서 꺼내온 출처 논문 정보 배열을 일치하는 메세지 객체의 `sources` 자리에 주입하고 취합해 최종 히스토리 데이터로 가공 반환합니다.

---

### 📄 [api/v1/chat/endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/endpoints.py)
세션 관리 및 일반 RAG 답변, 토큰 실시간 스트리밍 송출, 대화 내역 조회를 처리하는 클라이언트 연결 지점 컨트롤러입니다.

#### 1) 함수 및 라우터
*   **`@router.post("/sessions")`**: 신규 RAG 대화방을 생성하여 래퍼 응답을 줍니다.
*   **`@router.get("/sessions")`**: 회원의 전체 RAG 대화방 이력을 최신 등록순으로 반환합니다.
*   **`@router.delete("/sessions/{session_id}")`**: 본인 소유의 대화 세션 및 누적 히스토리를 파괴합니다.
*   **`@router.patch("/sessions/{session_id}")`**: 대화방 이름을 사용자가 요청한 이름으로 갱신합니다.
*   **`@router.post("/sessions/{session_id}/messages")`**: RAG 비즈니스 로직을 동기 수행하여 최종 완성형 답변과 출처 카드를 반환합니다.
*   **`@router.post("/sessions/{session_id}/messages/stream")`**: 타이핑 효과를 구현하기 위해 답변 토큰들을 실시간 Chunked Response(media_type="text/plain") 형태로 서빙합니다.
*   **`@router.get("/sessions/{session_id}/messages")`**: 과거 주고받았던 모든 대화 이력과 매핑된 출처 카드 데이터 리스트를 가져옵니다.
*   **`@router.post("/sessions/{session_id}/generate-title")`**: 첫 발화 질문을 던졌을 때 방 제목을 자동 요약 추천/갱신 적용하는 라우터입니다.

---

## 8. 🛡️ 보안 격리 피어리뷰 및 모의 디펜스 도메인 (Defense Arena Domain)

### 📄 [api/v1/defense_arena/entity.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/entity.py)
기밀 유출 방지를 위한 보안 격리용 세션 정보, 문서 파싱 후 저장되는 pgvector 3072차원 임베딩 텍스트 청크, 심사위원과의 모의 구두 디펜스 대화 이력 테이블을 정의하는 ORM 엔티티 파일입니다.

#### 1) 클래스
*   **`DefenseArenaSessionEntity(Base)`**: 보안 격리 구역 테이블 매핑 클래스(`defense_arena_session`)입니다. 파일명, 임시 저장 경로, 청킹 분할 조각 수 및 만료 시간 갱신(`updated_at`) 필드를 둡니다.
*   **`DefenseArenaChunkEntity(Base)`**: 격리 문서의 텍스트 조각과 3072차원 임베딩 벡터(`Vector(3072)`)를 매핑 저장하는 테이블(`defense_arena_chunk`)입니다. 부모 세션 삭제 시 CASCADE 제거됩니다.
*   **`DefenseHistoryEntity(Base)`**: 심사위원과 나눈 이력을 턴(`turn`)별로 기록하는 테이블(`defense_history`)입니다. 심사위원의 압박 질문(`question`), 사용자의 소명 반론 답변(`answer`), 답변 점수(`score`), 평가 피드백(`feedback`)을 칼럼화하여 저장합니다.

---

### 📄 [api/v1/defense_arena/models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/models.py)
PDF 업로드 결과, 종합 피어리뷰 리포트 구성 요소, RAG 기반 가설 검증 결과 및 턴제 구두 디펜스 질의응답 피드백에 사용되는 Pydantic 구조화 DTO 규격 파일입니다.

#### 1) 클래스
*   **`UploadResponse`**: PDF 파싱 후 session_id와 텍스트 청킹 조각 개수 반환 DTO.
*   **`AgentOpinion`**: 3대 에이전트(방법론, 신규성, 학술문체)가 제출하는 개별 점수와 크리틱 의견 DTO.
*   **`PeerReviewReport`**: 3대 에이전트 비평을 규합한 최종 종합 스코어 및 요약 평가 보고서 구조화 DTO.
*   **`HypothesisRequest`**: 검증을 바라는 학술적 가설 입력 DTO.
*   **`HypothesisVoteItem`**: 1회 독립 추론 시 LLM이 투표할 결론(SUPPORT, REFUTE, INSUFFICIENT_EVIDENCE) 및 사유 DTO.
*   **`HypothesisVerificationResult`**: 3회 독립 시행 투표 집계(다수결 합의율, 세부 사유 리스트 및 인용 텍스트 리스트) 결과 DTO.
*   **`DefenseChatRequest`**: 구두 질문에 대응하는 사용자의 반론 텍스트 DTO.
*   **`DefenseChatResponse`**: 다음 질문, 방금 제출한 답변의 점수, 꼬리물기 피드백, 디펜스 완료 여부 및 완료 시에 서빙되는 최종 디펜스 스코어카드 명세 DTO.
*   **`ScoreDTO`**: 실시간 소명 답변에 대한 100점 만점 채점 및 개별 조언 피드백 구조화 DTO.

---

### 📄 [api/v1/defense_arena/dao.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/dao.py)
임시 구역 내의 세션 생성, 활동 갱신, 세션 CASCADE 삭제 쿼리 및 업로드된 3072차원 벡터를 대상으로 질의어와 코사인 거리가 가까운 청크를 꺼내오는 RAG 쿼리 함수, 디펜스 구두 이력 CRUD 작업을 담당합니다.

#### 1) 클래스
*   **`DefenseArenaDao`**: 보안 격리 업무 DB 처리를 대행합니다.
    *   `__init__(self, orm_session: OrmSessionDep)`: ORM 세션을 주입받습니다.
    *   `async def create_session(self, session: DefenseArenaSessionEntity) -> DefenseArenaSessionEntity`: 보안 격리 세션을 DB에 추가합니다.
    *   `async def get_session(self, session_id: str) -> DefenseArenaSessionEntity | None`: 세션 단건을 조회합니다.
    *   `async def update_session_activity(self, session_id: str) -> None`: 활동 연장을 위해 세션의 `updated_at`을 현재 일시로 즉각 갱신합니다.
    *   `async def delete_session(self, session_id: str) -> bool`: 세션을 삭제 처리합니다. (CASCADE 설정으로 하위 청크 및 디펜스 대화 테이블도 같이 소거됨)
    *   `async def list_expired_sessions(self, expire_minutes: int = 30) -> list[DefenseArenaSessionEntity]`: 마지막 갱신 시간 기준 30분 이상 휴면 중인 만료 대상 세션들을 스캔해 가져옵니다.
    *   `async def insert_chunks(self, chunks: list[DefenseArenaChunkEntity]) -> None`: 파싱 완료된 대량의 텍스트/임베딩 청크 목록을 일괄 적재(`add_all`)합니다.
    *   `async def similarity_search_in_session(self, session_id: str, query_vector: list[float], k: int = 3) -> list[tuple[DefenseArenaChunkEntity, float]]`: 업로드된 단일 파일 범위 안에서 유사도를 검색하는 특화 RAG 메서드입니다. 코사인 거리를 오름차순 정렬하여 상위 k개를 `(청크 엔티티, 1.0 - Cosine Distance 유사 점수)` 튜플 형태로 리턴합니다.
    *   `async def insert_defense_history(self, history: DefenseHistoryEntity) -> DefenseHistoryEntity`: 모의 디펜스 턴 기록 레코드를 저장합니다.
    *   `async def get_defense_history(self, session_id: str) -> list[DefenseHistoryEntity]`: 방 안에서 오간 대화 히스토리를 턴별 오름차순으로 정렬해 모두 가져옵니다.
    *   `async def get_defense_history_by_turn(self, session_id: str, turn: int) -> DefenseHistoryEntity | None`: 특정 턴수의 단건 디펜스 기록을 가져옵니다.
    *   `async def update_defense_history(self, history: DefenseHistoryEntity) -> DefenseHistoryEntity`: 꼬리물기 답변과 그에 대한 채점 및 피드백 데이터가 가득 찬 엔티티 상태를 병합(`merge`)하여 갱신 완료합니다.

---

### 📄 [api/v1/defense_arena/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/services.py)
격리 구역 내 PDF 파싱, Directory Traversal 방지 검증, Multi-Agent 종합 피어리뷰 실행, 자아-일관성(Self-Consistency) 다수결 가설 검증, 구두 모의 디펜스 세션 조율 및 물리/논리 데이터 영구 파쇄를 실행합니다.

#### 1) 클래스
*   **`DefenseArenaService`**: 보안 격리 아레나 관련 핵심 비즈니스 로직 클래스입니다.
    *   `__init__(self, defense_arena_dao: DefenseArenaDaoDep)`: 격리용 DAO 의존성을 주입받아 초기화합니다.
    *   `async def process_pdf_upload(self, file: UploadFile, mid: str) -> dict`: 사용자가 보낸 PDF 파일의 보안 격리 가공을 담당합니다.
        *   **로직**:
            1. `uploads/<session_id>` 경로에 격리 수용할 임시 폴더 개설.
            2. **OS Path Guard (Directory Traversal 방지)**: 타겟 폴더 경로와 실제 업로드 허용 상위 디렉토리를 대조하여 상위 경로 탈출 우회 접근 시도를 검출 차단.
            3. `pypdf`를 이용해 문서 내 텍스트를 추출. 공백이거나 파싱 실패 시 폴더를 즉시 날리고 비즈니스 오류 발생.
            4. `RecursiveCharacterTextSplitter`(크기 1000자, 오버랩 200자)로 텍스트를 분할.
            5. `DefenseArenaSessionEntity` 생성 및 DB 등록.
            6. 각 청크 텍스트에 대하여 `text-embedding-3-large` 3072차원 임베딩 벡터를 추출하여 `DefenseArenaChunkEntity`로 묶어 DB에 다량 일괄 적재(`insert_chunks`).
    *   `async def run_peer_review(self, session_id: str, target_journal: str, mid: str) -> PeerReviewReport`: 격리 문서 내용을 기반으로 3대 비평가 시뮬레이션을 돌립니다.
        *   **로직**:
            1. 보안 세션 유효성 검증 및 활동 시간(`updated_at`) 갱신.
            2. 기밀 유지를 만족하는 상태에서 문서 전체의 맥락 파악을 위해 대표 텍스트 청크 10개를 순차 로드하여 임시 조립.
            3. `ChatOpenAI(temp=0.2)` 모델에 구조화 출력 명세인 `PeerReviewReport`를 연동(`with_structured_output`)하여 3대 특화 에이전트가 target_journal 투고 자격 부합 여부를 검사하는 건설적인 비평 보고서를 완성형으로 받아 반환. (이때 `isinstance` 검사 타입 가드 적용)
    *   `async def verify_hypothesis(self, session_id: str, hypothesis: str, mid: str) -> HypothesisVerificationResult`: 임베딩 데이터 RAG 검색을 결합하여 가설 신뢰도를 검증합니다.
        *   **로직**:
            1. 유저 연구 가설 문장을 임베딩 벡터로 변환하여 격리 문서 내 RAG 유사 청크 5개를 검색하고, 증거용 문장 목록(`citations`)으로 축적.
            2. **Self-Consistency 기법**: LLM의 임의 추론 편향을 억제하기 위해 온도를 다르게 설정(`temp=0.5 + i * 0.1`)하여 `ChatOpenAI` 모델에 3회 개별 독립 질의하여 `HypothesisVoteItem` 구조화 결론을 채집.
            3. 3회 투표 결과에 대해 다수결(Majority Voting) 연산을 수행하여 지지율(`consensus_ratio`)과 최종 참/거짓 결론(`verdict`)을 산출하여 반환.
    *   `async def process_defense_chat(self, session_id: str, user_response: Optional[str], mid: str) -> DefenseChatResponse`: 심사위원과의 턴제 구두 디펜스 세션을 지휘합니다.
        *   **로직**:
            *   **첫 턴 시작 시**: 문서 RAG를 통해 핵심 청크 2개를 추출해 이를 토대로 가장 치명적이고 비판적인 1차 구두 압박 질문을 LLM으로 생성. 질문 레코드를 DB에 턴 1로 생성 보관하고 전달.
            *   **후속 턴 진행 시**:
                1. 직전 턴 질문 및 유저 소명 답변 텍스트를 LLM 채점 체인(`ScoreDTO` 구조화 형식)에 태워 100점 만점 평점 점수와 매서운 비평 피드백을 계산하여 DB를 갱신.
                2. 총 누적 턴수가 3턴에 달한 경우(`is_finished` = True): 턴 전체의 문답 명세를 규합하여 최종 저널 심사 종합 의견서(`final_report`)를 LLM으로 빌드하여 반환하고 세션 마감 처리.
                3. 아직 디펜스가 더 필요한 경우: 사용자의 이전 소명 내용 중 허술한 지점을 꼬리물기 압박 질문으로 새롭게 생성하여 다음 턴 DB 빈 레코드를 준비해 둔 뒤 반환.
    *   `async def wipe_out_expired_sessions(self, expire_minutes: int = 30) -> int`: 30분 미활동 보안 격리 구역의 세션 물리 PDF 파일 및 DB 임시 데이터(Cascade) 일괄 영구 소거(Wipe Out).
        *   **로직**:
            1. 만료 임계치(30분)가 넘은 세션들을 리스트업.
            2. 각 만료 세션별로 디렉토리 트래버스 보안 우회를 막는 OS Path Guard 검증을 한 번 더 수행하여 검증 통과 시 해당 세션의 로컬 임시 uploads 폴더를 물리 삭제(`shutil.rmtree`).
            3. DB에서 세션 레코드 삭제(`delete_session`). ON DELETE CASCADE 설정에 의해 pgvector 임베딩 청크 및 모의 디펜스 대화 기록 테이블 내용이 영구적 완전 소거(Wipe Out) 처리됨.

---

## 9. 💎 사용자 커스텀 연구 공간 도메인 (Gems Domain)

### 📄 [api/v1/gems/entity.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/entity.py)
유저가 직접 도메인과 시스템 지시 프롬프트를 지정해 생설하는 사용자 정의 연구 비서(Gem)의 메타데이터를 영구 저장하는 데이터베이스 엔티티 파일입니다.

#### 1) 클래스
*   **`GemEntity(Base)`**: `gem` 테이블 매핑 클래스입니다.
    *   **Fields**: `gem_id` (PK, UUID), `member_id` (소유자 ID), `name` (Gem 이름), `db_sources` (참조 도메인 쉼표 구분 문자열, e.g. "bio,cs"), `system_prompt` (Gem 페르소나/지시어), `created_at` (생성일시).

---

### 📄 [api/v1/gems/models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/models.py)
연구 스페이스 Gem의 신규 개설, 변경 내용 전달 및 전용 RAG 에이전트 대화 진행 시 입출력을 제어하는 Pydantic DTO 명세입니다.

#### 1) 클래스
*   **`GemCreateRequest` & `GemUpdateRequest`**: Gem 에이전트 생성 및 부분 수정용 DTO.
*   **`GemResponse`**: Gem 메타데이터 정보 출력 DTO (db_sources의 콤마 데이터를 배열 리스트 형태로 출력).
*   **`GemChatRequest`**: 특정 대화방(`thread_id`)을 통한 커스텀 Gem 대화 요청 DTO.
*   **`GemChatResponse`**: RAG 설명(explanation) 및 요약 인용 논문 리스트(`papers`), 날 것의 RAG 검색 출처 청크 목록(`sources`)으로 이루어진 응답 DTO.
*   **응답 래퍼 DTO**: `GemListResponseWrapper`, `GemResponseWrapper`, `GemChatResponseWrapper`.

---

### 📄 [api/v1/gems/dao.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/dao.py)
사용자 정의 Gem의 생성, 회원별 목록, 단건 갱신 및 Gem 에이전트 삭제 시 DB를 소거하는 물리 DAO 파일입니다.

#### 1) 클래스
*   **`GemDao`**: Gem 테이블 DB 처리를 대행합니다.
    *   `__init__(self, orm_session: OrmSessionDep)`: ORM 세션을 바인딩합니다.
    *   `async def insert(self, gem_entity: GemEntity) -> GemEntity`: 신규 Gem 메타데이터를 삽입합니다.
    *   `async def select_by_member(self, member_id: str) -> list[GemEntity]`: 회원 ID에 부합하는 Gem 리스트를 최신순으로 가져옵니다.
    *   `async def select_by_id(self, gem_id: str) -> GemEntity | None`: Gem 고유키로 단건의 사양을 가져옵니다.
    *   `async def update(self, gem_entity: GemEntity) -> GemEntity`: 변경된 Gem 상태를 DB 세션에 병합(`merge`) 갱신합니다.
    *   `async def delete(self, gem_id: str) -> None`: 해당 Gem의 메타데이터를 DB에서 지웁니다.

---

### 📄 [api/v1/gems/gem_agent.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/gem_agent.py)
개별 Gem 마다 설정된 서로 다른 RAG 데이터소스(bio, cs, astronomy)와 연결된 RAG 검색 툴들을 동적 추출하고, 유저가 지정한 프롬프트를 AI 에이전트에 실시간 바인딩하여 챗봇 런타임을 동적 빌딩해주는 에이전트 엔진 파일입니다.

#### 1) 클래스
*   **`GemAgentState(TypedDict)`**: Gem 에이전트의 대화 히스토리 상태 딕셔너리 스키마. (messages, RAG sources 누적)
*   **`GemPaperRef(BaseModel)` & `GemAnswer(BaseModel)`**: Gem 에이전트의 최종 RAG 답변 마크다운 설명 및 인용 논문 정보 구조화 포맷입니다.
*   **`GemAgent`**: 다이내믹 룰 RAG 에이전트를 실시간 가동하는 클래스입니다.
    *   `__init__(self, model: str = "openai:gpt-4o-mini")`: LLM 모델명을 수용합니다.
    *   `async def _initialize(self)`: 대화 체크포인터 테이블 실존 여부를 멱등 체크하고 `AsyncPostgresSaver`를 생성합니다.
    *   `def _build_system_prompt(self, db_sources: list[str], persona_prompt: str) -> str`: 사용자가 지정한 페르소나 문구 하단에, 선택된 RAG 데이터소스(bio/cs/astronomy)에 부합하는 툴 호출 명령 지침과 **"한국어로 질문해도 RAG 툴 검색어 query는 핵심 영문 학술 단어로 자동 변환하여 던질 것"**에 대한 프롬프트 명령 지침을 조합하여 최종 시스템 프롬프트를 획득합니다.
    *   `def _build_agent(self, db_sources: list[str], system_prompt: str)`: 동적으로 RAG 툴 세트와 시스템 프롬프트 지침을 뽑아내어 `create_agent`로 **Gem 런타임 에이전트 인스턴스를 동적 설계/생성**해 반환합니다.
    *   `async def run(self, message: str, thread_id: str, db_sources: list[str], system_prompt: str) -> dict`: thread_id로 대화 내역을 유지/복구한 상태에서, 동적으로 빌드된 전용 Gem 에이전트에 질의를 주입하여 구조화 RAG 설명과 출처 리스트 정보를 반환합니다.
    *   `async def get_history(...) -> list[dict]`: 대화 이력에서 human/ai 발화 내역을 조회합니다. (JSON 형태로 저장되어 있다면 explanation 텍스트만 파싱 추출함)
    *   `async def clear_history(self, thread_id: str) -> None`: 특정 Gem 대화 세션 스레드의 대화 기록 내역을 일괄 제거합니다.

---

### 📄 [api/v1/gems/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/services.py)
Gem의 생성/수정/삭제 조율 및 Gem RAG 에이전트를 동적으로 동작시켜 실시간 상담 답변을 반환하고 대화 이력을 가져오는 비즈니스 레이어 서비스 파일입니다.

#### 1) 클래스
*   **`GemService`**: Gem 비즈니스 로직 클래스입니다.
    *   `__init__(self, gem_dao: GemDaoDep, gem_agent: GemAgentDep)`: DAO와 에이전트 엔진을 바인딩합니다.
    *   `async def create_gem(self, member_id: str, name: str, db_sources: list[str], system_prompt: str) -> GemEntity`: 선택된 도메인이 유효(bio/cs/astronomy)한지 검사한 뒤 고유 UUID를 엮어 신규 Gem 메타 데이터를 생성합니다.
        *   **Raises**: `BusinessException` (허용되지 않은 RAG 소스 포함 시 오류 유발)
    *   `async def list_gems(self, member_id: str) -> list[GemEntity]`: 회원 소유의 Gem 비서 목록을 가져옵니다.
    *   `async def _get_owned_gem(self, member_id: str, gem_id: str) -> GemEntity`: 본인 소유의 Gem 에이전트 인스턴스 사양인지 조회 검사하는 내부 헬퍼 메서드입니다.
        *   **Raises**: `BusinessException` (미존재 세션이거나 소유권이 없는 경우 접근 제한 예외)
    *   `async def update_gem(self, member_id: str, gem_id: str, name: str | None, db_sources: list[str] | None, system_prompt: str | None) -> GemEntity`: 이름이나 프롬프트, RAG 대상 소스 등 요청으로 유입된 특정 명세 필드만 부분 교체 수정합니다.
    *   `async def delete_gem(self, member_id: str, gem_id: str) -> None`: Gem 정보 및 대화 체크포인트를 DB에서 일괄 영구 소거합니다.
    *   `async def send_message(self, member_id: str, gem_id: str, thread_id: str, message: str) -> dict`: Gem의 설정(데이터소스, 지침 프롬프트)을 추출한 뒤 동적 RAG 에이전트를 시동하여 메시지 질의 답변과 출처 카드를 반환합니다.
    *   `async def get_messages(self, member_id: str, gem_id: str, thread_id: str) -> list[dict]`: 지정된 Gem과의 대화 이력을 순서대로 반환합니다.

---

### 📄 [api/v1/gems/endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/endpoints.py)
커스텀 연구 에이전트의 CRUD 및 개별 생성된 Gem 에이전트와의 RAG 채팅 질의응답을 매핑하는 컨트롤러 파일입니다.

#### 1) 함수 및 라우터
*   **`def _to_gem_response(gem_entity) -> GemResponse`**: DB의 콤마 구분형 도메인 텍스트 필드를 Pydantic 리스트 DTO로 가공해서 전달하기 위한 내부 포맷팅 함수입니다.
*   **`@router.post("")`**: 신규 사용자 정의 Gem 비서를 개설하여 결과를 응답합니다.
*   **`@router.get("")`**: 사용자가 소유 중인 전체 Gem 리스트를 가져옵니다.
*   **`@router.put("/{gem_id}")`**: Gem의 지침 프롬프트나 연동 도메인을 수정 갱신합니다.
*   **`@router.delete("/{gem_id}")`**: Gem 메타데이터를 영구 차단 소거합니다.
*   **`@router.post("/{gem_id}/chat")`**: 특정 Gem에 RAG 질문을 물려 답변 결과를 가져옵니다.
*   **`@router.get("/{gem_id}/chat/{thread_id}/messages")`**: 해당 Gem과 주고받았던 스레드의 대화 히스토리 내역을 일괄 조회하는 라우터입니다.

---

## 10. 🔔 SSE 실시간 및 누적 알림 도메인 (Notification Domain)

### 📄 [api/v1/notification/entity.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/notification/entity.py)
유저의 실시간 수신 알림 및 오프라인 상태 시 누적된 이력 알림의 고유 식별자, 분류 정보, 비동기 태스크 링크 상태 등을 데이터베이스 `notification` 테이블에 매핑하는 엔티티 클래스 파일입니다.

#### 1) 클래스
*   **`NotificationEntity(Base)`**: `notification` 테이블 매핑 클래스입니다.
    *   **Fields**: `id` (PK, String(50)), `mid` (수신 회원 ID, FK -> `member.mid`), `title` (알림 제목), `message` (알림 본문), `type` (알림 유형: info, success, danger, warning), `task_id` (연계된 비동기 작업 식별 ID, Nullable), `read` (읽음 표시 여부), `created_at` (생성일시).

---

### 📄 [api/v1/notification/models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/notification/models.py)
알림 정보 조회 및 목록 전달 시 반환할 Pydantic DTO 명세입니다.

#### 1) 클래스
*   **`NotificationDTO(BaseDTO)`**: 알림 상세 조회 응답 DTO.
*   **`NotificationListResponse(BaseDTO)`**: 알림 목록 응답 DTO.

---

### 📄 [api/v1/notification/notifier.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/notification/notifier.py)
비동기 배치 태스크 완료, 실패 등 시스템 이벤트를 실시간 접속 상태의 다수 브라우저 리스너에 즉각 통보하는 인메모리 SSE 브로드캐스트 퍼블리셔 파일입니다.

#### 1) 클래스
*   **`NotificationBroadcaster`**: 실시간 비동기 이벤트 분배 시스템 클래스입니다.
    *   `__init__(self) -> None`: 리스너들을 격리 수용할 비동기 큐 셋(`_listeners`)을 준비합니다.
    *   `subscribe(self) -> asyncio.Queue`: 새롭게 SSE 커넥션을 체결한 브라우저 클라이언트 연결에 대해 전용 비동기 `Queue`를 개설하여 셋에 등록하고 이를 반환합니다.
    *   `close(self) -> None`: 서버 리로드나 셧다운 이벤트 발생 시, 구독 중인 모든 클라이언트 리스너 큐에 `None` 종결 플래그(sentinel)를 전달하고 셋을 안전 해제합니다.
    *   `unsubscribe(self, queue: asyncio.Queue) -> None`: 연결이 끊긴 클라이언트의 비동기 큐를 구독 리스트에서 제거하여 리소스 낭비를 방지합니다.
    *   `async def broadcast(self, message: dict) -> None`: 비동기 알림 생성 시, 현재 연결된 모든 브라우저 리스너 큐에 대하여 동시적으로 메시지 이벤트를 `put` 송출합니다. (`asyncio.gather` 비동기 일괄 분배 처리)

---

### 📄 [api/v1/notification/dao.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/notification/dao.py)
알림 엔티티의 적재, 사용자별 알림 최신순 조회, 읽음 마킹, 읽음 일괄 마킹 및 개별/전체 삭제 쿼리 동작을 대행하는 DAO 파일입니다.

#### 1) 클래스
*   **`NotificationDao`**: 알림 테이블 DB 처리를 대행합니다.
    *   `__init__(self, orm_session: OrmSessionDep)`: ORM 세션을 주입받습니다.
    *   `async def create_notification(self, id: str, mid: str, title: str, message: str, type: str, task_id: Optional[str] = None) -> NotificationEntity`: 신규 알림 레코드를 저장합니다.
    *   `async def list_notifications(self, mid: str) -> List[NotificationEntity]`: 사용자 식별자 수신 알림 목록을 최신순으로 정렬해 모두 가져옵니다.
    *   `async def mark_as_read(self, id: str, mid: str) -> bool`: 개별 알림의 읽음 컬럼을 True로 바꾸고 성공 여부를 반환합니다.
    *   `async def mark_all_as_read(self, mid: str) -> None`: 사용자의 전체 미읽음 알림을 대상을 `read = True`로 일괄 업데이트합니다.
    *   `async def delete_notification(self, id: str, mid: str) -> bool`: 개별 알림 1건을 소거합니다.
    *   `async def delete_all_notifications(self, mid: str) -> None`: 사용자의 알림 테이블 이력을 일괄 삭제합니다.

---

### 📄 [api/v1/notification/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/notification/services.py)
알림 목록/읽음 비즈니스 로직과 함께, 구독 비동기 큐로부터 수신된 메시지를 SSE(Server-Sent Events) 프로토콜 규격으로 조립하고 Nginx 프록시 타임아웃을 방지하기 위해 주기적으로 keep-alive 데이터를 보내는 비동기 스트림 제너레이터를 공급하는 서비스 파일입니다.

#### 1) 클래스
*   **`NotificationService`**: 알림 업무 비즈니스 서비스 클래스입니다.
    *   `__init__(self, notification_dao: NotificationDaoDep)`: 알림 DAO를 바인딩합니다.
    *   `async def list_notifications(self, mid: str) -> list[NotificationEntity]`: 알림 상세 리스트를 끕니다.
    *   `async def mark_as_read(self, id: str, mid: str) -> bool`: 개별 알림을 읽음 마킹 처리합니다.
    *   `async def mark_all_as_read(self, mid: str) -> None`: 전체 알림 일괄 읽음을 실행합니다.
    *   `async def delete_notification(self, id: str, mid: str) -> bool`: 특정 알림을 제거합니다.
    *   `async def delete_all_notifications(self, mid: str) -> None`: 전체 알림 소거를 실행합니다.
    *   `async def stream_notifications(self, request: Request, mid: str) -> AsyncGenerator[str, None]`: 실시간 비동기 SSE 채널의 알림 스트림을 공급하는 비동기 제너레이터 함수입니다.
        *   **로직**:
            1. 전역 `notification_broadcaster.subscribe()` 호출로 전용 큐 생성.
            2. 무한 루프 내에서 브라우저 이탈 여부(`await request.is_disconnected()`) 상시 점검.
            3. `asyncio.wait_for`를 통해 1.0초 주기로 전용 큐에서 들어오는 이벤트 데이터를 대기.
            4. **Nginx 프록시 차단 방어 (keep-alive)**: 1초간 수신 메시지가 없을 시 `TimeoutError`를 캐치하여 `: keep-alive\n\n` 데이터 조각을 스트림으로 지속 송출함으로써 SSE 연결 유지 보장.
            5. 큐에서 메시지가 인출된 경우, 수신 회원 타겟(`event_mid`)이 본인이 아닌 경우 필터링 제거하고, 일치하는 메시지는 `data: JSON_STRING\n\n` 규격으로 포매팅하여 yield 송출.
            6. 루프 탈출 시 브로드캐스터 구독 해제(`unsubscribe`).

---

### 📄 [api/v1/notification/endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/notification/endpoints.py)
실시간 브라우저 연결을 수립하는 SSE 채널 경로와 알림 조회/읽음/삭제 처리를 매핑하는 컨트롤러 파일입니다.

#### 1) 함수 및 라우터
*   **`@router.get("/stream")`**: 실시간 통합 푸시 알림 이벤트를 SSE로 양방향 연결해 주는 스트리밍 라우터입니다. Nginx 버퍼링에 의한 알림 지연을 막기 위해 응답 헤더에 `X-Accel-Buffering: no`, `Cache-Control: no-cache`를 설정하여 스트림 응답을 반환합니다.
*   **`@router.get("")`**: 도달한 오프라인/온라인 알림 목록 조회를 매핑합니다.
*   **`@router.put("/{id}/read")`**: 개별 알림 1건을 읽음으로 고쳐 둡니다.
*   **`@router.put("/read-all")`**: 전체 수신 알림들을 일괄 읽음으로 변경합니다.
*   **`@router.delete("/{id}")`**: 알림 1건을 삭제합니다.
*   **`@router.delete("")`**: 알림 전체를 삭제 갱신합니다.

---

## 11. 📊 연구 공백 분석 및 매트릭스 도출 도메인 (Research Gap Domain)

### 📄 [api/v1/research_gap/entity.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/entity.py)
비동기 배치 분석 태스크의 수명 주기(상태, 진척도 %, 분석 JSON 결과, 번역 완료 JSON 결과, 실패 로그)를 저장하는 테이블을 매핑하는 엔티티 정의 파일입니다.

#### 1) 클래스
*   **`ResearchGapTaskEntity(Base)`**: `research_gap_task` 테이블 매핑 클래스입니다.
    *   **Fields**: `task_id` (PK, String(50)), `mid` (회원 ID), `domain` (학술 영역), `query` (분석 검색 주제), `status` (PENDING/RUNNING/COMPLETED/FAILED), `progress` (진척율 0~100), `result` (최종 영문 리포트 JSON), `translated_result` (국문 번역 리포트 JSON), `error_message` (오류 로그), `created_at` (생성일시), `updated_at` (수정일시).

---

### 📄 [api/v1/research_gap/models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/models.py)
비동기 분석 요청, 상태 진척 결과, 개별 논문의 해결 문제 및 한계점 리스트(각각 최대 2개 제약), 종합 연구 공백 매트릭스 규격과 다량 삭제 수용을 정의하는 DTO 파일입니다.

#### 1) 클래스
*   **`AnalyzeRequest`**: 분석 도메인(cs/bio/astronomy) 및 키워드 요청 DTO.
*   **`TaskStatusResponse`**: 비동기 배치 작업 진척율(%) 및 상태 응답 DTO.
*   **`AnalysisItem`**: 요약 요점(`summary`)과 근거 원문 영문 구절(`source_quote`) DTO.
*   **`PaperAnalysisResult`**: 개별 논문 분석 구조 DTO. Pydantic Structured Output에 대응하며, **`problems_solved`와 `limitations` 리스트의 크기는 최대 2개(`max_length=2`)로 엄격 제한**되어 연구 정보가 축약 전달되도록 설계되어 있습니다.
*   **`ResearchGapMatrix`**: 연구 공백 최종 종합 매트릭스 DTO. 분석 논문 정보 매트릭스, 공통의 한계점 리스트, 이를 해소할 혁신적 AI 추천 로드맵 주제 및 방법론 목록(`suggested_directions`)으로 구조화됩니다.
*   **`TaskResultResponse`**: 최종 분석 결과 조회용 DTO.
*   **`TranslateRequest`**: 영문 리포트 JSON 번역 위임용 DTO.
*   **`BulkDeleteRequest`**: 여러 task_id를 일괄 전달해 소거하기 위한 DTO.

---

### 📄 [api/v1/research_gap/embedding.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/embedding.py)
OpenAI 임베딩 모델을 활용해 연구 질의 텍스트에 부합하는 pgvector 3072차원 검색용 실수 벡터를 인코딩하는 헬퍼 클래스 파일입니다.

#### 1) 클래스
*   **`EmbeddingModelHelper`**: OpenAI 임베딩 생성 클래스입니다.
    *   `__init__(self) -> None`: 지연 변수를 셋업합니다.
    *   `get_embeddings(self) -> OpenAIEmbeddings`: `text-embedding-3-large` (3072 차원) 사양으로 LangChain 임베딩 클라이언트를 최초 시점에 초기화해 싱글톤 형태로 재사용 공급합니다.
    *   `encode(self, text: str) -> list[float]`: 인입된 단일 텍스트 문자열에 대응하여 3072차원의 엠베딩 실수 벡터 배열로 인코딩을 수행해 가져옵니다.

---

### 📄 [api/v1/research_gap/dao.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/dao.py)
비동기 연구 분석 태스크 레코드의 PENDING 생성, 진행도/결과/실패 로그 갱신, 한국어 번역 캐싱 갱신, 목록 조회 및 1건/다건 일괄 SQL DELETE 물리 작업을 수행하는 DAO 파일입니다.

#### 1) 클래스
*   **`ResearchGapDao`**: 연구 공백 태스크 DB 처리를 대행합니다.
    *   `__init__(self, orm_session: OrmSessionDep)`: 세션을 주입받습니다.
    *   `async def create_task(self, task_id: str, domain: str, query: str, mid: str) -> ResearchGapTaskEntity`: PENDING 상태와 진행율 0으로 신규 분석 태스크 레코드를 추가합니다.
    *   `async def get_task(self, task_id: str, mid: Optional[str] = None) -> Optional[ResearchGapTaskEntity]`: 태스크 식별자로 단건을 조회합니다.
    *   `async def update_task_progress(self, task_id: str, status: str, progress: int, result: Optional[dict] = None, error_message: Optional[str] = None) -> Optional[ResearchGapTaskEntity]`: 상태 및 진척도(%), 분석 보고서 JSON, 오류 메세지를 갱신합니다.
    *   `async def update_task_translation(self, task_id: str, translated_result: dict) -> Optional[ResearchGapTaskEntity]`: 번역 적용 완료된 국문 JSON 보고서 데이터를 캐싱 컬럼인 `translated_result`에 영구 갱신합니다.
    *   `async def list_tasks(self, mid: str) -> list[ResearchGapTaskEntity]`: 회원 ID가 의뢰한 분석 기록 리스트를 생성 최신순으로 가져옵니다.
    *   `async def delete_task(self, task_id: str, mid: str) -> bool`: 특정 1건의 분석 기록을 지웁니다.
    *   `async def delete_tasks(self, task_ids: list[str], mid: str) -> int`: 인입된 다건의 task_id 배열 리스트와 매치되는 레코드 전체를 DB에서 일괄 삭제(raw DELETE)하고 삭제 처리된 레코드 개수를 반환합니다.

---

### 📄 [api/v1/research_gap/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/services.py)
분석 진척 상태 조회 및 비동기 예약 스케줄링, RAG 기반 유사도 검색을 통합한 상위 4개 고유 문헌 추출, OpenAI structured output을 활용한 문헌별 핵심 비평 추출 및 종합 매트릭스 합성, 번역 캐싱 및 SSE 브로드캐스트 전송 비즈니스 로직을 집행하는 대규모 코어 서비스 파일입니다.

#### 1) 클래스
*   **`ResearchGapService`**: 연구 공백 분석 핵심 업무 비즈니스 서비스 클래스입니다.
    *   `__init__(self, research_gap_dao: ResearchGapDaoDep) -> None`: DAO 의존성을 엮어 초기화합니다.
    *   `async def get_task_status(self, task_id: str, mid: str) -> dict`: 분석 진행도 상황을 DTO 규격에 대응시켜 조회 반환합니다. (미존재 시 `TaskNotFoundError` 예외 유발)
    *   `async def get_task_result(self, task_id: str, mid: str) -> dict`: 완성된 분석 리포트 본문(영문/국문) 및 상태 정보를 획득해 가져옵니다.
    *   `async def start_analysis(self, domain: str, query: str, background_tasks, mid: str) -> str`: 분석 의뢰를 샌드위치 접수합니다.
        *   **로직**:
            1. 입력 도메인의 유효성을 파악 (현재 cs/bio/astronomy만 수용). 불일치 시 `BusinessException` 예외 유발.
            2. UUID로 task_id 생성 후 DB에 PENDING 상태로 선제 적재.
            3. `FastAPI BackgroundTasks` 작업 대기열에 비동기 배치 작업 루틴(`run_batch_analysis`)을 바인딩하여 백그라운드 구동을 예약하고 ID를 우선 즉각 반환.
    *   `async def run_batch_analysis(self, task_id: str, domain: str, query: str, mid: str) -> None`: 비동기로 백그라운드 구동을 시작하는 배치 코어 메서드입니다.
        *   **로직**:
            1. 상태를 RUNNING(진행률 10%)으로 갱신 후 커밋.
            2. 검색주제(`query`)를 임베딩 벡터로 변환.
            3. `common_rag_pipeline.similarity_search`를 가동하여 k=25개 유사 논문 청크를 한 번에 대량 소환 (RAG 검색).
            4. **고유 문헌 필터링 및 병합**: 여러 청크에 걸쳐 쪼개진 텍스트를 `arxiv_id` 기준으로 중복 분류하여 정리하고, 일치하는 논문은 청크들을 상호 병합. 이 중 유사도가 가장 매칭도가 높은 **상위 4개 고유 문헌**을 분석 대상군으로 강제 필터링하여 준비. (논문이 한 편도 없으면 FAILED 업데이트 처리)
            5. 상태를 RUNNING(진행률 40%)으로 갱신 후 커밋.
            6. **논문별 개별 분석**: `ChatOpenAI(temp=0)` 모델에 구조화 출력 `PaperAnalysisResult` 규격을 바인딩하여 4개의 논문 Abstract에 대하여 해결 기법(최대 2개), 한계 과제(최대 2개) 및 **이를 설명하는 논문 내 verbatim 실존 영문 인용구(`source_quote`)를 copy해 그대로 추출**.
            7. 상태를 RUNNING(진행률 80%)으로 갱신 후 커밋.
            8. **최종 보고서 합성**: 위 단계에서 수집된 4대 논문 비평 매트릭스를 단일 텍스트 컨텍스트로 결합하여, `ChatOpenAI` 모델에 구조화 `ResearchGapMatrix` 규격을 바인딩해 호출. 전체 논문군이 안고 있는 공통적 한계점(`common_limitations`)과 공백을 메워 나갈 **3개의 혁신적 추천 연구 로드맵 방향성(`suggested_directions`)을 생성**.
            9. 합성 시 유실될 수 있는 원본의 논문별 RAG 유사도 수치 정보를 `similarity` 필드에 복원 대입하여 최종 JSON 딕셔너리로 저장하고 상태를 COMPLETED(진행률 100%)로 갱신 적용.
            10. `NotificationDao`를 열어 비동기 완료 알림 엔티티(`NotificationEntity`)를 저장 및 트랜잭션 커밋.
            11. **SSE 브로드캐스트 발행**: 전역 `notification_broadcaster.broadcast`를 호출하여 SSE 연결 클라이언트에게 태스크 완료 푸시 이벤트를 즉각 실시간 전파.
            12. **예외 방어**: 연산 도중 에러가 터진 경우 FAILED 상태 및 진척율 100%, 오류 상세 문구 기재 업데이트 및 실패 알림 DB 저장 및 SSE 채널 실패 푸시 브로드캐스트 전송.
    *   `async def translate_matrix(self, task_id: str, mid: str) -> dict`: 추출 완료된 영문 RAG 분석 명세를 깔끔한 학술형 국문으로 번역 캐싱합니다.
        *   **로직**:
            1. DB에 `translated_result` 번역본이 이미 존재하면 즉각 반환 (Cache Hit).
            2. 영문 결과가 부재하거나 미완료 시 `BusinessException` 예외 유발.
            3. AI 번역 체인을 가동하되, **"Transformer, RAG, MLP, DNA, Redshift 등 통상적인 학술 약어/약칭명은 훼손 없이 영문 상태를 보존하거나 한국어 병기를 결합할 것"**과 **"논문의 근거 팩트인 verbatim 'source_quote' 인용 필드는 번역을 배제하고 영어 원문 그대로를 무조건 보존할 것"**에 대한 엄격한 번역 지침 프롬프트를 `ChatOpenAI`에 제공하여 한국어 `ResearchGapMatrix` DTO를 합성.
            4. 구조화 합성 과정에서 탈락될 우려가 있는 원본 유사도 점수와 영문 `source_quote` 데이터를 1:1 대조해 번역 결과 DTO에 복원하여 DB에 `translated_result`로 최종 영구 저장 후 반환.
    *   `async def list_user_tasks(self, mid: str) -> list[dict]`: 사용자가 수행했던 분석 배치 태스크들의 메타데이터 목록을 가져옵니다.
    *   `async def delete_user_task(self, task_id: str, mid: str) -> bool`: 태스크 1건을 소거합니다. (권한 없을 시 `TaskNotFoundError` 예외 유발)
    *   `async def delete_user_tasks(self, task_ids: list[str], mid: str) -> int`: 다건의 태스크 일괄 삭제를 처리하고 지워진 행의 개수를 반환합니다.

---

### 📄 [api/v1/research_gap/endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/endpoints.py)
비동기 문헌 분석 배치 예약을 대행하고 상태 조회 및 번역 지시, 다중 이력 일괄 영구 삭제 경로를 정의하는 컨트롤러 파일입니다.

#### 1) 함수 및 라우터
*   **`@router.post("/analyze")`**: 도메인 분석 주제를 인입받아 비동기 스케줄링을 연동하고 생성된 UUID `task_id`를 즉시 반환합니다. (상태 코드 `201 Created`)
*   **`@router.get("/tasks/{task_id}")`**: 현재 백그라운드에서 열심히 돌아가고 있는 배치의 진행도(%) 상태를 묻는 라우터입니다.
*   **`@router.get("/tasks/{task_id}/result")`**: 완료된 분석 태스크의 결과 리포트 JSON 본문을 조회합니다.
*   **`@router.post("/tasks/{task_id}/translate")`**: 영문 분석 리포트를 국문으로 기계 번역하여 캐시 갱신하고 결과를 반환합니다.
*   **`@router.get("/tasks")`**: 회원이 개설했던 모든 분석 배치 작업의 히스토리 이력을 가져옵니다.
*   **`@router.delete("/tasks/{task_id}")`**: 단건의 분석 기록 이력을 DB에서 제거합니다.
*   **`@router.post("/tasks/bulk-delete")`**: 화면에서 체크박스로 다중 선택한 분석 이력들을 일괄 완전 제거하는 라우터입니다.

---

## 12. 🔍 RAG 기반 논문 유사도 검색 도메인 (Similarity Search Domain)

### 📄 [api/v1/similarity_search/models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/similarity_search/models.py)
순수 RAG 유사 논문 검출 질의 시 전달받을 데이터와 결과 조각 사양을 정의하는 DTO 파일입니다.

#### 1) 클래스
*   **`SimilaritySearchRequest(BaseDTO)`**: RAG 검색 질의어(`query`)와 반환 대상 문서 수(`top_k`) 명세 DTO.
*   **`SimilaritySearchResultItem(BaseDTO)`**: 검출 문서 1건 정보 DTO. (doc_id, title, text_chunk, 1.0 - Distance 유사 스코어)
*   **`SimilaritySearchResponse(BaseDTO)`**: 유사 문서 리스트를 감싸 전달하는 응답 DTO.

---

### 📄 [api/v1/similarity_search/endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/similarity_search/endpoints.py)
세 학술 도메인(생명공학, 컴퓨터과학, 천문학)의 pgvector 컬렉션 저장소를 직접 RAG 검색하여 연관 텍스트 청크와 논문 상세를 뽑아내는 API 엔드포인트 파일입니다.

#### 1) 함수 및 라우터
*   **`@router.post("/bio")`**: `common_rag_pipeline.similarity_search`에 "bio" 도메인을 지시 호출하여 관련 생명과학 논문 리스트와 유사 점수 응답을 가공 반환합니다.
*   **`@router.post("/cs")`**: `common_rag_pipeline.similarity_search`에 "cs" 도메인을 지시 호출하여 관련 인공지능/머신러닝 유사 논문 목록을 가져옵니다.
*   **`@router.post("/astronomy")`**: `common_rag_pipeline.similarity_search`에 "astronomy" 도메인을 지시 호출하여 우주/천문학 유사 논문 목록을 가져옵니다.
