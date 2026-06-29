import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.common.entities import PaperFullTextCacheEntity
from api.common.paper_crawler import paper_crawler

logger = logging.getLogger(__name__)


class PaperCacheService:
    """논문 본문 데이터의 조회 및 크롤링 캐싱을 조율하는 서비스 클래스입니다."""

    async def get_paper_full_text(
        self, db: AsyncSession, paper_id: str, domain: str
    ) -> str:
        """논문 ID를 기반으로 캐시 테이블을 조회하며, 없을 경우 크롤링하여 저장 후 반환합니다.

        Args:
            db (AsyncSession): SQLAlchemy 비동기 데이터베이스 세션.
            paper_id (str): 대상 논문 ID (arXiv ID 등).
            domain (str): 학술 분야 도메인 구분 ('bio', 'cs', 'astronomy').

        Returns:
            str: 논문의 전체 본문 텍스트.

        Raises:
            Exception: 크롤링 및 텍스트 추출 최종 실패 시 예외가 전파됩니다.
        """
        clean_id = paper_id.strip()
        logger.info(f"논문 본문 요청: ID='{clean_id}', Domain='{domain}'")

        # 1. DB 캐시 조회 (Cache Hit 확인)
        query = select(PaperFullTextCacheEntity).where(PaperFullTextCacheEntity.paper_id == clean_id)
        result = await db.execute(query)
        cached_paper = result.scalar_one_or_none()

        if cached_paper:
            logger.info(f"캐시 히트(Cache Hit) 성공: ID='{clean_id}'")
            return cached_paper.full_text

        # 2. 캐시 미스(Cache Miss) 시 온디맨드 크롤링 수행
        logger.info(f"캐시 미스(Cache Miss): ID='{clean_id}' 크롤링을 수행합니다.")
        try:
            crawled = await paper_crawler.crawl_paper(clean_id)
        except Exception as e:
            logger.error(f"논문 ID '{clean_id}' 크롤링 중 예외 발생: {e}")
            raise RuntimeError(f"논문을 크롤링하지 못했습니다 (ID={clean_id}): {e}") from e

        full_text = crawled["full_text"]
        new_cache = PaperFullTextCacheEntity(
            paper_id=clean_id,
            title=crawled.get("title") or f"arXiv Paper {clean_id}",
            full_text=full_text,
            domain=domain,
            source=crawled["source"],
        )

        try:
            db.add(new_cache)
            await db.commit()
            logger.info(f"신규 논문 본문 적재 완료 및 캐싱 성공: ID='{clean_id}'")
        except Exception as e:
            # 트랜잭션 에러 발생 시 롤백 수행
            await db.rollback()
            logger.warning(f"논문 본문 DB 적재 실패 (롤백 처리됨, 텍스트는 임시 반환): {e}")

        return full_text


# 싱글톤 인스턴스
paper_cache_service = PaperCacheService()
