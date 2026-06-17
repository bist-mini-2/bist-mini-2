import logging
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select
from api.database.config.dbsession import OrmSessionDep
from api.v1.cs.entity import CsEmbeddingEntity, PaperCsEntity


class CsDao:
    """CS 논문 메타데이터 및 임베딩 테이블에 관한 데이터 액세스 객체(DAO)입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        self.logger = logging.getLogger(f"{__name__}.CsDao")
        self.orm_session = orm_session

    async def select_similar_chunks(
        self, query_vector: list[float], top_k: int
    ) -> list[dict]:
        """임베딩 벡터를 기준으로 코사인 유사도가 가장 높은 상위 K개의 논문 청크를 딕셔너리 리스트로 조회합니다.

        Args:
            query_vector (list[float]): 질의어 임베딩 벡터.
            top_k (int): 반환할 상위 결과 개수.

        Returns:
            list[dict]: doc_id, title, text_chunk, score 필드를 가진 딕셔너리 리스트.
        """
        self.logger.info("select_similar_chunks 실행")
        distance_expr = CsEmbeddingEntity.embedding.cosine_distance(query_vector)
        score_expr = (1.0 - distance_expr).label("score")

        stmt = (
            select(
                CsEmbeddingEntity.doc_id,
                PaperCsEntity.title,
                CsEmbeddingEntity.text_chunk,
                score_expr
            )
            .join(PaperCsEntity, CsEmbeddingEntity.doc_id == PaperCsEntity.doc_id)
            .order_by(distance_expr.asc())
            .limit(top_k)
        )

        query_result = await self.orm_session.execute(stmt)
        return [dict(row) for row in query_result.mappings().all()]


CsDaoDep = Annotated[CsDao, Depends(CsDao)]
