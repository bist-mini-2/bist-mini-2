import logging
from typing import Any, Dict, List
from langchain.embeddings import init_embeddings
from langchain_postgres import PGVector
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


class CommonRagPipeline:
    """공통 RAG 파이프라인 서비스 클래스입니다.

    3개 학술 도메인(bio, cs, astronomy)의 논문 임베딩 검색 및
    유사도 계산 처리를 단일 langchain pgvector 구조로 추상화하여 수행합니다.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.CommonRagPipeline")
        self._embeddings = None

    def get_embeddings(self):
        """임베딩 인스턴스를 지연 로딩으로 초기화 및 공유합니다."""
        if self._embeddings is None:
            self._embeddings = init_embeddings(model=EMBED_MODEL)
        return self._embeddings

    async def similarity_search(
        self,
        domain: str,
        query: str,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """지정된 도메인 컬렉션에서 질의어와 유사도가 높은 문서를 검색합니다.

        Args:
            domain (str): 학술 도메인 명 ('bio', 'cs', 'astronomy').
            query (str): 사용자의 질의 텍스트.
            k (int): 반환할 상위 문서의 개수. Defaults to 3.

        Returns:
            List[Dict[str, Any]]: 유사 논문 청크 정보 목록. 각 딕셔너리는 다음 키를 가집니다:
                - doc_id (str): 논문 고유 ID (arxiv_id).
                - title (str): 논문 제목.
                - text_chunk (str): 문서 텍스트 청크 본문.
                - score (float): 코사인 유사도 점수 (1.0 - distance).

        Raises:
            ValueError: 지원하지 않는 도메인이 입력된 경우.
        """
        if domain not in DOMAIN_COLLECTIONS:
            raise ValueError(f"지원하지 않는 도메인입니다: {domain}")

        collection_name = DOMAIN_COLLECTIONS[domain]
        self.logger.info(
            f"RAG Similarity Search: Domain='{domain}', Collection='{collection_name}', k={k}")

        vectorstore = PGVector(
            embeddings=self.get_embeddings(),
            collection_name=collection_name,
            connection=CONNECTION,
            async_mode=True,
        )

        results = await vectorstore.asimilarity_search_with_score(query, k=k)

        formatted_results = []
        for doc, score in results:
            meta = doc.metadata or {}
            arxiv_id = meta.get("arxiv_id") or meta.get("doc_id") or ""
            title = meta.get("title", "")

            # 코사인 유사도 계산 (1.0 - 거리 점수)
            similarity = round(1.0 - score, 4)

            formatted_results.append({
                "doc_id": arxiv_id,
                "title": title,
                "text_chunk": doc.page_content,
                "score": similarity
            })

        return formatted_results


# 싱글톤 인스턴스 생성
common_rag_pipeline = CommonRagPipeline()


@tool
async def search_bio_papers(
    query: str,
    runtime: ToolRuntime,
    k: int = 3
) -> Command:
    """생명공학·유전체학(q-bio.GN) 논문에서 관련 내용을 검색하는 도구.
    유전체학, 유전자 매핑, 시퀀싱 분석 등 생물학 질문에 사용.
    """
    results = await common_rag_pipeline.similarity_search("bio", query, k=k)

    if not results:
        msg = f"q-bio.GN 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    output_lines = [f"검색 결과: '{query}' (q-bio.GN 논문)\n", "=" * 80]
    sources = []
    for idx, r in enumerate(results, 1):
        arxiv_id = r["doc_id"]
        title = r["title"]
        score = r["score"]
        output_lines.append(f"\n[논문 {idx}] (유사도: {score:.4f})")
        output_lines.append(f"제목: {title}")
        output_lines.append(f"arXiv ID: {arxiv_id}")
        output_lines.append(f"\n내용:\n{r['text_chunk']}\n")
        output_lines.append("-" * 80)
        snippet = " ".join((r["text_chunk"] or "").split())
        if len(snippet) > 160:
            snippet = snippet[:160].rstrip() + "…"
        sources.append({"arxiv_id": arxiv_id, "title": title, "summary": snippet})

    tool_text = "\n".join(output_lines)
    return Command(update={
        "messages": [ToolMessage(content=tool_text, tool_call_id=runtime.tool_call_id)],
        "sources": sources,
    })


@tool
async def search_cs_papers(
    query: str,
    runtime: ToolRuntime,
    k: int = 3
) -> Command:
    """컴퓨터 과학(Neural and Evolutionary Computing, cs.NE 카테고리) 관련 학술 논문 데이터베이스에서 검색을 수행합니다.
    인공신경망, 진화 컴퓨팅, 유전 알고리즘, 신경망 학습 다이내믹스 등의 개념에 대한 질문에 대답하거나 참고 자료가 필요할 때 이 툴을 사용하세요.
    """
    results = await common_rag_pipeline.similarity_search("cs", query, k=k)

    if not results:
        msg = f"cs.NE 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    output_lines = [f"검색 결과: '{query}' (cs.NE 논문)\n", "=" * 80]
    sources = []
    for idx, r in enumerate(results, 1):
        arxiv_id = r["doc_id"]
        title = r["title"]
        score = r["score"]

        output_lines.append(f"\n[논문 {idx}] (유사도: {score:.4f})")
        output_lines.append(f"제목: {title}")
        output_lines.append(f"arXiv ID: {arxiv_id}")
        output_lines.append(f"\n내용:\n{r['text_chunk']}\n")
        output_lines.append("-" * 80)

        snippet = " ".join((r["text_chunk"] or "").split())
        if len(snippet) > 160:
            snippet = snippet[:160].rstrip() + "…"
        sources.append({"arxiv_id": arxiv_id, "title": title, "summary": snippet})

    tool_text = "\n".join(output_lines)
    return Command(update={
        "messages": [ToolMessage(content=tool_text, tool_call_id=runtime.tool_call_id)],
        "sources": sources,
    })


@tool
async def search_astronomy_papers(
    query: str,
    runtime: ToolRuntime,
    k: int = 3
) -> Command:
    """지구 및 행성 천체물리학(astro-ph.EP) 논문에서 관련 내용을 검색하는 도구입니다.
    행성 대기, Mars 지질학, 행성 형성 등에 관한 질문에 대답하거나 참고 자료가 필요할 때 이 툴을 사용하세요.
    """
    results = await common_rag_pipeline.similarity_search("astronomy", query, k=k)

    if not results:
        msg = f"astro-ph.EP 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    output_lines = [f"검색 결과: '{query}' (astro-ph.EP 논문)\n", "=" * 80]
    sources = []
    for idx, r in enumerate(results, 1):
        arxiv_id = r["doc_id"]
        title = r["title"]
        score = r["score"]

        output_lines.append(f"\n[논문 {idx}] (유사도: {score:.4f})")
        output_lines.append(f"제목: {title}")
        output_lines.append(f"arXiv ID: {arxiv_id}")
        output_lines.append(f"\n내용:\n{r['text_chunk']}\n")
        output_lines.append("-" * 80)

        snippet = " ".join((r["text_chunk"] or "").split())
        if len(snippet) > 160:
            snippet = snippet[:160].rstrip() + "…"
        sources.append({"arxiv_id": arxiv_id, "title": title, "summary": snippet})

    tool_text = "\n".join(output_lines)
    return Command(update={
        "messages": [ToolMessage(content=tool_text, tool_call_id=runtime.tool_call_id)],
        "sources": sources,
    })


