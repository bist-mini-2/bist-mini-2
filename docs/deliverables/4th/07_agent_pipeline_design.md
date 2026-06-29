# 7. 핵심 기능별 에이전트 파이프라인 설계 및 최적화 성과

본 문서는 `bist-mini-2` 플랫폼의 3대 핵심 기능인 **일반 채팅 허브**, **대규모 문헌 분석기**, **맞춤형 젬 팩토리** 각각에 대하여 개별 설계 문서에 정의된 **아키텍처 및 시퀀스 흐름(Architecture & Sequence Flows)**을 기준으로 기술한 프로젝트 최종 완성 보고서(Completion Report)입니다. 구글 독스(Google Docs) 본문 서식에 완벽히 연동되도록 작성되었습니다.

---

## 💬 7-1. 일반 채팅 허브 (General Chat Hub) 파이프라인 흐름

일반 채팅 허브는 듀얼 RAG 엔진과 웹 실시간 정보망을 무조건 병렬로 인출 및 융합 합성하는 실시간 대화형 파이프라인입니다.

> 📢 **[구글 독스 이미지 삽입 안내 - 일반 채팅 허브 아키텍처]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/chat-hub-system_architecture.png`

### 1) 시스템 아키텍처 및 데이터 흐름 (Architecture Flow)
1.  **사용자 입력 진입 (Ingress)**: 사용자 발화가 `ChatService`에 들어오면 인텐트 분석을 위해 `ChatMultiAgentSupervisor`가 호출됩니다.
2.  **의도 분리 및 키워드 추출 (Analysis)**: `AnalysisNode` (`gpt-4o-mini` 활용)가 가동되어 자연어 질문에서 RAG용 영어 키워드(`paper_query`)와 실시간 웹 서치용 쿼리(`web_query`)를 인출해 냅니다.
3.  **무조건적 병렬 인출 (Parallel Dispatch)**: 지연을 유발하는 조건부 분기 단계를 거치지 않고, `asyncio.gather`를 통해 `PaperNode` (pgvector RAG 검색)와 `WebNode` (Tavily Web Search)를 병렬 가동하여 순차 실행 대비 약 **23%의 레이턴시 단축(9.22초 ➡️ 7.10초)**을 수립합니다.
4.  **최종 융합 답변 합성 (Synthesis)**: `SynthesisNode` (`gpt-4o` 활용)가 구동되어 RAG 논문 컨텍스트와 실시간 수집된 최신 웹 마켓 동향 데이터를 한 문맥 내에 크로스-조인(Cross-Join) 합성합니다.

> 📢 **[구글 독스 이미지 삽입 안내 - 일반 채팅 허브 시퀀스]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/chat-hub-system_sequence.png`

### 2) 제어권 흐름 및 사후 백업 (Sequence Flow)
*   합성 노드에서 출력되는 마크다운 결과물은 FastAPI `StreamingResponse` 비동기 제너레이터를 타고 SSE(Server-Sent Events) 이벤트 스트림 형식으로 사용자 브라우저에 실시간 타이핑 렌더링됩니다.
*   합성 연산이 완료되면 에이전트의 전체 대화 히스토리 상태는 LangGraph Saver(`AsyncPostgresSaver`) 체커포인터에 영구 적재되어 세션 복원력을 보장합니다.
*   동시에 관계형 DB 트랜잭션이 트리거되어 RAG에 인용된 논문 출처 카드를 `chat_source` 테이블에 저장하고, 후속 추천 Q&A 3선을 `chat_suggestions` 테이블에 백업 커밋합니다.

---

## 📊 7-2. 대규모 문헌 분석기 (Research Gap Analyzer) 파이프라인 흐름

대규모 문헌 분석기는 수십 편의 선행 연구 데이터를 비동기 배치로 처리하여 '해결된 문제'와 '한계점'을 추론하고 SSE 완료 메시지를 방송하는 배치형 분석 파이프라인입니다.

> 📢 **[구글 독스 이미지 삽입 안내 - 대규모 문헌 분석기 아키텍처]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/research-gap-analyzer_architecture.png`

### 1) 시스템 아키텍처 및 데이터 흐름 (Architecture Flow)
1.  **비동기 분석 접수 (Queueing)**: 사용자가 분석을 의뢰하면 `ResearchGapService`가 즉시 고유 `task_id`를 발급하고 데이터베이스 상태를 `PENDING` (진행률 10%)으로 적재하며 브라우저 블로킹을 해제하기 위해 HTTP 202 Accepted를 반환합니다.
2.  **1단계: RAG 검색 및 개별 팩트 해체 (Retrieval & Analysis)**: FastAPI `BackgroundTasks` 백그라운드 스레드가 구동되어 `k=25` RAG 검색 결과에서 중복 문헌을 필터링해 4개 핵심 논문을 선출합니다 (진행률 40% 상태 갱신). 이후 `gpt-4o-mini` Structured Output을 타격하여 Problems Solved와 Limitations를 해체합니다.
3.  **팩트 가드 오버라이트 (Fact Guard)**: 오역 및 정보 왜곡을 예방하기 위해, 요약 한글 번역 전 영문 원어 근거 문장인 `source_quote` 필드를 파이썬 서비스 레이어 상에서 100% 강제 보존 오버라이트합니다 (진행률 80% 상태 갱신).
4.  **2단계: 종합 공백 추론 및 최종 완료 (Synthesis & Complete)**: 4개 논문의 Limitations 교집합을 추론해 AI 혁신 연구 기회를 도출하고 결과서를 DB `translated_result` JSONB 캐시 열에 영구 적재합니다.

> 📢 **[구글 독스 이미지 삽입 안내 - 대규모 문헌 분석기 시퀀스]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/research-gap-analyzer_sequence.png`

### 2) 제어권 흐름 및 완료 알림 (Sequence Flow)
*   백그라운드 루프가 100%에 다다르면 DB의 status를 `COMPLETED`로 변경하고, `notification` 알림 테이블에 새 레코드를 인서트합니다.
*   이와 동시에 `notification_broadcaster`를 가동해 SSE 리스너 채널로 완료 이벤트를 방송(Broadcast)하여 사용자의 브라우저 우측 상단에 실시간 알림 팝업창을 즉각 표출시킵니다.

---

## ⚙️ 7-3. 맞춤형 연구 비서 젬 팩토리 (Research Gem Factory) 파이프라인 흐름

젬 팩토리는 사용자의 맞춤형 페르소나 Prompt와 주입된 파일 셋을 런타임에 동적으로 주입하고, 물리적 보안 격리 및 소멸(Wipe-out)을 수립하는 프라이버시 전용 파이프라인입니다.

> 📢 **[구글 독스 이미지 삽입 안내 - 젬 팩토리 아키텍처]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/research-gem-factory_architecture.png`

### 1) 시스템 아키텍처 및 데이터 흐름 (Architecture Flow)
1.  **젬 메타데이터 생성 (Registration)**: 사용자가 지정한 페르소나 및 db_sources 범위를 `gem` 관계형 테이블에 등록합니다.
2.  **온디맨드 격리 임베딩 (Isolated Embedding)**: 연구용 PDF 주입 시 pdfium 500자 단위 청킹 과정을 거친 후, `gem_{gem_id}_files` 라는 독립 생성된 단독 pgvector 컬렉션 공간에 text-embedding-3-large 3072차원 벡터 데이터로 벌크 적재하여 타 대화방과의 RAG 데이터를 물리 차단합니다.
3.  **런타임 클로저 툴 주입 (Closure Binding)**: 젬과의 대화 가동 시점에, 해당 젬의 고유 식별자(`gem_id`)를 내부 렉시컬 스코프에 캡처하는 **클로저(Closure) 함수**를 백엔드에서 실시간 생성해 `search_gem_files` 도구로 Supervisor Agent에 바인딩합니다.
4.  **Cascade 물리 완전 소멸 (Wipe-out)**: 사용자가 젬을 삭제하면 Cascade 연쇄 메타 드롭 규칙과 pgvector DB의 `DROP TABLE / DROP COLLECTION` 명령어가 실행되어 스레드 내 잔여 데이터를 0 Byte로 완전 소거(Shredding)합니다.

> 📢 **[구글 독스 이미지 삽입 안내 - 젬 팩토리 시퀀스]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/research-gem-factory_sequence.png`

### 2) 제어권 흐름 및 대화 세션 복원 (Sequence Flow)
*   사용자 대화 발화 유입 시 `GemAgent`가 구동되며, 젬 고유의 시스템 프롬프트가 Agent Supervisor에 동적 바인딩됩니다.
*   동시에 `AsyncPostgresSaver`를 노크해 thread_id와 매핑된 이전 대화 히스토리 및 출처 리스트(`sources`)를 PostgreSQL checkpoints 테이블로부터 온디맨드로 완전 복원하여 연속적인 멀티턴 RAG 대화를 가동합니다.
