# ⚙️ 백엔드 개발 체크리스트 (Backend Development Checklist)

본 체크리스트는 FastAPI, SQLAlchemy, LangChain 기반 백엔드 서비스 개발 시 준수해야 하는 코딩 가이드라인 및 검증 규칙입니다. 모든 백엔드 수정 PR은 아래 항목을 통과해야 합니다.

---

## 1. API 응답 및 예외 처리 (API Response & Exception Handling)
- [ ] **일관된 응답 구조**: 모든 HTTP API 응답이 표준 JSON 구조를 따르고 있습니까?
  - **성공 (200/201)**: `{ "status": "success", "data": { ... } }`
  - **실패 (4xx/5xx)**: `{ "status": "error", "message": "에러 발생 원인 및 설명" }`
- [ ] **HTTP 상태 코드 매핑 규칙**:
  - `200 OK`: 일반 조회 및 성공적인 비즈니스 로직 처리 완료 시.
  - `201 Created`: 신규 리소스(DB 레코드, 파일 등)가 성공적으로 적재되었을 때.
  - `400 Bad Request`: 입력 값 유효성 검증 실패 (`Pydantic ValidationError`) 및 비즈니스 예외 발생 시.
  - `401 Unauthorized`: 인증 토큰이 없거나 잘못된 인증 시도 시.
  - `403 Forbidden`: 요청 권한이 부족하여 리소스 접근이 거부되었을 때.
  - `404 Not Found`: 존재하지 않는 Thread ID, 파일 경로, API 엔드포인트 요청 시.
  - `500 Internal Server Error`: 백엔드 서버 내부의 미처리 런타임 예외 발생 시.
- [ ] **동적 API 캐싱 방지**: 모든 동적 API 엔드포인트 응답 헤더에 캐시 방지 필드가 강제 주입되어 있습니까?
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`
  - 정적 라우팅 시 커스텀 StaticFiles 서브클래스(`NoCacheStaticFiles`)를 사용하고 있습니까?

## 2. FastAPI 의존성 주입 (FastAPI Dependency Injection)
- [ ] **Annotated 의존성 주입**: 모든 FastAPI 의존성 주입 매개변수 선언 시 `typing.Annotated` 방식을 사용하고 있습니까?
  - *올바른 예*: `db: Annotated[AsyncSession, Depends(get_db)]`
  - *잘못된 예*: `db: AsyncSession = Depends(get_db)`
- [ ] **공통 타입 Alias 재사용**: `api/dependencies.py`에 선언된 공통 의존성 Alias를 임포트하여 일관되게 사용하고 있습니까?
  - `DbSession = Annotated[AsyncSession, Depends(get_db)]`
  - `CurrentUser = Annotated[User, Depends(get_current_user)]`
- [ ] **2단계 보안 검증 패턴**: JWT 토큰 검증 시, 1단계(`APIRouter` 레벨)에서 토큰 유효성 검증 및 캐시 적재를 수행하고, 2단계(컨트롤러 레벨)에서 캐싱된 토큰 정보를 호출하여 중복 디코딩을 회피하고 있습니까?

## 3. Pydantic DTO (Pydantic DTOs)
- [ ] **BaseDTO 상속**: 모든 Pydantic 스키마 모델이 `api/database/config/dto_base.py`에 정의된 `BaseDTO`를 상속받고 있습니까?
  - `ConfigDict(from_attributes=True)` 설정을 상속받아 구현해야 합니다.
- [ ] **물리적 파일 분리**: 모든 DTO 클래스가 엔드포인트 파일 내부에 선언되지 않고, 각 기능별 폴더(`api/v1/[기능]/models.py`) 내에 명확히 물리적으로 분리되어 작성되었습니까?

## 4. SQLAlchemy AsyncSession 및 MissingGreenlet 에러 방지
- [ ] **지연 로딩(Lazy Loading) 금지**: 관계 필드 접근 시 `MissingGreenlet` 에러 방지를 위해 Eager Loading을 명시적으로 사용했습니까?
  - `selectinload(Model.relation)` 또는 필요한 컬럼만 직접 프로젝션 조회(`.mappings().all()`)를 수행해야 합니다.
- [ ] **비동기 드라이버 사용**: 데이터베이스 연결 문자열이 `asyncpg` 드라이버를 기반으로 기재되었습니까?
- [ ] **비동기 트랜잭션 수명 주기**:
  - `db.flush()`: 트랜잭션 도중 자동 생성 키(PK) 획득이나 데이터베이스 제약 조건 검증이 필요할 때만 호출합니다.
  - `db.commit()`: 비즈니스 트랜잭션이 안전하게 마무리되는 최종 시점에만 한 번 호출하여 세션을 반환합니까?

## 5. LangChain Structured Output 타입 검증
- [ ] **타입 가드(Type Guard) 적용**: `with_structured_output` API의 반환 결과에 대해 `isinstance` 타입 검증을 명시적으로 적용했습니까?
  ```python
  result = await structured_chat.ainvoke(content)
  if not isinstance(result, TargetDTO):
      raise TypeError(f"Expected TargetDTO, got {type(result)}")
  ```

## 6. StreamingResponse 및 제너레이터 구현 규칙
- [ ] **문자열 타입 캐스팅**: 제너레이터 루프 내부에서 yield를 수행하기 전 문자열 타입 검증을 거쳤습니까?
  ```python
  if isinstance(content, str) and content:
      yield content
  ```
- [ ] **비동기 제너레이터 프라이밍(Priming)**: 양방향 데이터 전송(`.send()`) 로직 설계 시, 최초 1회 `await generator.__anext__()` (또는 `next()`)를 호출하여 시동을 건 후 `.send()`를 사용합니까?
- [ ] **파일 다운로드**: 대용량 파일 다운로드 처리 시 `StreamingResponse` 대신 `FileResponse`를 우선 사용하고, `Content-Disposition` 헤더를 설정하여 전달했습니까?

## 7. 로깅 (Logging)
- [ ] **LLM 콜백 통합**: LLM의 프롬프트 입출력 내역을 표준 규격에 따라 콘솔 및 파일에 기록하는 커스텀 로깅 핸들러를 주입했습니까?
- [ ] **SQL 쿼리 로깅 통합**: SQL 실행 로그가 stdout이 아닌 파이썬 표준 `logging` 패키지로 수집되도록 설정했습니까?
  - `logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)`

## 8. 일반 패턴 및 문서화 (General Patterns & Documentation)
- [ ] **싱글톤 패턴**: DB 접속 엔진, 앱 설정 정보 등 전역적으로 공유되는 자원은 파이썬 모듈 캐싱 메커니즘을 이용한 싱글톤 인스턴스 형태로 임포트하여 사용합니까?
- [ ] **표준 Google 스타일 Docstring**: 모든 모듈, 함수 및 클래스 선언부 하단에 Google 스타일의 Docstring(인자 타입, 설명, 반환 값 및 발생 가능 예외)을 필수로 기재했습니까?
