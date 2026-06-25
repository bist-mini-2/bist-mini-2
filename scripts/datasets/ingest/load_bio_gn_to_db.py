"""bio_gn_embeddings.jsonl → PostgreSQL + pgvector 2-테이블 적재 (2단계).

1단계(``embed_bio_gn.py``)가 생성한 jsonl을 한 줄씩 읽어 ``paper_bio``(메타데이터)와
``bio_embeddings``(3072차원 벡터) 두 테이블에 벌크 UPSERT한다.

구현 메모(환경 기준):
    팀 표준 작업 지시서는 psycopg2 + ``execute_values`` 패턴을 참고하라고 안내하지만,
    이 프로젝트의 ``backend/requirements.txt`` 는 psycopg(v3) + pgvector 를 고정하고
    있으며 psycopg2 는 설치되어 있지 않다. 따라서 동일한 "다중 행 한 번에 INSERT +
    ON CONFLICT UPSERT" 의미를 psycopg(v3) 위에서 구현한다. 벡터는 pgvector 텍스트
    리터럴(``[v1,v2,...]``)로 직렬화하여 ``::vector`` 캐스트로 적재한다.

실행:
    python scripts/datasets/load_bio_gn_to_db.py
"""

import json
import os
import sys
import time

import psycopg

# 콘솔 한글 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────────────────────────────────────────────────────────────
# 경로 및 DB 접속 설정 (기존 scripts 방식과 동일하게 __file__ 기준 상대 처리)
# ──────────────────────────────────────────────────────────────────────────
INPUT_FILE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../data/raw/archive/bio_gn_embeddings.jsonl",
    )
)
DB_CONN_STRING = "postgresql://postgres:postgres@localhost:5432/postgres"
BATCH_INSERT_SIZE = 5000  # 한 번에 INSERT할 레코드 단위
EMBEDDING_DIM = 3072

DDL_STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS vector;",
    """
    CREATE TABLE IF NOT EXISTS paper_bio (
        arxiv_id         VARCHAR(30) PRIMARY KEY,
        title            TEXT NOT NULL,
        abstract         TEXT NOT NULL,
        categories       TEXT NOT NULL,
        primary_category VARCHAR(30),
        update_date      VARCHAR(20)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bio_embeddings (
        arxiv_id  VARCHAR(30) PRIMARY KEY REFERENCES paper_bio(arxiv_id) ON DELETE CASCADE,
        title     TEXT NOT NULL,
        embedding vector(3072) NOT NULL
    );
    """,
]

# paper_bio: 메타데이터 UPSERT
PAPER_INSERT_SQL = (
    "INSERT INTO paper_bio "
    "(arxiv_id, title, abstract, categories, primary_category, update_date) "
    "VALUES {values} "
    "ON CONFLICT (arxiv_id) DO UPDATE SET "
    "title=EXCLUDED.title, abstract=EXCLUDED.abstract, "
    "categories=EXCLUDED.categories, primary_category=EXCLUDED.primary_category, "
    "update_date=EXCLUDED.update_date"
)
PAPER_ROW_TEMPLATE = "(%s, %s, %s, %s, %s, %s)"

# bio_embeddings: 벡터 UPSERT (embedding 은 ::vector 캐스트)
EMB_INSERT_SQL = (
    "INSERT INTO bio_embeddings (arxiv_id, title, embedding) "
    "VALUES {values} "
    "ON CONFLICT (arxiv_id) DO UPDATE SET "
    "embedding=EXCLUDED.embedding, title=EXCLUDED.title"
)
EMB_ROW_TEMPLATE = "(%s, %s, %s::vector)"


def execute_values(cursor, insert_sql: str, row_template: str, rows: list[tuple]) -> None:
    """psycopg(v3)용 다중 행 INSERT 헬퍼. psycopg2 ``execute_values`` 를 대체합니다.

    ``insert_sql`` 의 ``{values}`` 자리에 행 개수만큼의 플레이스홀더를 채워 한 번의
    ``execute`` 로 여러 행을 적재한다.

    Args:
        cursor: psycopg 커서
        insert_sql (str): ``{values}`` 플레이스홀더를 포함한 INSERT 문
        row_template (str): 한 행의 플레이스홀더 템플릿 (예: ``"(%s, %s)"``)
        rows (list[tuple]): 적재할 행 튜플 리스트
    """
    if not rows:
        return
    values_clause = ",".join([row_template] * len(rows))
    flat_params = [value for row in rows for value in row]
    cursor.execute(insert_sql.format(values=values_clause), flat_params)


def to_vector_literal(embedding: list[float]) -> str:
    """임베딩 리스트를 pgvector 텍스트 리터럴 문자열로 변환합니다.

    Args:
        embedding (list[float]): 3072차원 임베딩 벡터

    Returns:
        str: ``"[v1,v2,...]"`` 형식의 pgvector 리터럴
    """
    return "[" + ",".join(repr(float(v)) for v in embedding) + "]"


def flush_batch(conn, cursor, paper_rows: list[tuple], emb_rows: list[tuple]) -> int:
    """한 배치를 FK 순서(paper_bio → bio_embeddings)대로 벌크 UPSERT합니다.

    배치 단위로 commit하며, 오류 발생 시 rollback 후 해당 배치를 로깅하고 0을 반환해
    전체 적재를 중단하지 않는다.

    Args:
        conn: psycopg 커넥션
        cursor: psycopg 커서
        paper_rows (list[tuple]): paper_bio 행 리스트
        emb_rows (list[tuple]): bio_embeddings 행 리스트

    Returns:
        int: 성공적으로 적재(commit)한 레코드 수. 실패 시 0.
    """
    if not paper_rows:
        return 0
    try:
        # FK 순서 준수: paper_bio 를 먼저 INSERT 한 뒤 bio_embeddings 를 INSERT
        execute_values(cursor, PAPER_INSERT_SQL, PAPER_ROW_TEMPLATE, paper_rows)
        execute_values(cursor, EMB_INSERT_SQL, EMB_ROW_TEMPLATE, emb_rows)
        conn.commit()
        return len(paper_rows)
    except Exception as e:  # noqa: BLE001 - 배치 단위 격리, 전체 중단 금지
        conn.rollback()
        ids = [row[0] for row in paper_rows]
        print(f"  ⚠️ 배치 적재 실패 (rollback 후 계속): {len(ids)}건 | 사유: {e}")
        return 0


def main():
    """jsonl 임베딩 파일을 읽어 2-테이블 구조로 DB에 벌크 적재합니다."""
    print(f"📂 임베딩 파일 읽는 중: {INPUT_FILE_PATH}")
    if not os.path.exists(INPUT_FILE_PATH):
        print("❌ 임베딩 결과 파일이 없습니다. 1단계(embed_bio_gn.py)를 먼저 완료하세요.")
        return

    try:
        conn = psycopg.connect(DB_CONN_STRING)
    except Exception as e:  # noqa: BLE001
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("💡 PostgreSQL 이 localhost:5432 에서 구동 중인지 확인하세요.")
        return

    cursor = conn.cursor()

    # 스키마 생성 (IF NOT EXISTS)
    for stmt in DDL_STATEMENTS:
        cursor.execute(stmt)
    conn.commit()

    paper_rows: list[tuple] = []
    emb_rows: list[tuple] = []
    inserted_count = 0
    skipped_count = 0
    start_time = time.time()

    print("🚀 PostgreSQL pgvector 벌크 적재 시작...")
    with open(INPUT_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print("  ⚠️ JSON 파싱 실패 (건너뜀)")
                continue

            arxiv_id = record.get("arxiv_id")
            embedding = record.get("embedding")
            if not arxiv_id or embedding is None:
                continue

            # 벡터 차원 방어 검증
            if len(embedding) != EMBEDDING_DIM:
                print(
                    f"  ⚠️ 경고: arxiv_id {arxiv_id} 벡터 차원 {len(embedding)} "
                    f"(3072 필요). skip."
                )
                skipped_count += 1
                continue

            paper_rows.append(
                (
                    arxiv_id,
                    record.get("title", ""),
                    record.get("abstract", ""),
                    record.get("categories", ""),
                    record.get("primary_category"),
                    record.get("update_date"),
                )
            )
            emb_rows.append(
                (arxiv_id, record.get("title", ""), to_vector_literal(embedding))
            )

            if len(paper_rows) >= BATCH_INSERT_SIZE:
                inserted = flush_batch(conn, cursor, paper_rows, emb_rows)
                inserted_count += inserted
                paper_rows = []
                emb_rows = []
                elapsed = time.time() - start_time
                print(
                    f"  > DB 적재 진행: 누적 {inserted_count:,} 건 "
                    f"(소요 {elapsed:.1f}초)"
                )

        # 잔여 데이터 처리
        if paper_rows:
            inserted_count += flush_batch(conn, cursor, paper_rows, emb_rows)

    total_elapsed = time.time() - start_time
    print(
        f"\n🎉 2단계 완료! 총 {inserted_count:,} 건 적재 "
        f"(스킵 {skipped_count:,} 건) | 소요 {total_elapsed:.2f}초"
    )

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
