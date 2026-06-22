import asyncio
import logging
from typing import Annotated, TypedDict, Any, cast

from fastapi import Depends
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import add_messages
from api.common.rag_pipeline import (
    search_bio_papers,
    search_cs_papers,
    search_astronomy_papers,
)
from api.database.config.psycopg_pool import psycopg_pool as chat_psycopg_pool

class GemAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    sources: list[dict]   # 검색된 논문 출처 누적

logger = logging.getLogger(__name__)

# db_sources 값 → 실제 tool 매핑
_TOOL_MAP = {
    "bio": search_bio_papers,
    "cs": search_cs_papers,
    "astronomy": search_astronomy_papers,
}


class GemAgent:
    """Gem 전용 에이전트.

    db_sources 목록에 해당하는 RAG 도구만 선택적으로 탑재하고,
    사용자가 지정한 system_prompt를 페르소나로 바인딩한다.
    대화 이력은 AsyncPostgresSaver가 thread_id별로 영구 저장한다.
    chat_psycopg_pool을 재사용하므로 별도 풀을 생성하지 않는다.
    """

    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.GemAgent")
        self.model = model
        self.checkpointer = None
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """최초 1회 psycopg 풀 확인 후 checkpointer를 생성한다."""
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            if chat_psycopg_pool.closed:
                await chat_psycopg_pool.open()
            self.checkpointer = AsyncPostgresSaver(cast(Any, chat_psycopg_pool))

            # checkpoints 테이블이 이미 있으면 setup() 생략 (chat_agent가 이미 생성했을 수 있음)
            async with chat_psycopg_pool.connection() as conn:
                cur = await conn.execute(
                    "SELECT 1 FROM pg_tables "
                    "WHERE schemaname='public' AND tablename='checkpoints'"
                )
                exists = await cur.fetchone()
                if not exists:
                    # checkpoints가 없는데 checkpoint_migrations가 있으면 setup()이 테이블을 생성하지 않으므로
                    # 관련 테이블을 일괄 삭제하여 setup()이 처음부터 깨끗이 생성하도록 유도합니다.
                    await conn.execute("DROP TABLE IF EXISTS checkpoint_migrations, checkpoint_blobs, checkpoint_writes CASCADE;")
            if not exists:
                assert self.checkpointer is not None
                await self.checkpointer.setup()

            self._initialized = True
            self.logger.info("GemAgent checkpointer 초기화 완료")

    def _build_agent(self, db_sources: list[str], system_prompt: str):
        """db_sources에 맞는 tool 목록과 system_prompt로 agent를 동적으로 생성한다."""
        tools = [_TOOL_MAP[src] for src in db_sources if src in _TOOL_MAP]
        if not tools:
            # 소스가 하나도 없으면 bio를 기본으로 사용
            tools = [search_bio_papers]

        source_desc = ", ".join(db_sources) if db_sources else "bio"
        full_system_prompt = f"""{system_prompt}

사용 가능한 RAG 도구: {source_desc} 논문 검색 도구.
- 반드시 관련 도구를 사용하여 논문에서 근거를 찾아 답변하세요.
- 출처(논문 제목, arXiv ID)를 반드시 명시하세요.
- 검색 결과에 없는 정보는 추측하지 마세요.

CRITICAL — 언어 규칙:
- 사용자 질문의 언어를 감지하여 항상 같은 언어로 답변하세요.
- 한국어 질문 → 한국어 답변, 영어 질문 → 영어 답변.
"""
        return create_agent(
            model=self.model,
            tools=tools,
            system_prompt=full_system_prompt,
            checkpointer=self.checkpointer,
            state_schema=cast(Any, GemAgentState),
        )

    async def run(self, message: str, thread_id: str, db_sources: list[str], system_prompt: str) -> dict:
        """메시지를 처리하여 answer와 sources를 반환한다(대화 기록 자동 저장/복원).

        Args:
            message (str): 사용자 입력 메시지.
            thread_id (str): 대화 스레드 ID (Gem별 고유 thread 사용).
            db_sources (list[str]): 탑재할 RAG 소스 목록.
            system_prompt (str): Gem의 페르소나 시스템 프롬프트.

        Returns:
            dict: answer(str)와 sources(list[dict]) 포함 딕셔너리.
        """
        await self._initialize()
        agent = self._build_agent(db_sources, system_prompt)
        try:
            result = await agent.ainvoke(
                {
                    "messages": [{"role": "user", "content": message}],
                    "sources": [],
                },
                {"configurable": {"thread_id": thread_id}},
            )
            seen = set()
            unique_sources = []
            for s in result.get("sources", []):
                key = s.get("arxiv_id") or s.get("doc_id", "")
                if key not in seen:
                    seen.add(key)
                    unique_sources.append(s)

            return {
                "answer": result["messages"][-1].content,
                "sources": unique_sources,
            }
        except Exception as e:
            self.logger.error(f"Gem 대화 처리 실패 (thread_id={thread_id}): {e}")
            return {
                "answer": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "sources": [],
            }

    async def get_history(self, thread_id: str, db_sources: list[str], system_prompt: str) -> list[dict]:
        """대화 스레드의 user/assistant 메시지 내역을 순서대로 반환한다.

        Args:
            thread_id (str): 조회할 대화 스레드 ID.
            db_sources (list[str]): agent 재생성용 RAG 소스 목록.
            system_prompt (str): agent 재생성용 시스템 프롬프트.

        Returns:
            list[dict]: [{role, content}] 형식의 대화 내역 리스트.
        """
        await self._initialize()
        agent = self._build_agent(db_sources, system_prompt)
        state = await agent.aget_state(
            {"configurable": {"thread_id": thread_id}}
        )
        messages = state.values.get("messages", []) if state.values else []

        history = []
        for msg in messages:
            msg_type = getattr(msg, "type", None)
            content = getattr(msg, "content", "")
            if msg_type == "human":
                history.append({"role": "user", "content": content})
            elif msg_type == "ai" and content:
                history.append({"role": "assistant", "content": content})
        return history

    async def clear_history(self, thread_id: str) -> None:
        """대화 스레드의 모든 기록을 삭제한다.

        Args:
            thread_id (str): 삭제할 대화 스레드 ID.
        """
        await self._initialize()
        assert self.checkpointer is not None
        await self.checkpointer.adelete_thread(thread_id)


# 싱글톤 인스턴스
_gem_agent = GemAgent()


def get_gem_agent() -> GemAgent:
    """GemAgent 싱글톤 인스턴스를 반환하는 의존성 제공자."""
    return _gem_agent


GemAgentDep = Annotated[GemAgent, Depends(get_gem_agent)]
