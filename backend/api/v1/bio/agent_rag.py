from typing import Annotated, TypedDict
from fastapi import Depends
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.graph import add_messages
from langgraph.types import Command
from langchain_postgres import PGVector
from langchain.embeddings import init_embeddings
from api.v1.bio.vectorstore_conf import COLLECTION_NAME, CONNECTION, EMBED_MODEL

DISTANCE_THRESHOLD = 0.65


# 1) 커스텀 state 정의 (강사님 sec07 패턴) — sources 필드 추가
class BioAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    sources: list[dict]   # 검색된 논문 출처 누적


# 2) tool이 검색하면서 sources를 state에 기록 (Command 반환)
@tool
async def search_bio_papers(query: str, runtime: ToolRuntime, k: int = 3) -> Command:
    """
    생명공학·유전체학(q-bio.GN) 논문에서 관련 내용을 검색하는 도구.
    유전체학, 유전자 매핑, 시퀀싱 분석 등 생물학 질문에 사용.
    """
    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name=COLLECTION_NAME,
        connection=CONNECTION,
        async_mode=True,
    )
    results = await vectorstore.asimilarity_search_with_score(query, k=k)
    filtered = [(doc, dist) for doc, dist in results if dist < DISTANCE_THRESHOLD]

    if not filtered:
        msg = f"q-bio.GN 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    # LLM에게 줄 텍스트(답변 생성용)
    output_lines = [f"검색 결과: '{query}'\n", "=" * 80]
    # state에 저장할 출처 구조(정확한 sources)
    sources = []
    for idx, (doc, score) in enumerate(filtered, 1):
        arxiv_id = doc.metadata.get("arxiv_id", "")
        title = doc.metadata.get("title", "")
        output_lines.append(f"\n[논문 {idx}] (거리: {score:.4f})")
        output_lines.append(f"제목: {title}")
        output_lines.append(f"arXiv ID: {arxiv_id}")
        output_lines.append(f"\n내용:\n{doc.page_content}\n")
        output_lines.append("-" * 80)
        sources.append({"arxiv_id": arxiv_id, "title": title})

    tool_text = "\n".join(output_lines)

    # 핵심: 답변용 텍스트는 ToolMessage로, 출처는 state의 sources에 동시 기록
    return Command(update={
        "messages": [ToolMessage(content=tool_text, tool_call_id=runtime.tool_call_id)],
        "sources": sources,
    })


class BioRagAgent:
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.system_prompt = """
        당신은 생명공학·유전체학(q-bio.GN) 논문 전문가입니다.

        사용 가능한 도구:
        **search_bio_papers**: q-bio.GN 논문 검색

        지침:
        - 사용자의 질문에 답하기 위해 반드시 search_bio_papers 도구로 관련 논문을 검색하세요.
        - 검색된 논문에 기반해서만 답변하고, 논문 제목과 arXiv ID를 출처로 명시하세요.
        - 검색 결과에 없는 정보는 추측하지 말고 "해당 정보를 논문에서 찾을 수 없습니다"라고 답하세요.
        - 생명공학·유전체학 외 주제(천문학, 컴퓨터과학 등)는 이 시스템에서 다루지 않는다고 안내하세요.

        CRITICAL — 언어 규칙:
        - 사용자 질문의 언어를 감지하세요.
        - 항상 사용자 질문과 같은 언어로 답변하세요.
        - 한국어 질문 → 한국어 답변, 영어 질문 → 영어 답변.
        - 검색된 논문이나 이 프롬프트의 언어와 무관하게 언어를 바꾸지 마세요.
        """
        self.agent = create_agent(
            model=model,
            tools=[search_bio_papers],
            state_schema=BioAgentState,   # ← state 스키마 연결 (강사님 sec07 패턴)
        )

    # 3) run()이 answer와 sources를 함께 반환
    async def run(self, question: str) -> dict:
        result = await self.agent.ainvoke({
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question},
            ],
            "sources": [],   # 초기값
        })
        return {
            "answer": result["messages"][-1].content,
            "sources": result.get("sources", []),   # state에서 정확한 출처 꺼냄
        }

BioRagAgentDep = Annotated[BioRagAgent, Depends(BioRagAgent)]