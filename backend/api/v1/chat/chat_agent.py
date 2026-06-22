import asyncio
import logging
from typing import Annotated, TypedDict, Any, cast

from fastapi import Depends
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from langgraph.graph import add_messages
from api.common.rag_pipeline import search_bio_papers, search_astronomy_papers, search_cs_papers
from api.database.config.psycopg_pool import psycopg_pool as chat_psycopg_pool
from pydantic import BaseModel, Field

class BioAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    sources: list[dict]   # 검색된 논문 출처 누적

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
        당신은 생명공학·유전체학(q-bio.GN)과 천문학(astro-ph.EP) 논문을 다루는 연구 조력자입니다.

        작업 방식:
        - 질문 주제를 파악해서 알맞은 검색 도구를 사용합니다.
          · 생명공학·유전체학(유전자, DNA, 시퀀싱 등) → search_bio_papers
          · 천문학(외계행성, 행성, 천체물리 등) → search_astronomy_papers
          · 컴퓨터과학(신경망, 진화 알고리즘, 딥러닝 등) → search_cs_papers
        - 검색된 논문 내용을 근거로, explanation에 질문에 대한 설명을 마크다운으로 풍부하게 작성합니다.
          핵심 용어는 **굵게** 강조하고, 내용이 길면 ## 소제목으로 구조를 나눠도 좋습니다.
          질문에 맞춰 설명 길이를 조절합니다.
          단, 개별 논문을 "1. 2. 3."처럼 번호로 나열하지는 마세요. 논문 하나하나는 papers가 담당합니다.
        - papers에는 답변의 근거가 된 논문 각각을 정리합니다(제목, arxiv_id, 한 줄 요약).
        - 검색 결과에 없는 내용은 지어내지 말고, explanation에 "관련 논문을 찾지 못했습니다"라고 적습니다.
        - 항상 사용자가 질문한 언어로 답합니다(한국어 질문이면 한국어로).
        """
        # 스트리밍 전용 프롬프트 — 구조화 출력이 없으므로 논문을 본문에 나열하지 않게 한다.
        # (참고 논문은 검색된 출처를 카드로 따로 보여줌)
        self.stream_system_prompt = """
        당신은 생명공학·유전체학(q-bio.GN), 천문학(astro-ph.EP), 컴퓨터과학(cs.NE) 논문을 다루는 연구 조력자입니다.

        작업 방식:
        - 질문 주제를 파악해서 알맞은 검색 도구를 사용합니다.
          · 생명공학·유전체학 → search_bio_papers
          · 천문학 → search_astronomy_papers
          · 컴퓨터과학 → search_cs_papers
        - 검색된 논문 내용을 근거로, 질문에 대한 설명을 마크다운으로 풍부하게 작성합니다.
          핵심 용어는 **굵게** 강조하고, 길면 ## 소제목으로 나눠도 좋습니다.
        - 중요: 참고한 논문 목록을 본문에 나열하거나 "관련 논문" 같은 섹션을 만들지 마세요.
          논문 출처는 화면에 별도 카드로 표시되므로, 당신은 설명에만 집중합니다.
        - 검색 결과에 없는 내용은 지어내지 말고, 못 찾으면 "관련 논문을 찾지 못했습니다"라고 적습니다.
        - 항상 사용자가 질문한 언어로 답합니다.
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
            self.checkpointer = AsyncPostgresSaver(cast(Any, chat_psycopg_pool))
            # 시스템 프롬프트는 create_agent에 전달 — 영구 저장되는 대화 기록에 매 턴 중복 누적되지 않도록.
            self.agent = create_agent(
                model=self.model,
                tools=[search_bio_papers, search_astronomy_papers, search_cs_papers],
                system_prompt=self.system_prompt,
                checkpointer=self.checkpointer,
                state_schema=cast(Any, BioAgentState),   # 출처 추적 위해 bio의 state 패턴 활용
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
                    # checkpoints가 없는데 checkpoint_migrations가 있으면 setup()이 테이블을 생성하지 않으므로
                    # 관련 테이블을 일괄 삭제하여 setup()이 처음부터 깨끗이 생성하도록 유도합니다.
                    await conn.execute("DROP TABLE IF EXISTS checkpoint_migrations, checkpoint_blobs, checkpoint_writes CASCADE;")
            if not exists:
                assert self.checkpointer is not None
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
        assert self.agent is not None
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

    async def run_stream(self, message: str, conversation_id: str):
        """메시지를 처리하면서 답변 텍스트(explanation)를 토큰 단위로 흘려보낸다(스트리밍).

        run()과 달리 response_format(structured output)을 쓰지 않는다. structured output은
        JSON이 완성돼야 파싱되므로 스트리밍과 충돌하기 때문이다. 그래서 response_format을 뺀
        스트리밍 전용 에이전트(_stream_agent)를 최초 1회만 lazy 생성해 재사용한다.
        도구/system_prompt/checkpointer/state_schema는 메인 에이전트와 동일하다.

        astream(stream_mode=["messages"])은 답변 토큰과 함께 도구 호출/도구 결과 토큰도 섞어
        내보내므로, 실제 답변 텍스트 토큰만 골라 yield 한다. 출처(sources)는 여기서 yield하지
        않고 state(checkpointer)에 누적되며, 스트리밍 종료 후 get_latest_sources()로 조회한다.
        """
        await self._initialize()

        if not hasattr(self, "_stream_agent") or self._stream_agent is None:
            self._stream_agent = create_agent(
                model=self.model,
                tools=[search_bio_papers, search_astronomy_papers, search_cs_papers],
                system_prompt=self.stream_system_prompt,
                checkpointer=self.checkpointer,
                state_schema=cast(Any, BioAgentState),
                # response_format 없음 — 스트리밍 위해 일반 마크다운 텍스트로 출력
            )

        assert self._stream_agent is not None
        async for stream_mode, chunk in self._stream_agent.astream(
            {"messages": [{"role": "user", "content": message}], "sources": []},
            {"configurable": {"thread_id": conversation_id}},
            stream_mode=cast(Any, ["messages"]),
        ):
            token, metadata = chunk
            # 도구 노드에서 나온 토큰(검색 결과 등)은 답변이 아니므로 건너뛴다.
            if isinstance(metadata, dict) and metadata.get("langgraph_node") == "tools":
                continue
            # 도구 호출(tool_calls)만 담은 AI 토큰도 답변 텍스트가 아니므로 건너뛴다.
            if getattr(token, "tool_calls", None):
                continue
            content = getattr(token, "content", "")
            if not content:
                continue
            yield content

    async def get_latest_sources(self, conversation_id: str) -> list[dict]:
        """스트리밍 종료 후 state(checkpointer)에 누적된 검색 출처를 중복 제거하여 반환한다.

        run_stream의 도구가 state.sources에 기록한 실제 검색 결과를 꺼낸다.
        arxiv_id 기준으로 중복을 제거하고 순서를 유지한다(run()과 동일한 규칙).
        """
        await self._initialize()
        agent = getattr(self, "_stream_agent", None) or self.agent
        assert agent is not None
        state = await agent.aget_state(
            {"configurable": {"thread_id": conversation_id}}
        )
        raw_sources = state.values.get("sources", []) if state.values else []
        seen = set()
        unique_sources = []
        for s in raw_sources:
            if s["arxiv_id"] not in seen:
                seen.add(s["arxiv_id"])
                unique_sources.append(s)
        return unique_sources

    async def get_history(self, conversation_id: str) -> list[dict]:
        """대화 스레드의 사용자/어시스턴트 메시지 내역을 순서대로 반환한다.

        시스템 메시지·도구 호출 메시지는 제외하고, 사용자(user)와 어시스턴트(assistant)
        실제 발화만 [{role, content}] 리스트로 정리한다.
        """
        await self._initialize()
        assert self.agent is not None
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
        assert self.checkpointer is not None
        await self.checkpointer.adelete_thread(conversation_id)

    async def generate_title(self, question: str) -> str:
        """사용자의 첫 질문을 바탕으로 간결한 채팅방 제목을 생성한다.

        답변 생성과 동일한 모델(gpt-4o-mini)을 재사용하되, 제목 생성용
        경량 LLM 객체는 최초 1회만 만들어 보관한다. 도구 호출이나 대화
        기록이 필요 없는 단순 변환이므로 에이전트가 아니라 모델을 직접 호출한다.
        """
        # 제목 생성용 LLM은 최초 1회만 생성해 재사용
        if not hasattr(self, "_title_model") or self._title_model is None:
            self._title_model = init_chat_model(self.model)

        assert self._title_model is not None
        prompt = (
            "다음 질문을 한국어로 6~20자의 간결한 채팅방 제목으로 만들어줘.\n"
            "- 제목만 출력하고 따옴표나 군더더기 설명은 붙이지 마.\n"
            "- 질문의 핵심 주제를 자연스럽게 요약해.\n\n"
            f"질문: {question}"
        )
        try:
            response = await self._title_model.ainvoke(prompt)
            content = response.content
            if isinstance(content, str):
                title = content.strip().strip('"').strip("'")
            else:
                title = ""
            # 혹시 너무 길면 잘라서 안전하게
            return title[:30] if title else question[:30]
        except Exception as e:
            self.logger.error(f"제목 생성 실패: {e}")
            # 실패 시 질문 앞부분으로 폴백
            return question[:30]
    
    
    
# 싱글톤으로 관리 — _initialized 플래그와 풀 생명주기를 요청 간에 유지하기 위함.
_chat_agent = ChatAgent()


def get_chat_agent() -> ChatAgent:
    """ChatAgent 싱글톤 인스턴스를 반환하는 의존성 제공자."""
    return _chat_agent


ChatAgentDep = Annotated[ChatAgent, Depends(get_chat_agent)]
