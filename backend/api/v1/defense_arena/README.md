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

## 🧪 유닛 테스트 실행 (Unit Test)

본 모듈의 비즈니스 서비스 로직 및 엔드포인트 응답 무결성을 보장하기 위해 mock fixture를 사용한 유닛 테스트가 작성되어 있습니다. 백엔드 루트 폴더에서 아래의 명령어로 검증할 수 있습니다.

```bash
$ PYTHONPATH=. venv/bin/pytest tests/test_defense_arena.py
```
