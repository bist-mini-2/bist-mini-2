import logging
from datetime import datetime          # ← 추가
from zoneinfo import ZoneInfo

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain_community.tools.tavily_search import TavilySearchResults
from api.common.config import settings

logger = logging.getLogger(__name__)

EMBED_MODEL = "openai:text-embedding-3-large"
CONNECTION = settings.PGVECTOR_URL

DOMAIN_COLLECTIONS = {
    "bio": "bio_embeddings",
    "cs": "cs_embeddings",
    "astronomy": "astronomy_embeddings"
}


@tool
async def search_web(
    query: str,
    runtime: ToolRuntime,
    max_results: int = 4
) -> Command:
    """논문 데이터베이스(arXiv)에서 적절한 자료를 찾지 못했을 때 웹에서 정보를 검색하는 도구.
    최신 동향, 일반 상식, arXiv 범위 밖 주제 등 논문 검색으로 답할 수 없을 때만 사용하세요.
    """
    logger.info(f"search_web('{query}') 호출")

    # Tavily 호출은 어떤 이유로든 실패할 수 있으므로, 예외가 스트림을 죽이지 않도록 방어한다.
    try:
        tavily = TavilySearchResults(max_results=max_results, search_depth="basic")
        results = await tavily.ainvoke(query)
    except Exception as e:
        logger.error(f"search_web 실패: {type(e).__name__}: {e}")
        msg = f"웹 검색에 실패했습니다({type(e).__name__}). 웹 정보 없이 답변하거나, 모른다고 안내하세요."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    # 일부 버전은 list[dict]가 아니라 문자열을 반환할 수 있으므로 방어한다.
    if isinstance(results, str):
        return Command(update={
            "messages": [ToolMessage(content=results, tool_call_id=runtime.tool_call_id)],
        })

    if not results:
        msg = f"웹에서 '{query}'에 대한 결과를 찾지 못했습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    output_lines = [f"웹 검색 결과: '{query}'\n", "=" * 80]
    web_sources = []
    for idx, r in enumerate(results, 1):
        if not isinstance(r, dict):
            continue
        url = r.get("url", "")
        title = r.get("title", "") or url
        content = r.get("content")
        if not isinstance(content, str):
            content = ""

        output_lines.append(f"\n[{idx}] {title}")
        output_lines.append(f"URL: {url}")
        output_lines.append(f"내용:\n{content}\n")
        output_lines.append("-" * 80)

        snippet = " ".join(content.split())
        if len(snippet) > 200:
            snippet = snippet[:200].rstrip() + "…"
        web_sources.append({"url": url, "title": title, "summary": snippet})

    tool_text = "\n".join(output_lines)
    return Command(update={
        "messages": [ToolMessage(content=tool_text, tool_call_id=runtime.tool_call_id)],
        "web_sources": web_sources,
    })
    

@tool
def get_current_datetime() -> str:
    """현재 날짜와 시간을 한국 시간(Asia/Seoul) 기준 ISO-8601 문자열로 반환합니다.
    '오늘', '지금', '현재', '최근' 등 현재 시점이 필요한 질문에 사용하세요.

    Returns:
        str: ISO-8601 형식의 한국 시간 문자열 (예: 2026-06-23T14:30:00+09:00)
    """
    now = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    logger.info(f"get_current_datetime() 호출 → {now}")
    return now