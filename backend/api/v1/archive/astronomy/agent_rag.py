import logging
from typing import Annotated

from fastapi import Depends
from langchain.agents import create_agent
from langchain.embeddings import init_embeddings
from langchain.tools import tool
from langchain_postgres import PGVector

from api.common.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "astro-ph-EP"
CONNECTION = settings.PGVECTOR_URL
EMBED_MODEL = "openai:text-embedding-3-large"


###############################################################
# 도구 정의
###############################################################

@tool
async def search_astronomy_papers(query: str, k: int = 3) -> str:
    """
    지구 및 행성 천체물리학(astro-ph.EP) 논문에서 관련 내용을 검색하는 도구입니다.

    Args:
        query: 검색할 질문이나 키워드 (예: "exoplanet atmosphere", "Mars geology", "planetary formation")
        k: 검색할 논문 개수 (기본값: 3)

    Returns:
        str: 검색된 논문 제목, 요약, 메타데이터
    """
    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name=COLLECTION_NAME,
        connection=CONNECTION,
        async_mode=True,
    )
    results = await vectorstore.asimilarity_search_with_score(query, k=k)
    if not results:
        return f"astro-ph.EP 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."

    output_lines = [f"검색 결과: '{query}' (astro-ph.EP 논문)\n"]
    output_lines.append("=" * 80 + "\n")
    for idx, (doc, score) in enumerate(results, 1):
        output_lines.append(f"\n[논문 {idx}] (유사도: {score:.4f})")
        if doc.metadata:
            if "title" in doc.metadata:
                output_lines.append(f"제목: {doc.metadata['title']}")
            if "arxiv_id" in doc.metadata:
                output_lines.append(f"arXiv ID: {doc.metadata['arxiv_id']}")
            if "categories" in doc.metadata:
                output_lines.append(f"카테고리: {doc.metadata['categories']}")
            if "update_date" in doc.metadata:
                output_lines.append(f"업데이트: {doc.metadata['update_date']}")
        output_lines.append(f"\n내용:\n{doc.page_content}\n")
        output_lines.append("-" * 80)

    return "\n".join(output_lines)


###############################################################
# Agent 클래스 정의
###############################################################

class AstronomyRAGAgent:
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.AstronomyRAGAgent")
        self.system_prompt = """
        You are an expert in Earth and Planetary Astrophysics (astro-ph.EP).

        Available tools:
        **search_astronomy_papers**: Search astro-ph.EP papers

        Guidelines:
        - Use the search_astronomy_papers tool to find relevant papers for the user's question.
        - Provide accurate and detailed answers based on the retrieved papers.
        - Always cite paper titles and arXiv IDs as sources.
        - If the information is not found in the papers, say so — do not speculate.
        - Explain technical astronomy terms in an accessible way.

        CRITICAL — LANGUAGE RULE:
        - Detect the language of the user's question.
        - Always respond in the SAME language as the user's question.
        - If the user writes in English → respond in English.
        - If the user writes in Korean → respond in Korean.
        - Never switch languages regardless of the language used in the retrieved papers or this prompt.
        """
        self.agent = create_agent(
            model=model,
            tools=[search_astronomy_papers]
        )

    async def run(self, question: str) -> str:
        result = await self.agent.ainvoke(
            {"messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question}
            ]}
        )
        return result["messages"][-1].content


# ============================================================
# 의존성 타입 별칭 정의
# ============================================================
AstronomyRAGAgentDep = Annotated[AstronomyRAGAgent, Depends(AstronomyRAGAgent)]
