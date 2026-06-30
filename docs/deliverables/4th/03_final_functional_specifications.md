# [4차 산출물] 03. 최종 기능 상세 명세서 (Final Functional Specifications)

본 문서는 `bist-mini-2` platforms의 마일스톤에 맞추어 실제 설계 및 최종 가동 완료된 기능군과 향후 추가 개발을 위해 규정된 로드맵을 정의한 **최종 기능 상세 명세서**입니다. 본 시스템은 3대 코어 도메인 pgvector DB를 RAG 레이어로 결합하고, 완료된 3대 주요 화면과 향후 추가될 1대 보안 화면을 포함한 화면 분리 아키텍처를 정의하고 있습니다.

---

## 🏛️ 화면별 기능 배치 및 화면 분리 설계

1. **일반 챗 허브 (General Chat Hub)**: 빠른 속도의 RAG 파이프라인과 실시간 웹 크롤링을 결합하여 사용자의 일반적인 대화 및 가벼운 탐색에 대해 즉각적인 응답(스트리밍)을 지원합니다.
2. **대규모 문헌 스펙 비교 및 공백(Research Gap) 분석기**: 수십 편의 논문 데이터를 비동기 배치로 읽어 '해결된 문제'와 '한계점'을 일괄 분석합니다. 오랜 연산 시간이 소요되므로 일반 챗 허브 창을 블로킹하지 않도록 백그라운드로 처리하고 전용 매트릭스 대시보드 UI로 시각화합니다.
3. **맞춤형 연구 비서 (Research Gem) 팩토리**: 사용자가 특정 데이터 소스(RAG DB)와 페르소나(System Prompt)를 조합해 만든 맞춤형 에이전트들을 카드 형태로 스토어에 보관하고 호출할 수 있는 독립 제어판입니다.
4. **보안 피어 리뷰 및 가설 디펜스 아레나 (보안 샌드박스) - [향후 개발 로드맵]**: 기밀 연구 초안의 유출을 차단하는 격리 환경을 유지하고, 다중 에이전트 토론 및 실시간 모의 디펜스를 진행하는 독립 보안 전용 탭입니다.

---

## 📂 1. 공통 3대 도메인 pgvector 데이터베이스 및 RAG 검색 엔진

모든 기능군은 백엔드 공통 RAG 검색 레이어([rag_pipeline.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/rag_pipeline.py))를 공유하며, HNSW(Hierarchical Navigable Small World) 인덱스를 탑재하여 코사인 유사도 $0.35$ 이상의 신뢰성 높은 청크를 고속 추출합니다.

| 기능 코드 | 도메인 구분 | 대상 데이터셋 및 규모 | 엔드포인트 / 검색 도구 | Input 파라미터 | Output 데이터 구조 | 구현 상세 설명 |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **F-RAG-01** | **생명공학<br>(Bio)** | • ArXiv `q-bio.GN` (Genomics) 및 주요 분과 학술 자료<br>• **총 54,066건** (초록 기준) | `POST /similarity-search/bio`<br>도구: `search_bio_papers` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str: ArXiv ID)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • 생명과학 연구자의 유전자 편집, 단백질 구조 분석용 pgvector 검색 지원. 3072차원 임베딩 벡터 매칭. |
| **F-RAG-02** | **컴퓨터 과학<br>(CS)** | • ArXiv `cs.NE` (Evolutionary Computing) 및 기계학습 분야<br>• **총 17,825건** (초록 기준) | `POST /similarity-search/cs`<br>도구: `search_cs_papers` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id`<br>&nbsp;&nbsp;- `title`<br>&nbsp;&nbsp;- `text_chunk`<br>&nbsp;&nbsp;- `score` | • 신경망 튜닝, 인공신경망 진화 등 딥러닝 핵심 개념 탐색용 고속 매칭 최적화. |
| **F-RAG-03** | **천문학<br>(Astronomy)** | • ArXiv `astro-ph.EP` (Earth & Planetary Astrophysics)<br>• **총 35,083건** (초록 기준) | `POST /similarity-search/astronomy`<br>도구: `search_astronomy_papers` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id`<br>&nbsp;&nbsp;- `title`<br>&nbsp;&nbsp;- `text_chunk`<br>&nbsp;&nbsp;- `score` | • 외계행성, 궤도역학, 우주 기원 이론 검증용. 3072차원 대형 천체물리 임베딩 공간 확보. |

### 1.1 공통 RAG 검색 레이어 세부 기능 명세

#### 🧬 [F-RAG-01] 생명공학 (Bio) RAG 검색 엔진 요구 명세
1. **F-RAG-01-01. q-bio.GN 기반 유전체학 논문 컨텍스트 쿼리 연산**: 사용자가 입력한 자연어 질문(한글/영어)을 수신하여 5.4만 건의 유전체학 및 Genomics 관련 논문 초록 데이터베이스 상에서 코사인 유사도 벡터 검색을 지원해야 한다.
2. **F-RAG-01-02. 바이오 도메인 전용 코사인 유사도 임계치 필터링**: 생명과학 연구의 엄밀성 확보와 허위 지식 유입 방지를 위해, RAG 검색 결과 중 코사인 유사도 0.35 미만의 매칭 청크는 최종 답변 합성 컨텍스트에서 강제 배제(Drop)해야 한다.
3. **F-RAG-01-03. 다중 유전공학 서브 카테고리 필터링 지원**: 사용자가 특정 세부 분과 학술 영역을 타겟팅할 수 있도록, `q-bio.GN` 외에 `q-bio.BM` (Biomolecules), `q-bio.CB` (Cell Behavior) 등 cmetadata JSONB 내 카테고리를 활용한 복합 조건절 조회를 지원해야 한다.

#### 💻 [F-RAG-02] 컴퓨터 과학 (CS) RAG 검색 엔진 요구 명세
1. **F-RAG-02-01. cs.NE 기반 진화 컴퓨팅 및 신경망 논문 매칭**: 진화 알고리즘, 심층 인공신경망 아키텍처 이론 등 1.7만 건의 컴퓨터 과학 논문 초록을 대상으로 형태소 및 의미적 키워드를 매칭하여 관련 기술 레코드를 탐색해 내야 한다.
2. **F-RAG-02-02. 딥러닝 고유 기술 명사(Named Entity) 가중치 매칭**: `Transformer`, `Adam Optimizer`, `Backpropagation` 등 인공지능 분야의 핵심 전용 기명 용어(Named Entity)들을 임베딩 공간 상에서 손실 없이 식별하여 정확한 유사 조각을 추출해야 한다.
3. **F-RAG-02-03. 다중 카테고리 교차 참조(Cross-Matching) 검색**: 하나의 논문이 컴퓨터 과학(`cs.NE`) 외에 기계학습(`cs.LG`), 인공지능(`cs.AI`) 등 복수 도메인에 걸쳐 등록된 경우, 두 영역의 융합 쿼리에 대해 관계형 교차 매칭을 통해 중복 없이 관련 정보를 수집해야 한다.

#### 🔭 [F-RAG-03] 천문학 (Astronomy) RAG 검색 엔진 요구 명세
1. **F-RAG-03-01. astro-ph.EP 기반 외계행성 및 행성계 물리학 문헌 검색**: 3.5만 건의 지구/행성 천체물리 논문에서 궤도 역학, 분광 분석, 대기 관측 모델 등 천문학 연구자용 고가치 전문 지식을 탐색해 내야 한다.
2. **F-RAG-03-02. 천체 고유 명칭 및 관측 장비 모델 식별**: `JWST` (제임스 웹 우주망원경), `TESS`, `Kepler-186f` 등 천문 관측 도구 및 성운/행성 고유 번호 기호를 임베딩 공간에서 혼동 없이 일치시켜 검색해야 한다.
3. **F-RAG-03-03. HNSW 기반 대용량 임베딩 공간 탐색 속도 보장**: 천문학 도메인의 RAG 검색 성능(Latency) 유지를 위해, PostgreSQL의 pgvector 테이블 상에 구현된 HNSW 인덱스를 타격하여 쿼리 당 평균 50 ms 미만의 데이터베이스 조회를 보장해야 한다.

---

## 🚦 2. 4대 주요 화면별 상세 기능 스펙 (구현 완료 및 미구현 로드맵 대조)

### 2.1 일반 챗 허브 (General Chat Hub)
일반 챗 허브는 가벼운 질문에 대해 논문 RAG와 웹 실시간 검색을 무조건적으로 병렬 가동하여, 융합 지식을 단일 마크다운 답변으로 완성하고 실시간 토큰 스트리밍을 공급하는 기본 통제판입니다.

* **DB 매핑 테이블**: `chat_session`, `chat_sources`, `chat_suggestions`
* **체크포인터**: `AsyncPostgresSaver` 활용 (Thread ID 단위 보존)

| 기능 코드 | 상세 기능명 | 상태 | 백엔드 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 기능 상세 및 DB 연동 명세 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-01-01** | 쿼리 최적화 분석기 | **완료** | gpt-4o-mini / `AnalysisNode` | • `user_question` (str) | • `paper_query` (str)<br>• `web_query` (str) | • 자연어 발화에서 영어 학술 최적 키워드와 웹 타겟 서치 쿼리를 분리 인출. |
| **F-01-02** | 듀얼 트랙 병렬 가동 | **완료** | `asyncio.gather` 비동기 태스크 | • `paper_query` (str)<br>• `web_query` (str) | • `paper_res` (dict)<br>• `web_res` (dict) | • `paper_node`와 `web_node`를 조건부 분기 없이 무조건 동시 가동하여 입체적 지식풀 확보. |
| **F-01-03** | 융합 답변 합성 엔진 | **완료** | OpenAI gpt-4o / `SynthesisNode` | • `paper_context` (str)<br>• `web_context` (str) | • `final_response` (str: MD) | • 학술 팩트(논문)와 상용화 동향(웹)을 한 문맥 내에 크로스-참조 결합하여 리포트형 답변 렌더링. |
| **F-01-04** | 토큰 단위 스트리밍 | **완료** | FastAPI `StreamingResponse` | • `session_id` (str)<br>• `message` (str) | • `SSE Token Stream`<br>(JSON lines) | • `synthesis` 노드의 텍스트 토큰을 실시간으로 프론트엔드로 푸시. |
| **F-01-05** | 다중 출처 사후 적재 | **완료** | PostgreSQL DAO 연동 | • `session_id` (str)<br>• `message_index` (int) | N/A (성공 코드) | • 대화 완료 후 RAG에 사용된 ArXiv 논문 서지 정보를 `chat_sources` 테이블에 index 결합 저장. |
| **F-01-06** | 후속 질문 추천 생성 | **완료** | `generate_suggestions` 모듈 | • `question` (str)<br>• `answer` (str) | • `suggestions`: List of `question` | • 방금 오고 간 Q&A를 바탕으로 꼬리 질문 3선을 자동 추출하여 `chat_suggestions` 테이블에 기록. |
| **F-01-07** | 세션 복원 및 단일화 | **완료** | `GET /chat/sessions/{session_id}/messages` | • `session_id` (str) | • `messages`: Array of Message DTO (with sources/suggestions) | • DB 세션 and `PostgresSaver`를 조회해 텍스트 이력에 출처 카드와 추천 질문을 병합 주입하여 복원 반환. |

---

### 2.2 대규모 문헌 스펙 비교 및 공백(Research Gap) 분석기
수십 편의 선행 연구 데이터를 비동기로 메타 분석하여 연도별 스펙 매트릭스 및 연구 공백 제안 대시보드를 구축합니다.

* **DB 매핑 테이블**: `research_gap_task`, `notification`
* **비동기 큐**: FastAPI `BackgroundTasks` 활용

| 기능 코드 | 상세 기능명 | 상태 | 백엔드 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 기능 상세 및 DB 연동 명세 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-02-01** | 비동기 분석 접수 API | **완료** | `POST /research-gap/analyze` | • `domain` (str)<br>• `query` (str) | • `task_id` (str: UUID) | • 대규모 배치 의뢰 즉시 `task_id`를 반환하고, 분석 상태를 `PENDING`으로 최초 적재. |
| **F-02-02** | 중복 논문 선출 가공 | **완료** | `run_batch_analysis` 배치 루프 | • `task_id` (str) | • `papers_list` (List of 4) | • k=25 RAG 검색 결과에서 중복 문헌을 제거하고 가장 유사도 높은 4개 고유 본문 병합 선출. (진행률 40%) |
| **F-02-03** | 개별 문헌 팩트 해체 | **완료** | `gpt-4o-mini` 구조화 출력 | • `content` (str: Abstract) | • `PaperAnalysisResult` DTO | • Problems Solved와 Limitations를 각 2개씩 요약하고 근거 영문 문장을 `source_quote`에 영구 보존. |
| **F-02-04** | 연구 공백 합성 리포트 | **완료** | `gpt-4o-mini` 종합 추론 | • `matrix_data` (str) | • `ResearchGapMatrix` DTO | • 4개 논문 limitations의 공통 교집합(Common Limitations)을 추론하고 혁신 미래 과제 3선 제안. (진행률 100%) |
| **F-02-05** | SSE 완료 알림 푸시 | **완료** | `notification_broadcaster` | • `task_id` (str) | • `event: task_completed`<br>(SSE push payload) | • 완료 즉시 `notification` 테이블 적재 및 SSE Broadcaster를 통한 브라우저 팝업 알림 실시간 발송. |
| **F-02-06** | 아카데믹 다국어 번역 | **완료** | `POST /research-gap/tasks/{task_id}/translate` | • `task_id` (str) | • `translated`: JSON Object | • 영문 분석 결과를 한국어로 변역하여 `translated_result`에 저장(캐싱). 단, `source_quote`는 원어로 복원. |

---

### 2.3 보안 피어 리뷰 및 디펜스 아레나 (보안 샌드박스) - [향후 개발 로드맵 / 미구현]
기밀 유지가 필수적인 사용자 논문 초안(Draft)을 보안 격리 환경(샌드박스)에 올려 가설을 검증하고, AI 심사위원단과의 실시간 꼬리 질문 모의 디펜스를 진행하는 설계 규격입니다.

* **DB 매핑 테이블**: `defense_arena_session`, `defense_arena_chunk`, `defense_history` (향후 구축 예정)

| 기능 코드 | 상세 기능명 | 상태 | 백엔드 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 기능 상세 및 DB 연동 명세 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-03-01** | PDF 격리 업로드 | **미구현** | `POST /defense-arena/upload-isolated` | • `file` (UploadFile) | • `session_id` (str)<br>• `file_name` (str) | • 격리 디렉토리에 저장 후 해당 세션 전용 임시 pgvector 인덱스 동적 생성 설계. |
| **F-03-02** | 30분 수명 주기 소거 | **미구현** | 백그라운드 Shredding 데몬 | N/A | N/A (자동 소멸) | • 30분 무활동 감지 시 PDF 물리 삭제 및 pgvector 임시 컬렉션 공간 영구 파쇄 설계. |
| **F-03-03** | 다중 에이전트 토론 | **미구현** | LangGraph 협업 에이전트 | • `session_id` (str) | • `overall_score` (int)<br>• `review_report` (str) | • 방법론 검증, 신규성 분석, 학술 에디터 3인이 상태값을 공유하며 토론을 벌여 종합 피드백 DTO를 도출하는 구조. |
| **F-03-04** | 자기 일관성 가설 검증 | **미구현** | `POST /defense-arena/verify-hypothesis` | • `session_id` (str)<br>• `hypothesis` (str) | • `verdict` (SUPPORT/REFUTE)<br>• `rationale` (str) | • N회 독립 추론 다수결 합의(Self-Consistency) 알고리즘을 타격해 가설 참/거짓 판정 설계. |
| **F-03-05** | 압박 질문 디펜스 챗 | **미구현** | `POST /defense-arena/defense/chat` | • `session_id` (str)<br>• `user_response` (str) | • `refutation_question`<br>• `score` (int), `feedback`<br>• `is_finished` (bool) | • 심사위원 에이전트가 한계점을 물고 질문을 던지고, 유저의 방어 답변을 실시간 채점하는 시뮬레이터 설계. |

---

### 2.4 맞춤형 연구 비서 (Research Gem) 팩토리 & 스토어
자신만의 페르소나와 개별 주입 문서(RAG)를 가진 특화 비서 에이전트 Gem을 생성 및 저장하고, 격리된 1:1 RAG 전용 대화를 조립하는 도구 공장입니다.

* **DB 매핑 테이블**: `gem`
* **격리 데이터**: 젬별 개별 pgvector 컬렉션 (`gem_{gem_id}_files`) 동적 생성 및 사용

| 기능 코드 | 상세 기능명 | 상태 | 백엔드 엔드포인트 / 기술 | Input 스펙 | Output 스펙 | 기능 상세 및 DB 연동 명세 |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **F-04-01** | 특화 비서 Gem 개설 | **완료** | `POST /gems` | • `name` (str)<br>• `db_sources` (List)<br>• `system_prompt` (str) | • `gem_id` (str)<br>• `name` (str) | • 참조 도메인 필터(CS/Bio/Astronomy)와 페르소나 지침을 정의해 데이터베이스 `gem` 마스터에 등록. |
| **F-04-02** | 개인 문서 RAG 적재 | **완료** | `POST /gems/{gem_id}/upload-files` | • `files` (List of UploadFile) | • `gem_id` (str)<br>• `status` (SUCCESS) | • 젬 고유의 전용 pgvector 컬렉션 생성 및 주입된 사용자 연구 파일들을 800자 단위 청크 임베딩 완료. |
| **F-04-03** | 클로저 기반 1:1 대화 | **완료** | `POST /gems/{gem_id}/chat` | • `message` (str)<br>• `thread_id` (str) | • `answer` (str)<br>• `sources` (List) | • 도메인 RAG와 Gem 파일 RAG 도구를 동적으로 캡처한 클로저(Closure)를 활용해 병렬 도구 호출 RAG 스트리밍. |
| **F-04-04** | 젬 파기 및 영구 제거 | **완료** | `DELETE /gems/{gem_id}` | • `gem_id` (str) | N/A (성공 코드) | • `gem` 마스터 레코드 Cascade 삭제 및 pgvector 컬렉션 드롭(`adelete_collection()`)을 통한 임베딩 영구 완전 파쇄. |

---

## 📂 3. 에이전트 공통 메모리 및 시스템 인프라 사양 (구축 완료)

*   **실시간 스트리밍 아키텍처 (Real-time Streaming)**:
    - 에이전트 연산의 각 단계(쿼리 분석, 병렬 RAG 수행 로그 등) 및 최종 답변을 `StreamingResponse`를 통해 클라이언트에 점진적으로 송신합니다.
*   **PostgreSQL 기반 히스토리 영구 보존 (`PostgresSaver`)**:
    - 대화 이력 및 LangGraph 상태 저장소는 비동기식 `PostgresSaver`를 구축하여 Thread ID별로 안정적으로 영구 보존합니다.
*   **컨텍스트 최적화 요약 미들웨어 (`SummarizationMiddleware`)**:
    - 대화의 길이가 임계치를 초과할 시, 오래된 대화 턴을 핵심 요약본으로 압축 보존하여 LLM 컨텍스트 한계를 방어합니다.
