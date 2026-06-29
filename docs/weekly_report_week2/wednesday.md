## **📝 이번 주 실제 개발 내용 요약 (수요일)**
- **대용량 벡터 데이터베이스 백업 시 네트워크 교착 방지용 Paging 설계**:
	- pgvector 테이블(`langchain_pg_embedding`)에 적재된 수만 건의 3072차원 대용량 임베딩 데이터를 한 번에 조회할 경우, 메모리 초과 및 네트워크 타임아웃으로 원격 연결이 단절(Hang)되는 문제를 해결하기 위해 `LIMIT`와 `OFFSET`을 이용한 5,000건 단위의 분할 쿼리(Paging) 스캔 방식을 설계했습니다.
- **Parquet 포맷 변환을 통한 효율적 허브 적재**:
	- JSON/CSV 백업 방식에 비해 디스크 성능 및 압축률이 극적으로 향상되고 컬럼별 스키마가 완격히 유지되는 **Parquet** 파일 포맷을 활용하여 Hugging Face Dataset 객체로 파이썬 메모리 내에서 즉각 변환 및 적재하는 흐름을 적용했습니다.
- **Dataset Card (README.md) 자동 생성 및 업로드 자동화**:
	- 데이터셋 업로드 완료 시, ArXiv 소스 기원 정보 및 OpenAI `text-embedding-3-large` 인코딩 사양, 도메인별 컬렉션 데이터 스키마 명세를 Markdown 파일로 즉시 렌더링하고 `HfApi`를 통해 레포지토리에 자동 Push해주는 데이터 관리 자동화 파이프라인을 구축했습니다.

---

## **💻 핵심 코드 예제 및 상세 해설**

### **1. 대용량 임베딩 분할 조회(Paging) 및 Pandas 변환 (\\[upload_to_huggingface.py\\](file:///Users/pileuszu/Repos/bist-mini-2/scripts/datasets/huggingface/upload_to_huggingface.py))**
대용량 pgvector 테이블 스캔 시 메모리 누수와 타임아웃을 완전 방지하는 안정적 스캐너 로직입니다.
```python
import psycopg
import pandas as pd
from tqdm import tqdm

def fetch_collection_data(conn_str: str, collection_name: str) -> pd.DataFrame:
    # 비동기 엔진 스트링을 동기식 psycopg 연결 주소로 변환
    sync_conn_str = conn_str.replace("postgresql+psycopg_async://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")
    print(f"📖 DB에서 컬렉션 스캔 시작: '{collection_name}'...")
    
    data = []
    chunk_size = 5000  # 5,000건 단위 분할 인출 설정
    
    with psycopg.connect(sync_conn_str) as conn:
        with conn.cursor() as cur:
            # 컬렉션 고유 UUID 획득
            cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s", (collection_name,))
            collection_uuid = cur.fetchone()[0]
            
            # 총 레코드 수 인출
            cur.execute("SELECT count(*) FROM langchain_pg_embedding WHERE collection_id = %s", (collection_uuid,))
            total_records = cur.fetchone()[0]
            
            offset = 0
            pbar = tqdm(total=total_records, desc=f"[{collection_name} 다운로드]")
            
            # [Paging loop]
            while offset < total_records:
                cur.execute("""
                    SELECT id, embedding, document, cmetadata 
                    FROM langchain_pg_embedding 
                    WHERE collection_id = %s
                    ORDER BY id
                    LIMIT %s OFFSET %s
                """, (collection_uuid, chunk_size, offset))
                
                rows = cur.fetchall()
                if not rows:
                    break
                    
                for row_id, embedding, document, cmetadata in rows:
                    meta = cmetadata or {}
                    arxiv_id = meta.get("arxiv_id") or meta.get("doc_id") or ""
                    title = meta.get("title") or ""
                    categories = meta.get("categories") or ""
                    update_date = meta.get("update_date") or ""
                    
                    # pgvector vector 형식을 float 리스트로 파싱
                    parsed_embed = parse_embedding(embedding)
                    
                    data.append({
                        "uuid": str(row_id),
                        "arxiv_id": arxiv_id,
                        "title": title,
                        "categories": categories,
                        "update_date": update_date,
                        "text_chunk": document or "",
                        "embedding": parsed_embed
                    })
                
                offset += len(rows)
                pbar.update(len(rows))
            pbar.close()
            
    return pd.DataFrame(data)
```

### **🔍 주요 구문 및 설계 해설:**
- **`LIMIT %s OFFSET %s`**: 5,000개 단위로 트랜잭션을 끊어서 조회함으로써, 데이터베이스 버퍼 오버헤드를 막고 네트워크 지연이나 유실로 인해 쿼리가 처음부터 튕겨 나가는 예외 상황을 완벽히 방지합니다.

---

### **2. Hugging Face Dataset Card (README) 생성 및 푸시 (\\[upload_to_huggingface.py\\](file:///Users/pileuszu/Repos/bist-mini-2/scripts/datasets/huggingface/upload_to_huggingface.py))**
Hugging Face CLI에 의존하지 않고, 코드로 직접 메타데이터가 기입된 README.md 파일을 동적으로 업로드하여 Dataset Card를 구성하는 기능입니다.
```python
from datasets import Dataset, DatasetDict
from huggingface_hub import HfApi

def upload_dataset(dataset_dict: DatasetDict, repo_id: str, hf_token: str):
    # 1. DatasetDict를 Hugging Face Hub에 Parquet 형식으로 백업 푸시
    dataset_dict.push_to_hub(
        repo_id=repo_id,
        token=hf_token,
        private=True # 내부 프로젝트용 비공개 업로드
    )
    
    # 2. README.md Dataset Card 작성 및 비동기 업로드
    readme_content = f"""---
license: mit
task_categories:
- text-retrieval
language:
- en
tags:
- embedding
---
# BIST ArXiv Domain Embeddings Dataset
본 데이터셋은 **'논문 AI 에이전트 채팅 플랫폼 (Bist Mini 2)'**의 RAG 및 검색 엔진의 소스로 활용하기 위해 구축된 3대 학술 도메인 특화 벡터 임베딩 데이터셋입니다.
* **임베딩 모델:** OpenAI **`text-embedding-3-large`** (3072차원)
* **도메인 구성:** bio, cs, astronomy (3대 subsets 구성)
"""
    api = HfApi()
    api.upload_file(
        path_or_fileobj=readme_content.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
        token=hf_token
    )
    print("✅ Dataset Card (README.md) 업로드 성공!")
```

### **🔍 주요 구문 및 설계 해설:**
- **`HfApi().upload_file`**: 로컬에 디렉토리 저장 공간을 낭비하여 빌드하지 않고, 메모리 내의 바이트 스트림(`readme_content.encode("utf-8")`)을 원격 API 서버로 즉시 업로드함으로써 간결성과 기기 독립성을 극대화합니다.
