# 📜 통합 개발 및 협업 컨벤션 (Integrated Development & Collaboration Conventions)

본 문서는 **'논문 AI 에이전트 채팅 플랫폼 (Paper Agent Chat Platform)'** 프로젝트의 코드 품질 향상, 일관된 아키텍처 유지, 그리고 원활한 협업을 위해 정의된 통합 개발 가이드라인입니다. 

조직 전역의 Git/GitHub 협업 규칙과 프로젝트 백엔드의 기술적 코딩 컨벤션을 모두 포함하고 있으므로, 모든 팀원은 작업을 시작하기 전에 본 문서를 필독하고 준수해야 합니다.

---

## 📂 목차
- [1. 🤝 Git & GitHub 협업 컨벤션](#1--git--github-협업-컨벤션)
  - [브랜치 전략 (Branching Strategy)](#브랜치-전략-branching-strategy)
  - [커밋 메시지 규칙 (Commit Message Conventions)](#커밋-메시지-규칙-commit-message-conventions)
  - [PR 및 코드 리뷰 프로세스](#pr-및-코드-리뷰-프로세스)
  - [CI/CD 및 자동화 워크플로우](#cicd-및-자동화-워크플로우)
- [2. ⚙️ 백엔드 코딩 및 아키텍처 컨벤션](#2-️-백엔드-코딩-및-아키텍처-컨벤션)
  - [API 응답 및 전역 예외 처리 규격](#api-응답-및-전역-예외-처리-규격)
  - [FastAPI Annotated 기반 의존성 주입](#fastapi-annotated-기반-의존성-주입)
  - [Pydantic DTO 전역 설정](#pydantic-dto-전역-설정)
  - [SQLAlchemy AsyncSession 및 MissingGreenlet 방지](#sqlalchemy-asyncsession-및-missinggreenlet-방지)
  - [LangChain Structured Output 타입 검증](#langchain-structured-output-타입-검증)
  - [StreamingResponse 및 제너레이터 구현 규칙](#streamingresponse-및-제너레이터-구현-규칙)
  - [LLM 및 DB 로깅 가이드라인](#llm-및-db-로깅-가이드라인)
  - [에이전트 공유 상태 및 앱 수명 주기](#에이전트-공유-상태-및-앱-수명-주기)
  - [환경 변수 및 도구(Tool) 개발 보안](#환경-변수-및-도구tool-개발-보안)
  - [싱글톤 패턴 및 표준 Docstring](#싱글톤-패턴-및-표준-docstring)

---

## 1. 🤝 Git & GitHub 협업 컨벤션

### 브랜치 전략 (Branching Strategy)
우리 팀은 **GitHub Flow** 기반의 브랜치 전략을 사용합니다. 모든 작업은 개별 기능 브랜치에서 진행되며, Pull Request(PR)를 통한 리뷰 및 테스트 성공 후 `main` 브랜치로 병합됩니다.

#### 🌿 브랜치 유형 및 네이밍 규칙
브랜치 이름은 `작업유형/기능요약` 형태로 소문자와 하이픈(`-`)을 사용하여 작성합니다.
*   **`main`**: 프로덕션 배포 브랜치입니다. 언제나 즉시 배포할 수 있는 안정된 상태로 유지되어야 합니다.
*   **`feature/`**: 새로운 기능 개발 (예: `feature/login-form`, `feature/payment-api`)
*   **`fix/`**: 버그 수정 (예: `fix/token-expiration`, `fix/ui-overflow`)
*   **`refactor/`**: 코드 리팩터링 (예: `refactor/clean-auth-logic`)
*   **`docs/`**: 문서 생성 및 수정 (예: `docs/api-specification`)
*   **`design/`**: CSS, 퍼블리싱 등 UI 디자인 및 스타일 작업 (예: `design/landing-page-hero`)

#### 🔄 작업 및 배포 흐름
1. `main` 브랜치에서 최신 코드를 pull 받습니다.
2. 새로운 작업 브랜치를 생성합니다 (`git checkout -b feature/your-feature`).
3. 변경 사항을 구현하고 커밋 메시지 규칙에 맞춰 커밋을 작성합니다.
4. 원격 저장소(Origin)에 브랜치를 푸시합니다.
5. GitHub에서 `main` 브랜치를 대상으로 Pull Request (PR)를 생성합니다.
6. 팀원의 코드 리뷰 피드백을 수용하여 반영합니다.
7. 최소 1명 이상의 **Approve**와 자동화 빌드/테스트(CI) 성공 확인 후 머지(Merge)합니다.

---

### 커밋 메시지 규칙 (Commit Message Conventions)
일관된 프로젝트 히스토리 관리를 위해 **Conventional Commits** 양식을 준수합니다.

#### 💬 커밋 메시지 구조
```text
<type>(<scope>): <subject>  # 제목 (최대 50자, 영어/한글 모두 가능하나 명확하게)

<body>                      # 본문 (생략 가능, 구체적인 변경 사항 기술)

<footer>                    # 바닥글 (생략 가능, 연관된 Issue 번호 표기)
```

#### 📌 커밋 타입 (Type)
| 타입 | 설명 |
| :--- | :--- |
| **`feat`** | 새로운 기능 추가 |
| **`fix`** | 버그 수정 |
| **`design`** | CSS 및 UI 스타일 변경 작업 |
| **`refactor`** | 코드 리팩터링 (기능 추가나 버그 수정이 없는 코드 개선) |
| **`docs`** | 문서 변경 (README, API 가이드 등) |
| **`style`** | 코드 포맷팅, 세미콜론 누락 등 (코드의 동작 변화가 전혀 없는 경우) |
| **`test`** | 테스트 코드 추가 또는 수정 |
| **`chore`** | 빌드 업무 수정, 패키지 매니저 설정, 환경 설정 변경 등 |
| **`rename`** | 파일 혹은 폴더명 변경, 위치 이동 |
| **`remove`** | 파일 삭제 |

#### ⚠️ 작성 규칙
*   제목 첫 글자는 대문자를 지양하며, 마침표(`.`)는 붙이지 않습니다.
*   제목은 명확한 개조식(한글) 또는 동사 원형(영어)으로 시작합니다.
*   본문에는 **어떻게(How)**보다 **무엇을(What)**, **왜(Why)** 변경했는지 서술합니다.

---

### PR 및 코드 리뷰 프로세스

#### 📝 PR 작성 및 진행 순서
1. **PR 제목**: 커밋 컨벤션과 동일하게 작성합니다. (예: `feat(auth): 카카오 로그인 연동`)
2. **템플릿 작성**: PR 생성 시 기본으로 제공되는 **Pull Request Template** 양식을 준수하여 내용을 성실히 기재합니다.
3. **Self Review**: PR을 생성하기 전 변경 사항을 자체 검토하여 불필요한 주석, 디버깅 로그(`print`, `console.log` 등)가 남아있지 않은지 반드시 확인합니다.
4. **Reviewer 지정**: 해당 기능과 연관성이 높거나 도메인 지식이 있는 팀원을 리뷰어로 지정합니다.

> [!IMPORTANT]
> **PR 생성 시 검증 체크리스트**
> - [ ] 개발 환경에서 빌드 및 컴파일에 성공했는가?
> - [ ] 작업한 기능에 대해 유닛 테스트를 진행했거나 테스트 코드를 작성했는가?
> - [ ] 불필요한 콘솔 로그, 임시 print문, 또는 쓰이지 않는 주석을 제거했는가?
> - [ ] 프로젝트 코드 스타일 가이드를 준수했는가?

---

### CI/CD 및 자동화 워크플로우
프로젝트 저장소에는 협업 생산성 향상을 위해 다음과 같은 GitHub Actions 워크플로우가 구성되어 있습니다.

1. **Auto PR Description (`auto-pr.yml`)**
   *   PR이 오픈되거나 새로운 커밋이 푸시될 때, 중앙 조직의 `.github` 저장소 내 `auto-pr-writer.yml`과 연동되어 Gemini API를 통해 변경 사항 요약 설명(Description)을 자동으로 작성해 줍니다.
2. **Python Build & Test CI (`test.yml`)**
   *   `main` 및 `test` 브랜치에 대해 PR이 올라왔을 때 동작합니다.
   *   Python 3.12 환경에서 의존성을 설치하고, **Ruff**를 사용해 정적 코드 분석(Lint Check)을 수행하며, **pytest**를 실행하여 테스트 케이스 통과 여부를 자동으로 검증합니다.

---
---

## 2. ⚙️ 백엔드 코딩 및 아키텍처 컨벤션

### API 응답 및 전역 예외 처리 규격

#### 🟢 일관된 API 응답 구조
프론트엔드 파싱 편의성을 위해 모든 HTTP API 응답은 아래의 전역 공통 JSON 구조를 따릅니다.
*   **성공 시 (HTTP 200/201)**:
    ```json
    {
      "status": "success",
      "data": { ... }
    }
    ```
*   **실패 시 (HTTP 4xx/5xx)**:
    ```json
    {
      "status": "error",
      "message": "에러 발생 원인 및 설명"
    }
    ```

#### 🛑 HTTP 상태 코드 매핑 규칙
*   `200 OK`: 일반 조회 및 성공적인 비즈니스 로직 처리 완료 시.
*   `201 Created`: 신규 리소스(데이터베이스 레코드, 파일 등)가 성공적으로 적재되었을 때.
*   `400 Bad Request`: Pydantic ValidationError 등 파라미터 유효성 검증 실패 및 비즈니스 예외 발생 시.
*   `401 Unauthorized`: 인증 토큰이 없거나 잘못된 인증 시도 시.
*   `403 Forbidden`: 요청 권한이 부족하여 리소스 접근이 거부되었을 때.
*   `404 Not Found`: 존재하지 않는 Thread ID, API Endpoint, 리소스 요청 시.
*   `500 Internal Server Error`: 백엔드 런타임 내 처리되지 않은 미상의 예외 발생 시.

#### 🔒 동적 API 캐싱 방지 정책
실시간 대화 정보 및 에이전트의 답변 API는 클라이언트 또는 CDN 등 프론트/중간 서버에서 캐싱을 원천 방지해야 합니다. 따라서 모든 동적 API 응답 헤더에 아래 필드를 강제 주입합니다.
```http
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
```

#### 🛠️ 전역 공통 응답 DTO 및 예외 처리기 구현
성공 및 실패 시의 응답 규격을 전역적으로 통일하기 위해 공통 응답 DTO(`SuccessResponse`, `ErrorResponse`)를 사용하고, 예외 발생 시 전역 예외 처리기를 통해 자동 포맷팅합니다.
*   **공통 응답 DTO**: [dto_base.py](file:///d:/Repo/bist-mini-2-backend/api/database/config/dto_base.py)에 정의된 `SuccessResponse` 및 `ErrorResponse`를 상속 및 적용합니다.
*   **예외 처리기 구현**: [exception_handler.py](file:///d:/Repo/bist-mini-2-backend/api/common/exception_handler.py)의 `register_exception_handler(app)`를 통해 `HTTPException`, `RequestValidationError`, `Exception` 등을 캐치하여 `status`, `message` 형태의 규격화된 에러 JSON 응답을 반환합니다.
*   **캐시 방지 자동화**: `main.py`에 HTTP 미들웨어를 추가하여 모든 `/api/v1/*` 동적 API 응답 헤더에 `Cache-Control`을 자동 주입하고, `/static/*` 정적 파일은 `NoCacheStaticFiles` 커스텀 서브클래스를 사용해 브라우저 캐싱을 방지합니다.

---

### FastAPI Annotated 기반 의존성 주입

#### 🏷️ Annotated 공식 도입
IDE 자동 완성, 코드 가독성 및 정적 분석기(Pyright)의 명확한 분석 지원을 위해 FastAPI 매개변수 선언 시 `typing.Annotated` 방식을 필수로 사용합니다.
*   ❌ **금지**: `db: AsyncSession = Depends(get_db)`
*   ✅ **권장**: `db: Annotated[AsyncSession, Depends(get_db)]`

#### 🔗 공통 타입 Alias 정의
여러 컨트롤러/라우터에서 공통으로 호출하는 의존성은 `api/dependencies.py` 파일 내에 사전 정의하여 일관되게 임포트합니다.
```python
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
```

#### 🛡️ Depends 캐싱을 활용한 2단계 보안 검증 패턴
FastAPI의 `Depends` 캐시 메커니즘(`use_cache=True`)을 활용해 중복되는 JWT 복호화 및 유저 조회 쿼리 비용을 회피합니다.
1.  **1단계 (Router 레벨)**: `dependencies=[Depends(verify_access_token)]` 설정을 통해 진입 지점에서 유효성 및 권한을 1차 검증하고, 추출된 유저 데이터를 캐시에 적재합니다.
2.  **2단계 (Controller 레벨)**: 실제 엔드포인트 핸들러 인자에서 `payload: LoginCheckDep`과 같이 호출하여 검증된 데이터를 재계산 없이 즉시 재사용합니다.

---

### Pydantic DTO 전역 설정

#### 📦 Custom Base Class 패턴 적용
프로젝트 내부의 모든 Pydantic Schema(DTO)는 기본 `BaseModel`이 아닌, 전역 설정이 주입된 `BaseDTO`를 상속받아 구현합니다.

*   **정의 위치**: [dto_base.py](file:///d:/Repo/bist-mini-2-backend/api/database/config/dto_base.py)
*   **설정 방식**:
    ```python
    from pydantic import BaseModel, ConfigDict
    
    class BaseDTO(BaseModel):
        model_config = ConfigDict(
            from_attributes=True  # ORM 객체(Entity) 속성을 DTO 모델로 자동 매핑 지원
        )
    ```

#### 📂 DTO 물리적 분리 및 위치 규칙
엔드포인트 라우터 파일의 크기가 불필요하게 커지는 것을 방지하고 단일 책임 원칙(SRP)을 준수하기 위해, 모든 Pydantic DTO 클래스는 엔드포인트 파일 내부에 정의하지 않고 반드시 별도의 `schemas` 폴더 내에 분리하여 작성합니다.
*   **정의 위치**: `api/v1/schemas/` (예: [auth.py](file:///d:/Repo/bist-mini-2-backend/api/v1/schemas/auth.py))
*   **사용 방식**: 엔드포인트 파일(`api/v1/endpoints/*.py`)에서는 해당 `schemas` 모듈로부터 DTO를 임포트하여 `response_model` 및 타입 어노테이션에 지정합니다.

---

### SQLAlchemy AsyncSession 및 MissingGreenlet 방지

비동기 루프 내에서 DB 지연 로딩(Lazy Loading) 발생 시 `MissingGreenlet` 에러가 발생하므로, 관계 필드에 대한 지연 조회를 금지하고 아래의 대응법 중 하나를 적용해야 합니다.

#### 💡 해결책 A: 프로젝션 직접 조회 (권장)
단순 읽기 전용 API는 필요한 컬럼만 `select` 인자로 직접 명시하여 `.mappings().all()`을 호출하고, `RowMapping` 딕셔너리를 활용해 DTO로 즉시 직렬화합니다.

#### 💡 해결책 B: Eager Loading 명시
ORM 모델을 직접 다뤄야 하는 경우, 명시적으로 관계 필드를 함께 로드하도록 쿼리를 작성합니다.
```python
# selectinload를 통한 즉시 로딩 기법 적용
stmt = select(User).options(selectinload(User.posts)).where(User.id == user_id)
```

#### 🔄 비동기 트랜잭션 (Flush vs Commit) 수명 주기 규칙
*   **`db.flush()`**: 비동기 트랜잭션 수행 도중 기본 키(PK)의 획득이나 데이터베이스 단의 제약 조건 검증(유효성 검사 등)이 중간 단계에서 필요할 때만 호출합니다.
*   **`db.commit()`**: 전체 비동기 비즈니스 트랜잭션이 안전하게 마무리되는 최종 시점에만 한 번 호출하여 락(Lock)을 해제하고 세션을 안전하게 풀로 반환합니다.

---

### LangChain Structured Output 타입 검증

#### 🎯 Type Guard를 사용한 타입 안정성 확보
LangChain의 `with_structured_output` API는 `Runnable[Any, BaseModel | dict]` 타입을 반환하므로 컴파일 단계에서 Pyright 에러를 방지하고 런타임 안정성을 보장하기 위해 `isinstance` 검증을 의무 적용합니다.
```python
result = await structured_chat.ainvoke(content)

# 명시적인 타입 가드 수행
if not isinstance(result, TargetDTO):
    raise TypeError(f"Expected TargetDTO, got {type(result)}")
return result
```

---

### StreamingResponse 및 제너레이터 구현 규칙

#### 🔤 Generator Yield 타입 캐스팅
FastAPI `StreamingResponse`는 오직 `str`과 `bytes` 타입 스트림만 전송할 수 있습니다. LLM Chunk의 content가 리스트 등으로 추론될 가능성을 원천 차단하기 위해 `isinstance` 타입 체크 후 yield합니다.
```python
async for chunk in chat.astream(messages):
    content = chunk.content
    if isinstance(content, str) and content:
        yield content
```

#### ⚙️ 비동기 제너레이터 양방향 데이터 주입 (Priming)
제너레이터에 값을 밀어 넣는(`.send()`) 로직 설계 시, `next()` 호출과 `.send()`의 동시 혼용으로 루프 내부에서 `None` 데이터가 이중 주입되는 오류를 예방해야 합니다.
*   **프라이밍(Priming)**: 루프가 동작하기 전, 최초 1회에 한해서만 `await generator.__anext__()` (또는 `next(generator)`)를 호출하여 시동을 겁니다.
*   **실행**: 본격적인 데이터 흐름 제어는 오직 `send(값)` 메서드만 호출하여 양방향 데이터를 전송합니다.

#### 📥 파일 다운로드 API 가이드라인
*   대용량 다운로드 처리 시 메모리 오버헤드를 막기 위해 `StreamingResponse` 대신 **`FileResponse`** 사용을 강력히 권장합니다.
*   다운로드 시 브라우저 내에서 즉각 렌더링되거나 오작동하지 않도록 아래 헤더를 명시해 반환해야 합니다.
    ```python
    headers = {"Content-Disposition": 'attachment; filename="filename.pdf"'}
    ```

---

### LLM 및 DB 로깅 가이드라인

1.  **통합 LLM 로깅 콜백**: 디버깅과 토큰 비용 추적을 위해 LLM에 대한 프롬프트 입력과 반환된 응답 출력을 공통 규격에 따라 콘솔 및 파일에 기록하는 커스텀 로깅 핸들러를 주입합니다.
2.  **컬러 로깅**: 백엔드 콘솔의 출력 가시성을 위해 `colorlog` 라이브러리를 적용하고 레벨별로 일관되게 포맷팅합니다.
3.  **SQL 쿼리 로깅 연동**: SQL 쿼리 로그를 콘솔에 난잡하게 출력하지 않고, 파이썬 표준 `logging` 패키지로 수집하여 콘솔 및 통합 에이전트 로그 파일에 함께 통합시킵니다.
    ```python
    import logging
    # SQLAlchemy 로그를 파이썬 로깅 모듈에 통합
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    ```

---

### 에이전트 공유 상태 및 앱 수명 주기

#### 📊 에이전트 공유 상태 (Shared State) 설계
*   LangGraph 오케스트레이션 노드(질문 분석, RAG, 브라우징 등) 간 데이터 공유를 위한 `Shared State`는 단일 Pydantic 스키마 구조로 프로젝트 루트에 공통 정의합니다.
*   에이전트 노드는 해당 스키마에 정의된 속성 키와 자료형에 맞춰서만 값을 읽고 업데이트해야 합니다.

#### 🔄 FastAPI Lifespan 및 CORS
*   데이터베이스 커넥션 풀의 생명 주기는 서버 구동 시 오픈하고, 종료 시 소멸하도록 `lifespan` 비동기 컨텍스트 핸들러 안에서 명확하게 관리합니다.
*   Next.js 등 웹 프론트엔드 도메인 연동을 위해 허용 Origin을 지정한 CORS 미들웨어를 활성화하고, 허용 도메인은 환경 변수(`ALLOWED_ORIGINS`)를 통해 설정합니다.

---

### 환경 변수 및 도구(Tool) 개발 보안

#### 🔐 환경 변수(Environment Variables) 제어
*   API 키(OpenAI, Tavily 등)나 데이터베이스 연결 정보 같은 민감한 설정값은 코드에 직접 기입(Hard-coding)할 수 없으며, 반드시 `.env` 파일에 기록하고 `Pydantic-Settings` 라이브러리를 통해 싱글톤으로 읽어 들여 사용합니다.

#### 📂 로컬 파일 시스템 도구(File Tool)의 경로 검증
*   로컬 디렉터리 내에 파일을 쓰거나 읽는 에이전트용 도구를 개발할 경우, 악의적인 상대 경로 탐색(`../..`) 공격을 감지해 사전에 오류를 방지하도록 차단 유효성 검사 로직을 필수로 구현해야 합니다.

#### 🛠️ LLM 노출 제어 및 Direct Return
*   외부 API 키 등 민감 데이터가 LLM 프롬프트 Context 상에 노출되지 않도록 `context_schema` 속성을 사용해 내부적으로만 관리되도록 설정합니다.
*   LLM의 불필요한 부가 요약 없이 데이터를 있는 그대로 즉시 반환해야 하는 API 도구는 `return_direct=True` 속성을 강제 주입하여 실행 속도와 안정성을 제고합니다.

---

### 싱글톤 패턴 및 표준 Docstring

#### 🧩 Python 모듈 캐싱 기반 싱글톤(Singleton)
*   DB 접속 엔진, 앱 설정 정보(`Settings`), API 클라이언트 등 전역적으로 1개의 인스턴스만 공유되어야 하는 자원은 파이썬 자체의 **모듈 임포트 캐싱(`sys.modules`) 메커니즘**을 사용해 싱글톤을 구축합니다.
*   생성자 `Class()`를 반복 호출해 새 개체를 만드는 구문을 배제하고, 모듈 파일 내부에서 생성한 글로벌 인스턴스 변수를 임포트하여 사용하게 함으로써 리소스 경합 및 동기화 상태 불일치를 원천 방지합니다.

#### ✍️ 표준 Google 스타일 Docstring 적용
협업 및 Sphinx 등의 아키텍처 문서 자동 생성 도구를 지원하기 위해, 프로젝트의 모든 클래스, 함수, 모듈 선언문 하단에는 아래 규칙의 **Google Style Docstring**을 필수 기재합니다.
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
