# 📋 논문 AI 에이전트 채팅 플랫폼 상세 기능 명세서 & 개발 컨벤션 (Granular Functional Specification & Conventions)

본 문서는 **'논문 AI 에이전트 채팅 플랫폼 (Paper Agent Chat Platform)'**의 구현을 위한 초정밀 기능 명세서입니다. 
본 시스템은 **"대량의 논문 데이터(수십만 건)가 데이터베이스에 적재 및 벡터화되어 있다"**는 전제 하에 작동하며, 백엔드와 프론트엔드가 정확한 스펙으로 매핑되어 개발될 수 있도록 각 기획 유즈케이스(UC-1 ~ UC-4) 및 화면(W-01 ~ W-07)별 상세 스펙을 정밀 분할하여 기술합니다.

---

## 🏛️ 아키텍처적 당위성: 왜 개별 탭으로 화면을 물리적 분리해야 하는가?

본 플랫폼은 단순한 LLM Wrapper 챗봇이 아닌, 고급 연구 및 보안 검증 작업을 수행하는 시스템입니다. 각 핵심 기능(Chat Hub, Library, Secure Sandbox, Peer Review Workshop)을 단일 대화창의 Tool Calling으로 합치지 않고 **좌측 사이드바 탭 메뉴로 물리적 분리하여 구현해야만 하는 기술적 및 기획적 당위성**은 다음과 같습니다.

### 1. 🛡️ [Secure Sandbox 탭] 보안 격리성(Security Isolation) 및 안심(Reassurance) UX 보장
*   **보안 컨텍스트의 물리적 분리**: 일반 채팅방(`Chat Hub`)은 대화 이력이 영구 보존되며 외부 웹 검색(Tavily 등)이 빈번하게 발생하여 컨텍스트 노출 위험이 높습니다. 반면 `Secure Sandbox`는 기업 기밀(미발표 신약 PDF, 특허 초안)을 다룹니다.
*   **메모리 오염 및 유출 방지**: 단일 대화창 내에서 LLM의 Tool 호출을 통해 기밀 문서를 다룰 경우, 대화 히스토리 및 LLM 컨텍스트 윈도우 내에 기밀 정보가 잔존하여 이후의 일반 질문에 대한 답변으로 유출될 위험이 기술적으로 존재합니다.
*   **수명 주기 제어**: 샌드박스는 **30분 미활동 시 백그라운드 스케줄러(F-02-E-2)에 의한 자동 파쇄(Wipe Out)**를 보장합니다. 일반 대화방과 화면을 분리함으로써 사용자가 "격리되고 안전한 보안 영역에 진입함"을 시각적으로 인지할 수 있고, 물리적인 로컬 파일 시스템 및 임시 pgvector 테이블의 소멸 시점을 명확하게 통제할 수 있습니다.

### 2. ⏳ [Peer Review Workshop 탭] 비동기 장기 실행(Stateful Long-running) 프로세스 격리
*   **독립적인 UI 상태(State) 보존**: 피어 리뷰 워크숍은 3대 전문 에이전트가 conditional edge 분기를 타고 수십 초 이상 의견을 나누는 **고부하 LangGraph 멀티 에이전트 연산**입니다.
*   **작업 블로킹 방지**: 사용자가 논문 초안에 대한 장시간의 피어 리뷰 연산을 돌려둔 상태에서, 다른 선행 연구를 탐색하거나 일반 채팅(`Chat Hub`)을 하고 싶을 수 있습니다. 만약 단일 채팅방에서 툴로 리뷰를 실행하면 리뷰가 완료될 때까지 대화창이 블로킹되거나 토큰 스트리밍이 뒤섞이게 됩니다.
*   **대시보드형 시각화 필요성**: 에이전트 간의 실시간 토론 상태 변화(`W-09` Debate Arena) 및 구절별 원문-수정본 대비표(`W-07`)는 대화방의 좁은 말풍선 형태로 렌더링하기에 정보 밀도가 지나치게 높습니다. 독립 탭으로 분리하여 연산 리소스를 백그라운드로 격리하고, 화면의 공간적 활용도를 극대화해야 합니다.

### 3. 📂 [Library & Reports 탭] 데이터 수명 주기(Lifecycle) 및 보존성 불일치
*   **데이터의 영속성(Persistence) 차이**: 대화방 스레드는 휘발성 성격이 강해 사용자가 수시로 생성하고 영구 삭제(`DELETE /chat-threads/{id}`)합니다. 반면, 완성된 문헌 리포트와 즐겨찾기(Star) 논문은 수개월 이상 장기 보관해야 하는 **지식 자산**입니다.
*   **참조 효율성 극대화**: 수십 개의 대화 히스토리 폴더 속에서 과거에 다운로드했던 특정 요약 노트를 찾으려면 대화 이력을 일일이 탐색해야 하는 엄청난 피로도가 발생합니다.
*   **DB 무결성 유지**: 대화 세션이 파괴되더라도 그 안에서 저장해 둔 리포트 카드는 보관함(`W-04`)에 그대로 보존되어야 합니다. 두 데이터 간의 상이한 수명 주기를 UI와 DB 레벨에서 물리적으로 분리함으로써 데이터 무결성 설계를 단순화할 수 있습니다.

---

## 📂 1. 공통 3대 도메인 pgvector DB 및 RAG 검색 엔진 명세 (공통 분담)

본 플랫폼의 핵심인 3대 도메인 학술 데이터셋을 PostgreSQL pgvector DB에 적재, 임베딩 처리 및 유사도 검색을 수행하는 엔진입니다. 팀원 3인이 각 학술 도메인(의학/바이오, 컴퓨터 과학, 자연 과학)을 한 분야씩 전담하여 데이터 적재 및 검색 API 파이프라인을 구축할 수 있도록 독립적인 기능 단위로 정의합니다.

### 📂 1.1 상세 RAG 기능 매핑 표

| 기능 코드 | 하위 구분 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 (파라미터) | Output 스펙 (결과 데이터) | 상세 설명 |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-RAG-01** | 데이터/RAG | 의학/바이오(NFCorpus) RAG 파이프라인 구축 | **P0** | PostgreSQL pgvector / `POST /similarity-search/medical` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • NFCorpus/TREC-COVID 데이터셋의 pgvector 테이블(`medical_embeddings`) 설계 및 데이터 500자 단위 청킹 적재<br>• 입력된 의학 질문 벡터와 의학 논문 청크 간의 유사도(L2/Cosine)를 연산하여 상위 3개 검색 결과 반환 (의학 전담 개발자 분담) |
| **F-RAG-02** | 데이터/RAG | 컴퓨터 과학(SCIDOCS) RAG 파이프라인 구축 | **P0** | PostgreSQL pgvector / `POST /similarity-search/cs` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • SCIDOCS 데이터셋의 pgvector 테이블(`scidocs_embeddings`) 설계 및 데이터 500자 단위 청킹 적재<br>• 입력된 CS 질문 벡터와 CS 논문 청크 간의 유사도(L2/Cosine)를 연산하여 상위 3개 검색 결과 반환 (CS 전담 개발자 분담) |
| **F-RAG-03** | 데이터/RAG | 자연 과학(SciFact) RAG 파이프라인 구축 | **P0** | PostgreSQL pgvector / `POST /similarity-search/science` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • SciFact 데이터셋의 pgvector 테이블(`science_embeddings`) 설계 및 데이터 500자 단위 청킹 적재<br>• 입력된 자연과학 가설 벡터와 SciFact 논문 근거 청크 간의 유사도(L2/Cosine)를 연산하여 상위 3개 검색 결과 반환 (자연과학 전담 개발자 분담) |

---

## 🚦 2. UC-1 관련 기능 세분화 명세 (CS 연구조사 및 출처 검증 - W-01, W-05)

### 📂 2.1 상세 기능 매핑 표

| 기능 코드 | 하위 구분 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 (파라미터) | Output 스펙 (결과 데이터) | 상세 설명 |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-01-B-1** | 에이전트 | Step-Back 쿼리 생성기 | **P1** | Advanced Prompt | • `user_question` (str) | • `abstracted_queries`: Array of `query` (str) | • 질문의 원리를 파악하기 위해 상위 레벨의 추상화된 질문 및 대안 쿼리를 유도하는 프롬프트(Step-Back) 구현 |
| **F-01-B-2** | 에이전트 | CoT 추론 엔진 (스트리밍) | **P1** | LangChain / SSE | • `thread_id` (str)<br>• `message` (str) | • `text_token` (str)<br>• `thinking_step` (str) | • "단계별로 생각하기" 프롬프트를 에이전트 노드에 주입하고, 최종 토큰 출력 전 생성되는 CoT(생각의 사슬) 과정을 클라이언트에 SSE 스트리밍으로 실시간 송출 |
| **F-01-C-1** | DTO 정의 | 인용 출처 메타 DTO | **P0** | Pydantic 스키마 | N/A | • `CitationSource` 객체:<br>&nbsp;&nbsp;- `index` (int)<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `authors` (str)<br>&nbsp;&nbsp;- `year` (int) | • 최종 에이전트 답변 문장의 인라인 번호(`[1]`, `[2]`)에 1:1로 매핑되는 서지 정보 Pydantic 구조체 정의 |
| **F-01-C-2** | 구조화 출력 | 구조화 출력 변환 에이전트 | **P0** | `POST /agent-structured-output` | • `llm_raw_response` (str) | • `answer` (str)<br>• `sources`: Array of `CitationSource` | • Pydantic 스펙을 활용하여 LLM의 생성 답변과 사용된 문헌 인용 목록을 하나의 JSON 구조체로 강제 정제하여 내보내는 API (RAG 검색은 **F-RAG-02**의 CS 검색 엔진 연계) |
| **F-01-D-1** | 시각화 | 인용 관계망 조회 API | **P1** | `GET /papers/{id}/citations` | • `id` (str - 논문 ID) | • `nodes`: Array of Paper<br>• `links`: Array of Link | • 타겟 논문의 인용/피인용 계보(Citation & References) 목록을 노드와 링크 형태의 JSON 구조로 변환하여 W-05 화면 렌더링 지원 |
| **F-01-D-2** | 연구 보조 | 논문 상세 서지 정보 API | **P1** | `GET /papers/{id}/details` | • `id` (str) | • `title` (str)<br>• `abstract` (str)<br>• `authors` (str)<br>• `journal` (str) | • 인용 관계 그래프 클릭 시 우측 상세 패널에 출력될 개별 논문의 상세 초록 및 메타데이터 정보를 데이터베이스에서 가져오는 API |

---

## 🚦 3. UC-2 관련 기능 세분화 명세 (신약 가설검증 및 보안 리포트 - W-02, W-04, W-06, W-08)

### 📂 3.1 상세 기능 매핑 표

| 기능 코드 | 하위 구분 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 (파라미터) | Output 스펙 (결과 데이터) | 상세 설명 |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-02-B-3** | 가설 검증 | 자기 일관성 추론 에이전트 | **P0** | Self-Consistency Logic / SSE | • `hypothesis` (str)<br>• `evidence_chunks`<br>• `turns` (int) | • `verdict` (str: SUPPORT/REFUTE)<br>• `confidence_score` (float)<br>• `stream_logs`: Array of `log` | • 의학 RAG(**F-RAG-01**), 과학 RAG(**F-RAG-03**) 및 격리 업로드 문서 DB에서 관련 근거를 취합하여 가설에 대해 N회 독립 추론 및 다수결 합의(Majority Voting)하고, 각 추론 단계 및 합의 도출 과정 로그를 SSE 스트리밍으로 송출하여 실시간 중계 |
| **F-02-C-1** | 에이전트 | 단발성 대화 API | **P1** | `POST /chat-model` | • `message` (str) | • `response` (str) | • DB 세션이나 메모리 로드 없이 신속하게 LLM 응답을 확인할 수 있는 디버깅용 단발성 대화 처리 |
| **F-02-C-2** | 에이전트 | 시스템 페르소나 주입 API | **P1** | `POST /chat-with-system` | • `persona_instruction` (str)<br>• `message` (str) | • `response` (str) | • 연구 보조 에이전트의 역할(친절한 분석가, 엄격한 검토자 등)을 시스템 프롬프트에 동적 주입하여 대화에 반영하는 API |
| **F-02-D-1** | 데이터 | PDF 포맷 검증 및 파싱 모듈 | **P2** | PyPDF / pdfplumber | • `file_binary` (bytes) | • `extracted_text` (str) | • 사용자 업로드 PDF 파일의 확장자 검증(MIME-Type) 및 유효 텍스트 추출 모듈 |
| **F-02-D-2** | 사용자 PDF | PDF 격리 업로드 및 임베딩 API | **P2** | `POST /validation/upload-isolated` | • `file` (UploadFile)<br>• `session_id` (str) | • `session_file_id` (str)<br>• `chunk_count` (int) | • 보안 유출 방지를 위해 사용자가 제출한 기밀 PDF 문서를 해당 `session_id` 메모리 컨텍스트 스코프 안에서만 검색되도록 임시 임베딩 인덱스화하여 적재 |
| **F-02-E-1** | 파일 보안 | 로컬 파일 이탈 가드 및 암호화 | **P2** | OS Path Guard / AES-256 | • `file_path` (str) | N/A | • 업로드된 PDF 파일 저장 시 Sandbox 디렉토리 외곽으로의 파일 시스템 경로 이탈 방지(Directory Traversal 예방) 및 local AES-256 암호화 저장 |
| **F-02-E-2** | 파일 보안 | 세션 소거 및 Timeout 데몬 | **P2** | Background Task | N/A | N/A | • 샌드박스 세션 비활성화 30분 초과 시 백그라운드 스케줄러가 세션 PDF 파일 및 관련 pgvector 임시 테이블 공간을 영구 삭제(Shredding) 처리 |
| **F-02-F-1** | DTO 정의 | 문헌 요약 리포트 스키마 | **P2** | Pydantic 스키마 | N/A | • `ReportDTO`:<br>&nbsp;&nbsp;- `title`, `background`<br>&nbsp;&nbsp;- `findings`: Array of String<br>&nbsp;&nbsp;- `limitations`: Array of String | • 샌드박스 세션의 가설 검증 결과 및 RAG 문맥을 기반으로 연구 보고서를 생성하기 위한 Pydantic 데이터 구조 정의 |
| **F-02-F-2** | 리포트 생성 | 리포트 다운로드/내보내기 API | **P2** | `GET /reports/{id}/export` | • `report_id` (str)<br>• `format` (str: pdf/md) | • FileResponse (Binary Stream) | • Pydantic 요약 보고서 데이터를 Markdown 혹은 PDF 형식의 스트림으로 렌더링하여 클라이언트 다운로드 지원 |
| **F-02-G-1** | 문헌 보관함 | 보관함 영구 등록 API | **P2** | `POST /library/archive` | • `report_id` (str)<br>• `report_data` (JSON) | • `archive_id` (str) | • 생성 완료된 DTO 보고서를 PostgreSQL 메인 테이블에 영구 아카이브 등록 |
| **F-02-G-2** | 문헌 보관함 | 보관함 카드 조회 및 Star 관리 API | **P2** | `GET /library/archive` | 없음 | • `archived_reports`: Array of Card<br>• `starred_papers`: Array of Paper | • 유저 문헌 보관함(W-04) 진입 시 저장된 과거 리포트 카드 리스트 및 유저가 즐겨찾기(Star) 표시한 논문 리스트 로드 API |
| **F-02-H-1** | 세션 관리 | 샌드박스 세션 상세 조회 API | **P1** | `GET /sandbox/sessions/{id}` | • `id` (str - 세션 ID) | • `session_data`: JSON Object | • 특정 샌드박스 세션의 설정 가설, 업로드 파일 목록, 검증 완료된 스코어카드 및 단계별 검증 로그 복원 |
| **F-02-H-2** | 세션 관리 | 샌드박스 세션 영구 완전 소거 API | **P1** | `DELETE /sandbox/sessions/{id}` | • `id` (str - 세션 ID) | • `status` (str: "purged") | • 사용자의 명시적 Wipe Out 요청 시 해당 샌드박스 세션의 설정 가설, 업로드된 기밀 문서 파일, 관련 임시 임베딩 인덱스를 물리적으로 영구 완전 소거 |


---

## 🚦 4. UC-3 관련 기능 세분화 명세 (다중 에이전트 피어 리뷰 워크숍 - W-07, W-09)

### 4.1 상세 기능 매핑 표

| 기능 코드 | 하위 구분 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 (파라미터) | Output 스펙 (결과 데이터) | 상세 설명 |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-03-A-1** | 에이전트 | 방법론 검증 에이전트 노드 | **P1** | LangGraph Node | `state`: ReviewState | `state`: Updated Methodology | • 논문의 연구 설계, 대조군 설정, 데이터 타당성을 검증하여 평점 및 피드백을 Shared State에 누적 |
| **F-03-A-2** | 에이전트 | 신규성 분석 에이전트 노드 | **P1** | LangGraph Node | `state`: ReviewState | `state`: Updated Novelty | • 타겟 저널 수준 대비 기존 연구들과의 차별점 및 신규성 요소를 판별하여 Shared State에 누적 |
| **F-03-A-3** | 에이전트 | 학술 스타일/영어 교정 노드 | **P1** | LangGraph Node | `state`: ReviewState | `state`: Updated Style | • 아카데믹 영작 문체 및 저널 포맷(Style) 규격을 평가하고, 구절별 원문-수정 대비표 데이터 생성 |
| **F-03-A-4** | 피어 리뷰 | 피어 리뷰 워크숍 실행 API | **P1** | `POST /academic-peer-review` / SSE | • `draft_text` (str)<br>• `target_journal` (str)<br>• `focus_weights` (JSON) | • `overall_score` (int)<br>• `review_report` (str)<br>• `scorecard` (JSON)<br>• `diff_table`: Array of Diff<br>• `debate_stream`: SSE Stream | • 3대 에이전트가 W-09 토론 아레나 상에서 실시간으로 대화를 주고받는 에이전트 토론(Debate) 로그 및 LangGraph 노드 활성 상태를 SSE 스트리밍으로 중계하고 최종 종합 DTO 반환 |
| **F-03-B-1** | 시각화 | LangGraph 노드 상태 로거 | **P1** | LangGraph State Tracer | `state`: ReviewState | N/A | • 에이전트 실행 과정 중 현재 어느 에이전트 노드가 활성화되어 동작 중인지에 대한 노드 수명 주기 정보를 기록 및 반환 대기 처리 |
| **F-03-B-2** | 시각화 | 에이전트 관계 그래프 API | **P1** | `GET /graph-structure` | 없음 | • `graph_nodes`: Array of Node<br>• `graph_edges`: Array of Edge | • LangGraph 오케스트레이션의 에이전트 노드 상태 구조도를 W-07 및 W-09 화면의 프론트엔드 시각화 맵에 연동하기 위한 데이터 반환 |

---

## 🚦 5. UC-4 관련 기능 세분화 명세 (시스템 개발자 독립 검증 - W-03)

### 5.1 상세 기능 매핑 표

| 기능 코드 | 하위 구분 | 상세 기능명 | 우선순위 | 엔드포인트 / 기술 | Input 스펙 (파라미터) | Output 스펙 (결과 데이터) | 상세 설명 |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **V-01-A** | 체크리스트 | 단순 정보 구조화 추출 API | **P2** | `POST /validation/structure` | • `raw_text` (str)<br>• `schema_type` (str) | • `structured_json` (JSON) | • 영화 시놉시스, 피자 주문 토글, 고객 정보 등 비학술 도메인의 비정형 텍스트를 전달받아 Pydantic Validator로 지정된 JSON 형태로 구조화 출력 테스트 |
| **V-02-A** | 도구 연동 | 알람 설정 mock 도구 연동 | **P2** | LangChain Tool Calling | • `alarm_time` (str)<br>• `label` (str) | • `status` (str: "success")<br>• `message` (str) | • 시간 설정을 시뮬레이션하고 에이전트를 거치지 않고 직접 결과를 호출부에 출력하는 mock 알람 트리거 |
| **V-02-B** | 도구 연동 | 차량 번호판 direct 반환 검증 | **P2** | Image Tool Calling | • `image_base64` (str) | • `plate_number` (str)<br>• `return_direct` (bool = True) | • LLM 요약 미들웨어를 거치지 않고 이미지 내 차량 번호판 문자 영역을 파싱하여 다이렉트로 원문 출력 처리 |

---

## 📂 6. 백그라운드 데이터 적재 및 청킹 유틸리티 명세 (개발용 유틸)

> [!NOTE]
> 본 기능들은 최종 유저가 프론트엔드에서 호출하는 API가 아니며, 시스템 구동 전 데이터베이스 환경 구축 및 대용량 텍스트 전처리를 위해 팀원들이 전용으로 가동할 유틸리티 기능들입니다.

### 6.1 데이터 수집 및 동기화 유틸리티
*   **`U-01-A` (의학 MTEB 적재 유틸)**:
    *   *내용*: NFCorpus 및 TREC-COVID 원본 XML/TSV 데이터셋을 로드하고 파싱하여, PostgreSQL 데이터베이스의 테이블에 메타데이터와 함께 동기화하는 배치 스크립트. (`P2`)
*   **`U-01-B` (컴퓨터 과학 MTEB 적재 유틸)**:
    *   *내용*: SCIDOCS 데이터셋의 JSON 인덱스 문서를 파싱하고, 카테고리 필터와 초록 정보를 추출하여 DB에 대량 로드하는 벌크 적재 유틸리티. (`P2`)
*   **`U-01-C` (자연 과학 MTEB 적재 유틸)**:
    *   *내용*: SciFact 데이터셋의 학술 가설 텍스트와 초록 관계 매핑 JSON 스크립트를 로드하여 데이터베이스의 가설 테이블로 저장하는 배치 툴. (`P2`)

### 6.2 텍스트 추출 및 청킹 (Chunking) 유틸리티
*   **`U-02-A` (의학/바이오 텍스트 청킹 유틸)**:
    *   *내용*: 로드한 의학 텍스트를 문장 경계 보존(Sentence-boundary preservation)이 가미된 500자 단위 청크(Chunk Size)와 50자 오버랩(Overlap) 규격으로 분할하여 적재 테이블에 벌크 전송. (`P2`)
*   **`U-02-B` (컴퓨터 과학 텍스트 청킹 유틸)**:
    *   *내용*: CS 학술 문서의 섹션(도입부, 방법론, 실험 등) 단위 메타데이터가 보존될 수 있도록 단어 경계 청킹 엔진을 적용하여 500자 단위로 정밀 청킹 처리. (`P2`)
*   **`U-02-C` (자연 과학 텍스트 청킹 유틸)**:
    *   *내용*: SciFact 텍스트의 참/거짓 증명 근거가 분할되면서 논리 관계가 끊어지는 현상을 막기 위해 500자 단위 청크와 최대 100자의 유연한 중첩 오버랩 구간을 적용해 전처리. (`P2`)

---

## 📂 7. 에이전트 공통 메모리 및 시스템 인프라 사양

모든 도메인 에이전트 및 대화형 API가 공유하여 사용하는 인프라 백엔드 사양입니다.

*   **실시간 스트리밍 아키텍처 (Real-time Streaming)**:
    *   에이전트 실행 시 생성되는 중간 노드 상태 정보(예: `['의학 RAG 검색 중', 'Tavily 실시간 탐색 중']`) 및 최종 답변의 토큰을 `StreamingResponse`를 통해 글자 단위(Token-by-Token)로 클라이언트에 실시간 송신합니다.
*   **PostgreSQL 기반 히스토리 영구 보존 (`PostgresSaver`)**:
    *   세션은 1단계 로컬 RAM 메모리(`InMemorySaver`)에서 테스트 가능하며, 최종 사양은 PostgreSQL 데이터베이스를 연동하여 `PostgresSaver`를 비동기식으로 구현합니다. Thread ID 식별자를 기준으로 영구 보존됩니다.
*   **컨텍스트 최적화 요약 미들웨어 (`SummarizationMiddleware`)**:
    *   LLM 컨텍스트 한계(Token Limit)를 방지하기 위해, 대화 히스토리의 토큰 크기가 임계치를 초과할 시 오래된 대화 턴(Turn)을 핵심 요약본으로 자동 압축 보존하되 최근 대화는 무손실 유지합니다.

---

## ⚙️ 8. 개발 및 공통 코드 컨벤션 (Development & Coding Conventions)

백엔드 아키텍처의 일관된 코드 품질을 유지하고, 3인의 개발자가 모듈 단위로 독립적이면서도 조화롭게 개발을 연동할 수 있도록 공통 개발 규칙을 별도 문서로 분리하였습니다.

*   **상세 가이드라인**: [백엔드 개발 및 공통 코드 컨벤션 (code-conventions.md)](file:///c:/Repo/bist-mini-2-backend/docs/code-conventions.md)
*   **주요 포함 사양**:
    *   API 응답 및 전역 예외 처리 규격 (HTTP 캐시 방지 및 상태 코드 매핑)
    *   FastAPI Annotated DI & 의존성 캐시 활용 2단계 보안 검증 패턴
    *   Pydantic DTO 전역 설정 및 SQLAlchemy AsyncSession 연동 규칙 (`MissingGreenlet` 해결)
    *   비동기 트랜잭션 수명 주기 (`Flush` vs `Commit`)
    *   제너레이터 `send()` 호출 제한 및 스트리밍 타입 가드
    *   임포트 캐싱 기반 파이썬 모듈 레벨 싱글톤(Singleton) 설계
    *   Google 스타일 Docstring 및 Sphinx 자동화 가이드
