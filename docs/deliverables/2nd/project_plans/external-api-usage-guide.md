# 🔌 외부 클라이언트 연동용 임베딩 API 서버 사용 가이드 (External API Usage Guide)

본 문서는 동일한 로컬 네트워크(공유기 Wi-Fi/LAN) 대역에 연결된 **외부 노트북/클라이언트 기기**에서 맥미니 M4의 고성능 GPU 기반 임베딩 프록시 서버(FastAPI)를 활용하여 3072차원의 임베딩 벡터를 추출하고 애플리케이션(LangChain 등)에 연동하는 방법을 설명합니다.

---

## 🌐 1. 네트워크 통신 구성 (Network Configuration)

맥미니 M4 단독 서빙 아키텍처로 개편되어, Ollama 등 중간 REST API 통신 모듈을 전혀 거치지 않고 FastAPI가 직접 GPU(MPS) 메모리에 모델을 적재하여 직접 추론합니다. 외부 노트북에서는 FastAPI 중계 포트인 `8001` 번호 하나만 호출하여 연동할 수 있습니다.

*   **임베딩 API 서버 (맥미니 M4)**: `192.168.5.13`
    *   **임베딩 서비스 포트**: `8001` (FastAPI)
*   **클라이언트 노트북 (외부 기기)**: 동일 Wi-Fi에 접속된 기기 (예: `192.168.5.10`)
*   **서빙 모델 가중치**: Hugging Face 원본 `Qwen/Qwen3-Embedding-4B` (Apple Silicon GPU MPS 가속 활성화)

---

## ⚡ 2. 임베딩 차원 스펙 및 제로 패딩 (Zero-Padding)
*   `Qwen3-Embedding-4B` 모델의 물리적 원본 출력은 **2,560차원**입니다.
*   사용자 데이터베이스 스키마 `vector(3072)` 및 OpenAI `text-embedding-3-large` 와의 플러그앤플레이 호환을 맞추기 위해, 서버 단에서 **부족한 뒷부분을 `0.0`으로 자동 채우는 제로 패딩(Zero-Padding)**을 적용하여 **최종 3,072차원**을 출력합니다.
*   코사인 유사도(Cosine Similarity)는 두 벡터의 방향성(각도)만을 연산하므로, 벡터 뒤에 무의미한 `0.0` 성분을 512개 덧붙이더라도 **RAG 검색 성능 및 코사인 유사도 연산 점수는 원본 연산 결과와 100% 일치함이 보장**됩니다.

---

## 🛠️ 3. API 엔드포인트 명세 (API Endpoints)

### 3.1 Ollama 호환 임베딩 API (LangChain OllamaEmbeddings 연동용)
*   **Method**: `POST`
*   **URL**: `http://192.168.5.13:8001/api/embeddings`
*   **Request Body**:
    ```json
    {
      "model": "qwen3-embedding",
      "prompt": "임베딩을 생성할 텍스트 샘플입니다." // 단일 텍스트(str) 또는 다중 텍스트 리스트(List[str]) 입력 가능
    }
    ```
*   **Response Body**:
    ```json
    {
      "embedding": [0.0125, -0.0456, 0.0891, ... (2560차원 값) ... 0.0, 0.0, 0.0 (총 3072차원)]
    }
    ```

### 3.2 OpenAI 호환 임베딩 API (LangChain OpenAIEmbeddings 연동용)
*   **Method**: `POST`
*   **URL**: `http://192.168.5.13:8001/v1/embeddings`
*   **Request Body**:
    ```json
    {
      "model": "qwen3-embedding",
      "input": ["첫 번째 텍스트", "두 번째 텍스트"] // 단일 텍스트(str) 또는 다중 텍스트 리스트(List[str]) 입력 가능
    }
    ```
*   **Response Body**:
    ```json
    {
      "object": "list",
      "data": [
        {
          "object": "embedding",
          "embedding": [0.0125, -0.0456, ... (3072차원 벡터)],
          "index": 0
        },
        {
          "object": "embedding",
          "embedding": [0.0781, -0.0212, ... (3072차원 벡터)],
          "index": 1
        }
      ],
      "model": "qwen3-embedding",
      "usage": {
        "prompt_tokens": 12,
        "total_tokens": 12
      }
    }
    ```

---

## 🐍 4. Python 연동 코드 예시 (Python Code Examples)

### 4.1 `requests` 라이브러리를 사용한 다중 텍스트 병렬 호출
외부 노트북 환경에서 프록시 서버로 배치를 날리면, 프록시 서버 내부의 스레드 풀에서 맥미니 GPU에 병렬 연산 요청을 쏘아 고속으로 응답을 리턴합니다.

```python
import requests

API_URL = "http://192.168.5.13:8001/api/embeddings"

# 1. 단일 혹은 다중 텍스트 준비
payload = {
    "model": "qwen3-embedding",
    "prompt": [
        "컴퓨터 과학 논문 초록 데이터셋의 유사도를 코사인 유사도로 판별합니다.",
        "생명공학 도메인 RAG 임베딩 파이프라인 성능을 테스트합니다.",
        "천문학 및 우주 과학 우주선 궤도 예측 분석 데이터셋 가이드라인."
    ]
}

# 2. POST 요청
try:
    response = requests.post(API_URL, json=payload, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    vectors = result.get("embedding")
    
    print(f"✅ 배치 임베딩 추출 완료!")
    print(f"   - 추출된 벡터 개수: {len(vectors)}개")
    print(f"   - 개별 벡터 차원 수: {len(vectors[0])}차원 (3072차원 확인)")
except requests.exceptions.RequestException as e:
    print(f"❌ 임베딩 서버 연결 실패: {e}")
```

---

## 🦜 5. LangChain 프레임워크 연동 (LangChain Integration)

### 5.1 `OllamaEmbeddings` 클래스 사용법 (권장)
LangChain의 커뮤니티 모듈을 사용하여 맥미니의 직접 서빙 포트 `8001`을 다이렉트로 매핑합니다.

```python
from langchain_community.embeddings import OllamaEmbeddings

# LangChain 초기화 및 API 엔드포인트 바인딩
embeddings = OllamaEmbeddings(
    base_url="http://192.168.5.13:8001",  # 맥미니 API 서버 주소
    model="qwen3-embedding"
)

# 단일 쿼리 벡터 추출 예시
query_vector = embeddings.embed_query("논문 에이전트 RAG 파이프라인")
print(f"OllamaEmbeddings 추출 성공 (차원수: {len(query_vector)})")
```

### 5.2 `OpenAIEmbeddings` 클래스 사용법 (OpenAI 호환 포트 매핑)
기존 OpenAI 코드에서 주소와 모델명만 한 줄 바꿔서 그대로 마이그레이션할 때 유용합니다.

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="qwen3-embedding",
    openai_api_base="http://192.168.5.13:8001/v1",  # OpenAI 호환용 엔드포인트 주소
    openai_api_key="local-dummy-key"  # API 키 유효성 통과용 더미 값
)

# 다중 문서 임베딩 추출 예시
docs_vectors = embeddings.embed_documents([
    "의학 논문 초록 RAG 검색을 위한 예시 텍스트입니다.",
    "천문학 이미지 캡셔닝 정형화 메타데이터입니다."
])
print(f"OpenAIEmbeddings 배치 추출 성공 (문서 개수: {len(docs_vectors)}, 차원수: {len(docs_vectors[0])})")
```

---

## 🐘 6. 데이터베이스(pgvector) 세팅 참고사항

`Qwen3-Embedding-4B` 모델에 제로 패딩을 거쳐 출력되는 차원은 **3072차원**이므로, 데이터베이스에 테이블을 생성할 때 컬럼 규격을 `vector(3072)`로 맞춰주어야 합니다.

```sql
-- 1. pgvector 확장 모듈 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 3072차원을 수용하는 논문 임베딩 저장 테이블 생성 예시
CREATE TABLE cs_embeddings (
    chunk_id SERIAL PRIMARY KEY,
    doc_id VARCHAR(50) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(3072) NOT NULL, -- 3072차원 벡터 타입 지정
    chunk_index INTEGER NOT NULL
);

-- 3. 코사인 유사도 고속 연산을 위한 HNSW 인덱스 생성
CREATE INDEX idx_cs_hnsw ON cs_embeddings 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

---

## ⚡ 7. 성능 최적화 및 동시성 가이드 (Performance & Concurrency Tuning)

### 7.1 동시성 스레드 풀 (`MAX_WORKERS`) 설정 권장사항
*   **왜 30개 내외가 최적인가?**
    *   FastAPI의 동기 추론 핸들러(`def`)는 내부 스레드 풀(`ThreadPoolExecutor`)을 통해 다중 요청을 처리합니다.
    *   하지만 GPU(Apple Silicon MPS) 연산은 단일 하드웨어 가속기에서 물리적으로 직렬/병렬 텐서 연산으로 변환되어 수행됩니다.
    *   동시 요청 스레드(`MAX_WORKERS`)를 30개 이상으로 과도하게 늘릴 경우, GPU VRAM 컨텍스트 스위칭 오버헤드와 커널 경합으로 인해 오히려 개별 요청의 처리 지연(Latency)이 증가하고 하드웨어 병목이 심화될 수 있습니다.
    *   맥미니 M4 기준 **20~30개의 스레드 워커**가 GPU 가속 성능을 최대로 쥐어짜면서도 데드락 없이 안정적으로 가동할 수 있는 최적의 임계점입니다.

### 7.2 모델 크기별 성능 및 속도 비교 (0.6B vs 4B)
프로젝트 요구 스펙에 따라 정확도 우선(4B) 또는 속도 우선(0.6B) 모델을 선택하여 교체 서빙할 수 있습니다.

| 모델명 | 파라미터 크기 | 기본 차원 | 3072차원 변환 방식 | 상대 속도 비교 | VRAM 점유량 | 추천 시나리오 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3-Embedding-4B** | 약 40억 (4B) | 2,560 | 512차원 제로 패딩 | **1.0x (기준)** | 약 8.2 GB | 고품질 RAG, 복잡한 의미론적 유사도 검색 |
| **Qwen3-Embedding-0.6B**| 약 6억 (0.6B) | 1,024 | 2,048차원 제로 패딩 | **4.0x ~ 6.0x (빠름)**| 약 1.3 GB | 실시간 대용량 문서 배치 임베딩, 고속 질의응답 |

*   **0.6B 모델의 3072차원 변환 지원**:
    *   0.6B 모델은 기본 1,024차원을 출력하지만, API 서버 환경 변수 `EMBEDDING_DIM=3072` 설정이 적용되면 서버가 부족한 뒷부분 2,048차원을 자동으로 `0.0`으로 패딩합니다.
    *   이를 통해 DB 스키마(`vector(3072)`)를 수정할 필요 없이 플러그앤플레이로 가볍고 빠른 0.6B 모델로 스위칭하여 활용할 수 있습니다.

### 7.3 모델 스위칭 방법
1. Hugging Face 등에서 0.6B 모델 가중치 폴더를 다운로드하여 `embedding-pipeline/models/Qwen3-Embedding-0.6B` 경로에 저장합니다.
2. `embedding-pipeline/main.py`의 `HF_MODEL_NAME` 경로를 해당 폴더로 수정합니다.
3. `.env` 파일에서 `EMBEDDING_DIM=3072`를 유지하고 서버를 재기동합니다.

