import logging
from typing import Annotated

from fastapi import Depends
from langchain.agents import create_agent
from langchain.tools import tool

from api.common.config import settings

logger = logging.getLogger(__name__)


###############################################################
# 도구 정의 (Config 없이 독립적으로 동작하는 RAG 검색 도구)
###############################################################

@tool
async def search_cs_papers(query: str, k: int = 3) -> str:
    """
    컴퓨터 과학(Neural and Evolutionary Computing, cs.NE 카테고리) 관련 학술 논문 데이터베이스에서 검색을 수행합니다.
    인공신경망, 진화 컴퓨팅, 유전 알고리즘, 신경망 학습 다이내믹스 등의 개념에 대한 질문에 대답하거나 참고 자료가 필요할 때 이 툴을 사용하세요.

    Args:
        query: 검색할 질문이나 키워드 (예: "neural network", "genetic algorithm", "evolutionary strategy")
        k: 검색할 논문 개수 (기본값: 3)

    Returns:
        str: 검색된 논문 제목, 요약, 메타데이터
    """
    from langchain.embeddings import init_embeddings
    from langchain_postgres import PGVector
    from api.v1.cs.vectorstore_conf import COLLECTION_NAME, CONNECTION, EMBED_MODEL

    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name=COLLECTION_NAME,
        connection=CONNECTION,
        async_mode=True,
    )
    results = await vectorstore.asimilarity_search_with_score(query, k=k)

    if not results:
        return f"cs.NE 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."

    output_lines = [f"검색 결과: '{query}' (cs.NE 논문)\n"]
    output_lines.append("=" * 80 + "\n")
    for idx, (doc, score) in enumerate(results, 1):
        similarity = 1.0 - float(score)
        output_lines.append(f"\n[논문 {idx}] (유사도: {similarity:.4f})")
        output_lines.append(f"제목: {doc.metadata.get('title', '')}")
        output_lines.append(f"arXiv ID: {doc.metadata.get('arxiv_id') or doc.metadata.get('doc_id') or ''}")
        output_lines.append(f"\n내용:\n{doc.page_content}\n")
        output_lines.append("-" * 80)

    return "\n".join(output_lines)


###############################################################
# Agent 클래스 정의
###############################################################

class CSRAGAgent:
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.CSRAGAgent")
        self.system_prompt = """
        You are an expert in Computer Science, specifically in Neural and Evolutionary Computing (cs.NE).

        Available tools:
        **search_cs_papers**: Search cs.NE papers

        Guidelines:
        - Use the search_cs_papers tool to find relevant papers for the user's question.
        - Provide accurate and detailed answers based on the retrieved papers.
        - Always cite paper titles and arXiv IDs as sources.
        - If the information is not found in the papers, say so — do not speculate.
        - Explain technical computer science terms in an accessible way.

        CRITICAL — LANGUAGE RULE:
        - Detect the language of the user's question.
        - Always respond in the SAME language as the user's question.
        - If the user writes in English → respond in English.
        - If the user writes in Korean → respond in Korean.
        - Never switch languages regardless of the language used in the retrieved papers or this prompt.
        """
        self.agent = create_agent(
            model=model,
            tools=[search_cs_papers]
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
CSRAGAgentDep = Annotated[CSRAGAgent, Depends(CSRAGAgent)]
