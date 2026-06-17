import asyncio
import logging
from typing import Annotated

from fastapi import Depends
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# bio 폴더는 읽기/ import만 (수정하지 않음). RAG tool과 state 스키마를 재사용한다.
from api.v1.bio.agent_rag import BioAgentState, search_bio_papers
from api.v1.chat.psycopg_pool_conf import chat_psycopg_pool

logger = logging.getLogger(__name__)


class ChatAgent:
    """대화 히스토리 + 생명공학 논문 RAG를 통합한 에이전트.

    강사 sec06 HistoryPostgreSQLAgent 패턴을 따르되, bio의 search_bio_papers tool을 물려
    유전체학 질문에 답하면서 출처(sources)를 추적한다.
    대화 내역은 AsyncPostgresSaver가 thread_id(=conversation_id=session_id)별로 영구 저장한다.
    """

    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.ChatAgent")
        self.model = model
        # checkpointer/agent는 running event loop가 필요하므로 _initialize에서 lazy 생성한다.
        self.checkpointer = None
        self.agent = None
        # 시스템 프롬프트는 bio의 것과 동일 (유전체학 전문가 + 언어 규칙 + 출처 명시)
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
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """최초 1회 psycopg 풀을 열고 checkpointer 테이블을 생성한다(비동기 lazy 초기화).

        chat_psycopg_pool은 open=False로 생성되므로, setup() 전에 풀을 열어야 한다.
        FastAPI lifespan을 수정하지 않고 chat 내부에서 풀 생명주기를 자체 관리한다.
        """
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            if chat_psycopg_pool.closed:
                await chat_psycopg_pool.open()
            # checkpointer/agent는 running event loop 안에서 생성해야 한다.
            self.checkpointer = AsyncPostgresSaver(chat_psycopg_pool)
            # 시스템 프롬프트는 create_agent에 전달 — 영구 저장되는 대화 기록에 매 턴 중복 누적되지 않도록.
            self.agent = create_agent(
                model=self.model,
                tools=[search_bio_papers],
                system_prompt=self.system_prompt,
                checkpointer=self.checkpointer,
                state_schema=BioAgentState,   # 출처 추적 위해 bio의 state 패턴 활용
            )
            await self.checkpointer.setup()
            self._initialized = True
            self.logger.info("ChatAgent checkpointer 초기화 완료")

    async def run(self, message: str, conversation_id: str) -> dict:
        """메시지를 처리하여 answer와 sources를 반환한다(대화 기록 자동 저장/복원).

        Args:
            message (str): 사용자 질문.
            conversation_id (str): 대화 스레드 ID(= 채팅방 session_id).

        Returns:
            dict: {"answer": 답변 텍스트, "sources": 참고 출처 리스트}.
        """
        await self._initialize()
        result = await self.agent.ainvoke(
            {
                "messages": [{"role": "user", "content": message}],
                "sources": [],   # 이번 턴의 출처 초기값
            },
            {"configurable": {"thread_id": conversation_id}},
        )
        # 출처 중복 제거 (arxiv_id 기준, 순서 유지)
        seen = set()
        unique_sources = []
        for s in result.get("sources", []):
            if s["arxiv_id"] not in seen:
                seen.add(s["arxiv_id"])
                unique_sources.append(s)
        
        return {
            "answer": result["messages"][-1].content,
            "sources": unique_sources
        }

    async def get_history(self, conversation_id: str) -> list[dict]:
        """대화 스레드의 사용자/어시스턴트 메시지 내역을 순서대로 반환한다.

        시스템 메시지·도구 호출 메시지는 제외하고, 사용자(user)와 어시스턴트(assistant)
        실제 발화만 [{role, content}] 리스트로 정리한다.
        """
        await self._initialize()
        state = await self.agent.aget_state(
            {"configurable": {"thread_id": conversation_id}}
        )
        messages = state.values.get("messages", []) if state.values else []

        history = []
        for msg in messages:
            msg_type = getattr(msg, "type", None)
            content = getattr(msg, "content", "")
            if msg_type == "human":
                history.append({"role": "user", "content": content})
            elif msg_type == "ai" and content:
                # 도구 호출만 있는(content 비어있는) AI 메시지는 제외
                history.append({"role": "assistant", "content": content})
        return history

    async def clear_history(self, conversation_id: str) -> None:
        """대화 스레드의 모든 기록을 삭제한다(방 삭제 시 대화 내용도 함께 제거)."""
        await self._initialize()
        await self.checkpointer.adelete_thread(conversation_id)


# 싱글톤으로 관리 — _initialized 플래그와 풀 생명주기를 요청 간에 유지하기 위함.
_chat_agent = ChatAgent()


def get_chat_agent() -> ChatAgent:
    """ChatAgent 싱글톤 인스턴스를 반환하는 의존성 제공자."""
    return _chat_agent


ChatAgentDep = Annotated[ChatAgent, Depends(get_chat_agent)]
