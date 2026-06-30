import os
import json
import time
import sys
from openai import OpenAI
from dotenv import load_dotenv

# 콘솔 출력 인코딩 강제 설정 (윈도우 cp949 환경 대응)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# .env 로드
load_dotenv()

# 1. 경로 및 설정 정보
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/archive/arxiv-metadata-oai-snapshot.json"))
OUTPUT_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/archive/local_embeddings_output.jsonl"))

MODEL_NAME = "text-embedding-3-large"
BATCH_SIZE = 100  # OpenAI API 배치 사이즈
TARGET_COUNT = 5000  # cs.NE 도메인 추출 목표 건수


def chunk_text(text, chunk_size=500, overlap=50):
    """500자 단위, 50자 오버랩의 슬라이딩 윈도우 청킹 로직 구현."""
    chunks = []
    if not text:
        return chunks
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start += (chunk_size - overlap)
    return chunks


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[Error] OPENAI_API_KEY is not set in environment or .env file.")
        print("Please edit the .env file in the backend directory first.")
        return

    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=api_key)

    # 출력 디렉토리 확인 및 생성
    os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)

    if not os.path.exists(DATA_PATH):
        print(f"[Error] Source data not found: {DATA_PATH}")
        return

    print(f"[Start] cs.NE papers {TARGET_COUNT} collect & chunking...")
    
    collected_papers = []
    start_time = time.time()

    # 1. 데이터 수집 및 청킹 (메모리에 메타데이터와 청크 텍스트 적재)
    with open(DATA_PATH, "r", encoding="utf-8") as infile:
        for line in infile:
            if len(collected_papers) >= TARGET_COUNT:
                break
            try:
                data = json.loads(line)
                categories = data.get("categories", "")
                
                # cs.NE (Neural and Evolutionary Computing) 도메인 필터링
                if not any(cat == "cs.NE" for cat in categories.strip().split()):
                    continue
                
                doc_id = data.get("id")
                title = data.get("title", "").strip().replace("\n", " ")
                abstract = data.get("abstract", "").strip().replace("\n", " ")
                authors = data.get("authors", "").strip().replace("\n", " ")
                journal_ref = data.get("journal-ref", "")
                doi = data.get("doi", "")

                if not abstract:
                    continue

                # 초록 청킹 분할
                chunks = chunk_text(abstract, chunk_size=500, overlap=50)
                
                collected_papers.append({
                    "doc_id": doc_id,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "journal_ref": journal_ref if journal_ref else "",
                    "doi": doi if doi else "",
                    "categories": categories,
                    "chunk_texts": chunks
                })

                if len(collected_papers) % 500 == 0:
                    print(f"  > Collected: {len(collected_papers)} / {TARGET_COUNT}")

            except Exception as e:
                print(f"[Warning] line parsing error (skip): {e}")

    print(f"[Completed] Data collect completed. Total {len(collected_papers)} papers. (Time: {time.time() - start_time:.1f}s)")

    # 2. 모든 청크들을 평탄화(Flatten)하여 배치 임베딩 연산용 리스트 구성
    all_chunks_to_encode = []
    for paper_idx, paper in enumerate(collected_papers):
        for chunk_idx, chunk_text_str in enumerate(paper["chunk_texts"]):
            all_chunks_to_encode.append({
                "paper_idx": paper_idx,
                "chunk_index": chunk_idx,
                "text": chunk_text_str
            })

    total_chunks = len(all_chunks_to_encode)
    print(f"[Start] Total chunks: {total_chunks:,}. Starting OpenAI batch embedding...")

    # 배치 단위 임베딩 연산 진행
    start_embed = time.time()
    embeddings = []
    
    # BATCH_SIZE 단위 루프
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = all_chunks_to_encode[i:i+BATCH_SIZE]
        texts = [item["text"] for item in batch]
        
        # API 호출 및 재시도 로직
        retries = 3
        while retries > 0:
            try:
                response = client.embeddings.create(
                    input=texts,
                    model=MODEL_NAME,
                    dimensions=3072
                )
                # 응답에서 임베딩 벡터 추출 및 순서에 맞춰 추가
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                print(f"\n⚠️ OpenAI API Error: {e}. Retrying in 5 seconds... ({retries} retries left)")
                time.sleep(5)
                retries -= 1
        else:
            print(f"\n❌ Failed to get embeddings for chunk batch {i} to {i+BATCH_SIZE}. Exiting.")
            return
            
        if (i + BATCH_SIZE) % 500 == 0 or (i + BATCH_SIZE) >= total_chunks:
            current_processed = min(i + BATCH_SIZE, total_chunks)
            elapsed = time.time() - start_embed
            rate = current_processed / elapsed
            print(f"  > Embedding: {current_processed:,} / {total_chunks:,} chunks... (Rate: {rate:.1f} items/sec)")

    print(f"[Completed] Embedding calculations completed. (Time: {time.time() - start_embed:.1f}s)")

    # 3. 임베딩 벡터를 다시 각 논문 모델 구조에 매핑
    for idx, item in enumerate(all_chunks_to_encode):
        paper_idx = item["paper_idx"]
        chunk_idx = item["chunk_index"]
        chunk_text_str = item["text"]
        vector = embeddings[idx]

        if "chunks" not in collected_papers[paper_idx]:
            collected_papers[paper_idx]["chunks"] = []

        collected_papers[paper_idx]["chunks"].append({
            "chunk_index": chunk_idx,
            "chunk_text": chunk_text_str,
            "embedding": vector
        })

    # 4. JSON Line 형태로 로컬 디스크 출력
    print(f"[Save] Saving file: {OUTPUT_FILE_PATH}")
    with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as outfile:
        for paper in collected_papers:
            # chunk_texts 키 제거 후 chunks (벡터 포함) 리스트 저장
            if "chunk_texts" in paper:
                del paper["chunk_texts"]
            outfile.write(json.dumps(paper, ensure_ascii=False) + "\n")

    total_elapsed = time.time() - start_time
    print(f"\n[Completed] RAG embedding file saved! Total {len(collected_papers):,} papers ({total_chunks:,} chunks) | Total Time: {total_elapsed:.2f}s")


if __name__ == "__main__":
    main()
