import os
import json
import time
import sys
import asyncio
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
from sqlalchemy.ext.asyncio import AsyncSession

# 데이터 경로 및 출력 경로 설정 (스크립트 위치 기준 4레벨 위가 workspace root)
ROOT_DIR = os.path.abspath(os.path.join(script_dir, "../../../.."))
INPUT_FILE_PATH = os.path.abspath(os.path.join(ROOT_DIR, "data/raw/archive/local_embeddings_output.jsonl"))

BATCH_SIZE = 100  # 데이터베이스 벌크 인서트 배치 단위


async def process_and_save_batch(session: AsyncSession, papers: list[dict]) -> tuple[int, int]:
    """한 배치의 논문 데이터를 검증하고 DB에 적재합니다.

    Args:
        session (AsyncSession): SQLAlchemy 비동기 세션 객체.
        papers (list[dict]): 검증 및 저장할 논문 데이터 리스트.

    Returns:
        tuple[int, int]: (신규 추가된 논문 수, 신규 추가된 임베딩 청크 수)
    """
    doc_ids = [paper["doc_id"] for paper in papers]
    
    # 이미 존재하는 doc_id들 조회 (중복 데이터 삽입 방지)
    existing_doc_ids = set()
    stmt = select(PaperCsEntity.doc_id).where(PaperCsEntity.doc_id.in_(doc_ids))
    result = await session.execute(stmt)
    for doc_id in result.scalars():
        existing_doc_ids.add(doc_id)
        
    papers_to_insert = []
    embeddings_to_insert = []
    
    for paper in papers:
        doc_id = paper["doc_id"]
        if doc_id in existing_doc_ids:
            continue
            
        paper_entity = PaperCsEntity(
            doc_id=doc_id,
            title=paper["title"],
            abstract=paper["abstract"],
            authors=paper["authors"],
            journal_ref=paper.get("journal_ref", ""),
            doi=paper.get("doi", ""),
            categories=paper["categories"]
        )
        papers_to_insert.append(paper_entity)
        
        # chunks 리스트에서 각 청크별 엔티티 생성
        for chunk in paper.get("chunks", []):
            embedding_entity = CsEmbeddingEntity(
                doc_id=doc_id,
                chunk_text=chunk["chunk_text"],
                embedding=chunk["embedding"],
                chunk_index=chunk["chunk_index"]
            )
            embeddings_to_insert.append(embedding_entity)
            
    if papers_to_insert:
        # 부모(paper_cs) 테이블 flush 후 자식(cs_embeddings) 테이블을 추가하여 FK 제약 조건 충족
        session.add_all(papers_to_insert)
        await session.flush()
        
        session.add_all(embeddings_to_insert)
        await session.commit()
        return len(papers_to_insert), len(embeddings_to_insert)
    
    return 0, 0


async def main() -> None:
    """로컬 캐시 파일에서 임베딩 데이터를 읽고 비동기로 DB 적재를 진행하는 메인 함수."""
    if not os.path.exists(INPUT_FILE_PATH):
        print(f"\n{RED}{BOLD}[Error] Embedding file not found: {INPUT_FILE_PATH}{RESET}")
        return

    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}{GREEN}🚀 [START] 로컬 임베딩 캐시 ({INPUT_FILE_PATH}) DB 적재 파이프라인{RESET}")
    print(f"{BOLD}======================================================================{RESET}")
    
    start_time = time.time()
    
    total_processed_papers = 0
    total_inserted_papers = 0
    total_inserted_chunks = 0
    
    # 데이터베이스 세션을 열어 배치별로 처리
    async with session_maker() as session:
        batch_papers = []
        
        with open(INPUT_FILE_PATH, "r", encoding="utf-8") as infile:
            for line in infile:
                if not line.strip():
                    continue
                try:
                    paper = json.loads(line)
                    batch_papers.append(paper)
                except Exception as e:
                    print(f"\n{YELLOW}⚠️ JSON 파싱 실패: {e}{RESET}")
                    continue
                
                # 배치 사이즈에 도달하면 DB에 저장
                if len(batch_papers) >= BATCH_SIZE:
                    inserted_p, inserted_c = await process_and_save_batch(session, batch_papers)
                    total_inserted_papers += inserted_p
                    total_inserted_chunks += inserted_c
                    total_processed_papers += len(batch_papers)
                    
                    print(f"  > 누적 읽은 논문: {total_processed_papers:,} 건 | 신규 DB 적재: {total_inserted_papers:,} 건 (청크: {total_inserted_chunks:,} 개)")
                    batch_papers = []
            
            # 남은 마지막 배치 처리
            if batch_papers:
                inserted_p, inserted_c = await process_and_save_batch(session, batch_papers)
                total_inserted_papers += inserted_p
                total_inserted_chunks += inserted_c
                total_processed_papers += len(batch_papers)
                print(f"  > 최종 누적 읽은 논문: {total_processed_papers:,} 건 | 최종 DB 적재: {total_inserted_papers:,} 건 (청크: {total_inserted_chunks:,} 개)")
                
    total_elapsed = time.time() - start_time
    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}{GREEN}🎉 [SUCCESS] 로컬 임베딩 DB 적재 완료!{RESET}")
    print(f"  - 총 읽은 논문: {total_processed_papers:,} 건")
    print(f"  - 신규 DB 적재 논문: {total_inserted_papers:,} 건")
    print(f"  - 신규 DB 적재 청크: {total_inserted_chunks:,} 개")
    print(f"  - 총 소요 시간: {total_elapsed:.2f} 초")
    print(f"{BOLD}======================================================================{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
