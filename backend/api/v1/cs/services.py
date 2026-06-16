import logging
from typing import Annotated
from fastapi import Depends
from api.v1.cs.dao import CsDaoDep
from api.v1.cs.embedding import embedding_helper
from api.v1.cs.models import SimilaritySearchResult, SimilaritySearchResponse


class CsService:
    """컴퓨터 과학(CS) 도메인의 RAG 유사도 검색 및 임베딩 처리 비즈니스 로직을 처리합니다."""

    def __init__(self, cs_dao: CsDaoDep) -> None:
        self.logger = logging.getLogger(f"{__name__}.CsService")
        self.cs_dao = cs_dao

    async def search_similar_papers(self, query: str, top_k: int) -> SimilaritySearchResponse:
        """질의어(Query)를 임베딩으로 변환한 뒤, 유사도가 높은 상위 논문 청크 목록을 검색합니다.

        Args:
            query (str): 사용자의 질의 텍스트.
            top_k (int): 반환할 상위 결과 개수.

        Returns:
            SimilaritySearchResponse: 매칭된 유사 청크 목록을 포함한 DTO 응답 객체.
        """
        self.logger.info("search_similar_papers 실행")
        # 1. 쿼리 텍스트 임베딩 생성 (싱글톤 helper 활용)
        query_vector = embedding_helper.encode(query)

        # 2. DAO를 통해 유사도 높은 청크들 조회
        raw_results = await self.cs_dao.select_similar_chunks(query_vector, top_k)

        # 3. DTO 리스트로 결과 변환
        results_list = []
        for doc_id, title, chunk_text, score in raw_results:
            results_list.append(
                SimilaritySearchResult(
                    doc_id=doc_id,
                    title=title,
                    text_chunk=chunk_text,
                    score=score
                )
            )

        return SimilaritySearchResponse(results=results_list)


CsServiceDep = Annotated[CsService, Depends(CsService)]
