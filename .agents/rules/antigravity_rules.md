---
trigger: always_on
glob: *
description: 프로젝트의 백엔드 및 프론트엔드 개발 컨벤션을 엄격하게 준수하고, 규칙 파일을 스스로 수정 및 보완할 수 있습니다.
---

# Antigravity Agent Rules

- **[통합 개발 가이드라인 최우선 준수]** 에이전트(Antigravity)는 백엔드 및 프론트엔드 코드의 수정, 생성, 리팩토링 시 아래 명시된 개발 컨벤션을 반드시 최우선적으로 준수해야 합니다.
- **[스스로 규칙 수정 권한 (Self-Modification Directive)]** 에이전트는 프로젝트 요구사항의 변화, 프레임워크 변경 및 개발 상황에 맞춰 본 규칙 파일(`antigravity_rules.md`)을 스스로 수정, 편집 및 보완할 수 있는 권한을 가집니다. 추가되거나 수정되는 사항이 있을 경우 주저하지 말고 본 규칙 파일의 지시문을 갱신하십시오.

---

## ⚙️ 백엔드 개발 컨벤션 (Backend Conventions)

### 1. API 응답 및 예외 처리
- 모든 HTTP API 응답은 일관된 JSON 구조를 따릅니다.
  - **성공 (200/201)**: `{ "status": "success", "data": { ... } }`
  - **실패 (4xx/5xx)**: `{ "status": "error", "message": "에러 발생 원인 및 설명" }`
  - **예외 사항 (인증 API)**: OAuth2.0 표준 규격(RFC 6749)을 활용하는 Swagger UI의 `Authorize` 자물쇠 인증 기능과의 호환성을 보장하기 위해, 로그인/토큰 발급 엔드포인트(예: `/auth/login`)에 한해서는 응답 성공 래퍼를 씌우지 않고 루트 레벨에 `access_token`과 `token_type`이 담긴 플랫 JSON 구조를 직접 반환합니다.
- **HTTP 상태 코드 매핑 규칙**:
  - `200 OK`: 일반 조회 및 성공적인 비즈니스 로직 처리 완료 시.
  - `201 Created`: 신규 리소스(DB 레코드, 파일 등)가 성공적으로 적재되었을 때.
  - `400 Bad Request`: 입력 값 유효성 검증 실패 (`Pydantic ValidationError`) 및 비즈니스 예외 발생 시.
  - `401 Unauthorized`: 인증 토큰이 없거나 잘못된 인증 시도 시.
  - `403 Forbidden`: 요청 권한이 부족하여 리소스 접근이 거부되었을 때.
  - `404 Not Found`: 존재하지 않는 Thread ID, 파일 경로, API 엔드포인트 요청 시.
  - `500 Internal Server Error`: 백엔드 서버 내부의 미처리 런타임 예외 발생 시.
- **동적 API 캐싱 방지**: 모든 동적 API 엔드포인트 응답 헤더에 cache 방지 필드가 강제 주입되어야 합니다:
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`
  - 정적 라우팅 시 커스텀 StaticFiles 서브클래스(`NoCacheStaticFiles`)를 사용합니다.

### 2. FastAPI 의존성 주입
- **Annotated 의존성 주입**: 모든 FastAPI 의존성 주입 매개변수 선언 시 `typing.Annotated` 방식을 사용합니다.
  - *올바른 예*: `db: Annotated[AsyncSession, Depends(get_db)]`
  - *잘못된 예*: `db: AsyncSession = Depends(get_db)`
- **공통 타입 Alias 재사용**: `api/dependencies.py`에 선언된 공통 의존성 Alias를 임포트하여 사용합니다.
  - `DbSession = Annotated[AsyncSession, Depends(get_db)]`
  - `CurrentUser = Annotated[User, Depends(get_current_user)]`
- **2단계 보안 검증 패턴**: JWT 토큰 검증 시, 1단계(`APIRouter` 레벨)에서 토큰 유효성 검증 및 캐시 적재를 수행하고, 2단계(컨트롤러 레벨)에서 캐싱된 토큰 정보를 호출하여 중복 디코딩을 회피합니다.

### 3. Pydantic DTO
- **BaseDTO 상속**: 모든 Pydantic 스키마 모델이 `api/database/config/dto_base.py`에 정의된 `BaseDTO`를 상속받습니다 (`ConfigDict(from_attributes=True)` 설정을 상속).
- **물리적 파일 분리**: 모든 DTO 클래스가 엔드포인트 파일 내부에 선언되지 않고, 각 기능별 폴더(`api/v1/[기능]/models.py`) 내에 명확히 물리적으로 분리되어 작성되어야 합니다.

### 4. SQLAlchemy AsyncSession 및 MissingGreenlet 에러 방지
- **지연 로딩(Lazy Loading) 금지**: 관계 필드 접근 시 `MissingGreenlet` 에러 방지를 위해 Eager Loading을 명시적으로 사용합니다.
  - `selectinload(Model.relation)` 또는 필요한 컬럼만 직접 프로젝션 조회(`.mappings().all()`)를 수행합니다.
- **비동기 드라이버 사용**: 데이터베이스 연결 문자열이 `asyncpg` 드라이버를 기반으로 동작하도록 구성합니다.
- **비동기 트랜잭션 수명 주기**:
  - `db.flush()`: 트랜잭션 도중 자동 생성 키(PK) 획득이나 데이터베이스 제약 조건 검증이 필요할 때만 호출합니다.
  - `db.commit()`: 비즈니스 트랜잭션이 안전하게 마무리되는 최종 시점에만 한 번 호출하여 세션을 반환합니다.

### 5. LangChain Structured Output 타입 검증
- **타입 가드(Type Guard) 적용**: `with_structured_output` API의 반환 결과에 대해 `isinstance` 타입 검증을 명시적으로 적용합니다.
  ```python
  result = await structured_chat.ainvoke(content)
  if not isinstance(result, TargetDTO):
      raise TypeError(f"Expected TargetDTO, got {type(result)}")
  ```

### 6. StreamingResponse 및 제너레이터 구현 규칙
- **문자열 타입 캐스팅**: 제너레이터 루프 내부에서 yield를 수행하기 전 문자열 타입 검증을 수행합니다.
  ```python
  if isinstance(content, str) and content:
      yield content
  ```
- **비동기 제너레이터 프라이밍(Priming)**: 양방향 데이터 전송(`.send()`) 로직 설계 시, 최초 1회 `await generator.__anext__()` (또는 `next()`)를 호출하여 시동을 건 후 `.send()`를 사용합니다.
- **파일 다운로드**: 대용량 파일 다운로드 처리 시 `StreamingResponse` 대신 `FileResponse`를 우선 사용하고, `Content-Disposition` 헤더를 설정하여 전달합니다.

### 7. 로깅
- **LLM 콜백 통합**: LLM의 프롬프트 입출력 내역을 표준 규격에 따라 콘솔 및 파일에 기록하는 커스텀 로깅 핸들러를 주입합니다.
- **SQL 쿼리 로깅 통합**: SQL 실행 로그가 stdout이 아닌 파이썬 표준 `logging` 패키지로 수집되도록 설정합니다.
  - `logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)`

### 8. 일반 패턴 및 문서화
- **싱글톤 패턴**: DB 접속 엔진, 앱 설정 정보 등 전역적으로 공유되는 자원은 파이썬 모듈 캐싱 메커니즘을 이용한 싱글톤 인스턴스 형태로 임포트하여 사용합니다.
- **표준 Google 스타일 Docstring**: 모든 모듈, 함수 및 클래스 선언부 하단에 Google 스타일의 Docstring(인자 타입, 설명, 반환 값 및 발생 가능 예외)을 필수로 기재합니다.

### 9. RAG 데이터 가공 및 임베딩 규격
- **RAG 텍스트 청킹(Chunking) 표준 규격**: 논문 초록 분할 시, 단락의 문맥 유실 방지를 위해 **500자(Characters) 단위** 분할 및 **50자의 중첩 영역(Overlap)**을 부여하는 슬라이딩 윈도우 방식을 필수로 준수해야 합니다.
- **임베딩 벡터 차원**: 임베딩 차원은 **3072차원**을 표준으로 채택하며, 3대 학술 영역 벡터 테이블(`cs_embeddings`, `bio_embeddings`, `astronomy_embeddings`)에 적재할 때 vector(3072) 스펙을 준수해야 합니다.
- **인덱스 성능 최적화**: pgvector 인덱스 형식은 코사인 유사도 연산 속도와 정확도 보장을 위해 **HNSW (Hierarchical Navigable Small World)** 방식을 사용하고, 생성 시 `WITH (m = 16, ef_construction = 64)` 설정을 필수로 적용해야 합니다.

### 10. 보안 샌드박스 및 파일 파쇄 규칙
- **샌드박스 세션 수명 주기 및 완전 소거(Wipe Out)**: 30분 미활동 시 세션 PDF 파일 및 pgvector 임시 테이블 공간을 영구 완전 소거(Wipe Out)하도록 처리합니다. (DB의 `ON DELETE CASCADE` 연쇄 작동 및 물리 파일 `os.remove` 처리 등)
- **보안 취약점 방지**: PDF 격리 업로드 및 관리 시, 디렉토리 트래버스(Directory Traversal) 우회 방지를 위한 **OS Path Guard** 검증을 필수로 수행해야 합니다.

### 11. API 캐싱 및 비동기 푸시 알림 (성능 최적화)
- **Redis 캐싱 정책**: 읽기 연산 부하가 크고 구조가 고정적인 API(예: `GET /papers/{id}/citations` 인용 관계망 조회 및 반복 RAG 쿼리)에는 **Redis 인메모리 캐시**를 거치도록 설계하고, 실시간 동적 대화나 보안 세션은 노캐시 정책을 유지해야 합니다.
- **비동기 알림 방식 (Push-based)**: 대규모 문헌 분석(`POST /research-gap/analyze`)과 같이 처리 시간이 긴 백그라운드 비동기 작업은 클라이언트의 Polling 부하를 방지하기 위해, 완료 시 백엔드에서 **SSE 푸시 이벤트**를 발생시켜 알림 인박스에 즉각 수신 통보되도록 연동합니다.

### 12. 도메인별 독립 구현 및 Git 충돌 방지
- 각 학술 도메인(bio, cs, astronomy 등)은 Git Merge Conflict를 원천적으로 방지하기 위해 공통 폴더(예: `backend/api/common/`)의 코드를 직접 수정하거나 공유하지 않는 것을 원칙으로 합니다.
- 임베딩 모듈과 같이 도메인별로 사용하는 유틸리티 및 RAG 핵심 기능은 공통 모듈에 선언하지 않고, 각 기능의 개별 v1/[도메인]/ 내부(예: `backend/api/v1/cs/embedding.py`)에 독립적으로 구현하여 격리해야 합니다.

---

## 🌐 프론트엔드 개발 컨벤션 (Frontend Conventions)

### 1. 기술 스택 제약 사항
- **JavaScript 사용 (TypeScript 금지)**: 전체 코드베이스는 반드시 **JavaScript**(`.js`, `.jsx`, `.mjs`)로 작성되어야 하며, 경로 설정 및 alias 매핑을 위해 `jsconfig.json`을 사용합니다.
- **Vanilla CSS 및 Bootstrap 5 사용 (Tailwind CSS 금지)**: UI 스타일링을 위해 **Vanilla CSS**와 **Bootstrap 5**만을 사용해야 합니다. 명시적 요청이 없는 한 Tailwind CSS 클래스 및 설정 파일 사용은 금지됩니다.
- **Axios를 통한 API 요청**: 백엔드와의 모든 비동기 API 통신은 Axios를 사용하며, 관련 통신 모듈은 `src/apis/` 디렉토리에 분리합니다.

### 2. Next.js App Router 구조
- **라우팅 구조**: 모든 페이지 구성이 Next.js App Router 규격에 따라 `src/app/` 하위 폴더 구조로 설계되어야 합니다 (동적 세그먼트 파라미터는 `[param]` 폴더 명 사용).
- **서버 및 클라이언트 컴포넌트 분리**:
  - 기본적으로 모든 컴포넌트는 Server Component로 유지됩니다.
  - React 훅(`useState`, `useEffect`, `useContext` 등)이 필요한 파일에만 상단에 `"use client"` 지시어를 사용합니다.

### 3. 스타일링 및 Bootstrap 통합
- **Bootstrap 클라이언트 컴포넌트 로드**: 루트 `layout.js`에 `BootstrapClient.js` 래퍼 컴포넌트가 적절하게 마운트되어야 합니다 (Bootstrap CSS 스타일 및 JS 번들 스크립트가 클라이언트 단에서 작동하도록 설정).
- **Bootstrap 유틸리티 클래스 활용**: 페이지 레이아웃 구조화 및 컴포넌트 디자인 시 Bootstrap의 표준 스타일 클래스(`container`, `row`, `col-*`, `d-flex`, `justify-content-*`, `align-items-*`, `shadow`, `border-0`, `rounded-*` 등)를 적극적으로 활용합니다.
- **커스텀 스타일 가이드 (인라인 CSS 완전 배제)**: 추가 커스텀 스타일이 필요할 경우, `src/app/globals.css` 또는 모듈형 CSS 스타일시트(`*.module.css`)에만 추가해 구현합니다. JSX/JS 코드 내에서 인라인 `style={{ ... }}` 속성을 선언하는 것은 일관성과 유지보수성 확보를 위해 엄격하게 금지하며, 발견 시 반드시 CSS 모듈 혹은 공통 클래스로 리팩토링하여 이관해야 합니다.
- **아이콘 사용 규칙 (이모지 사용 금지)**: UI 데코레이션이나 네비게이션 아이콘 등 모든 시각적 기호 표시 시 텍스트 이모지(이모티콘)의 사용을 금지하고, 반드시 **Bootstrap Icons** 클래스(`bi bi-*`)를 사용하여 일관성 있고 깔끔한 스타일을 유지해야 합니다.

### 4. 상태 관리 및 Context API
- **Context API를 통한 전역 상태 관리**: 사용자 인증 정보나 시스템 설정과 같이 여러 컴포넌트에서 공유되어야 하는 상태 정보들은 React **Context API**를 구현해 관리합니다.
  - 생성된 컨텍스트 관련 파일은 `src/contexts/` 폴더 내에 정의되어야 합니다.
  - 컨텍스트 프로바이더는 필요한 하위 컴포넌트 트리(주로 `layout.js` 단)를 감싸도록 설정합니다.

### 5. 협업 및 커밋 컨벤션
- **브랜치 전략**: `main` 브랜치가 아닌, 개별 기능 작업을 위한 브랜치(`feature/`, `fix/`, `refactor/`, `design/`, `docs/` 등)를 생성해 작업합니다.
- **커밋 메시지 규칙**: 모든 커밋 메시지가 Conventional Commits 형식을 준수해야 합니다 (`feat`, `fix`, `design`, `docs`, `refactor` 등).
- **PR 전 셀프 리뷰**: PR 생성 전 변경 사항 중 임시로 작성한 디버깅 로그(`console.log` 등)나 불필요한 주석이 남아있지 않은지 검토합니다.
- **자동 커밋 및 푸시 금지**: 에이전트는 임의로 자동 `git commit` 및 `git push` 명령을 수행해서는 안 됩니다. 코드의 수정이 끝난 후, 사용자에게 작업 완료를 알리고 명시적인 동의나 명령을 받은 경우에만 커밋/푸시 작업을 진행해야 합니다.

### 6. 비동기 작업 및 실시간 알림 연동
- **SSE Push 알림 수신**: 백그라운드 비동기 분석 작업 및 구독 가설의 완료/업데이트 알림은 폴링을 통한 오버헤드를 줄이기 위해, 백엔드로부터의 **SSE(Server-Sent Events) 스트림**을 수신하여 클라이언트 단의 탑바 알림 또는 인박스(Trend Inbox) UI에 실시간 갱신 및 배달되도록 구현합니다.
