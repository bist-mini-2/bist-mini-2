import asyncio
import logging
from typing import Annotated

from fastapi import Depends
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# bio 폴더는 읽기/ import만 (수정하지 않음). RAG tool과 state 스키마를 재사용한다.
from api.v1.bio.agent_rag import BioAgentState, search_bio_papers
from api.v1.chat.psycopg_pool_conf import chat_psycopg_pool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)



class BioPaperRef(BaseModel):
    """답변 근거가 된 논문 한 편."""
    arxiv_id: str = Field(description="논문의 arXiv ID (예: 2504.10388)")
    title: str = Field(description="논문 제목")
    summary: str = Field(description="이 논문이 질문과 어떻게 관련되는지 한 문장 요약")


class BioAnswer(BaseModel):
    """생명공학 RAG 답변 구조."""
    explanation: str = Field(description="질문에 대한 자연스러운 설명. 논문 나열이 아니라 질문에 직접 답하는 서술형 설명을 작성한다.")
    papers: list[BioPaperRef] = Field(default_factory=list, description="답변 근거가 된 논문 목록")

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
        당신은 생명공학·유전체학(q-bio.GN) 분야의 논문을 잘 아는 연구 조력자입니다.

        작업 방식:
        - 모든 질문에 대해 먼저 search_bio_papers 도구로 관련 논문을 검색합니다.
        - explanation에는 질문에 대한 설명을 마크다운으로 풍부하고 읽기 좋게 작성합니다.
          핵심 용어나 개념은 **굵게** 강조하고, 내용이 길면 ## 소제목으로 구조를 나눠도 좋습니다.
          사용자가 자세한 설명을 원하면 충분히 길게, 간단한 질문이면 간결하게 길이를 조절합니다.
          단, 개별 논문을 "1. 2. 3."처럼 번호로 나열하지는 마세요. 논문 하나하나의 제목·요약은 papers가 담당합니다.
          논문 내용을 설명에 녹일 때는 "~한 연구도 있습니다" 처럼 자연스러운 문장으로 풀어 씁니다.
        - papers에는 답변의 근거가 된 논문 각각을 정리합니다(제목, arxiv_id, 한 줄 요약).
        - 검색 결과에 없는 내용은 지어내지 말고, explanation에 "관련 논문을 찾지 못했습니다"라고 적습니다.
        - 생명공학·유전체학 외 주제(천문학, 컴퓨터과학 등)는 이 시스템의 범위가 아니라고 안내합니다.
        - 항상 사용자가 질문한 언어로 답합니다(한국어 질문이면 한국어로).
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
                response_format=BioAnswer
            )

            # checkpoint 테이블이 이미 있으면 setup()을 건너뛴다.
            # (이미 존재하는 테이블에 대해 setup()이 hang 될 수 있으므로 멱등 처리)
            async with chat_psycopg_pool.connection() as conn:
                cur = await conn.execute(
                    "SELECT 1 FROM pg_tables "
                    "WHERE schemaname='public' AND tablename='checkpoints'"
                )
                exists = await cur.fetchone()
            if not exists:
                await self.checkpointer.setup()

            self._initialized = True
            self.logger.info("ChatAgent checkpointer 초기화 완료")

    async def run(self, message: str, conversation_id: str) -> dict:
        """메시지를 처리하여 answer와 sources를 반환한다(대화 기록 자동 저장/복원).

        대화 처리 중 오류(OpenAI 장애, 네트워크 실패 등) 발생 시 예외를 잡아
        사용자에게 재시도를 안내한다. LangGraph 체크포인터는 단계별 즉시 저장
        구조라 단일 트랜잭션으로 원자성을 보장하기 어려우므로, 예외 처리로
        깨진 상태가 사용자에게 노출되지 않게 방어한다.
        """
        await self._initialize()
        try:
            result = await self.agent.ainvoke(
                {
                    "messages": [{"role": "user", "content": message}],
                    "sources": [],
                },
                {"configurable": {"thread_id": conversation_id}},
            )
            # 출처 중복 제거 (arxiv_id 기준, 순서 유지) — 실제 검색된 출처
            seen = set()
            unique_sources = []
            for s in result.get("sources", []):
                if s["arxiv_id"] not in seen:
                    seen.add(s["arxiv_id"])
                    unique_sources.append(s)

            # 구조화된 답변(response_format) 꺼내기
            structured = result.get("structured_response")
            if structured:
                answer = structured.explanation
                papers = [p.model_dump() for p in structured.papers]
            else:
                # 혹시 구조화 실패 시 fallback (기존 방식)
                answer = result["messages"][-1].content
                papers = []

            return {
                "answer": answer,
                "papers": papers,
                "sources": unique_sources,
            }
        except Exception as e:
            self.logger.error(f"대화 처리 실패 (conversation_id={conversation_id}): {e}")
            return {
                "answer": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "papers": [],
                "sources": [],
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
