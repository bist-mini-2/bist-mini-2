"""arXiv q-bio.GN(유전체학) 논문 필터링 + OpenAI 임베딩 → jsonl 저장 (1단계).

arXiv 메타데이터 덤프(약 5.3GB JSONL)를 한 줄씩 스트리밍하며 q-bio.GN 카테고리
논문만 필터링하고, OpenAI ``text-embedding-3-large``(3072차원)로 100건 단위
배치 임베딩하여 결과를 jsonl 파일로 저장한다.

재실행 안전성(idempotent):
    출력 jsonl이 이미 존재하면 처리 완료된 arxiv_id 집합을 로드(resume)하고
    append 모드로 이어서 기록한다. 따라서 중간에 끊겨도 다시 실행하면 남은 건만
    이어서 처리하며, 최종 실패했던 배치도 다음 실행에서 자연스럽게 재시도된다.

실행:
    # 저장소 루트에서 실행 (cwd = repo root)
    python scripts/datasets/embed_bio_gn.py
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from tqdm import tqdm

# 콘솔 한글 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────────────────────────────────────────────────────────────
# 경로 및 상수 설정 (기존 scripts 방식과 동일하게 __file__ 기준 상대 처리)
# ──────────────────────────────────────────────────────────────────────────
INPUT_FILE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../data/raw/archive/arxiv-metadata-oai-snapshot.json",
    )
)
OUTPUT_FILE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../data/raw/archive/bio_gn_embeddings.jsonl",
    )
)
# .env 는 backend/.env 에 위치하므로 경로를 명시적으로 지정한다.
ENV_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../backend/.env")
)

TARGET_CATEGORY = "q-bio.GN"
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072
BATCH_SIZE = 100  # 임베딩 배치 호출 단위 (한 건씩 호출 금지)


@retry(
    retry=retry_if_exception_type(
        (RateLimitError, APIError, APITimeoutError, APIConnectionError)
    ),
    wait=wait_random_exponential(min=1, max=60),  # 1~60초, 지터(jitter) 포함
    stop=stop_after_attempt(6),                    # 최대 6회 시도
    reraise=True,
)
def embed_batch(client, texts: list[str]) -> list[list[float]]:
    """OpenAI 임베딩 배치 호출. 일시적 오류 시 지수 백오프로 재시도합니다.

    Args:
        client: OpenAI 클라이언트 인스턴스
        texts (list[str]): 임베딩할 텍스트 배치

    Returns:
        list[list[float]]: 각 텍스트의 3072차원 임베딩 벡터 리스트

    Raises:
        OpenAIError: 최대 재시도 횟수 초과 시 마지막 예외를 재발생
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIM,
    )
    return [item.embedding for item in response.data]


def load_processed_ids(output_path: str) -> set[str]:
    """기존 출력 jsonl에서 이미 처리 완료된 arxiv_id 집합을 로드합니다(resume).

    Args:
        output_path (str): 출력 jsonl 파일 경로

    Returns:
        set[str]: 이미 임베딩이 저장된 arxiv_id 집합. 파일이 없으면 빈 집합.
    """
    processed: set[str] = set()
    if not os.path.exists(output_path):
        return processed

    print("🔍 기존 출력 파일 감지. 처리 완료된 ID를 로드합니다(resume)...")
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                processed.add(record["arxiv_id"])
            except (json.JSONDecodeError, KeyError):
                # 손상된 줄은 무시 (다음 실행에서 자연스럽게 재처리 대상으로 남음)
                continue
    print(f"   -> 이미 처리 완료된 논문 수: {len(processed):,} 건")
    return processed


def flush_batch(client, outfile, batch_records: list[dict]) -> tuple[int, int]:
    """배치 레코드를 임베딩하여 jsonl로 기록합니다.

    재시도까지 모두 실패한 배치는 전체를 멈추지 않고 skip하며 실패 id를 로깅한다.
    개별 벡터의 차원이 3072가 아니면 해당 레코드만 skip + 경고한다.

    Args:
        client: OpenAI 클라이언트 인스턴스
        outfile: append 모드로 열린 출력 파일 핸들
        batch_records (list[dict]): 메타데이터와 임베딩 입력 텍스트(``_text``)를
            담은 레코드 리스트

    Returns:
        tuple[int, int]: (성공적으로 기록한 건수, 실패/스킵한 건수)
    """
    if not batch_records:
        return 0, 0

    texts = [rec["_text"] for rec in batch_records]
    try:
        embeddings = embed_batch(client, texts)
    except Exception as e:  # noqa: BLE001 - 최종 실패 배치는 멈추지 않고 skip
        failed_ids = [rec["arxiv_id"] for rec in batch_records]
        print(f"  배치 임베딩 최종 실패, skip: {failed_ids} | 사유: {e}")
        return 0, len(batch_records)

    success = 0
    skipped = 0
    for rec, emb in zip(batch_records, embeddings):
        if len(emb) != EMBEDDING_DIM:
            print(
                f"  ⚠️ 경고: arxiv_id {rec['arxiv_id']} 벡터 차원이 "
                f"{len(emb)}차원 (3072 필요). skip."
            )
            skipped += 1
            continue

        out_record = {
            "arxiv_id": rec["arxiv_id"],
            "title": rec["title"],
            "abstract": rec["abstract"],
            "categories": rec["categories"],
            "primary_category": rec["primary_category"],
            "update_date": rec["update_date"],
            "embedding": emb,
        }
        outfile.write(json.dumps(out_record, ensure_ascii=False) + "\n")
        success += 1

    outfile.flush()
    return success, skipped


def main():
    """q-bio.GN 논문을 스트리밍 필터링하여 임베딩 후 jsonl로 저장합니다."""
    load_dotenv(dotenv_path=ENV_FILE_PATH)
    if not os.getenv("OPENAI_API_KEY"):
        print(f"❌ OPENAI_API_KEY 가 설정되어 있지 않습니다. ({ENV_FILE_PATH})")
        return

    if not os.path.exists(INPUT_FILE_PATH):
        print(f"❌ 원본 데이터를 찾을 수 없습니다: {INPUT_FILE_PATH}")
        return

    client = OpenAI()
    os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)

    processed_ids = load_processed_ids(OUTPUT_FILE_PATH)

    scanned = 0          # 스캔한 전체 줄 수
    gn_matched = 0       # q-bio.GN 매칭 수
    embedded_success = 0 # 임베딩 성공(기록) 수
    failed_count = 0     # 실패/스킵 수

    batch_records: list[dict] = []

    print(f"🚀 q-bio.GN 필터링 + 임베딩 시작 (배치 {BATCH_SIZE}건 단위)...")
    # 원본은 절대 통째로 로드하지 않고 한 줄씩 스트리밍 처리한다.
    with open(INPUT_FILE_PATH, "r", encoding="utf-8") as infile, open(
        OUTPUT_FILE_PATH, "a", encoding="utf-8"
    ) as outfile:
        for line in tqdm(infile, desc="scan", unit="line"):
            scanned += 1
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"  ⚠️ JSON 파싱 실패 (건너뜀): line {scanned}")
                continue

            # 필터: categories 를 split 한 리스트에 q-bio.GN 포함 여부
            cats = data.get("categories", "").split()
            if TARGET_CATEGORY not in cats:
                continue
            gn_matched += 1

            arxiv_id = data.get("id")
            if arxiv_id in processed_ids:
                continue  # 이미 처리한 id skip (resume)

            abstract = data.get("abstract", "").strip()
            if not abstract:
                continue  # abstract 비었으면 skip

            title = data.get("title", "").strip()
            # abstract 내 개행은 공백으로 치환하여 임베딩 입력 구성
            abstract_clean = abstract.replace("\n", " ")
            text = f"{title}\n\n{abstract_clean}"

            batch_records.append(
                {
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "abstract": abstract_clean,
                    "categories": data.get("categories", ""),
                    "primary_category": cats[0],  # 첫 번째 카테고리
                    "update_date": data.get("update_date"),
                    "_text": text,
                }
            )

            if len(batch_records) >= BATCH_SIZE:
                ok, bad = flush_batch(client, outfile, batch_records)
                embedded_success += ok
                failed_count += bad
                batch_records = []

        # 잔여 배치 처리
        if batch_records:
            ok, bad = flush_batch(client, outfile, batch_records)
            embedded_success += ok
            failed_count += bad

    print("\n🎉 1단계 완료!")
    print(f"   스캔한 줄 수      : {scanned:,}")
    print(f"   q-bio.GN 매칭 수  : {gn_matched:,}")
    print(f"   임베딩 성공 수    : {embedded_success:,}")
    print(f"   실패/스킵 수      : {failed_count:,}")
    print(f"   출력 파일         : {OUTPUT_FILE_PATH}")


if __name__ == "__main__":
    main()
