import os
import json
import time
import psycopg2
from psycopg2.extras import execute_values

# 1. 경로 및 DB 접속 설정 정보
OUTPUT_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/archive/local_embeddings_output.jsonl"))
DB_CONN_STRING = "postgresql://postgres:postgres@localhost:5432/postgres"
BATCH_INSERT_SIZE = 5000  # 한 번에 INSERT할 레코드 단위

def main():
    print(f"📂 로컬 임베딩 파일 읽는 중: {OUTPUT_FILE_PATH}")
    if not os.path.exists(OUTPUT_FILE_PATH):
        print("❌ 임베딩 결과 파일이 존재하지 않습니다. 1단계 연산을 먼저 완료해 주세요.")
        return

    try:
        conn = psycopg2.connect(DB_CONN_STRING)
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("💡 PostgreSQL 서버가 켜져 있는지, 커넥션 문자열이 맞는지 확인해 주세요.")
        return

    # 3대 타겟 도메인 임베딩 테이블 생성 및 pgvector 확장 확인
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
    start_time = time.time()

    print("🚀 PostgreSQL pgvector 벌크 적재 시작...")
    
    with open(OUTPUT_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                arxiv_id = record.get("arxiv_id")
                embedding = record.get("embedding")
                
                if arxiv_id and embedding:
                    # 3072차원이 맞는지 다시 한번 확인하여 방어 코드 구성
                    if len(embedding) == 3072:
                        insert_data.append((arxiv_id, embedding))
                    else:
                        print(f"⚠️ 경고: arxiv_id {arxiv_id}의 벡터 차원이 {len(embedding)}차원입니다. (3072차원 필요, 스킵)")
                
                # BATCH_INSERT_SIZE 만큼 쌓이면 DB 벌크 인서트 수행
                if len(insert_data) >= BATCH_INSERT_SIZE:
                    execute_values(
                        cursor,
                        "INSERT INTO cs_embeddings (arxiv_id, embedding) VALUES %s ON CONFLICT (arxiv_id) DO UPDATE SET embedding = EXCLUDED.embedding",
                        insert_data
                    )
                    conn.commit()
                    inserted_count += len(insert_data)
                    insert_data = []
                    
                    if inserted_count % 50000 == 0:
                        elapsed = time.time() - start_time
                        print(f"  > DB 적재 진행률: {inserted_count:,} 건 완료... (소요 시간: {elapsed:.1f}초)")
                        
            except Exception as e:
                conn.rollback()
                print(f"⚠️ 라인 적재 중 에러 발생 (건너뜀): {e}")

        # 잔여 데이터 처리
        if insert_data:
            execute_values(
                cursor,
                "INSERT INTO cs_embeddings (arxiv_id, embedding) VALUES %s ON CONFLICT (arxiv_id) DO UPDATE SET embedding = EXCLUDED.embedding",
                insert_data
            )
            conn.commit()
            inserted_count += len(insert_data)

    total_elapsed = time.time() - start_time
    print(f"\n🎉 전체 로컬 DB 벌크 적재 완료! 총 {inserted_count:,} 건 저장 성공 | 소요시간: {total_elapsed:.2f}초")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
