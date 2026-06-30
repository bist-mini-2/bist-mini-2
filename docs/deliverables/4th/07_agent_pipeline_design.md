# 7. 핵심 기능별 에이전트 파이프라인 설계 및 최적화 성과

본 문서는 `bist-mini-2` 플랫폼의 3대 핵심 기능인 **일반 채팅 허브**, **대규모 문헌 분석기**, **맞춤형 젬 팩토리** 각각에 대하여 개별적으로 동작하는 **파이프라인 아키텍처 흐름(Pipeline Architecture Flow)**을 단계별(Step-by-Step)로 기술한 랩업 리포트(Completion Report)입니다. 구글 독스(Google Docs) 본문 서식에 완벽히 연동되도록 작성되었으며, 각 기능별 전용 아키텍처 흐름도 이미지를 즉시 삽입할 수 있는 랜드마크를 제공합니다.

---

## 💬 7-1. 일반 채팅 허브 (General Chat Hub) 파이프라인 플로우

일반 채팅 허브는 질문의 라우팅 분기 판단에 따른 대기 지연을 예방하고, 학술 논문 DB와 실시간 웹 정보를 무조건 병렬로 인출 및 융합 합성하는 단방향 실시간 파이프라인입니다.

> 📢 **[구글 독스 이미지 삽입 영역 - 일반 채팅 허브 파이프라인]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/usecase_hubs_rag_flow.png`
> *   *(이 이미지는 Ingress부터 AnalysisNode, asyncio.gather 병렬 RAG, SynthesisNode, SSE 송출에 이르는 채팅 파이프라인 흐름을 도식화하고 있습니다.)*

*   **Step 1. 질의 진입 및 인텐트 분석 (Ingress & Analysis)**
    *   사용자의 입력 질문이 접수되면 `AnalysisNode` (`gpt-4o-mini` 기용)가 즉각 가동됩니다.
    *   질문을 파싱하여 의미적 RAG용 영어 키워드(`paper_query`)와 최신 상용 동향 수집용 검색어(`web_query`)로 즉시 분리·도출합니다.
*   **Step 2. 듀얼 트랙 무조건적 병렬 인출 (Parallel Dispatch)**
    *   조건부 라우팅을 거치지 않고, `asyncio.gather` 비동기 라이브러리를 통해 pgvector 논문 DB 검색(`PaperNode`)과 Tavily Search API 크롤링(`WebNode`)을 동시 가동합니다.
    *   두 I/O 연산을 병렬 실행함으로써 순차 지연 대비 **평균 23%의 레이턴시 단축(9.22초 ➡️ 7.10초)**을 수립했습니다.
*   **Step 3. 교차 융합 합성 및 인용 매핑 (Cross-Join & Synthesis)**
    *   `SynthesisNode` (`gpt-4o` 기용)가 가동되어, 검색된 고정 학술 정보(RAG)와 최신 웹 뉴스 컨텍스트를 한 프레임워크 내에서 조인(Join)합니다.
    *   인용된 ArXiv 논문의 식별 코드를 찾아내어 답변의 근거 자료로 1:1 결합(Mapping)을 진행합니다.
*   **Step 4. 스트리밍 송출 및 사후 데이터 적재 (Egress & Persist)**
    *   FastAPI의 `StreamingResponse` 비동기 제너레이터를 호출하여 답변 마크다운을 HTTP SSE(Server-Sent Events) 채널로 즉시 밀어냅니다.
    *   스트리밍이 완결되는 시점에 사용된 논문 서지를 관계형 DB의 `chat_source` 테이블에 비동기 트랜잭션 적재하고 후속 질문을 추천 생성합니다.

---

## 📊 7-2. 대규모 문헌 분석기 (Research Gap Analyzer) 파이프라인 플로우

대규모 문헌 분석기는 오랜 연산 시간이 소요되는 배치 성격의 의뢰를 백그라운드 스레드에서 안정적으로 병렬 해체 및 합성하고 실시간으로 알림을 중재하는 비동기 파이프라인입니다.

> 📢 **[구글 독스 이미지 삽입 영역 - 대규모 문헌 분석기 파이프라인]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/usecase_gap_analysis_flow.png`
> *   *(이 이미지는 BackgroundTasks 비동기 큐 접수, 중복 제거, Problems/Limitations 개별 해체, 공백 합성 및 번역 가드, SSE 브로드캐스트의 흐름을 도식화하고 있습니다.)*

*   **Step 1. 분석 요청 접수 및 비동기 큐 위임 (Queueing)**
    *   사용자가 분석 요청을 인가하면 백엔드는 고유 `task_id` (UUID)를 발급하고 `research_gap_task` 테이블에 초기 상태(`PENDING`)를 삽입합니다.
    *   사용자의 대기 차단을 막기 위해 연산 핸들러를 FastAPI `BackgroundTasks` 비동기 큐에 즉각 위임하고 클라이언트에 200 OK 응답을 즉시 반환합니다.
*   **Step 2. 중복 문헌 필터링 및 유사도 상위 논문 선출 (Deduplication)**
    *   백그라운드 스레드에서 해당 도메인 pgvector 검색(`k=25`)을 거쳐 중복된 문헌을 배제한 뒤 가장 무관 노이즈가 없는 핵심 4개 논문의 원본 초록 본문을 안전하게 추출합니다 (진행률 40% 상태 갱신).
*   **Step 3. 개별 문헌 팩트 해체 및 검증 근거 가드 (Deconstruction)**
    *   `gpt-4o-mini` 모델의 Structured Output 기능을 기용하여 각 개별 논문의 핵심 해결 과제(Problems Solved)와 한계점(Limitations)을 엄격한 JSON DTO로 추출합니다.
    *   이때 오역 방지와 학술적 엄밀성을 위해 팩트 검증 문장인 `source_quote` 문자열 리스트를 파이썬 서비스 레이어 가드를 통해 영어 원어 상태 그대로 100% 영구 보존합니다 (진행률 80% 상태 갱신).
*   **Step 4. 공백 추론 합성 및 SSE 완료 브로드캐스트 (Aggregation & Delivery)**
    *   4개 논문 limitations의 공통 교집합(Common Limitations)을 추론하고 혁신 미래 연구 과제 3선을 도출하는 종합 보고서를 최종 완성합니다.
    *   보고서 한글 번역 객체를 DB `translated_result` JSONB 캐시 영역에 적재하고, SSE Broadcaster 채널을 노크하여 클라이언트 브라우저 알림창(`notification` 연계)으로 "분석 완료" 이벤트를 실시간 발송합니다 (진행률 100% 완료).

---

## ⚙️ 7-3. 맞춤형 연구 비서 젬 팩토리 (Research Gem Factory) 파이프라인 플로우

젬 팩토리는 사용자의 맞춤형 페르소나 지침과 외부 연구 문서를 런타임에 동적으로 주입하여, 고도의 데이터 기밀 격리와 Cascade 생명주기 제어를 달성하는 파이프라인입니다.

> 📢 **[구글 독스 이미지 삽입 영역 - 젬 팩토리 파이프라인]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 클릭한 뒤, 아래 파일을 선택해 삽입해 주세요:
> *   **업로드 대상 파일**: `docs/deliverables/4th/usecase_gem_factory_flow.png`
> *   *(이 이미지는 개인 PDF 파싱/벡터 격리 적재, 런타임 클로저 툴 주입, 젬 삭제 시 DROP TABLE 완전 소멸에 이르는 기밀 생명주기를 도식화하고 있습니다.)*

*   **Step 1. 페르소나 바인딩 및 젬 등록 (Metadata Registration)**
    *   사용자가 맞춤형 연구 지침 프롬프트와 참조 도메인 카테고리를 설정하면, 백엔드는 관계형 DB의 `gem` 테이블에 메타 레코드를 영구 저장합니다.
*   **Step 2. 업로드 파일 온디맨드 벡터화 및 컬렉션 격리 (Isolated Embeddings)**
    *   사용자가 특정 젬에 개인 논문(PDF 등)을 업로드하면, 백그라운드에서 pdfium 파서를 통해 문서를 500자 크기로 자동 청킹합니다.
    *   `text-embedding-3-large` API를 통해 각 청크를 3072차원으로 변환한 뒤, 독립 생성된 전용 pgvector 저장 컬렉션인 `gem_{gem_id}_files` 테이블 공간에만 안전하게 벌크 적재하여 타 대화방과의 데이터 공유를 완벽하게 물리 차단합니다.
*   **Step 3. 런타임 클로저(Closure) 기반 동적 도구 주입 (Closure Binding)**
    *   해당 젬과의 세션 대화방이 개설되면, 백엔드는 런타임 시점에 해당 `gem_id`를 렉시컬 스코프 내에 가두는 **클로저(Closure) 함수**를 동적으로 빌드합니다.
    *   이 함수를 Supervisor Agent의 실행 컨텍스트에 툴(Tool)로 실시간 바인딩하여, 에이전트가 다른 스토리지 공간을 오염시키지 않고 지정된 전용 벡터 컬렉션에서만 검색을 하도록 강제 제어합니다.
*   **Step 4. Cascade 기반 물리 완전 소멸 (Wipe-out)**
    *   사용자가 젬을 삭제하면 관계형 데이터베이스 Cascade 연쇄 삭제 제약 조건에 의해 메타데이터가 영구 드롭됩니다.
    *   이와 동시에 백엔드는 데이터베이스 연결 드라이버를 통해 `gem_{gem_id}_files` 컬렉션 테이블 공간을 물리적으로 `DROP TABLE` 처리하여 디스크 내의 모든 벡터 데이터를 흔적 없이 영구 소멸(0 Byte)시킵니다.
