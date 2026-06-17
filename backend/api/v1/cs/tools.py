from typing import TYPE_CHECKING
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

if TYPE_CHECKING:
    from api.v1.cs.services import CsService


@tool
async def search_cs_papers(
    search_query: str,
    config: RunnableConfig
) -> str:
    """컴퓨터 과학(Neural and Evolutionary Computing, cs.NE 카테고리) 관련 학술 논문 데이터베이스에서 검색을 수행합니다.
    
    인공신경망, 진화 컴퓨팅, 유전 알고리즘, 신경망 학습 다이내믹스 등의 개념에 대한 질문에 대답하거나 참고 자료가 필요할 때 이 툴을 사용하세요.
    입력값(search_query)은 검색어 텍스트여야 합니다.

    Args:
        search_query (str): 검색할 질문이나 텍스트 키워드.
        config (RunnableConfig): 실행 설정 및 컨텍스트 정보.

    Returns:
        str: 검색 결과로 매칭된 상위 논문 청크 정보 문자열.
    """
    cs_service: "CsService | None" = config.get("configurable", {}).get("cs_service")
    if not cs_service:
        return "오류: cs_service가 설정에 제공되지 않았습니다."

    search_res = await cs_service.search_similar_papers(search_query, top_k=3)
    if not search_res:
        return "검색 결과가 데이터베이스에 존재하지 않습니다."
        
    formatted_results = []
    for idx, item in enumerate(search_res):
        formatted_results.append(
            f"[문서 {idx+1}]\n논문 ID: {item.doc_id}\n제목: {item.title}\n내용 청크: {item.text_chunk}\n"
        )
    return "\n".join(formatted_results)
