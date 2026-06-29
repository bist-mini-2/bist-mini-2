# 6. 플랫폼 주요 비즈니스 기능 상세 명세서 (Business Functional Specifications)

본 문서는 `bist-mini-2` 플랫폼의 3대 핵심 비즈니스 기능군인 **일반 채팅 허브 (F-01)**, **대규모 문헌 분석기 (F-02)**, **맞춤형 연구 비서 젬 팩토리 (F-03)** 각각에 대한 상세 기능 요구 사양을 표(Table) 형식으로 정의합니다. 본 명세는 각 기능별 입출력 구조, 비즈니스 규칙 및 관계형 데이터베이스(PostgreSQL) 적재 조건을 포함합니다.

---

## 💬 6-1. 일반 채팅 허브 (General Chat Hub - F-01) 요구 명세

일반 채팅 허브는 자연어 질문에 대해 논문 RAG와 웹 실시간 검색을 무조건적으로 병렬 가동하여, 융합 지식을 단일 마크다운 답변으로 완성하고 실시간 토큰 스트리밍을 공급하는 기본 제어 통제판입니다.

| 기능 코드 | 상세 기능명 | 입력 스펙 (Input) | 출력 스펙 (Output) | 비즈니스 규칙 및 작동 로직 | 기술 스택 및 DB 연동 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **F-01-01** | 병렬 RAG 및 웹 융합 검색 | • `session_id` (VARCHAR)<br>• `user_question` (TEXT) | • `paper_context` (TEXT)<br>• `web_context` (TEXT) | • 질문 의도를 분석하여 학술 영어 키워드와 웹 검색어를 분리 인출한 뒤, 분기 없이 무조건 병렬 실행(`asyncio.gather`)해 지연을 보장 단축함. | • `AnalysisNode` (gpt-4o-mini)<br>• pgvector & Tavily API |
| **F-01-02** | SSE 실시간 스트리밍 답변 | • `session_id` (VARCHAR)<br>• `message` (TEXT) | • `SSE Token Stream`<br>(JSON lines) | • GPT-4o 최종 마크다운 합성 답변을 HTTP Server-Sent Events(SSE) 방식을 사용해 토큰 발생 시마다 실시간 푸시 및 타자 효과 렌더링. | • FastAPI `StreamingResponse`<br>• OpenAI gpt-4o |
| **F-01-03** | 인용 출처 매핑 및 적재 | • `session_id` (VARCHAR)<br>• `message_index` (INT)<br>• `arxiv_id` (VARCHAR)<br>• `title` (VARCHAR) | N/A (성공 코드) | • 대화 RAG 컨텍스트로 실제 참조된 ArXiv 논문 서지 메타데이터(ID, 제목)를 답변과 인덱스 매핑하여 대화 완료 즉시 영구 적재. | • PostgreSQL `chat_source`<br>• ON DELETE CASCADE |

---

## 📊 6-2. 대규모 문헌 스펙 비교 및 공백(Research Gap) 분석기 요구 명세

대규모 문헌 스펙 비교 및 공백 분석기는 수십 편의 선행 연구 데이터를 비동기 배치로 읽어 '해결된 문제'와 '한계점'을 메타 분석하는 독립 대시보드 스펙입니다.

| 기능 코드 | 상세 기능명 | 입력 스펙 (Input) | 출력 스펙 (Output) | 비즈니스 규칙 및 작동 로직 | 기술 스택 및 DB 연동 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **F-02-01** | 비동기 배치 분석 접수 | • `domain` (VARCHAR)<br>• `query` (TEXT) | • `task_id` (VARCHAR: UUID) | • 분석 요청 즉시 고유 `task_id`를 발급하고 데이터베이스 상태를 `PENDING`으로 적재하며 연산은 `BackgroundTasks`로 오프로딩함. | • FastAPI `BackgroundTasks`<br>• `research_gap_task` |
| **F-02-02** | 학술 번역 및 원어 복원 | • `task_id` (VARCHAR) | • `translated_result` (JSONB) | • 영문 분석 결과를 한국어로 번역하되, 오역 및 팩트 왜곡 방지를 위해 핵심 인용구 `source_quote` 필드는 오리지널 영문으로 강제 오버라이트 보존. | • 파이썬 서비스 레이어 가드<br>• `translate_matrix` |
| **F-02-03** | SSE 완료 알림 및 캐싱 | • `task_id` (VARCHAR) | • `event: task_completed`<br>(SSE push payload) | • 진행률 100% 도달 즉시 DB status를 `COMPLETED`로 변경하고, `notification` 테이블 적재 및 SSE를 통해 실시간 완료 토스트 푸시. | • SSE Broadcaster<br>• `notification` |

---

## ⚙️ 6-3. 맞춤형 연구 비서 젬 팩토리 (Research Gem Factory - F-03) 요구 명세

맞춤형 연구 비서 젬 팩토리는 사용자가 특정 RAG 소스 참조 카테고리와 시스템 프롬프트 지침을 조합하여 개인화된 특화 비서(Gem)를 개설하고 RAG 대화를 가동하는 제어판 스펙입니다.

| 기능 코드 | 상세 기능명 | 입력 스펙 (Input) | 출력 스펙 (Output) | 비즈니스 규칙 및 작동 로직 | 기술 스택 및 DB 연동 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **F-03-01** | 맞춤형 페르소나 Gem 개설 | • `name` (VARCHAR)<br>• `db_sources` (VARCHAR)<br>• `system_prompt` (TEXT) | • `gem_id` (VARCHAR: UUID) | • 사용자가 설정한 RAG 참고 분야(cs, bio, astronomy) 및 시스템 프롬프트 가이드라인을 바인딩하여 젬 메타데이터 생성. | • PostgreSQL `gem` 테이블<br>• Supervisor Agent 프롬프트 주입 |
| **F-03-02** | 젬 전용 파일 적재 및 격리 | • `gem_id` (VARCHAR)<br>• `file` (UploadFile) | N/A (성공 코드) | • 개인 PDF 파일을 500자 청크 분할 및 임베딩하여 `gem_{gem_id}_files` 전용 컬렉션에 적재하고, 타 젬과의 RAG 데이터 접근을 물리적 격리. | • pgvector 격리 컬렉션<br>• pdfium & text-embedding-3-large |
| **F-03-03** | 젬 삭제 및 데이터 영구 소멸 | • `gem_id` (VARCHAR) | N/A (성공 코드) | • 젬 삭제 요청 시, Cascade 규칙에 의해 관련 대화 메타를 삭제하고, `gem_{gem_id}_files` 컬렉션을 DB에서 물리적으로 드롭(Drop)하여 완전 소거. | • `DROP TABLE` / `DROP COLLECTION`<br>• PostgreSQL metadata Cascade |
