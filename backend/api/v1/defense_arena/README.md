# Defense Arena & Peer Review Module (Feature 4)

본 모듈은 보안이 강화된 격리 샌드박스 환경에서 학술 논문(PDF)의 취약점을 심층 분석하고, 다자간 에이전트 비평(Peer Review), 자기 일관성(Self-Consistency) 기반 가설 검증, 그리고 가상 심사위원 에이전트와의 실시간 턴제 모의 면접(Defense Arena)을 수행하는 비즈니스 로직을 제공합니다.

---

## 📂 디렉토리 구조 (Directory Structure)

```text
backend/api/v1/defense_arena/
├── entity.py      # SQLAlchemy ORM 데이터베이스 모델 정의 (Session, Vector Chunks, Chat History)
├── dao.py         # SQLAlchemy 비동기 세션을 이용한 데이터 액세스 객체 (pgvector 유사도 검색 포함)
├── models.py      # FastAPI 입출력 유효성 검증용 Pydantic DTO 스키마 정의
├── services.py    # PDF 파싱, LLM 에이전트 오케스트레이션 및 비즈니스 로직 구현체
├── endpoints.py   # FastAPI 라우터 및 API 엔드포인트 선언 (/api/v1/defense-arena)
└── README.md      # 본 문서 (모듈 설명서)
```

---

## 🛠️ 핵심 기능 및 동작 메커니즘 (Core Features)

### 1. PDF 격리 업로드 및 임시 인덱싱 (F-02-A-1)
* **OS Path Guard**: 업로드 시 디렉토리 트래버설(Directory Traversal) 취약점을 차단하기 위해 `os.path.realpath` 기반 경로 검증을 강제 수행합니다.
* **텍스트 분할 & 임베딩**: `pypdf`를 사용하여 텍스트를 추출한 후 `RecursiveCharacterTextSplitter`를 통해 1000자(overlap 200자) 단위로 청킹합니다.
* **pgvector 3072차원 변환**: OpenAI의 `text-embedding-3-large` 모델을 활용하여 각 청크당 **3072차원 벡터**로 임베딩을 수행하고 DB 테이블에 일괄 적재합니다.

### 2. 30분 미활동 자동 세션 소거 데몬 (F-02-A-2 / Wipe Out)
* **수명 주기 관리**: 기밀 논문의 영구 유출을 방지하기 위해 사용자의 세션 정보는 데이터베이스와 격리 디렉토리에 **최대 30분간만 임시 유지**됩니다.
* **백그라운드 데몬**: `main.py`의 lifespan 데몬이 60초 간격으로 `updated_at` 시간 기준 30분 경과 세션을 스캔하여 자동 삭제 프로세스를 가동합니다.
* **Cascade & 물리 삭제**: DB의 `ON DELETE CASCADE` 연쇄 작동을 통해 연관 텍스트 청크와 디펜스 히스토리가 함께 정리되며, `shutil.rmtree`를 통해 로컬 격리 폴더가 하드디스크에서 물리 소거됩니다.

### 3. Multi-Agent 학술 피어리뷰 시뮬레이션 (F-02-A-3)
* **3대 에이전트 구성**:
  1. **Methodology Agent**: 실험 설계, 수식, 알고리즘 및 데이터 정합성 비평.
  2. **Novelty Agent**: 기존 선행 연구 대비 신규성과 기여도 분석.
  3. **Academic Style Agent**: 문장 구조, 학술 단어 오용, 논문 구성 가독성 비평.
* **구조화된 비평 도출**: LLM의 `with_structured_output` API를 활용하여 3대 에이전트의 개별 점수(0~100)와 비평 내용 및 전체 종합 심사평 요약을 DTO 규격에 맞춰 안전하게 파싱하여 반환합니다.

### 4. Self-Consistency 기반 가설 검증 (F-02-A-4)
* **RAG 기반 팩트 추출**: 사용자가 검증하고 싶은 가설을 던지면, 가설 벡터와 코사인 유사도가 가장 높은 문서 내 청크 5개를 RAG 검색하여 팩트 컨텍스트를 구성합니다.
* **3회 독립 시행 다수결**: LLM의 온도(temperature)를 다르게 주어 3번의 독립 추론을 거친 뒤, 투표율(SUPPORT / REFUTE / INSUFFICIENT_EVIDENCE)을 구하여 다수결 합의 결론과 의견 합의율(Consensus Ratio)을 도출합니다.

### 5. 턴제 모의 디펜스 아레나 및 실시간 채점 (F-02-A-5)
* **턴제 진행 (Turn-based)**: 총 3턴 동안 가상의 날카로운 심사위원 에이전트와 질문 및 반론을 주고받습니다.
* **실시간 평가**: 사용자가 답변을 제출할 때마다 Committee 에이전트가 답변의 논리적 방어력을 0~100점으로 채점하고 보충 피드백을 제공합니다.
* **최종 스코어카드**: 3턴 완료 시 최종 승인 등급(e.g., Major/Minor Revision, Reject)과 종합 심사요약 총평 카드가 렌더링됩니다.

---

## 🗄️ 데이터베이스 스키마 구조 (Database Schema)

### 1. `defense_arena_session` (세션 테이블)
* 사용자의 PDF 파일 업로드 및 활동 연장 정보를 추적합니다.
* `session_id` (PK, UUID), `member_id` (FK), `file_name`, `file_path`, `chunk_count`, `updated_at` (활동 연장 감지용)

### 2. `defense_arena_chunk` (RAG용 텍스트 청크 테이블)
* 논문 내 텍스트 청크와 pgvector 공간 정보를 저장합니다.
* `session_id` (FK - `ON DELETE CASCADE`), `chunk_index`, `text_chunk`, `embedding` (vector(3072) HNSW 인덱싱 연동)

### 3. `defense_history` (대화 이력 테이블)
* 디펜스 아레나에서 오고 간 질문, 답변, 평가 점수, 피드백을 관리합니다.
* `session_id` (FK - `ON DELETE CASCADE`), `turn` (턴 수), `question`, `answer` (Null 허용), `score` (Null 허용), `feedback` (Null 허용)

---

## 📡 API 사양서 요약 (API Spec Summary)

| Method | Endpoint | Description | Request Body (Form) | Response DTO |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/upload-isolated` | PDF 격리 임시 업로드 | `file` (Binary PDF File) | `UploadResponse` |
| **POST** | `/peer-review` | 3대 에이전트 심사 시뮬레이션 | `session_id`, `target_journal` | `PeerReviewReport` |
| **POST** | `/verify-hypothesis` | 자기 일관성 가설 투표 검증 | `session_id`, `hypothesis` | `HypothesisVerificationResult` |
| **POST** | `/defense/chat` | 턴제 심사위원 질문/답변 및 채점 | `session_id`, `user_response` (Optional) | `DefenseChatResponse` |

---

## 📋 E2E 통합 테스트 시나리오 (E2E Test Scenarios)

본 모듈의 전체적인 기능 연동 정합성을 수동 또는 자동화된 E2E 테스트로 검증하기 위한 5단계 표준 시나리오입니다.

### 시나리오 1: PDF 격리 업로드 및 가상 샌드박스 개설
1. **목적**: 기밀 보안 구역에 논문을 안전하게 적재하고 RAG를 위한 3072차원 임베딩 컬렉션이 생성되는지 검증합니다.
2. **테스트 절차**:
   - `POST /api/v1/defense-arena/upload-isolated` API에 테스트용 PDF 파일을 Multipart Form-Data로 전송합니다.
   - **OS Path Guard 검증**: 경로에 디렉토리 트래버설 취약 문자열(예: `../`)을 삽입하여 400 Bad Request 에러 및 접근 거부 처리가 정상 작동하는지 확인합니다.
3. **기대 결과**:
   - HTTP 201 Created 응답 수신.
   - 응답 DTO 내에 고유 `session_id`, 업로드된 `file_name`, 그리고 분할된 `chunk_count`가 반환되어야 합니다.
   - DB 테이블 `defense_arena_session` 및 `defense_arena_chunk`에 해당 레코드가 적재되고, pgvector 인덱스(HNSW)를 통한 조회가 가능해야 합니다.

### 시나리오 2: Multi-Agent 학술 피어 리뷰 생성
1. **목적**: 3대 에이전트(방법론, 신규성, 학술문체)가 토론(Debate)을 거쳐 구조화된 심사평 보고서를 정상적으로 도출하는지 확인합니다.
2. **테스트 절차**:
   - `POST /api/v1/defense-arena/peer-review` API에 이전 단계에서 획득한 `session_id`와 `target_journal` (예: "IEEE Access")을 전달합니다.
3. **기대 결과**:
   - HTTP 200 OK 응답 수신.
   - 응답 DTO에 `overall_score` (0~100점), 3대 분야별 상세 비평 내역, 그리고 최종 `review_report` 텍스트가 정상 구조화되어 반환되어야 합니다.

### 시나리오 3: 자기 일관성(Self-Consistency) 기반 연구 가설 검증
1. **목적**: 제시한 연구 가설에 대해 pgvector 유사도 검색 근거와 3회 독립 추론 다수결 합의가 설계대로 작동하는지 검증합니다.
2. **테스트 절차**:
   - `POST /api/v1/defense-arena/verify-hypothesis` API에 `session_id`와 연구 가설 텍스트(`hypothesis`, 예: "본 논문의 모델은 기존 기법 대비 연산 속도를 20% 단축한다.")를 전달합니다.
3. **기대 결과**:
   - HTTP 200 OK 응답 수신.
   - 응답 DTO 내에 최종 다수결 판정 (`verdict`: SUPPORT / REFUTE / INSUFFICIENT_EVIDENCE) 및 구체적인 근거 분석 텍스트인 `rationale`이 포함되어 반환되어야 합니다.

### 시나리오 4: 심사위원 에이전트 모의 디펜스 (턴제 질답 & 실시간 채점)
1. **목적**: 3턴 동안 진행되는 턴제 심사위원 압박 면접 시뮬레이션 및 실시간 채점/피드백 기능의 상태 전환을 검증합니다.
2. **테스트 절차**:
   - **1턴 (디펜스 시작)**: `POST /api/v1/defense-arena/defense/chat` API에 `session_id`만 전달하고 `user_response`는 누락(Optional)하여 첫 번째 심사위원 질문을 유도합니다.
   - **2~3턴 (반론 및 채점)**: 수신된 질문에 대해 사용자의 방어 논리 텍스트를 `user_response`에 담아 연속적으로 전송합니다.
3. **기대 결과**:
   - **1턴**: HTTP 200 OK 응답 수신. `refutation_question`에 첫 질문이 생성되고, `is_finished`는 `false`로 반환됩니다.
   - **2~3턴**: 답변 제출 시마다 에이전트가 채점한 `score` (0~100점)와 `feedback`이 실시간으로 반환됩니다.
   - **마지막 턴**: 3턴의 반론이 끝나면 `is_finished`가 `true`로 설정되고, 최종 승인 등급(Major Revision, Accept, Reject 등)이 포함된 최종 성적표가 반환되어야 합니다.
   - 모든 대화 내역은 DB `defense_history` 테이블에 안전하게 기록되어야 합니다.

### 시나리오 5: 30분 미활동 세션 자동 소거 (Shredding & Wipe Out)
1. **목적**: 논문 유출 방지를 위한 격리 디렉토리 물리 파쇄와 데이터베이스 임시 레코드 자동 삭제 데몬의 동작을 검증합니다.
2. **테스트 절차**:
   - `defense_arena_session` 테이블의 `updated_at` (또는 `created_at`) 컬럼의 값을 강제로 30분 이전으로 업데이트합니다.
   - 백그라운드 세션 소거 데몬 스케줄러가 트리거될 때까지 대기(또는 강제 트리거)합니다.
3. **기대 결과**:
   - 만료된 세션이 감지되어 데이터베이스의 `defense_arena_session` 테이블에서 해당 레코드가 성공적으로 제거되어야 합니다.
   - `ON DELETE CASCADE`에 의해 `defense_arena_chunk` 및 `defense_history` 테이블의 관련 임시 임베딩 청크와 대화 기록이 자동으로 연쇄 소거되어야 합니다.
   - 격리 업로드 디렉토리에 적재되었던 해당 PDF 파일이 물리적으로 디스크에서 영구 소거(`shutil.rmtree`)되어 복구가 불가능해야 합니다.

---

## 🧪 유닛 테스트 실행 (Unit Test)

본 모듈의 비즈니스 서비스 로직 및 엔드포인트 응답 무결성을 보장하기 위해 mock fixture를 사용한 유닛 테스트가 작성되어 있습니다. 백엔드 루트 폴더에서 아래의 명령어로 검증할 수 있습니다.

```bash
$ PYTHONPATH=. venv/bin/pytest tests/test_defense_arena.py
```

