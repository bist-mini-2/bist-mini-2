# 🔌 외부 클라이언트 연동용 임베딩 API 서버 사용 가이드 (External API Usage Guide)

본 문서는 동일한 로컬 네트워크(공유기 Wi-Fi/LAN) 대역에 연결된 **외부 노트북/클라이언트 기기**에서 맥미니 M4의 고성능 GPU 기반 임베딩 프록시 서버(FastAPI)를 활용하여 3072차원의 임베딩 벡터를 추출하고 애플리케이션(LangChain 등)에 연동하는 방법을 설명합니다.

---

## 🌐 1. 네트워크 통신 구성 (Network Configuration)

임베딩 중계 서버와 클라이언트 노트북은 동일한 서브넷 대역 내에서 내부 기가비트 대역폭으로 통신하여 레이턴시를 최소화합니다.

*   **임베딩 API 서버 (맥미니 M4)**: `192.168.5.13`
    *   **프록시 API 서버 포트**: `8001` (FastAPI)
    *   **원시 Ollama API 포트**: `11434`
*   **클라이언트 노트북 (외부 기기)**: 동일 Wi-Fi에 접속된 기기 (예: `192.168.5.10`)
*   **기본 임베딩 모델**: `qwen3-embedding` (3072차원 고해상도 벡터 모델)

---

## 🛠️ 2. API 엔드포인트 명세 (API Endpoints)

FastAPI 프록시 서버는 LangChain 등 다양한 프레임워크와의 플러그 앤 플레이 연동을 위해 **Ollama 표준 규격**과 **OpenAI 표준 규격**을 모두 지원합니다.

### 2.1 Ollama 호환 임베딩 API (LangChain OllamaEmbeddings 연동용)
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
      "embedding": [0.0125, -0.0456, 0.0891, ... 3072차원 플로팅 배열]
    }
    ```

### 2.2 OpenAI 호환 임베딩 API (LangChain OpenAIEmbeddings 연동용)
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
          "embedding": [0.0125, -0.0456, ...],
          "index": 0
        },
        {
          "object": "embedding",
          "embedding": [0.0781, -0.0212, ...],
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

## 🐍 3. Python 연동 코드 예시 (Python Code Examples)

### 3.1 `requests` 라이브러리를 사용한 다중 텍스트 병렬 호출
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
    print(f"   - 개별 벡터 차원 수: {len(vectors[0])}차원 (Qwen3 규격 확인)")
except requests.exceptions.RequestException as e:
    print(f"❌ 임베딩 서버 연결 실패: {e}")
```

---

## 🦜 4. LangChain 프레임워크 연동 (LangChain Integration)

### 4.1 `OllamaEmbeddings` 클래스 사용법 (권장)
LangChain의 커뮤니티 모듈을 사용하여 맥미니의 중계 포트 `8001`을 다이렉트로 매핑합니다.

```python
from langchain_community.embeddings import OllamaEmbeddings

# LangChain 초기화 및 API 엔드포인트 바인딩
embeddings = OllamaEmbeddings(
    base_url="http://192.168.5.13:8001",  # 맥미니 프록시 서버 주소
    model="qwen3-embedding"
)

# 단일 쿼리 벡터 추출 예시
query_vector = embeddings.embed_query("논문 에이전트 RAG 파이프라인")
print(f"OllamaEmbeddings 추출 성공 (차원수: {len(query_vector)})")
```

### 4.2 `OpenAIEmbeddings` 클래스 사용법 (OpenAI 호환 포트 매핑)
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

## 🐘 5. 데이터베이스(pgvector) 세팅 참고사항

`qwen3-embedding`은 **3072차원**의 벡터를 출력하므로, 데이터베이스에 테이블을 생성할 때 반드시 컬럼 규격을 `vector(3072)`로 맞춰주어야 합니다.

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
