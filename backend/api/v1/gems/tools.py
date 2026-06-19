from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain_postgres import PGVector
from langchain.embeddings import init_embeddings

from api.common.config import settings

# 공통 설정
EMBED_MODEL = "openai:text-embedding-3-large"


@tool
async def search_bio_papers(
    query: str,
    runtime: ToolRuntime,
    k: int = 3
) -> Command:
    """생명공학·유전체학(q-bio.GN) 논문에서 관련 내용을 검색하는 도구.
    유전체학, 유전자 매핑, 시퀀싱 분석 등 생물학 질문에 사용.
    """
    # bio 도메인은 별도 포트를 거치는 데이터베이스 connection을 활용함
    bio_connection = "postgresql+psycopg_async://postgres:postgres@kosa165.iptime.org:50003/postgres"
    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name="q-bio-GN",
        connection=bio_connection,
        async_mode=True,
    )
    results = await vectorstore.asimilarity_search_with_score(query, k=k)
    filtered = [(doc, dist) for doc, dist in results if dist < 0.65]

    if not filtered:
        msg = f"q-bio.GN 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    output_lines = [f"검색 결과: '{query}' (q-bio.GN 논문)\n", "=" * 80]
    sources = []
    for idx, (doc, score) in enumerate(filtered, 1):
        arxiv_id = doc.metadata.get("arxiv_id") or doc.metadata.get("doc_id") or ""
        title = doc.metadata.get("title", "")
        output_lines.append(f"\n[논문 {idx}] (거리: {score:.4f})")
        output_lines.append(f"제목: {title}")
        output_lines.append(f"arXiv ID: {arxiv_id}")
        output_lines.append(f"\n내용:\n{doc.page_content}\n")
        output_lines.append("-" * 80)
        sources.append({"arxiv_id": arxiv_id, "title": title})

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
    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name="cs-NE",
        connection=settings.PGVECTOR_URL,
        async_mode=True,
    )
    results = await vectorstore.asimilarity_search_with_score(query, k=k)

    if not results:
        msg = f"cs.NE 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    output_lines = [f"검색 결과: '{query}' (cs.NE 논문)\n", "=" * 80]
    sources = []
    for idx, (doc, score) in enumerate(results, 1):
        arxiv_id = doc.metadata.get("arxiv_id") or doc.metadata.get("doc_id") or ""
        title = doc.metadata.get("title", "")
        similarity = 1.0 - float(score)
        
        output_lines.append(f"\n[논문 {idx}] (유사도: {similarity:.4f})")
        output_lines.append(f"제목: {title}")
        output_lines.append(f"arXiv ID: {arxiv_id}")
        output_lines.append(f"\n내용:\n{doc.page_content}\n")
        output_lines.append("-" * 80)
        
        sources.append({"arxiv_id": arxiv_id, "title": title})

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
    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name="astro-ph-EP",
        connection=settings.PGVECTOR_URL,
        async_mode=True,
    )
    results = await vectorstore.asimilarity_search_with_score(query, k=k)

    if not results:
        msg = f"astro-ph.EP 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    output_lines = [f"검색 결과: '{query}' (astro-ph.EP 논문)\n", "=" * 80]
    sources = []
    for idx, (doc, score) in enumerate(results, 1):
        arxiv_id = doc.metadata.get("arxiv_id") or doc.metadata.get("doc_id") or ""
        title = doc.metadata.get("title", "")
        similarity = 1.0 - float(score)
        
        output_lines.append(f"\n[논문 {idx}] (유사도: {similarity:.4f})")
        output_lines.append(f"제목: {title}")
        output_lines.append(f"arXiv ID: {arxiv_id}")
        output_lines.append(f"\n내용:\n{doc.page_content}\n")
        output_lines.append("-" * 80)
        
        sources.append({"arxiv_id": arxiv_id, "title": title})

    tool_text = "\n".join(output_lines)
    return Command(update={
        "messages": [ToolMessage(content=tool_text, tool_call_id=runtime.tool_call_id)],
        "sources": sources,
    })
