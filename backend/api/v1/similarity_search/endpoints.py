"""유사도 검색(Biotechnology, Computer Science, Astronomy) HTTP API 엔드포인트를 정의하는 모듈입니다."""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, status

from api.common.auth import LoginCheckDep
from api.database.config.dto_base import SuccessResponse
from api.common.rag_pipeline import common_rag_pipeline
from api.v1.similarity_search.models import (
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    SimilaritySearchResultItem,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/similarity-search", tags=["Similarity Search"])


@router.post(
    "/bio",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="생명공학(Biotechnology) RAG 유사도 검색"
)
async def search_bio(
    payload: SimilaritySearchRequest,
    current_user: LoginCheckDep
) -> SuccessResponse:
    """생명공학 논문 데이터베이스에서 유사한 텍스트 청크를 검색합니다.

    Args:
        payload (SimilaritySearchRequest): 질의어 및 반환 개수가 담긴 요청 DTO.
        current_user (LoginCheckDep): 인증 완료된 사용자의 페이로드 정보.

    Returns:
        SuccessResponse: 검색된 유사 문서 목록을 담은 성공 응답 객체.
    """
    logger.info(f"Bio similarity search requested by user: {current_user['sub']}, query: '{payload.query}'")
    results = await common_rag_pipeline.similarity_search(
        domain="bio",
        query=payload.query,
        k=payload.top_k
    )
    formatted_results = [
        SimilaritySearchResultItem(
            doc_id=r["doc_id"],
            title=r["title"],
            text_chunk=r["text_chunk"],
            score=r["score"]
        )
        for r in results
    ]
    response_data = SimilaritySearchResponse(results=formatted_results)
    return SuccessResponse(data=response_data)


@router.post(
    "/cs",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="컴퓨터 과학(Computer Science) RAG 유사도 검색"
)
async def search_cs(
    payload: SimilaritySearchRequest,
    current_user: LoginCheckDep
) -> SuccessResponse:
    """컴퓨터 과학 논문 데이터베이스에서 유사한 텍스트 청크를 검색합니다.

    Args:
        payload (SimilaritySearchRequest): 질의어 및 반환 개수가 담긴 요청 DTO.
        current_user (LoginCheckDep): 인증 완료된 사용자의 페이로드 정보.

    Returns:
        SuccessResponse: 검색된 유사 문서 목록을 담은 성공 응답 객체.
    """
    logger.info(f"CS similarity search requested by user: {current_user['sub']}, query: '{payload.query}'")
    results = await common_rag_pipeline.similarity_search(
        domain="cs",
        query=payload.query,
        k=payload.top_k
    )
    formatted_results = [
        SimilaritySearchResultItem(
            doc_id=r["doc_id"],
            title=r["title"],
            text_chunk=r["text_chunk"],
            score=r["score"]
        )
        for r in results
    ]
    response_data = SimilaritySearchResponse(results=formatted_results)
    return SuccessResponse(data=response_data)


@router.post(
    "/astronomy",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="천문학(Astronomy) RAG 유사도 검색"
)
async def search_astronomy(
    payload: SimilaritySearchRequest,
    current_user: LoginCheckDep
) -> SuccessResponse:
    """천문학 논문 데이터베이스에서 유사한 텍스트 청크를 검색합니다.

    Args:
        payload (SimilaritySearchRequest): 질의어 및 반환 개수가 담긴 요청 DTO.
        current_user (LoginCheckDep): 인증 완료된 사용자의 페이로드 정보.

    Returns:
        SuccessResponse: 검색된 유사 문서 목록을 담은 성공 응답 객체.
    """
    logger.info(f"Astronomy similarity search requested by user: {current_user['sub']}, query: '{payload.query}'")
    results = await common_rag_pipeline.similarity_search(
        domain="astronomy",
        query=payload.query,
        k=payload.top_k
    )
    formatted_results = [
        SimilaritySearchResultItem(
            doc_id=r["doc_id"],
            title=r["title"],
            text_chunk=r["text_chunk"],
            score=r["score"]
        )
        for r in results
    ]
    response_data = SimilaritySearchResponse(results=formatted_results)
    return SuccessResponse(data=response_data)
