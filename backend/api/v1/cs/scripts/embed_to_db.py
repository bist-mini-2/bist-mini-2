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
# 스크립트 파일 위치 기준 backend 디렉토리 (4레벨 위)
backend_dir_from_script = os.path.abspath(os.path.join(script_dir, "../../../.."))
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

# 데이터 경로 및 출력 경로 설정 (스크립트 위치 기준 5레벨 위가 workspace root)
ROOT_DIR = os.path.abspath(os.path.join(script_dir, "../../../../.."))
INPUT_FILE_PATH = os.path.abspath(os.path.join(ROOT_DIR, "data/raw/archive/local_embeddings_output.jsonl"))

BATCH_SIZE = 100  # 데이터베이스 벌크 인서트 배치 단위


async def process_and_insert() -> None:
    """로컬 jsonl 파일에서 임베딩 완료된 데이터를 읽어 pgvector 데이터베이스로 벌크 적재하는 비동기 처리 함수."""
    start_time = time.time()
    
    if not os.path.exists(INPUT_FILE_PATH):
        print(f"{RED}[Error] Local cache file not found: {INPUT_FILE_PATH}{RESET}")
        return
        
    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}{GREEN}🚀 [START] 로컬 캐시 데이터 pgvector 데이터베이스 벌크 적재 ({INPUT_FILE_PATH}){RESET}")
    print(f"{BOLD}======================================================================{RESET}")

    collected_papers = []
    
    # 1. 파일 데이터 로드
    with open(INPUT_FILE_PATH, "r", encoding="utf-8") as infile:
        for line in infile:
            if line.strip():
                collected_papers.append(json.loads(line))
                
    total_papers = len(collected_papers)
    print(f"  > 로드된 캐시 논문 개수: {total_papers:,}건")
    
    if total_papers == 0:
        print(f"  {YELLOW}✓ 적재할 데이터가 존재하지 않습니다.{RESET}")
        return

    async with session_maker() as session:
        # 2. 데이터베이스 내 이미 존재하는 doc_id들 조회 (중복 데이터 삽입 방지)
        doc_ids = [paper["doc_id"] for paper in collected_papers]
        existing_doc_ids = set()
        
        # SQL IN 연산 최대 바인딩 한계(65535) 및 성능 상의 이유로 1000건 단위 분할 조회
        for i in range(0, len(doc_ids), 1000):
            batch_ids = doc_ids[i:i+1000]
            stmt = select(PaperCsEntity.doc_id).where(PaperCsEntity.doc_id.in_(batch_ids))
            result = await session.execute(stmt)
            for doc_id in result.scalars():
                existing_doc_ids.add(doc_id)
                
        print(f"  > {YELLOW}DB에 이미 존재하는 CS 논문:{RESET} {len(existing_doc_ids):,}건 (중복 스킵 처리 예정)")
        
        papers_to_insert = []
        embeddings_to_insert = []
        
        # 3. 데이터베이스 적재 객체 리스트 빌드
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
                    text_chunk=chunk["chunk_text"],
                    embedding=chunk["embedding"],
                    chunk_index=chunk["chunk_index"]
                )
                embeddings_to_insert.append(embedding_entity)
                
        # 4. 벌크 저장 실행
        if papers_to_insert:
            print(f"  > {CYAN}신규 데이터 적재 시작:{RESET} 논문 {len(papers_to_insert):,}건, 임베딩 청크 {len(embeddings_to_insert):,}개")
            
            # 부모(paper_cs) 테이블 벌크 인서트 진행
            session.add_all(papers_to_insert)
            # flush를 수행하여 DB 제약 조건상 FK 대상 PK(doc_id)를 미리 반영시킴
            await session.flush()
            
            # 자식(cs_embeddings) 테이블 벌크 인서트 진행
            # 1000개 단위로 세션 분할 add 및 flush 진행하여 메모리 관리 및 네트워크 부하 감소
            for i in range(0, len(embeddings_to_insert), 1000):
                batch_embeddings = embeddings_to_insert[i:i+1000]
                session.add_all(batch_embeddings)
                await session.flush()
                
            await session.commit()
            
            total_elapsed = time.time() - start_time
            print(f"\n{BOLD}======================================================================{RESET}")
            print(f"{BOLD}{GREEN}🎉 [SUCCESS] pgvector 데이터베이스 벌크 적재 완료!{RESET}")
            print(f"  - 적재 완료 논문: {len(papers_to_insert):,} 건")
            print(f"  - 적재 완료 청크: {len(embeddings_to_insert):,} 개")
            print(f"  - 총 소요 시간: {total_elapsed:.2f} 초")
            print(f"{BOLD}======================================================================{RESET}")
        else:
            print(f"  {YELLOW}✓ 추가할 신규 데이터가 없습니다. (적재 생략){RESET}")


if __name__ == "__main__":
    asyncio.run(process_and_insert())
