# Computer Science (CS) Domain RAG & Embedding Pipeline

이 디렉토리는 컴퓨터 과학(CS) 도메인의 ArXiv 학술 논문 데이터 수집, 텍스트 청킹, OpenAI 임베딩 생성 및 PostgreSQL(pgvector) 적재 프로세스와 관련 API 엔드포인트를 포함하고 있습니다.

## 📂 파일 구성 및 역할

- [cs_5000_embed_to_db.py](file:///c:/Repo/bist-mini-2/backend/api/v1/cs/cs_5000_embed_to_db.py): CS 도메인(`cs.NE` 카테고리) 논문 5,000건을 대상으로 500자 청킹(50자 오버랩)을 수행하고 OpenAI `text-embedding-3-large` API로 3,072차원 임베딩을 생성한 뒤, PostgreSQL 데이터베이스에 로드하는 독립 실행형 비동기 스크립트입니다.
- [embedding.py](file:///c:/Repo/bist-mini-2/backend/api/v1/cs/embedding.py): 실시간 유사도 검색 및 단일 텍스트 임베딩을 위한 OpenAI API 연동 싱글톤 헬퍼 모듈입니다.
- [endpoints.py](file:///c:/Repo/bist-mini-2/backend/api/v1/cs/endpoints.py): pgvector 코사인 유사도 거리를 활용한 RAG 기반 논문 유사도 검색 API (`POST /similarity-search/cs`)의 엔드포인트 구현부입니다.
- [services.py](file:///c:/Repo/bist-mini-2/backend/api/v1/cs/services.py): RAG 유사도 검색의 임베딩 변환 및 매핑 비즈니스 로직을 처리하는 서비스 레이어 클래스입니다.
- [dao.py](file:///c:/Repo/bist-mini-2/backend/api/v1/cs/dao.py): PostgreSQL/pgvector 데이터베이스에 접근하여 코사인 유사도 거리가 가까운 텍스트 조각을 조회하는 데이터 액세스 객체(DAO) 모듈입니다.
- [entity.py](file:///c:/Repo/bist-mini-2/backend/api/v1/cs/entity.py): SQLAlchemy 기반의 데이터베이스 테이블 매핑 엔티티 정의 파일입니다. (`paper_cs` 및 `cs_embeddings` 테이블)
- [models.py](file:///c:/Repo/bist-mini-2/backend/api/v1/cs/models.py): 요청 및 응답 검증을 위한 Pydantic DTO 정의 파일입니다.

---

## 💾 데이터베이스 스키마 구조

### 1. `paper_cs` (메타데이터 테이블)
- `doc_id` (VARCHAR(50), Primary Key): ArXiv 논문 ID
- `title` (TEXT): 논문 제목
- `abstract` (TEXT): 논문 초록 본문
- `authors` (TEXT): 논문 저자 목록
- `journal_ref` (TEXT): 게재 저널 정보
- `doi` (VARCHAR(100)): DOI 식별자
- `categories` (VARCHAR(100)): 학술 카테고리 태그

### 2. `cs_embeddings` (임베딩 청크 테이블)
- `chunk_id` (Integer, Primary Key, Auto Increment): 청크 식별자
- `doc_id` (VARCHAR(50), Foreign Key ON DELETE CASCADE): `paper_cs` 테이블과의 관계
- `chunk_text` (TEXT): 500자 크기로 슬라이싱된 본문 조각
- `embedding` (Vector(3072)): 3,072차원 조밀 벡터 데이터
- `chunk_index` (Integer): 초록 내에서 청크 번호 (0-indexed)

> [!NOTE]
> 인덱스는 코사인 유사도 검색 속도 극대화를 위해 pgvector의 **HNSW (Hierarchical Navigable Small World)** 인덱스가 적용되어 있습니다. (`WITH (m = 16, ef_construction = 64)`)

---

## 🚀 실행 가이드 (Running the Pipeline)

이 스크립트는 실행 경로에 무관하게 프로젝트 내의 `.env` 파일과 raw 데이터 스냅샷 경로를 자동으로 탐색하도록 설계되었습니다.

### 1. 사전 준비 (Prerequisites)
`backend/.env` 파일 내에 유효한 `OPENAI_API_KEY`와 `DATABASE_URL`이 기입되어 있고 PostgreSQL 서버가 가동 중이어야 합니다.

### 2. 실행 명령어 (Execution Command)

#### A. 리포지토리 루트 디렉토리에서 실행 시:
```bash
# Git Bash / MINGW64 (슬래시 / 사용)
./backend/.venv/Scripts/python.exe -u backend/api/v1/cs/cs_5000_embed_to_db.py

# PowerShell (역슬래시 \ 사용)
.\backend\.venv\Scripts\python.exe -u backend\api\v1\cs\cs_5000_embed_to_db.py
```

#### B. `backend` 디렉토리 내부에서 실행 시:
```bash
cd backend

# Git Bash / MINGW64 (슬래시 / 사용)
./.venv/Scripts/python.exe -u api/v1/cs/cs_5000_embed_to_db.py

# PowerShell (역슬래시 \ 사용)
.\.venv\Scripts\python.exe -u api\v1\cs\cs_5000_embed_to_db.py

> [!TIP]
> `-u` 플래그는 파이썬 표준 출력이 실시간으로 콘솔 및 로그 파일에 버퍼링 없이 즉시 출력되도록 도와주므로 실행 상황을 모니터링하기 용이합니다.
