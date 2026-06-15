# 🖥️ OpenAI Batch API 기반 대규모 임베딩 및 DB 적재 가이드 (OpenAI Batch API Pipeline Guide)

본 문서는 로컬 개발 환경(윈도우 PC)에서 대형 GPU 인프라 구축의 복잡성 및 불안정성을 배제하고, OpenAI의 **Batch API(50% 비용 할인)**를 활용하여 대용량 학술 논문 초록 데이터셋(138만 건 ~ 307만 건)을 고속으로 일괄 임베딩 변환한 뒤 로컬 PostgreSQL DB에 안정적으로 벌크 적재하기 위한 하이브리드 파이프라인 가이드라인입니다.

---

## 🏛️ 1. Batch API 기반 파이프라인 아키텍처

로컬 M4 중계 서버 및 Ollama API 통신을 전면 생략하고, OpenAI의 대규모 인프라를 활용하여 분산 연산된 임베딩 결과를 파일 단위로 주고받는 **배치(Batch) 비동기 처리 모델**을 채택합니다.

```mermaid
flowchart TD
    subgraph LocalPC ["Local PC (Windows Development Client)"]
        A[arxiv-metadata-oai-snapshot.json] -->|1. Stream Parsing| B[scripts/generate_batch_input.py]
        B -->|2. Generate Input File| C[batch_input.jsonl]
        F[batch_output.jsonl] -->|5. Bulk Insert| G[scripts/bulk_db_insert.py]
        G -->|6. Load Vectors| H[(PostgreSQL 17 / pgvector)]
    end

    subgraph OpenAICloud ["OpenAI Cloud Infrastructure"]
        C -->|3. File Upload & Create Batch| D[OpenAI Storage & Batch System]
        D -->|4. Parallel Large-Scale Inference| E[text-embedding-3-large]
        E -->|Output Generation| F
    end
```

---

## ⚙️ 2. 1단계: OpenAI Batch 입력용 파일(JSONL) 생성

OpenAI Batch API는 한 줄마다 하나의 독립된 API 요청 객체가 담겨 있는 `.jsonl` (JSON Lines) 형식의 파일을 입력으로 받습니다. 대용량 원본 파일에서 `abstract`를 추출하여 규격에 맞는 요청 파일로 변환합니다.

*   **OpenAI Batch 요청 규격 예시**:
    ```json
    {"custom_id": "arxiv-0704.0001", "method": "POST", "url": "/v1/embeddings", "body": {"model": "text-embedding-3-large", "input": "Abstract text here..."}}
    ```

### 2.1 입력 파일 생성 스크립트 (`scripts/experiments/generate_batch_input.py`)
```python
import os
import json

DATA_PATH = "../../data/raw/archive/arxiv-metadata-oai-snapshot.json"
OUTPUT_BATCH_PATH = "../../data/raw/archive/openai_batch_input.jsonl"
TARGET_MODEL = "text-embedding-3-large"

def generate_openai_batch_file():
    print(f"📂 ArXiv 데이터셋 읽는 중: {DATA_PATH}")
    if not os.path.exists(DATA_PATH):
        print("❌ 원본 JSON 파일을 찾을 수 없습니다.")
        return

    count = 0
    with open(DATA_PATH, "r", encoding="utf-8") as infile, \
         open(OUTPUT_BATCH_PATH, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            try:
                data = json.loads(line)
                # 3대 타겟 도메인(Computer Science - cs.*) 필터링 예시
                categories = data.get("categories", "")
                if not any(cat.startswith("cs.") for cat in categories.strip().split()):
                    continue
                
                arxiv_id = data.get("id")
                abstract = data.get("abstract", "").strip().replace("\n", " ")
                
                if not abstract:
                    continue
                
                # OpenAI Batch API 규격 객체 구성
                batch_request = {
                    "custom_id": f"arxiv-{arxiv_id}",
                    "method": "POST",
                    "url": "/v1/embeddings",
                    "body": {
                        "model": TARGET_MODEL,
                        "input": abstract
                    }
                }
                
                outfile.write(json.dumps(batch_request, ensure_ascii=False) + "\n")
                count += 1
                
                if count % 100000 == 0:
                    print(f"  > 생성 진행 중: {count:,} 건 변환 완료...")
                    
            except Exception as e:
                print(f"⚠️ 에러 라인 건너뜀: {e}")
                
    print(f"✅ Batch 입력 파일 생성 완료: {OUTPUT_BATCH_PATH} (총 {count:,} 건)")

if __name__ == "__main__":
    generate_openai_batch_file()
```

---

## 🚀 3. 2단계: OpenAI Batch 작업 제출 및 다운로드

생성된 `.jsonl` 파일을 OpenAI 서버에 업로드하고 배치 연산 작업을 시작합니다. 완료되면 결과 파일을 다운로드합니다.

*   *사전 요구사항*: `pip install openai` 및 `OPENAI_API_KEY` 환경 변수 세팅.

### 3.1 배치 제출 스크립트 (`scripts/experiments/run_openai_batch.py`)
```python
import os
import time
from openai import OpenAI

# OpenAI 클라이언트 초기화 (OPENAI_API_KEY 환경변수 로드)
client = OpenAI()

INPUT_FILE_PATH = "../../data/raw/archive/openai_batch_input.jsonl"

def run_batch():
    # 1. OpenAI 스토리지에 입력 파일 업로드
    print("📤 OpenAI 스토리지에 배치 파일을 업로드하는 중...")
    batch_file = client.files.create(
        file=open(INPUT_FILE_PATH, "rb"),
        purpose="batch"
    )
    file_id = batch_file.id
    print(f"✅ 파일 업로드 완료 (File ID: {file_id})")

    # 2. Batch 작업 생성
    print("🚀 Batch 작업을 생성하고 전송합니다...")
    batch_job = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/embeddings",
        completion_window="24h", # 24시간 내 완료 보장 (비용 50% 할인)
        metadata={
            "description": "arxiv-cs-embeddings-bulk"
        }
    )
    batch_id = batch_job.id
    print(f"✅ Batch 작업이 시작되었습니다 (Batch ID: {batch_id})")

    # 3. 비동기 모니터링 루프
    while True:
        status_job = client.batches.retrieve(batch_id)
        status = status_job.status
        print(f"⏱️ 현재 상태: {status} | 완료 건수: {status_job.request_counts.completed}/{status_job.request_counts.total}")
        
        if status == "completed":
            output_file_id = status_job.output_file_id
            print(f"🎉 Batch 완료! 결과 파일 ID: {output_file_id}")
            download_result(output_file_id)
            break
        elif status in ["failed", "expired", "cancelled"]:
            print(f"❌ Batch 작업 실패/취소됨: {status_job}")
            break
            
        time.sleep(60) # 1분 주기로 폴링

def download_result(output_file_id):
    print("📥 결과 파일을 다운로드합니다...")
    file_response = client.files.content(output_file_id)
    output_path = "../../data/raw/archive/openai_batch_output.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(file_response.text)
    print(f"✅ 결과 저장 완료: {output_path}")

if __name__ == "__main__":
    run_batch()
```

---

## 💾 4. 3단계: 다운로드 결과 파이썬 로컬 DB 벌크 적재

OpenAI로부터 받아온 결과 파일(`openai_batch_output.jsonl`)은 각 요청의 `custom_id`와 변환된 고품질 `embedding` 정보가 담겨 있습니다. 이를 파싱하여 로컬 PostgreSQL pgvector DB에 단시간 내에 Bulk Insert 처리합니다.

### 4.1 벌크 적재 스크립트 (`scripts/experiments/bulk_db_insert.py`)
```python
import os
import json
import psycopg2
from psycopg2.extras import execute_values

OUTPUT_FILE_PATH = "../../data/raw/archive/openai_batch_output.jsonl"
DB_CONN_STRING = "postgresql://postgres:postgres@localhost:5432/postgres"
BATCH_INSERT_SIZE = 5000  # DB 벌크 단위

def load_and_insert():
    print(f"📂 결과 파일 로드 중: {OUTPUT_FILE_PATH}")
    if not os.path.exists(OUTPUT_FILE_PATH):
        print("❌ 결과 파일을 찾을 수 없습니다. 다운로드가 완료되어야 합니다.")
        return

    conn = psycopg2.connect(DB_CONN_STRING)
    cursor = conn.cursor()
    
    # 3072차원 벡터 컬럼을 포함하는 테이블 생성 확인
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cs_embeddings (
            arxiv_id VARCHAR(50) PRIMARY KEY,
            embedding vector(3072)
        );
    """)
    conn.commit()

    insert_data = []
    inserted_count = 0

    print("🚀 로컬 PostgreSQL pgvector 벌크 적재 시작...")
    with open(OUTPUT_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                custom_id = data.get("custom_id", "")
                arxiv_id = custom_id.replace("arxiv-", "")
                
                # API 응답에서 임베딩 벡터 추출
                response_body = data.get("response", {}).get("body", {})
                embedding = response_body.get("data", [{}])[0].get("embedding", [])
                
                if arxiv_id and embedding:
                    insert_data.append((arxiv_id, embedding))
                
                if len(insert_data) >= BATCH_INSERT_SIZE:
                    execute_values(
                        cursor,
                        "INSERT INTO cs_embeddings (arxiv_id, embedding) VALUES %s ON CONFLICT (arxiv_id) DO UPDATE SET embedding = EXCLUDED.embedding",
                        insert_data
                    )
                    conn.commit()
                    inserted_count += len(insert_data)
                    print(f"  > 누적 적재 완료: {inserted_count:,} 건...")
                    insert_data = []
                    
            except Exception as e:
                conn.rollback()
                print(f"⚠️ 라인 적재 중 에러 발생: {e}")

    # 잔여 데이터 적재
    if insert_data:
        execute_values(
            cursor,
            "INSERT INTO cs_embeddings (arxiv_id, embedding) VALUES %s ON CONFLICT (arxiv_id) DO UPDATE SET embedding = EXCLUDED.embedding",
            insert_data
        )
        conn.commit()
        inserted_count += len(insert_data)

    print(f"🎉 로컬 DB 적재 완료! 총 {inserted_count:,} 건의 벡터 저장 완료.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_and_insert()
```

---

## 🔌 5. [온라인 쿼리] LangChain 연동 가이드

대량 데이터 적재는 Batch API로 오프라인 빌드하지만, 실제 챗봇 및 RAG 시스템을 구동할 때의 실시간 쿼리 임베딩은 기존 OpenAIEmbeddings SDK를 그대로 연동하여 동작시킵니다.

```python
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector

# 실시간 쿼리 임베딩 모델 로드 (3072차원 매핑)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# pgvector 데이터베이스 연동
vectorstore = PGVector(
    embeddings=embeddings,
    collection_name="cs_papers_collection",
    connection="postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)

# 실시간 RAG 유사도 검색
query = "What are the latest architectures in CNN visual models?"
docs = vectorstore.similarity_search(query, k=5)
```

---

## 📈 6. 아키텍처 전환 효과 분석

1.  **로컬 인프라 구축 공수 0%**: Mac Mini M4에 가상환경 설정, PyTorch-MPS 호환 버그 디버깅, Ollama 동시성 락 및 오류 대처 등 로컬 하드웨어 튜닝에 소요되는 고질적인 개발 공수가 완전히 생략됩니다.
2.  **안정적인 완료 보장**: 로컬 하드웨어 리포팅 중 다운, 네트워크 순간 유실 등의 이슈 없이 OpenAI 클라우드 인프라가 100% 에러 없이 연산을 완료해 줍니다.
3.  **저렴한 비용 도입**: 약 307만 건의 초록(평균 200토큰 내외)을 `text-embedding-3-large`로 빌드할 때 발생하는 비용은 원래 약 $80 수준이지만, **Batch API 50% 할인으로 단 $40 (한화 약 5만 5천 원)** 내외로 대규모 고품질 벡터 데이터베이스를 완벽하게 구축할 수 있습니다.
