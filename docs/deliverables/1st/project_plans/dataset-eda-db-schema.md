# 📊 MTEB 데이터셋 EDA 및 PostgreSQL/pgvector 스키마 설계서 (Dataset EDA & DB Schema Design)

본 문서는 **'논문 AI 에이전트 채팅 플랫폼 (Paper Agent Chat Platform)'**에서 활용할 MTEB(Massive Text Embedding Benchmark) 3대 데이터셋(의학, 컴퓨터 과학, 자연 과학)의 탐색적 데이터 분석(EDA) 결과와 이를 영구 저장하고 RAG 및 다중 에이전트 작업에 활용하기 위한 PostgreSQL 17 및 pgvector 기반 관계형 데이터베이스 스키마 명세서입니다.

---

## 🔍 1. MTEB 3대 데이터셋 탐색적 데이터 분석 (Dataset EDA)

플랫폼은 학술 연구의 도메인 특수성을 다루기 위해 MTEB(Massive Text Embedding Benchmark)에 포함된 의학, 컴퓨터 과학, 자연 과학 분야의 대표 데이터셋 3종을 학습 및 RAG 검색 소스로 활용합니다.

### 1.1 의학/생명공학 도메인: NFCorpus (NutritionFacts.org Corpus)
*   **데이터셋 개요 및 목적**:
    - NutritionFacts.org 웹사이트에서 추출한 일반 대중의 의학/영양 질문(Query)과 PubMed 학술 논문 초록(Document) 간의 상호 평가 및 관련성을 다루는 정보 검색 벤치마크 데이터셋입니다.
*   **구조 분석**:
    -   `corpus.jsonl` (PubMed Documents):
        -   `_id` (str): PubMed 고유 문서 키 (예: `MED-10`)
        -   `title` (str): 논문 제목
        -   `text` (str): 논문 초록 (Abstract)
        -   `metadata` (json): `{ "url": "..." }`
    -   `queries.jsonl` (User Queries):
        -   `_id` (str): 질의 고유 키 (예: `PLAIN-1`)
        -   `text` (str): 자연어로 작성된 영양/건강 의학 질문
    -   `qrels/train.tsv` (Relevance Judgments):
        -   `query-id` (str) - `doc-id` (str) - `rel` (int, 1~2단계 연관성 스코어)
*   **RAG 최적화 및 활용 전략**:
    -   일반 대중의 질문(질의)은 비학술적 단어를 많이 포함하는 반면, 논문 초록은 복잡한 의학 전문 용어로 구성되어 있어 **어휘적 불일치(Vocabulary Mismatch)**가 발생합니다.
    -   따라서 단순 키워드(BM25) 매칭의 한계를 극복하기 위해 `text-embedding-3-small` (1536차원) 조밀 벡터 임베딩을 이용한 시맨틱 유사도 검색을 주로 활용하되, 약물명이나 영양소 명칭의 정확성을 위해 하이브리드 검색을 고려합니다.
    -   추출된 청크 텍스트는 `bio_embeddings` 테이블에 적재됩니다.

### 1.2 컴퓨터 과학 도메인: SCIDOCS (Bibliographic Literature Benchmark)
*   **데이터셋 개요 및 목적**:
    - 컴퓨터 과학 분야의 논문 서지 구조(Bibliographic Network) 분석 및 추천 성능을 검증하기 위한 데이터셋입니다. 논문의 인용망(Citation), 공동 저자(Co-authorship), 학술지(Venue) 등 다각적인 메타데이터를 지니고 있습니다.
*   **구조 분석**:
    -   `corpus.jsonl` (CS Documents):
        -   `_id` (str): Semantic Scholar 고유 논문 ID
        -   `title` (str): 논문 제목
        -   `abstract` (str): 초록 본문
        -   `authors` (list[str]): 저자 이름 리스트
        -   `year` (int): 출판 연도
        -   `venue` (str): 발표 저널 또는 컨퍼런스 명칭
        -   `out_citations` (list[str]): 해당 논문이 인용한 타 논문 ID 목록
        -   `in_citations` (list[str]): 해당 논문을 인용한 타 논문 ID 목록
*   **RAG 최적화 및 활용 전략**:
    -   `F-01-A-5: 인용 관계망 조회 API`에서 D3.js 노드-링크 시각화 컴포넌트의 데이터 소스로 사용하기 위해, 논문 간의 인용 계보 정보를 데이터베이스 상에서 정규화된 조인 관계인 `paper_citation` 테이블로 분리하여 설계합니다.
    -   컴퓨터 과학 논문은 컨퍼런스(CVPR, NeurIPS, ACL 등) 및 저자 필터링 요구가 빈번하므로, 메타데이터 컬럼(`venue`, `authors`, `year`)을 별도 인덱싱 필드로 분리하여 RAG 검색 시 벡터 임베딩 필터 옵션으로 함께 적용합니다.

### 1.3 자연 과학 도메인: SciFact (Scientific Claim Verification)
*   **데이터셋 개요 및 목적**:
    - 과학적 주장(Claim)에 대해 학술 논문 초록들을 근거로 대조하여, 주장이 사실인지 여부를 판별(SUPPORT / CONTRADICT / NOT_ENOUGH_INFO)하고 증거 문장(Sentence-level Evidence)을 추출하는 팩트 체크 벤치마크 데이터셋입니다.
*   **구조 분석**:
    -   `corpus.jsonl` (Scientific Documents):
        -   `doc_id` (int): 논문 고유 ID
        -   `title` (str): 논문 제목
        -   `abstract` (list[str]): 문장 단위로 절단된 초록 본문 리스트
    -   `claims.jsonl` (User/Expert Hypotheses):
        -   `id` (int): 주장 고유 ID
        -   `claim` (str): 과학적 주장 서술문
        -   `citations` (list[json]): 지지/반박을 증명하는 `doc_id` 및 해당 논문 초록의 증거 문장 인덱스 리스트
*   **RAG 최적화 및 활용 전략**:
    -   `F-02-A-6: 최신 연구 동향 알림 구독 등록 API`를 통해 연구자가 설정한 가설에 대해, 이를 지지하거나 반박하는 증거를 탐색하는 **Fact-Checking 에이전트** 구현 시 핵심으로 활용됩니다.
    -   초록 데이터가 문장 단위(`list[str]`)로 분리되어 있으므로, 텍스트 청커 단계에서 단순 글자 수 윈도우 분할이 아닌 **문장 경계를 보존하는 문장형 청커(Sentence-based Chunker)**를 적용하고, 각 문장별 임베딩 벡터를 `astronomy_embeddings`에 매핑해 정확한 매칭 인덱스를 가리키도록 구조화합니다.

---

## 🗄️ 2. 데이터베이스 논리적/물리적 설계 (Database ERD & Schema)

전체 테이블은 데이터 무결성을 유지하기 위한 관계형 테이블(Member, Citations, Thread, Message)과 고성능 벡터 유사도 연산을 지원하기 위한 pgvector 테이블(Embeddings), 그리고 보안 샌드박스의 30분 소거 로직을 지원하는 격리 임시 테이블로 이원화하여 구성되었습니다.

### 2.1 관계형 스키마 ERD 및 테이블 연동 관계

```mermaid
erDiagram
    MEMBER {
        string mid PK "사용자 아이디"
        string mname "이름"
        string mpassword "비밀번호 해시"
        string memail "이메일 (Unique)"
        boolean menabled "활성 상태"
        string mrole "권한 그룹"
    }

    PAPER_CS {
        string doc_id PK "논문 고유 ID"
        string title "논문 제목"
        text abstract "초록"
        string authors "저자 목록"
        integer year "출판 연도"
        string venue "발표 컨퍼런스"
    }

    PAPER_BIO {
        string doc_id PK "논문 고유 ID"
        string title "논문 제목"
        text abstract "초록"
        string url "출처 링크"
    }

    PAPER_ASTRONOMY {
        string doc_id PK "논문 고유 ID"
        string title "논문 제목"
        text abstract "초록"
        string authors "저자 목록"
        integer year "출판 연도"
    }

    PAPER_CITATION {
        integer citation_id PK "인용 고유 키"
        string source_doc_id "인용하는 논문"
        string target_doc_id "피인용되는 논문"
        string domain "학술 영역 (CS/BIO/ASTRO)"
    }

    CHAT_THREAD {
        string thread_id PK "스레드 UUID"
        string mid FK "사용자 ID"
        timestamp created_at "생성 일시"
        timestamp updated_at "수정 일시"
    }

    CHAT_MESSAGE {
        integer message_id PK "메시지 고유 키"
        string thread_id FK "스레드 UUID"
        string role "보낸 사람 (user/assistant)"
        text content "메시지 본문"
        jsonb sources "참조 인용 데이터"
        timestamp created_at "작성 일시"
    }

    GEM_AGENT {
        string gem_id PK "젬 UUID"
        string mid FK "사용자 ID"
        string name "비서 젬 이름"
        jsonb db_sources "RAG 사용 데이터베이스 목록"
        text system_prompt "페르소나 지침"
        timestamp created_at "생성 일시"
    }

    HYPOTHESIS_SUBSCRIPTION {
        string subscription_id PK "구독 UUID"
        string mid FK "사용자 ID"
        text hypothesis "구독할 가설"
        string email "알림 수신 이메일"
        timestamp created_at "생성 일시"
    }

    INBOX_NOTIFICATION {
        string inbox_id PK "인박스 UUID"
        string subscription_id FK "구독 UUID"
        string type "알림 유형 (PRO/CONTRA)"
        string title "수집된 논문 제목"
        string authors "저자 목록"
        string journal "저널 정보"
        text summary "수집 요약문"
        timestamp created_at "수신 일시"
        boolean is_read "읽음 여부"
    }

    SANDBOX_SESSION {
        string session_id PK "세션 UUID"
        string mid FK "사용자 ID"
        timestamp created_at "생성 일시"
        timestamp expires_at "만료 일시 (30분)"
    }

    SANDBOX_FILE {
        string session_file_id PK "임시 파일 UUID"
        string session_id FK "세션 UUID"
        string file_name "파일명"
        string file_path "물리적 보관 경로"
        timestamp created_at "업로드 일시"
    }

    MEMBER ||--o{ CHAT_THREAD : "owns"
    MEMBER ||--o{ GEM_AGENT : "creates"
    MEMBER ||--o{ HYPOTHESIS_SUBSCRIPTION : "subscribes"
    MEMBER ||--o{ SANDBOX_SESSION : "opens"
    
    CHAT_THREAD ||--o{ CHAT_MESSAGE : "contains"
    
    HYPOTHESIS_SUBSCRIPTION ||--o{ INBOX_NOTIFICATION : "notifies"
    
    SANDBOX_SESSION ||--o{ SANDBOX_FILE : "contains"
    
    PAPER_CS ||--o{ PAPER_CITATION : "involved_in"
```

---

## 💾 3. PostgreSQL 17 & pgvector 물리 DDL 스크립트 (schema.sql)

다음은 데이터베이스 인스턴스를 구축하기 위한 표준 SQL DDL입니다. pgvector 인덱스 형식은 코사인 유사도 연산 속도와 정확도를 보장하는 **HNSW (Hierarchical Navigable Small World)** 방식을 기본 설정으로 채택하였습니다.

```sql
-- =========================================================================
-- 1. pgvector 확장 활성화 및 초기 설정
-- =========================================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- =========================================================================
-- 2. 사용자 계정 및 권한 관리 테이블
-- =========================================================================
CREATE TABLE member (
    mid VARCHAR(20) PRIMARY KEY,
    mname VARCHAR(20) NOT NULL,
    mpassword VARCHAR(255) NOT NULL,
    memail VARCHAR(255) UNIQUE NOT NULL,
    menabled BOOLEAN DEFAULT TRUE NOT NULL,
    mrole VARCHAR(20) NOT NULL
);

-- =========================================================================
-- 3. 도메인별 원본 학술 논문 메타데이터 테이블
-- =========================================================================
-- 컴퓨터 과학 논문
CREATE TABLE paper_cs (
    doc_id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,
    year INTEGER,
    venue VARCHAR(100)
);

-- 의학/생명공학 논문
CREATE TABLE paper_bio (
    doc_id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    url TEXT
);

-- 천문학/자연과학 논문
CREATE TABLE paper_astronomy (
    doc_id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,
    year INTEGER
);

-- =========================================================================
-- 4. 도메인별 벡터 임베딩 & 텍스트 청킹 스토어 (pgvector)
-- =========================================================================
-- 컴퓨터 과학 임베딩
CREATE TABLE cs_embeddings (
    chunk_id SERIAL PRIMARY KEY,
    doc_id VARCHAR(50) NOT NULL REFERENCES paper_cs(doc_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    chunk_index INTEGER NOT NULL
);

-- 의학 임베딩
CREATE TABLE bio_embeddings (
    chunk_id SERIAL PRIMARY KEY,
    doc_id VARCHAR(50) NOT NULL REFERENCES paper_bio(doc_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    chunk_index INTEGER NOT NULL
);

-- 천문학 임베딩
CREATE TABLE astronomy_embeddings (
    chunk_id SERIAL PRIMARY KEY,
    doc_id VARCHAR(50) NOT NULL REFERENCES paper_astronomy(doc_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    chunk_index INTEGER NOT NULL
);

-- =========================================================================
-- 5. 서지 관계망 인용 링크 테이블
-- =========================================================================
CREATE TABLE paper_citation (
    citation_id SERIAL PRIMARY KEY,
    source_doc_id VARCHAR(50) NOT NULL,
    target_doc_id VARCHAR(50) NOT NULL,
    domain VARCHAR(20) NOT NULL CHECK (domain IN ('CS', 'BIO', 'ASTRO')),
    CONSTRAINT unique_citation_pair UNIQUE (source_doc_id, target_doc_id)
);

CREATE INDEX idx_citation_source ON paper_citation(source_doc_id);
CREATE INDEX idx_citation_target ON paper_citation(target_doc_id);

-- =========================================================================
-- 6. 채팅 스레드 & 메시지 세션 저장 테이블 (PostgresSaver 스키마 연계)
-- =========================================================================
CREATE TABLE chat_thread (
    thread_id VARCHAR(50) PRIMARY KEY,
    mid VARCHAR(20) NOT NULL REFERENCES member(mid) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE chat_message (
    message_id SERIAL PRIMARY KEY,
    thread_id VARCHAR(50) NOT NULL REFERENCES chat_thread(thread_id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- =========================================================================
-- 7. 맞춤형 AI 비서 젬(Gem) 관리 테이블
-- =========================================================================
CREATE TABLE gem_agent (
    gem_id VARCHAR(50) PRIMARY KEY,
    mid VARCHAR(20) NOT NULL REFERENCES member(mid) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    db_sources JSONB NOT NULL, -- 예: ["cs_embeddings", "bio_embeddings"]
    system_prompt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- =========================================================================
-- 8. 가설 알림 구독 및 수신 인박스 테이블
-- =========================================================================
CREATE TABLE hypothesis_subscription (
    subscription_id VARCHAR(50) PRIMARY KEY,
    mid VARCHAR(20) NOT NULL REFERENCES member(mid) ON DELETE CASCADE,
    hypothesis TEXT NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE inbox_notification (
    inbox_id VARCHAR(50) PRIMARY KEY,
    subscription_id VARCHAR(50) NOT NULL REFERENCES hypothesis_subscription(subscription_id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('PRO_EVIDENCE', 'CONTRA_EVIDENCE', 'TASK_COMPLETE')),
    title TEXT NOT NULL,
    authors TEXT,
    journal TEXT,
    summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL
);

-- =========================================================================
-- 9. 보안 샌드박스 보관 세션 및 임시 적재 테이블
-- =========================================================================
CREATE TABLE sandbox_session (
    session_id VARCHAR(50) PRIMARY KEY,
    mid VARCHAR(20) NOT NULL REFERENCES member(mid) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE sandbox_file (
    session_file_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL REFERENCES sandbox_session(session_id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE sandbox_embeddings (
    chunk_id SERIAL PRIMARY KEY,
    session_file_id VARCHAR(50) NOT NULL REFERENCES sandbox_file(session_file_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    chunk_index INTEGER NOT NULL
);

-- =========================================================================
-- 10. HNSW 성능 최적화 벡터 검색용 인덱스 매핑 설정
-- =========================================================================
-- m개의 최대 연결 커넥션과 ef_construction 매개변수를 제어하여 정확도 성능 보장
CREATE INDEX idx_cs_hnsw ON cs_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_bio_hnsw ON bio_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_astro_hnsw ON astronomy_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_sandbox_hnsw ON sandbox_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- =========================================================================
-- 11. 보안 파쇄 관리 트리거 함수 (30분 초과 세션 자동 삭제 스케줄 지원)
-- =========================================================================
CREATE OR REPLACE FUNCTION purge_expired_sandboxes()
RETURNS void AS $$
BEGIN
    -- 만료 시간이 도래한 sandbox_session 데이터 삭제
    -- CASCADE 조건에 의해 sandbox_file 및 sandbox_embeddings 도 함께 연쇄 파쇄됩니다.
    DELETE FROM sandbox_session WHERE expires_at <= CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;
