# 📋 논문 AI 에이전트 플랫폼 상세 기능 명세서 (Functional Specification - 3rd Milestone)

본 문서는 **'논문 AI 에이전트 플랫폼 (Paper Agent Platform)'**의 최종 3차 구현 마일스톤에 맞추어 실제 연동 및 구축 완료된 상태를 명세하는 상세 기능 명세서입니다. 
본 시스템은 대화형 서비스인 `일반 챗 허브 (General Chat Hub)`를 기본으로 하고, 심층 추론이 필요한 3가지 핵심 기능(대규모 문헌 비교 분석기, 보안 샌드박스 피어 리뷰, 맞춤형 연구 비서 팩토리)을 더해 총 4가지의 기능군을 제공합니다.

---

## 🏛️ 아키텍처적 당위성: 개별 탭으로 화면을 물리적 분리해야 하는 이유

1. **일반 챗 허브 (General Chat Hub)**: 빠른 속도의 RAG 파이프라인을 통해 사용자의 일반적인 대화 및 가벼운 탐색에 대해 즉각적인 응답(스트리밍/완료형 선택)을 지원합니다.
2. **대규모 문헌 스펙 비교 및 공백(Research Gap) 분석기**: 수십 편의 논문 데이터를 비동기 배치로 읽어 '해결된 문제'와 '한계점'을 일괄 분석합니다. 오랜 연산 시간이 소요되므로 일반 챗 허브 창을 블로킹하지 않도록 백그라운드로 처리하고 전용 매트릭스/타임라인 대시보드 UI로 시각화합니다.
3. **보안 샌드박스 피어 리뷰 및 가설 디펜스 아레나**: 기밀 정보의 유출을 차단하는 격리 환경을 유지하고, 다중 에이전트(방법론/신규성/문체) 토론 및 실시간 모의 디펜스(채팅 및 실시간 채점)를 독립된 공간에서 진행합니다.
4. **맞춤형 연구 비서 (Research Gem) 팩토리**: 사용자가 특정 데이터 소스(RAG DB)와 페르소나(System Prompt)를 조합해 만든 맞춤형 에이전트들을 카드 형태로 스토어에 보관하고 호출할 수 있는 독립 제어판입니다.

---

## 📂 1. 공통 3대 도메인 pgvector DB 및 RAG 검색 엔진 명세 (구축 완료)

| 기능 코드 | 하위 구분 | 상세 기능명 | 상태 | 엔드포인트 / 기술 | Input 스펙 (파라미터) | Output 스펙 (결과 데이터) | 상세 설명 |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-RAG-01** | 데이터/RAG | 생명공학(Biotechnology) RAG 파이프라인 | **완료** | PostgreSQL pgvector / `POST /similarity-search/bio` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • ArXiv `q-bio.GN` 및 `q-bio.BM/MN/TO/CB/SC/OT` 카테고리 논문 데이터 **총 54,066건**의 초록을 단일 임베딩 벡터로 적재하여 유사도 검색 및 결과 반환 |
| **F-RAG-02** | 데이터/RAG | 컴퓨터 과학(Computer Science) RAG 파이프라인 | **완료** | PostgreSQL pgvector / `POST /similarity-search/cs` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • ArXiv 컴퓨터 과학 `cs.NE` (Neural and Evolutionary Computing) 카테고리 논문 **총 17,825건**의 초록을 단일 임베딩 벡터로 적재하여 유사도 검색 및 결과 반환 |
| **F-RAG-03** | 데이터/RAG | 천문학(Astronomy) RAG 파이프라인 | **완료** | PostgreSQL pgvector / `POST /similarity-search/astronomy` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • ArXiv 지구 및 행성 천체물리 `astro-ph.EP` 카테고리 논문 **총 35,083건**의 초록을 단일 임베딩 벡터로 적재하여 유사도 검색 및 결과 반환 |

---

## 🚦 2. MVP 1단계 (Phase 1) 상세 기능 명세 (구축 완료)

### 2.1 일반 챗 허브 (General Chat Hub)
일반 챗 허브는 가벼운 질문에 대한 RAG 검색 및 출처 매핑과 실시간 토큰 스트리밍을 제공하는 기본 소통 창구입니다.

| 기능 코드 | 상세 기능명 | 상태 | 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-01-A-1** | Step-Back 쿼리 생성기 | **완료** | Advanced Prompt | • `user_question` (str) | • `abstracted_queries`: Array of `query` (str) | • 질문을 추상화하여 RAG 검색 적합도를 넓히는 대안 쿼리 생성 모듈 |
| **F-01-A-2** | CoT 추론 엔진 (스트리밍) | **완료** | LangChain / SSE | • `session_id` (str)<br>• `message` (str) | • `text_token` (str) | • "단계별로 생각하기" 과정 및 실시간 답변을 SSE 스트리밍으로 송출하여 생각의 흐름 시각화 (스트리밍 전용 `/chat/sessions/{session_id}/messages/stream` 활용) |
| **F-01-A-3** | 인용 출처 메타 DTO 정의 | **완료** | Pydantic 스키마 | N/A | • `CitationSource` 객체:<br>&nbsp;&nbsp;- `arxiv_id` (str)<br>&nbsp;&nbsp;- `title` (str) | • 답변 본문의 인라인 번호(`[1]`, `[2]`)에 1:1로 매핑되는 서지 구조체 정의 |
| **F-01-A-4** | 구조화 출력 변환 및 답변 호출 | **완료** | `POST /chat/sessions/{session_id}/messages` | • `message` (str) | • `answer` (str)<br>• `sources`: Array of `CitationSource` | • Pydantic을 활용해 답변 텍스트와 참조 문헌 목록을 하나의 JSON 구조체로 출력 및 DB(`chat_source`) 저장 보장 |
| **F-01-A-5** | 인용 관계망 조회 | **완료** | `GET /papers/{id}/citations` | • `id` (str) | • `nodes`: Array, `links`: Array | • 타겟 논문의 인용/피인용 계보를 노드-링크 데이터 구조로 반환 (D3.js 시각화용) |

---

### 2.2 대규모 문헌 스펙 비교 및 공백(Research Gap) 분석기
수십 편의 선행 연구 데이터를 비동기로 메타 분석하여 연도별 스펙 매트릭스 및 연구 공백 제안 대시보드를 구축합니다.

| 기능 코드 | 상세 기능명 | 상태 | 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-01-B-1** | 비동기 분석 작업 요청 API | **완료** | `POST /research-gap/analyze` | • `domain` (str)<br>• `query` (str) | • `task_id` (str) | • 대량 분석 요청 시 즉시 `task_id`를 반환하고 백엔드 비동기 백그라운드 큐에 연산 적재 |
| **F-01-B-2** | 비동기 분석 작업 상태 조회 | **완료** | `GET /research-gap/tasks/{task_id}` | • `task_id` (str) | • `status` (str: RUNNING/COMPLETED)<br>• `progress` (int: 0~100) | • 분석 작업 상태 및 진행률을 폴링/조회하는 API (완료 시 알림 SSE 연동 지원) |
| **F-01-B-3** | 비동기 분석 최종 결과 조회 | **완료** | `GET /research-gap/tasks/{task_id}/result` | • `task_id` (str) | • `matrix_data`: JSON Object<br>• `gap_analysis`: TEXT | • 완료된 작업의 최종 비교 매트릭스 표 및 합성 리포트 획득 |
| **F-01-B-4** | 연구 공백 결과 한글 번역 | **완료** | `POST /research-gap/tasks/{task_id}/translate` | • `task_id` (str) | • `translated`: JSON Object | • 영문으로 완료된 비교 분석 결과를 한글로 번역하여 서버 DB에 영구 보존 |

---

### 2.3 보안 피어 리뷰 및 디펜스 아레나
기밀 유지 샌드박스 환경에서 PDF 분석 및 가설 검증을 거친 후, 3대 에이전트 토론을 통한 피어 리뷰 및 모의 디펜스를 원스톱으로 수행합니다.

| 기능 코드 | 상세 기능명 | 상태 | 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-02-A-1** | PDF 격리 업로드 및 임베딩 | **완료** | `POST /defense-arena/upload-isolated` | • `file` (UploadFile) | • `session_id` (str)<br>• `file_name` (str)<br>• `chunk_count` (int) | • 보안 샌드박스 세션 스코프 내에서만 조회되는 임시 임베딩 인덱스 적재 |
| **F-02-A-2** | 샌드박스 세션 자동 소거 데몬 | **완료** | OS Path Guard / Shredding | N/A | N/A | • 30분 미활동 시 세션 PDF 파일 및 pgvector 임시 테이블 공간을 영구 완전 소거 (Wipe Out) |
| **F-02-A-3** | 다중 에이전트 피어 리뷰 실행 | **완료** | `POST /defense-arena/peer-review` | • `session_id` (str)<br>• `target_journal` (str) | • `overall_score` (int)<br>• `review_report` (str) | • LangGraph 기반 3대 에이전트(방법론, 신규성, 학술문체)가 토론(Debate)을 거쳐 최종 종합 피드백 DTO 도출 |
| **F-02-A-4** | 자기 일관성(Self-Consistency) 가설 검증 | **완료** | `POST /defense-arena/verify-hypothesis` | • `session_id` (str)<br>• `hypothesis` (str) | • `verdict` (SUPPORT/REFUTE)<br>• `rationale` (str) | • 임시 업로드 문서 및 RAG DB에서 관련 근거를 취합해 N회 독립 추론 후 다수결 합의 도출 |
| **F-02-A-5** | 심사위원 에이전트 디펜스 아레나 | **완료** | `POST /defense-arena/defense/chat` | • `session_id` (str)<br>• `user_response` (str, optional) | • `refutation_question` (str)<br>• `score` (int), `feedback` (str)<br>• `is_finished` (bool) | • 피어 리뷰 보고서 기반으로 가상의 심사위원이 압박 질문을 던지고, 사용자의 방어 논리를 실시간 채점하는 시뮬레이터 |

---

### 2.4 맞춤형 연구 비서 (Research Gem) 팩토리 & 스토어
특정 지식 DB와 고유의 페르소나를 장착한 특화 에이전트(Gem)를 직접 조립 및 보관하고 사용합니다.

| 기능 코드 | 상세 기능명 | 상태 | 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 상세 설명 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-03-A-1** | 젬(Gem) 생성 API | **완료** | `POST /gems` | • `name` (str)<br>• `db_sources` (List of str)<br>• `system_prompt` (str) | • `gem_id` (str)<br>• `name` (str)<br>• `db_sources` (List) | • 지정된 이름, RAG 소스 참조 필터(생명공학/CS/천문학 DB 중 다중 선택), 시스템 프롬프트를 바인딩해 데이터베이스 `gem` 테이블에 영구 저장 |
| **F-03-A-2** | 젬(Gem) 목록 조회 API | **완료** | `GET /gems` | 없음 | • `gems`: Array of Gem Card | • 생성 및 스토어에 보관된 사용자 정의 젬 카드 리스트 호출 |
| **F-03-A-3** | 젬(Gem) 1:1 특화 대화 API | **완료** | `POST /gems/{gem_id}/chat` | • `thread_id` (str)<br>• `message` (str) | • `answer` (str)<br>• `sources`: Array | • 생성된 특정 젬의 페르소나와 지정된 RAG 필터를 타겟팅하여 격리된 1:1 대화를 진행 |

---

## 📂 3. 에이전트 공통 메모리 및 시스템 인프라 사양 (구축 완료)

*   **실시간 스트리밍 아키텍처 (Real-time Streaming)**:
    - 에이전트 연산의 각 단계(CoT 생각의 흐름, LangGraph 토론 단계 로그 등) 및 최종 답변을 `StreamingResponse`를 통해 클라이언트에 점진적으로 송신합니다.
*   **PostgreSQL 기반 히스토리 영구 보존 (`PostgresSaver`)**:
    - 대화 이력 및 LangGraph 상태 저장소는 비동기식 `PostgresSaver`를 구축하여 Thread ID별로 안정적으로 영구 보존합니다.
*   **컨텍스트 최적화 요약 미들웨어 (`SummarizationMiddleware`)**:
    - 대화의 길이가 임계치를 초과할 시, 오래된 대화 턴을 핵심 요약본으로 압축 보존하여 LLM 컨텍스트 한계를 방어합니다.
