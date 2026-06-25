import os
import json
import time
import sys
import psycopg

# 콘솔 출력 인코딩 강제 설정 (윈도우 cp949 환경 대응)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 1. 경로 및 DB 접속 설정 정보
OUTPUT_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/archive/local_embeddings_output.jsonl"))
DB_CONN_STRING = "postgresql://postgres:postgres@localhost:5432/postgres"
BATCH_INSERT_SIZE = 500  # 벌크 인서트 트랜잭션 묶음 단위 (논문 기준)


def main():
    print(f"[Load] Reading local embedding file: {OUTPUT_FILE_PATH}")
    if not os.path.exists(OUTPUT_FILE_PATH):
        print("[Error] Embedding file does not exist. Complete step 1 calculation first.")
        return

    try:
        conn = psycopg.connect(DB_CONN_STRING)
        cursor = conn.cursor()
        print("[DB] PostgreSQL database connection successful.")
    except Exception as e:
        print(f"[Error] Database connection failed: {e}")
        print("💡 Check if PostgreSQL server is running and the connection string is correct.")
        return

    # 1. pgvector 확장 및 스키마 테이블 빌드 (DDL)
    print("[Schema] Building DB schemas and verifying pgvector extension...")
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # paper_cs 메타데이터 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_cs (
                doc_id VARCHAR(50) PRIMARY KEY,
                title TEXT NOT NULL,
                abstract TEXT,
                authors TEXT,
                journal_ref TEXT,
                doi VARCHAR(100),
                categories VARCHAR(100)
            );
        """)
        
        # cs_embeddings 테이블 생성 (Foreign Key & ON DELETE CASCADE 설정 포함)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cs_embeddings (
                chunk_id SERIAL PRIMARY KEY,
                doc_id VARCHAR(50) NOT NULL REFERENCES paper_cs(doc_id) ON DELETE CASCADE,
                text_chunk TEXT NOT NULL,
                embedding vector(3072) NOT NULL,
                chunk_index INTEGER NOT NULL
            );
        """)
        
        # HNSW 코사인 유사도 인덱스 생성
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cs_hnsw 
            ON cs_embeddings USING hnsw (embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);
        """)
        
        conn.commit()
        print("[Schema] DB schemas and indexes successfully verified.")
    except Exception as e:
        conn.rollback()
        print(f"[Error] Exception occurred during DDL creation: {e}")
        cursor.close()
        conn.close()
        return

    # 2. 데이터 벌크 삽입 실행
    print("[Insert] Starting bulk data load to PostgreSQL...")
    start_time = time.time()
    
    papers_batch = []
    chunks_batch = []
    total_papers_inserted = 0
    total_chunks_inserted = 0

    with open(OUTPUT_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                doc_id = record.get("doc_id")
                title = record.get("title")
                abstract = record.get("abstract")
                authors = record.get("authors")
                journal_ref = record.get("journal_ref")
                doi = record.get("doi")
                categories = record.get("categories")
                chunks = record.get("chunks", [])

                if not doc_id:
                    continue

                # paper_cs 용 튜플 패킹
                papers_batch.append((
                    doc_id, title, abstract, authors, journal_ref, doi, categories
                ))

                # cs_embeddings 용 튜플 패킹
                for chunk in chunks:
                    chunk_index = chunk.get("chunk_index")
                    chunk_text = chunk.get("chunk_text")
                    embedding = chunk.get("embedding")
                    
                    if chunk_text and embedding and len(embedding) == 3072:
                        chunks_batch.append((
                            doc_id, chunk_text, embedding, chunk_index
                        ))

                # 임계 배치 크기에 도달하면 벌크 적재 수행
                if len(papers_batch) >= BATCH_INSERT_SIZE:
                    # 1) paper_cs 메타데이터 벌크 삽입 (중복 시 업데이트)
                    cursor.executemany(
                        """
                        INSERT INTO paper_cs (doc_id, title, abstract, authors, journal_ref, doi, categories) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s) 
                        ON CONFLICT (doc_id) DO UPDATE SET 
                            title = EXCLUDED.title,
                            abstract = EXCLUDED.abstract,
                            authors = EXCLUDED.authors,
                            journal_ref = EXCLUDED.journal_ref,
                            doi = EXCLUDED.doi,
                            categories = EXCLUDED.categories
                        """,
                        papers_batch
                    )

                    # 2) cs_embeddings 청크 벌크 삽입
                    cursor.executemany(
                        """
                        INSERT INTO cs_embeddings (doc_id, text_chunk, embedding, chunk_index) 
                        VALUES (%s, %s, %s, %s)
                        """,
                        chunks_batch
                    )

                    conn.commit()
                    total_papers_inserted += len(papers_batch)
                    total_chunks_inserted += len(chunks_batch)
                    papers_batch = []
                    chunks_batch = []
                    
                    print(f"  > Progress: Papers {total_papers_inserted:,} | Chunks {total_chunks_inserted:,} (Time: {time.time() - start_time:.1f}s)")

            except Exception as e:
                conn.rollback()
                print(f"[Warning] Error during line insert (skip): {e}")

        # 잔여 데이터 처리
        if papers_batch:
            try:
                cursor.executemany(
                    """
                    INSERT INTO paper_cs (doc_id, title, abstract, authors, journal_ref, doi, categories) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s) 
                    ON CONFLICT (doc_id) DO UPDATE SET 
                        title = EXCLUDED.title,
                        abstract = EXCLUDED.abstract,
                        authors = EXCLUDED.authors,
                        journal_ref = EXCLUDED.journal_ref,
                        doi = EXCLUDED.doi,
                        categories = EXCLUDED.categories
                    """,
                    papers_batch
                )

                cursor.executemany(
                    """
                    INSERT INTO cs_embeddings (doc_id, text_chunk, embedding, chunk_index) 
                    VALUES (%s, %s, %s, %s)
                    """,
                    chunks_batch
                )
                conn.commit()
                total_papers_inserted += len(papers_batch)
                total_chunks_inserted += len(chunks_batch)
            except Exception as e:
                conn.rollback()
                print(f"[Error] Error during leftover data insert: {e}")

    total_elapsed = time.time() - start_time
    print(f"\n[Completed] PostgreSQL bulk load successful! Papers: {total_papers_inserted:,}, Chunks: {total_chunks_inserted:,} | Total Time: {total_elapsed:.2f}s")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
