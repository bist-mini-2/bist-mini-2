# 6. 플랫폼 기능 요구 명세서 (Functional Specifications)

## 6-1. 공통 RAG 검색 레이어 요구 명세 (F-RAG)

모든 분석 및 대화 기능군이 공유하는 백엔드 공통 RAG 검색 엔진(pgvector 기반)의 도메인별 요약 테이블 및 3대 상세 기능 요구 명세입니다.

---

### A. 공통 RAG 검색 레이어 요약 명세

모든 기능군은 백엔드 공통 RAG 검색 레이어(`rag_pipeline.py`)를 공유하며, HNSW(Hierarchical Navigable Small World) 인덱스를 탑재하여 코사인 유사도 0.35 이상의 신뢰성 높은 청크를 고속 추출합니다.

| 기능 코드 | 도메인 구분 | 대상 데이터셋 및 규모 | 엔드포인트 / 검색 도구 | Input 파라미터 | Output 데이터 구조 | 구현 상세 설명 |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **F-RAG-01** | **생명공학<br>(Bio)** | • ArXiv `q-bio.GN` (Genomics) 및 주요 분과 학술 자료<br>• **총 54,066건** (초록 기준) | `POST /similarity-search/bio`<br>도구: `search_bio_papers` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id` (str: ArXiv ID)<br>&nbsp;&nbsp;- `title` (str)<br>&nbsp;&nbsp;- `text_chunk` (str)<br>&nbsp;&nbsp;- `score` (float) | • 생명과학 연구자의 유전자 편집, 단백질 구조 분석용 pgvector 검색 지원. 3072차원 임베딩 벡터 매칭. |
| **F-RAG-02** | **컴퓨터 과학<br>(CS)** | • ArXiv `cs.NE` (Evolutionary Computing) 및 기계학습 분야<br>• **총 17,825건** (초록 기준) | `POST /similarity-search/cs`<br>도구: `search_cs_papers` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id`<br>&nbsp;&nbsp;- `title`<br>&nbsp;&nbsp;- `text_chunk`<br>&nbsp;&nbsp;- `score` | • 신경망 튜닝, 인공신경망 진화 등 딥러닝 핵심 개념 탐색용 고속 매칭 최적화. |
| **F-RAG-03** | **천문학<br>(Astronomy)** | • ArXiv `astro-ph.EP` (Earth & Planetary Astrophysics)<br>• **총 35,083건** (초록 기준) | `POST /similarity-search/astronomy`<br>도구: `search_astronomy_papers` | • `query` (str)<br>• `top_k` (int = 3) | • `results`: Array of<br>&nbsp;&nbsp;- `doc_id`<br>&nbsp;&nbsp;- `title`<br>&nbsp;&nbsp;- `text_chunk`<br>&nbsp;&nbsp;- `score` | • 외계행성, 궤도역학, 우주 기원 이론 검증용. 3072차원 대형 천체물리 임베딩 공간 확보. |

---

### B. 각 도메인별 3대 상세 기능 요구 명세

#### 🧬 [F-RAG-01] 생명공학 (Bio) RAG 검색 엔진 요구 명세

1.  **F-RAG-01-01. q-bio.GN 기반 유전체학 논문 컨텍스트 쿼리 연산**
    *   **요구사항**: 사용자가 입력한 자연어 질문(한글/영어)을 수신하여 5.4만 건의 유전체학 및 Genomics 관련 논문 초록 데이터베이스 상에서 코사인 유사도 벡터 검색을 지원해야 한다.
    *   **입력 스펙**: `query` (질의어 문자열), `top_k` (반환 청크 수, 기본값 3)
    *   **출력 스펙**: ArXiv ID, 논문 제목, 텍스트 청크 본문, 유사도 점수(Score)를 포함한 JSON Array 구조.
    *   **검증 기준**: 유전자 편집(CRIPSR) 관련 질문 입력 시 1.5초 이내에 핵심 논문 청크 상위 3건을 정확히 반환하는가 여부.

2.  **F-RAG-01-02. 바이오 도메인 전용 코사인 유사도 임계치 필터링**
    *   **요구사항**: 생명과학 연구의 엄밀성 확보와 허위 지식 유입 방지를 위해, RAG 검색 결과 중 코사인 유사도 **0.35 미만**의 매칭 청크는 최종 답변 합성 컨텍스트에서 강제 배제(Drop)해야 한다.
    *   **연산 규칙**: `Similarity = 1.0 - Cosine_Distance` 계산 후 유사도 점수가 0.35 미만인 청크는 최종 리포트 합성 프롬프트에서 자동 여과 처리.
    *   **검증 기준**: 오도메인(예: 기계학습 관련 질문) 쿼리 입력 시, 바이오 RAG 결과가 컨텍스트로 전달되지 않고 차단되는가 여부.

3.  **F-RAG-01-03. 다중 유전공학 서브 카테고리 필터링 지원**
    *   **요구사항**: 사용자가 특정 세부 분과 학술 영역을 타겟팅할 수 있도록, `q-bio.GN` 외에 `q-bio.BM` (Biomolecules), `q-bio.CB` (Cell Behavior) 등 cmetadata JSONB 내 카테고리를 활용한 복합 조건절 조회를 지원해야 한다.
    *   **기술 명세**: PostgreSQL `cmetadata ->> 'categories'` 컬럼을 타겟으로 `LIKE` 또는 인덱스 매치 쿼리 실행.
    *   **검증 기준**: 세부 카테고리 필터를 적용했을 때, 타 분과 논문이 섞이지 않고 정확히 분리 조회되는가 여부.

---

#### 💻 [F-RAG-02] 컴퓨터 과학 (CS) RAG 검색 엔진 요구 명세

1.  **F-RAG-02-01. cs.NE 기반 진화 컴퓨팅 및 신경망 논문 매칭**
    *   **요구사항**: 진화 알고리즘, 심층 인공신경망 아키텍처 이론 등 1.7만 건의 컴퓨터 과학 논문 초록을 대상으로 형태소 및 의미적 키워드를 매칭하여 관련 기술 레코드를 탐색해 내야 한다.
    *   **입력 스펙**: `query` (컴퓨터공학 질의어), `top_k` (기본값 3)
    *   **출력 스펙**: `doc_id` (ArXiv ID), `title`, `text_chunk`, `score`
    *   **검증 기준**: 'Genetic Algorithm tuning' 등 신경망 최적화 쿼리 입력 시 연관된 핵심 방법론 논문이 상위 매칭에 검출되는가 여부.

2.  **F-RAG-02-02. 딥러닝 고유 기술 명사(Named Entity) 가중치 매칭**
    *   **요구사항**: `Transformer`, `Adam Optimizer`, `Backpropagation` 등 인공지능 분야의 핵심 전용 기명 용어(Named Entity)들을 임베딩 공간 상에서 손실 없이 식별하여 정확한 유사 조각을 추출해야 한다.
    *   **기술 명세**: 3072차원의 OpenAI `text-embedding-3-large` 임베딩 모델을 활용하여 의미론적 거리 측정.
    *   **검증 기준**: 특정 최적화 알고리즘 조회 시, 이름이 다른 유사 알고리즘보다 해당 타겟 알고리즘 논문이 최상위(Rank 1)에 위치하는가 여부.

3.  **F-RAG-02-03. 다중 카테고리 교차 참조(Cross-Matching) 검색**
    *   **요구사항**: 하나의 논문이 컴퓨터 과학(`cs.NE`) 외에 기계학습(`cs.LG`), 인공지능(`cs.AI`) 등 복수 도메인에 걸쳐 등록된 경우, 두 영역의 융합 쿼리에 대해 관계형 교차 매칭을 통해 중복 없이 관련 정보를 수집해야 한다.
    *   **검증 기준**: 복합 키워드 검색 시, 중복 논문 조각이 필터링되어 단일 문서(Unique Document)로만 SynthesisNode에 전달되는가 여부.

---

#### 🔭 [F-RAG-03] 천문학 (Astronomy) RAG 검색 엔진 요구 명세

1.  **F-RAG-03-01. astro-ph.EP 기반 외계행성 및 행성계 물리학 문헌 검색**
    *   **요구사항**: 3.5만 건의 지구/행성 천체물리 논문에서 궤도 역학, 분광 분석, 대기 관측 모델 등 천문학 연구자용 고가치 전문 지식을 탐색해 내야 한다.
    *   **입력 스펙**: `query` (천문학 질문), `top_k` (기본값 3)
    *   **출력 스펙**: `doc_id`, `title`, `text_chunk`, `score`
    *   **검증 기준**: 'Exoplanet transit detection method' 등의 관측 방법론 질문 시 해당 물리 이론 논문 초록이 검출되는가 여부.

2.  **F-RAG-03-02. 천체 고유 명칭 및 관측 장비 모델 식별**
    *   **요구사항**: `JWST` (제임스 웹 우주망원경), `TESS`, `Kepler-186f` 등 천문 관측 도구 및 성운/행성 고유 번호 기호를 임베딩 공간에서 혼동 없이 일치시켜 검색해야 한다.
    *   **기술 명세**: 특수기호 및 영문 대소문자 혼용에 대한 강건성(Robustness)을 유지하는 임베딩 매치 구현.
    *   **검증 기준**: 특정 관측위성(Kepler 등) 입력 시, 타 위성(Hubble 등)에 편향되지 않고 해당 장비로 관측한 논문들이 우선 조회되는가 여부.

3.  **F-RAG-03-03. HNSW 기반 대용량 임베딩 공간 탐색 속도 보장**
    *   **요구사항**: 천문학 도메인의 RAG 검색 성능(Latency) 유지를 위해, PostgreSQL의 pgvector 테이블 상에 구현된 HNSW 인덱스를 타격하여 쿼리 당 평균 **50 ms 미만**의 데이터베이스 조회를 보장해야 한다.
    *   **인덱스 설정**: `USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)`
    *   **검증 기준**: 연속적인 100회 검색 트래픽 인가 시, 데이터베이스 인출 단계 소요 시간이 평균 50 ms 이하를 기록하는가 여부.
