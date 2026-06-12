# 📋 논문 AI 에이전트 플랫폼 상세 기능 명세서 (MVP Phase 1 & 2)

본 문서는 **'논문 AI 에이전트 플랫폼 (Paper Agent Platform)'**의 최종 구현을 위한 초정밀 기능 명세서입니다. 
본 시스템은 대화형 서비스인 `일반 챗 허브 (General Chat Hub)`를 기본으로 하고, 심층 추론이 필요한 3가지 핵심 기능(대규모 문헌 비교 분석기, 보안 샌드박스 피어 리뷰 및 디펜스 아레나, 맞춤형 연구 비서 팩토리)을 더해 총 4가지의 기능군을 **MVP 1단계(Phase 1)**로 정의합니다. 정기적인 논문 데이터 수집 등 백그라운드 자동화 프로세스는 **MVP 2단계(Phase 2)**로 분류하여 개발 우선순위를 설정합니다.

---

## 🏛️ 아키텍처적 당위성: 개별 탭으로 화면을 물리적 분리해야 하는 이유

1. **일반 챗 허브 (General Chat Hub)**: 빠른 속도의 RAG 파이프라인을 통해 사용자의 일반적인 대화 및 가벼운 탐색에 대해 즉각적인 응답(Token-by-Token 스트리밍)을 지원합니다.
2. **대규모 문헌 스펙 비교 및 공백(Research Gap) 분석기**: 수십 편의 논문 데이터를 비동기 배치로 읽어 '해결된 문제'와 '한계점'을 일괄 분석합니다. 오랜 연산 시간이 소요되므로 일반 챗 허브 창을 블로킹하지 않도록 백그라운드로 처리하고 전용 매트릭스/타임라인 대시보드 UI로 시각화합니다.
3. **보안 샌드박스 피어 리뷰 및 가설 디펜스 아레나**: 기밀 정보의 유출을 차단하는 격리 환경(30분 자동 소거)을 유지하고, 다중 에이전트(방법론/신규성/문체) 토론 및 실시간 모의 디펜스(채팅 및 실시간 채점)를 독립된 공간에서 진행합니다.
4. **맞춤형 연구 비서 (Research Gem) 팩토리**: 사용자가 특정 데이터 소스(RAG DB)와 페르소나(System Prompt)를 조합해 만든 맞춤형 에이전트들을 카드 형태로 스토어에 보관하고 호출할 수 있는 독립 제어판입니다.

---

## 📂 1. 공통 3대 도메인 pgvector DB 및 RAG 검색 엔진 명세 (공통 분담)

| 기능 코드 | 하위 구분 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 (파라미터) | Output 스펙 (결과 데이터) | 상세 설명 |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-RAG-01** | 데이터/RAG | 의학/바이오(NFCorpus) RAG 파이프라인 | **P0** | PostgreSQL pgvector / `POST /similarity-search/medical` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • NFCorpus/TREC-COVID 데이터셋 pgvector 테이블(`medical_embeddings`) 500자 단위 청킹 적재 및 유사도 검색 반환 |
| **F-RAG-02** | 데이터/RAG | 컴퓨터 과학(SCIDOCS) RAG 파이프라인 | **P0** | PostgreSQL pgvector / `POST /similarity-search/cs` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • SCIDOCS 데이터셋 pgvector 테이블(`scidocs_embeddings`) 500자 단위 청킹 적재 및 유사도 검색 반환 |
| **F-RAG-03** | 데이터/RAG | 자연 과학(SciFact) RAG 파이프라인 | **P0** | PostgreSQL pgvector / `POST /similarity-search/science` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • SciFact 데이터셋 pgvector 테이블(`science_embeddings`) 500자 단위 청킹 적재 및 유사도 검색 반환 |

---

## 🚦 2. MVP 1단계 (Phase 1) 상세 기능 명세

### 2.1 일반 챗 허브 (General Chat Hub)
일반 챗 허브는 가벼운 질문에 대한 RAG 검색 및 출처 매핑과 실시간 토큰 스트리밍을 제공하는 기본 소통 창구입니다.

| 기능 코드 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-01-A-1** | Step-Back 쿼리 생성기 | **P1** | Advanced Prompt | • `user_question` (str) | • `abstracted_queries`: Array of `query` (str) | • 질문을 추상화하여 RAG 검색 적합도를 넓히는 대안 쿼리 생성 모듈 |
| **F-01-A-2** | CoT 추론 엔진 (스트리밍) | **P1** | LangChain / SSE | • `thread_id` (str)<br>• `message` (str) | • `text_token` (str)<br>• `thinking_step` (str) | • "단계별로 생각하기" 과정을 실시간 SSE 스트리밍으로 송출하여 생각의 흐름 시각화 |
| **F-01-A-3** | 인용 출처 메타 DTO 정의 | **P0** | Pydantic 스키마 | N/A | • `CitationSource` 객체:<br>&nbsp;&nbsp;- `index` (int), `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str), `authors` (str), `year` (int) | • 답변 본문의 인라인 번호(`[1]`, `[2]`)에 1:1로 매핑되는 서지 구조체 정의 |
| **F-01-A-4** | 구조화 출력 변환 에이전트 | **P0** | `POST /agent-structured-output` | • `llm_raw_response` (str) | • `answer` (str)<br>• `sources`: Array of `CitationSource` | • Pydantic을 활용해 답변 텍스트와 참조 문헌 목록을 하나의 JSON 구조체로 출력 보장 |
| **F-01-A-5** | 인용 관계망 조회 API | **P1** | `GET /papers/{id}/citations` | • `id` (str) | • `nodes`: Array, `links`: Array | • 타겟 논문의 인용/피인용 계보를 노드-링크 데이터 구조로 반환 (D3.js 시각화용) |

---

### 2.2 대규모 문헌 스펙 비교 및 공백(Research Gap) 분석기
수십 편의 선행 연구 데이터를 비동기로 메타 분석하여 연도별 스펙 매트릭스 및 연구 공백 제안 대시보드를 구축합니다.

| 기능 코드 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-01-B-1** | 비동기 분석 작업 요청 API | **P1** | `POST /research-gap/analyze` | • `paper_ids`: Array of `str`<br>• `focus_area` (str) | • `task_id` (str)<br>• `status` (str: PENDING) | • 대량 분석 요청 시 즉시 `task_id`를 반환하고 백엔드 비동기 큐에 연산 적재 |
| **F-01-B-2** | 비동기 분석 작업 상태 조회 | **P1** | `GET /research-gap/tasks/{task_id}` | • `task_id` (str) | • `status` (str: RUNNING/SUCCESS)<br>• `matrix_data`: JSON Object | • 분석 작업 상태 및 결과를 폴링/조회하는 API |
| **F-01-B-3** | 논문 한계점 및 해결과제 추출 | **P1** | Pydantic Structured Output | N/A | • `solved_problems`: Array of `str`<br>• `limitations`: Array of `str` | • RAG 파이프라인에서 추출한 논문 문맥에서 '기존 해결 문제'와 '한계점'을 구조화 데이터로 강제 변환 |
| **F-01-B-4** | 연구 공백(Research Gap) 제안 | **P2** | LLM Synthesis Node | • `matrix_data` (JSON) | • `gap_analysis` (str)<br>• `recommended_topics`: Array | • 일괄 취합된 매트릭스 데이터를 기반으로 학계의 공백 지점과 추천 연구 주제를 합성하여 출력 |

---

### 2.3 보안 샌드박스 피어 리뷰 및 가설 디펜스 아레나 (보안 샌드박스 + 피어 리뷰 결합)
기밀 유지 샌드박스 환경에서 PDF 분석 및 가설 검증을 거친 후, 3대 에이전트 토론을 통한 피어 리뷰 및 모의 디펜스를 원스톱으로 수행합니다. 변동 연구 동향은 능동적으로 알림 구독 처리됩니다.

| 기능 코드 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-02-A-1** | PDF 격리 업로드 및 임베딩 | **P1** | `POST /validation/upload-isolated` | • `file` (UploadFile)<br>• `session_id` (str) | • `session_file_id` (str)<br>• `chunk_count` (int) | • 보안 샌드박스 세션 스코프 내에서만 조회되는 임시 임베딩 인덱스 적재 |
| **F-02-A-2** | 샌드박스 세션 자동 소거 데몬 | **P1** | OS Path Guard / Shredding | N/A | N/A | • 30분 미활동 시 세션 PDF 파일 및 pgvector 임시 테이블 공간을 영구 완전 소거 (Wipe Out) |
| **F-02-A-3** | 다중 에이전트 피어 리뷰 실행 | **P1** | `POST /academic-peer-review` | • `draft_text` (str)<br>• `target_journal` (str) | • `overall_score` (int)<br>• `review_report` (str)<br>• `diff_table`: Array of Diff | • LangGraph 기반 3대 에이전트(방법론, 신규성, 학술문체)가 토론(Debate)을 거쳐 최종 종합 피드백 DTO 도출 |
| **F-02-A-4** | 자기 일관성(Self-Consistency) 가설 검증 | **P1** | Majority Voting Logic | • `hypothesis` (str)<br>• `turns` (int = 3) | • `verdict` (SUPPORT/REFUTE)<br>• `confidence_score` (float) | • 임시 업로드 문서 및 RAG DB에서 관련 근거를 취합해 N회 독립 추론 후 다수결 합의 도출 |
| **F-02-A-5** | 심사위원 에이전트 디펜스 아레나 | **P2** | `POST /sandbox/defense/chat` | • `session_id` (str)<br>• `user_response` (str) | • `refutation_question` (str)<br>• `score` (int), `feedback` (str) | • 피어 리뷰 보고서 기반으로 가상의 심사위원이 압박 질문을 던지고, 사용자의 방어 논리를 실시간 채점하는 시뮬레이터 |
| **F-02-A-6** | 최신 변동 동향 알림 구독 API | **P2** | `POST /sandbox/subscriptions` | • `hypothesis` (str)<br>• `email` (str) | • `subscription_id` (str) | • 검증 가설을 구독하면 백그라운드에서 주기적 탐색 후 메일함(Inbox) UI에 동향 배달 등록 |
| **F-02-A-7** | 알림 인박스(Trend Inbox) 조회 | **P2** | `GET /sandbox/subscriptions/inbox` | 없음 | • `inbox_items`: Array of Notification Card | • 구독된 가설을 지지/반박하는 최신 논문 서치 결과 및 변동 사항을 모아보는 전용 수신함 API |

---

### 2.4 맞춤형 연구 비서 (Research Gem) 팩토리 & 스토어
특정 지식 DB와 고유의 페르소나를 장착한 특화 에이전트(Gem)를 직접 조립 및 보관하고 사용합니다.

| 기능 코드 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-03-A-1** | 젬(Gem) 생성 API | **P1** | `POST /gems` | • `name` (str)<br>• `db_sources` (List of str)<br>• `system_prompt` (str) | • `gem_id` (str)<br>• `name` (str)<br>• `db_sources` (List) | • 지정된 이름, RAG 소스 참조 필터(의학/CS/자연과학 DB 중 다중 선택), 시스템 프롬프트를 바인딩해 영구 저장 |
| **F-03-A-2** | 젬(Gem) 목록 조회 API | **P1** | `GET /gems` | 없음 | • `gems`: Array of Gem Card | • 생성 및 스토어에 보관된 사용자 정의 젬 카드 리스트 호출 |
| **F-03-A-3** | 젬(Gem) 1:1 특화 대화 API | **P1** | `POST /gems/{gem_id}/chat` | • `thread_id` (str)<br>• `message` (str) | SSE Stream | • 생성된 특정 젬의 페르소나와 지정된 RAG 필터를 타겟팅하여 격리된 1:1 대화를 진행 |

---

## 📂 3. MVP 2단계 (Phase 2) 백그라운드 프로세스 명세 (2순위 개발 영역)

| 기능 코드 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | 스케줄/동작 주기 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **B-01-A-1** | arXiv/PubMed 정기 크롤러 데몬 | **P3** | HTTP Client Batch Service | 매일 02:00 (KST) | • arXiv 및 PubMed Open API를 호출하여 최근 등록된 타겟 도메인(의학, 컴퓨터과학, 자연과학) 논문의 메타데이터 및 PDF 링크 수집 |
| **B-01-A-2** | 신규 논문 파이프라인 적재 배치 | **P3** | Text Chunker & Embedder | 크롤링 완료 직후 | • 새로 수집된 논문 텍스트를 500자 단위 청킹 처리하고 OpenAI/BGE 임베딩 모델로 벡터 변환하여 pgvector 테이블에 bulk insert |
| **B-01-A-3** | 구독 가설 자동 매칭 변동 탐색 | **P3** | Vector Query Execution | 매주 월요일 03:00 | • 유저가 등록한 구독 가설(**F-02-A-6**)에 대해 RAG 유사도 검색을 재실행하여 신규 추가된 논문들의 지지/반박 여부를 판별하고 Inbox 적재 |

---

## 📂 4. 에이전트 공통 메모리 및 시스템 인프라 사양

*   **실시간 스트리밍 아키텍처 (Real-time Streaming)**:
    - 에이전트 연산의 각 단계(CoT 생각의 흐름, LangGraph 토론 단계 로그 등) 및 최종 답변을 `StreamingResponse`를 통해 클라이언트에 점진적으로 송신합니다.
*   **PostgreSQL 기반 히스토리 영구 보존 (`PostgresSaver`)**:
    - 대화 이력 및 LangGraph 상태 저장소는 비동기식 `PostgresSaver`를 구축하여 Thread ID별로 안정적으로 영구 보존합니다.
*   **컨텍스트 최적화 요약 미들웨어 (`SummarizationMiddleware`)**:
    - 대화의 길이가 임계치를 초과할 시, 오래된 대화 턴을 핵심 요약본으로 압축 보존하여 LLM 컨텍스트 한계를 방어합니다.

---

## ⚙️ 5. 개발 및 공통 코드 컨벤션 (Development & Coding Conventions)

모든 백엔드 및 프론트엔드 코드의 수정, 생성, 리팩토링 시 아래의 규칙을 엄격히 준수합니다.

*   **FastAPI DI 패턴**: 모든 의존성 주입 시 `typing.Annotated` 방식을 필수적으로 적용합니다 (예: `db: DbSession`).
*   **DTO 및 Entity 설계**: 모든 Pydantic 스키마는 `BaseDTO` (`from_attributes=True` 상속)를 상속하여 각 도메인 패키지 내 `models.py`로 물리적으로 분리합니다. 관계형 DB ORM 연결 시 Lazy Loading 대신 selectinload 등을 통한 Eager Loading을 강제합니다.
*   **API 응답 규격화**: 모든 응답은 `{"status": "success", "data": ...}` 래핑 규격을 따르며, 동적 API 응답 헤더에는 캐시 방지(`Cache-Control: no-store, no-cache...`) 필드를 강제 주입합니다.
*   **프론트엔드 스타일 및 연동**: TypeScript 대신 **JavaScript**를 사용하고, 인라인 CSS를 배제하며 **Vanilla CSS 및 Bootstrap 5**만을 활용합니다. 시각 기호 표시에는 텍스트 이모지 사용이 금지되고 **Bootstrap Icons** 클래스를 사용해야 합니다.
