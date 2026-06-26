import asyncio
import logging
from sqlalchemy import select
from api.database.config.dbsession import session_maker
from api.common.entities import PaperFullTextCacheEntity
from api.common.rag_pipeline import common_rag_pipeline

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_paper_fulltext_rag")

async def verify_stage2_rag():
    logger.info("=== STARTING STAGE-2 FULL-TEXT RAG VERIFICATION ===")
    
    paper_id = "2006.11367"
    domain = "cs"
    query = "attention mechanism transformers"
    
    async with session_maker() as db:
        # 1. 테스트 준비: 기존 레코드의 is_vectorized를 False로 재설정하여 온디맨드 빌드 시뮬레이션
        logger.info(f"1. Resetting 'is_vectorized' to False for paper {paper_id} in DB...")
        query_db = select(PaperFullTextCacheEntity).where(PaperFullTextCacheEntity.paper_id == paper_id)
        res = await db.execute(query_db)
        paper_entity = res.scalar_one_or_none()
        
        if not paper_entity:
            # 캐시가 없는 경우, 임시로 데이터 로드하여 캐시 생성
            from api.common.paper_cache_service import paper_cache_service
            logger.info(f"Paper {paper_id} not found in DB cache. Loading/crawling it first...")
            await paper_cache_service.get_paper_full_text(db, paper_id, domain)
            
            res = await db.execute(query_db)
            paper_entity = res.scalar_one_or_none()
            
        if paper_entity:
            paper_entity.is_vectorized = False
            db.add(paper_entity)
            await db.commit()
            logger.info(f"Successfully reset is_vectorized to False.")
        else:
            logger.error(f"Failed to find or create paper record for {paper_id}")
            return

        # 2. 1회차 호출 (온디맨드 벡터화 수행 기대)
        logger.info("--- 2. Call 1 (On-demand Vectorization Expected) ---")
        context_1 = await common_rag_pipeline.get_full_text_context(
            db=db,
            paper_ids=[paper_id],
            query=query,
            domain=domain,
            k=3
        )
        
        logger.info(f"Call 1 Finished. Retrieved {len(context_1)} chunks.")
        for idx, chunk in enumerate(context_1, 1):
            logger.info(f"Chunk {idx} (Score: {chunk['score']:.4f}): {chunk['text_chunk'][:150]}...")
            
        # 3. DB 상태 검증: is_vectorized가 True로 업데이트 되었는지 확인
        logger.info("--- 3. Verifying database flag update ---")
        res = await db.execute(query_db)
        paper_entity_updated = res.scalar_one_or_none()
        
        assert paper_entity_updated is not None, "Paper entity must exist"
        logger.info(f"Database Flag 'is_vectorized' after Call 1: {paper_entity_updated.is_vectorized}")
        assert paper_entity_updated.is_vectorized is True, "is_vectorized flag should have updated to True!"

        # 4. 2회차 호출 (온디맨드 벡터화 생략 및 pgvector 즉시 검색 기대)
        logger.info("--- 4. Call 2 (Vectorization Bypass & Direct Search Expected) ---")
        context_2 = await common_rag_pipeline.get_full_text_context(
            db=db,
            paper_ids=[paper_id],
            query=query,
            domain=domain,
            k=3
        )
        
        logger.info(f"Call 2 Finished. Retrieved {len(context_2)} chunks.")
        for idx, chunk in enumerate(context_2, 1):
            logger.info(f"Chunk {idx} (Score: {chunk['score']:.4f}): {chunk['text_chunk'][:150]}...")

        # 두 결과의 반환 개수 및 첫 번째 청크 비교
        assert len(context_1) == len(context_2), "Chunk count should match"
        if len(context_1) > 0:
            assert context_1[0]["text_chunk"] == context_2[0]["text_chunk"], "First chunk text should match"
        
        logger.info("=== STAGE-2 RAG INTEGRATION VERIFICATION PASSED ===")

if __name__ == "__main__":
    asyncio.run(verify_stage2_rag())
