import os
import json
import time
import sys
import asyncio
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv

# 콘솔 출력 인코딩 강제 설정 (윈도우 cp949 환경 대응)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ANSI 컬러 코드 정의 (콘솔 출력 가시성 확보)
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# .env 로드 및 실행 경로 유연화 설정
script_dir = os.path.dirname(os.path.abspath(__file__))
# 스크립트 파일 위치 기준 backend 디렉토리 (3레벨 위)
backend_dir_from_script = os.path.abspath(os.path.join(script_dir, "../../.."))
env_from_script = os.path.join(backend_dir_from_script, ".env")

# 실행 위치(CWD) 기준 .env 위치 확인
cwd = os.getcwd()
env_from_cwd_backend = os.path.join(cwd, "backend", ".env")
env_from_cwd_root = os.path.join(cwd, ".env")

# 순서대로 .env 파일이 존재하는지 검증하여 로드
loaded = False
for env_path in [env_from_script, env_from_cwd_backend, env_from_cwd_root]:
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        loaded = True
        break

if not loaded:
    load_dotenv()

# sys.path에 backend 디렉토리를 추가하여 api.* 모듈 임포트 가능하도록 설정
if backend_dir_from_script not in sys.path:
    sys.path.insert(0, backend_dir_from_script)

from api.database.config.dbsession import session_maker
from api.v1.cs.entity import PaperCsEntity, CsEmbeddingEntity
from sqlalchemy.future import select

# 데이터 경로 및 출력 경로 설정 (스크립트 위치 기준 4레벨 위가 workspace root)
ROOT_DIR = os.path.abspath(os.path.join(script_dir, "../../../.."))
DATA_PATH = os.path.abspath(os.path.join(ROOT_DIR, "data/raw/archive/arxiv-metadata-oai-snapshot.json"))
OUTPUT_FILE_PATH = os.path.abspath(os.path.join(ROOT_DIR, "data/raw/archive/local_embeddings_output.jsonl"))

MODEL_NAME = "text-embedding-3-large"
BATCH_SIZE = 100  # OpenAI API 배치 사이즈
TARGET_COUNT = 5000  # cs.NE 도메인 추출 목표 건수


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """500자 단위, 50자 오버랩의 슬라이딩 윈도우 청킹 로직 구현.

    Args:
        text (str): 분할할 입력 텍스트.
        chunk_size (int, optional): 각 청크의 최대 길이. Defaults to 500.
        overlap (int, optional): 청크 간 중복될 길이. Defaults to 50.

    Returns:
        list[str]: 분할된 텍스트 청크 리스트.
    """
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


async def save_to_db(collected_papers: list) -> None:
    """수집된 논문 메타데이터와 임베딩 청크들을 DB의 paper_cs 및 cs_embeddings 테이블에 비동기로 저장합니다.

    Args:
        collected_papers (list): 임베딩 벡터가 포함된 논문 데이터 리스트.
    """
    print(f"\n{BOLD}[4/4] 🗄️ PostgreSQL (pgvector) 데이터베이스 적재 시작...{RESET}")
    start_time = time.time()
    
    async with session_maker() as session:
        # 1. 대상 doc_id 목록 추출
        doc_ids = [paper["doc_id"] for paper in collected_papers]
        
        # 2. 이미 존재하는 doc_id들 조회 (중복 데이터 삽입 방지)
        existing_doc_ids = set()
        for i in range(0, len(doc_ids), 1000):
            batch_ids = doc_ids[i:i+1000]
            stmt = select(PaperCsEntity.doc_id).where(PaperCsEntity.doc_id.in_(batch_ids))
            result = await session.execute(stmt)
            for doc_id in result.scalars():
                existing_doc_ids.add(doc_id)
                
        print(f"  > {YELLOW}DB에 이미 존재하는 CS 논문:{RESET} {len(existing_doc_ids):,}건 (중복 스킵 처리 예정)")
        
        # 3. 신규 저장할 PaperCsEntity 및 CsEmbeddingEntity 목록 구성
        papers_to_insert = []
        embeddings_to_insert = []
        
        for paper in collected_papers:
            doc_id = paper["doc_id"]
            if doc_id in existing_doc_ids:
                continue
                
            paper_entity = PaperCsEntity(
                doc_id=doc_id,
                title=paper["title"],
                abstract=paper["abstract"],
                authors=paper["authors"],
                journal_ref=paper["journal_ref"],
                doi=paper["doi"],
                categories=paper["categories"]
            )
            papers_to_insert.append(paper_entity)
            
            for chunk in paper["chunks"]:
                embedding_entity = CsEmbeddingEntity(
                    doc_id=doc_id,
                    chunk_text=chunk["chunk_text"],
                    embedding=chunk["embedding"],
                    chunk_index=chunk["chunk_index"]
                )
                embeddings_to_insert.append(embedding_entity)
                
        # 4. 벌크 저장 실행
        if papers_to_insert:
            print(f"  > {CYAN}신규 데이터 적재:{RESET} 논문 {len(papers_to_insert):,}건, 임베딩 청크 {len(embeddings_to_insert):,}건")
            
            # 부모(paper_cs) 테이블 flush 후 자식(cs_embeddings) 테이블을 추가하여 FK 제약 조건 충족
            session.add_all(papers_to_insert)
            await session.flush()
            
            session.add_all(embeddings_to_insert)
            await session.commit()
            print(f"  {GREEN}✓ DB 적재 완료!{RESET} (소요 시간: {time.time() - start_time:.1f}초)")
        else:
            print(f"  {YELLOW}✓ 추가할 신규 데이터가 없습니다. (적재 생략){RESET}")


async def main() -> None:
    """CS.NE 도메인 논문을 수집하고 청킹한 후 OpenAI 임베딩 API를 통해 벡터화하여 저장 및 DB 업로드를 진행하는 메인 함수."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(f"\n{RED}{BOLD}[Error] OPENAI_API_KEY is not set in environment or .env file.{RESET}")
        print("Please edit the .env file in the backend directory first.")
        return

    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=api_key)

    # 출력 디렉토리 확인 및 생성
    os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)

    if not os.path.exists(DATA_PATH):
        print(f"\n{RED}{BOLD}[Error] Source data not found: {DATA_PATH}{RESET}")
        return

    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}{GREEN}🚀 [START] cs.NE 학술 논문 {TARGET_COUNT}건 임베딩 & DB 적재 파이프라인{RESET}")
    print(f"{BOLD}======================================================================{RESET}")
    
    print(f"\n{BOLD}[1/4] 📄 arxiv-metadata-oai-snapshot.json 로드 및 청킹 시작...{RESET}")
    
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
                    print(f"  > 수집 완료: {len(collected_papers):,} / {TARGET_COUNT:,} 건")

            except Exception as e:
                pass

    print(f"  {GREEN}✓ 데이터 수집 완료!{RESET} 총 {len(collected_papers):,}건 논문 수집 (소요 시간: {time.time() - start_time:.1f}초)")

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
    
    print(f"\n{BOLD}[2/4] 🧠 OpenAI 배치 임베딩 연산 시작...{RESET}")
    print(f"  > 총 청크 수: {total_chunks:,}개 (모델: {MODEL_NAME}, 3,072차원)")

    # 배치 단위 임베딩 연산 진행
    start_embed = time.time()
    embeddings = []
    
    # BATCH_SIZE 단위 루프
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = all_chunks_to_encode[i:i+BATCH_SIZE]
        texts = [item["text"] for item in batch]
        
        # API 호출 및 재시도 로직 (RateLimitError 발생 시 지수 백오프 적용)
        retries = 5
        delay = 5  # 초기 대기 시간 (초)
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
            except RateLimitError as e:
                print(f"\n{YELLOW}⚠️ Rate Limit Exceeded (HTTP 429): {e}. Retrying in {delay} seconds... ({retries} retries left){RESET}")
                time.sleep(delay)
                delay *= 2  # 대기 시간 2배 증가 (지수 백오프)
                retries -= 1
            except Exception as e:
                print(f"\n{RED}⚠️ OpenAI API Error: {e}. Retrying in {delay} seconds... ({retries} retries left){RESET}")
                time.sleep(delay)
                retries -= 1
        else:
            print(f"\n{RED}❌ Failed to get embeddings for chunk batch {i} to {i+BATCH_SIZE}. Exiting.{RESET}")
            return
            
        if (i + BATCH_SIZE) % 500 == 0 or (i + BATCH_SIZE) >= total_chunks:
            current_processed = min(i + BATCH_SIZE, total_chunks)
            elapsed = time.time() - start_embed
            rate = current_processed / elapsed
            print(f"  > 임베딩 진행: {current_processed:,} / {total_chunks:,} chunks... (속도: {rate:.1f} items/sec)")

    print(f"  {GREEN}✓ 임베딩 연산 완료!{RESET} (소요 시간: {time.time() - start_embed:.1f}초)")

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
    print(f"\n{BOLD}[3/4] 💾 로컬 캐시 파일 저장 중...{RESET}")
    print(f"  > 파일 경로: {OUTPUT_FILE_PATH}")
    with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as outfile:
        for paper in collected_papers:
            # chunk_texts 키 제거 후 chunks (벡터 포함) 리스트 저장
            if "chunk_texts" in paper:
                del paper["chunk_texts"]
            outfile.write(json.dumps(paper, ensure_ascii=False) + "\n")
    print(f"  {GREEN}✓ 로컬 캐시 파일 저장 완료!{RESET}")

    # 5. DB 저장
    await save_to_db(collected_papers)

    total_elapsed = time.time() - start_time
    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}{GREEN}🎉 [SUCCESS] RAG 임베딩 및 DB 업로드 완료!{RESET}")
    print(f"  - 총 수집 논문: {len(collected_papers):,} 건")
    print(f"  - 총 생성 청크: {total_chunks:,} 개")
    print(f"  - 총 소요 시간: {total_elapsed:.2f} 초")
    print(f"{BOLD}======================================================================{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
