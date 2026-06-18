# Research Gap Analyzer (대규모 문헌 비교 분석기)

본 모듈은 학계의 기존 연구 논문들을 다차원으로 비교 분석하여, 특정 키워드/기술 분야의 연구 공백(Research Gap)을 식별하고 새로운 연구 로드맵 및 주제를 제안하는 백그라운드 배치 분석 서비스입니다.

---

## 📂 파일 구조 및 역할

- [endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/endpoints.py): API 라우터 정의. 인증 및 예외 처리, 비동기 작업 예약 API 제공.
- [services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/services.py): 핵심 비즈니스 로직. 백그라운드 태스크 수행, LLM 호출 및 SSE 알림 발생 담당.
- [dao.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/dao.py): `research_gap_task` 테이블에 대한 데이터 접근(생성, 진행도 업데이트, 조회) 인터페이스.
- [entity.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/entity.py): SQLAlchemy ORM 엔티티 정의 (`research_gap_task` 테이블 스키마).
- [models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/models.py): Pydantic DTO 정의 (요청/응답 스키마 및 LLM Structured Output 검증용 모델).
- [embedding.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/embedding.py): OpenAI `text-embedding-3-large`를 활용한 3072차원 쿼리 벡터 변환 도구.

---

## 🔄 전체 시스템 흐름도 (Sequence Diagram)

문헌 비교 분석 요청부터 분석 완료 후 최종 결과 화면 렌더링까지의 시퀀스는 아래와 같이 진행됩니다.

```mermaid
sequenceDiagram
    autonumber
    actor User as 사용자
    participant FE as 프론트엔드 (Next.js)
    participant BE as 백엔드 (FastAPI)
    participant Service as ResearchGapService
    participant DB as 데이터베이스 (pgvector)
    participant OpenAI as OpenAI API (LLM / Embeddings)
    participant SSE as 알림 브로드캐스터 (SSE)

    %% 1. 요청 및 태스크 등록
    User->>FE: 키워드 입력 및 분석 시작 요청
    FE->>BE: POST /api/v1/research-gap/analyze (domain, query)
    Note over BE: 사용자 인증 (LoginCheckDep) 수행
    BE->>Service: start_analysis(domain, query, background_tasks, mid)
    
    Service->>DB: 신규 태스크 생성 (PENDING, progress=0)
    Service->>BE: BackgroundTasks 등록 (run_batch_analysis)
    Service-->>BE: task_id (UUID) 반환
    BE-->>FE: SuccessResponse (task_id) 반환

    %% 2. 프론트엔드 대기 및 폴링/SSE 감시
    par
        FE->>BE: GET /api/v1/research-gap/tasks/{task_id} (1.5초 주기 폴링)
        BE->>Service: get_task_status(task_id, mid)
        Service->>DB: 진행도 및 상태 조회
        DB-->>Service: status (RUNNING 등) & progress (%)
        Service-->>BE: 상태 반환
        BE-->>FE: SuccessResponse (status, progress) 반환
    and
        FE->>SSE: SSE 연결 유지 및 이벤트 모니터링 (NotificationContext)
    end

    %% 3. 백그라운드 배치 연산 실행
    Note over Service, OpenAI: [백그라운드 스레드] run_batch_analysis 시작
    Service->>DB: 상태 업데이트 (RUNNING, progress=10)
    
    Service->>OpenAI: query 임베딩 생성 (text-embedding-3-large, 3072차원)
    OpenAI-->>Service: query_vector 반환
    
    Service->>DB: pgvector 코사인 유사도 기준 Top-5 논문 조회
    DB-->>Service: 논문 목록 (title, abstract 등) 반환
    Service->>DB: 상태 업데이트 (RUNNING, progress=40)
    
    loop 각 논문별 분석 (5회 반복)
        Service->>OpenAI: Abstract 개별 분석 요청 (gpt-4o-mini + PaperAnalysisResult 구조화 출력)
        OpenAI-->>Service: PaperAnalysisResult (problems_solved, limitations) 반환
    end
    
    Service->>DB: 상태 업데이트 (RUNNING, progress=80)
    
    Service->>OpenAI: 연구 공백 매트릭스 합성 및 주제 제안 (gpt-4o-mini + ResearchGapMatrix 구조화 출력)
    OpenAI-->>Service: ResearchGapMatrix (common_limitations, suggested_directions) 반환
    
    alt 성공 시
        Service->>DB: 최종 결과 저장 및 완료 처리 (COMPLETED, progress=100)
        Service->>SSE: task_completed SSE 브로드캐스트 전송
        SSE-->>FE: SSE 수신 (Event: task_completed)
    else 에러 발생 시
        Service->>DB: 에러 로그 기록 및 실패 처리 (FAILED, progress=100, error_message)
        Service->>SSE: task_failed SSE 브로드캐스트 전송
        SSE-->>FE: SSE 수신 (Event: task_failed)
    end

    %% 4. 결과 렌더링
    FE->>FE: 폴링 중단 (Interval 해제)
    FE->>BE: GET /api/v1/research-gap/tasks/{task_id}/result
    BE->>Service: get_task_result(task_id, mid)
    Service->>DB: 최종 결과 조회
    DB-->>Service: ResearchGapMatrix 데이터 반환
    Service-->>BE: 데이터 반환
    BE-->>FE: SuccessResponse (result) 반환
    FE->>User: 매트릭스 테이블 및 AI Synthesis 추천 로드맵 화면 출력
```

---

## ⚙️ 상세 연산 흐름 설명 (Core Mechanics)

### 1. 비동기 작업 예약 (`POST /research-gap/analyze`)
- 사용자의 분석 요청 시 긴 대기 시간(LLM 호출 및 벡터 유사도 연산 등 약 10~20초 소요)으로 인한 HTTP Timeout을 방지하기 위해 **FastAPI의 `BackgroundTasks`**를 이용하여 작업을 즉시 백그라운드 스레드로 넘기고 `task_id`를 선 반환합니다.
- 비즈니스 예외 처리 및 도메인 검증("cs" 도메인만 지원)은 [endpoints.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/endpoints.py)가 아닌 서비스 레이어인 [services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/services.py) 내 `start_analysis`에 위임되어 처리됩니다.

### 2. 백그라운드 대용량 분석 배치 (`run_batch_analysis`)
- 백그라운드 작업 수행 시, `sqlalchemy.ext.asyncio.async_scoped_session` 및 `session_maker`를 통해 독립적인 DB 세션을 생성하여 단계별 진행도(Progress)와 상태를 안전하게 개별 커밋합니다.
- **임베딩 및 RAG 문헌 검색 (Progress: 10% ~ 40%)**:
  - [embedding.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/embedding.py) 내 `embedding_helper.encode`를 사용해 질의어를 3072차원 벡터로 변환합니다.
  - pgvector의 `cosine_distance` 연산자를 활용하여 `cs_embeddings` 테이블 내 입력 쿼리와 의미적으로 가장 유사한 논문 5개를 고속 탐색합니다.
- **LLM 구조화 정보 추출 (Progress: 40% ~ 80%)**:
  - 추출된 5개 논문 각각의 메타데이터와 내용을 `gpt-4o-mini` 모델로 보내고, `with_structured_output` API를 통해 `PaperAnalysisResult` 객체 형태로 정밀 추출합니다. (각 논문의 해결과제 `problems_solved` 및 한계점 `limitations` 추출)
- **연구 공백 합성 및 완료 통보 (Progress: 80% ~ 100%)**:
  - 추출된 개별 연구 성과와 한계점 매트릭스를 기반으로 `gpt-4o-mini`를 다시 호출하여 공통 연구 한계점(`common_limitations`) 및 앞으로 보완해 나갈 구체적인 3가지 신규 연구 제안 주제(`suggested_directions`)를 한국어로 구조화하여 합성(`ResearchGapMatrix`)합니다.
  - 성공적으로 완료되면 상태를 `COMPLETED`, 진행도를 `100`으로 DB를 업데이트한 후, **SSE (Server-Sent Events)** 채널(`notification_broadcaster`)을 통해 완료 알림 이벤트를 전역 브로드캐스트합니다.

### 3. 클라이언트-서버 동기화 (Polling + SSE Hybrid)
- **SSE(Server-Sent Events) 감시**: 프론트엔드([page.js](file:///Users/pileuszu/Repos/bist-mini-2/frontend/src/app/feature2/page.js))는 전역 알림 컨텍스트(`NotificationContext`)를 통해 백엔드에서 쏘아 올리는 실시간 SSE 완료/실패 이벤트를 받자마자 즉시 결과를 갱신하고 폴링 타이머를 해제합니다.
- **Fallback Polling**: 네트워크 단절 등으로 인해 SSE 이벤트가 유실되는 비정상 상황에 대비하여, 프론트엔드는 1.5초 간격으로 `GET /research-gap/tasks/{task_id}`를 명시적으로 폴링하며 진행률 바의 수치 갱신 및 상태 동기화의 안정성을 이중으로 보장합니다.

---

## 🛠️ 연동 및 규칙 가이드라인
- **DTO 설계**: 모든 입출력용 DTO는 `BaseDTO`를 상속하여 `ConfigDict(from_attributes=True)` 설정을 유지하고, 비즈니스 및 엔드포인트 코드 내부에 DTO를 혼재시키지 않고 명확히 [models.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/models.py)로 물리 분리하여 구현해야 합니다.
- **MissingGreenlet 에러 예방**: 관계 테이블을 조회하거나 연관 정보를 참조할 시에는 지연 로딩을 철저히 배제하고 `selectinload`를 사용하거나 쿼리 시 직접 컬럼을 프로젝션 조회하여 비동기 실행 오류를 방지해야 합니다.
