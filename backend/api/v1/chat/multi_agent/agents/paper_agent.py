import logging
from typing import Annotated, Any, AsyncGenerator, TypedDict, cast

from langchain.agents import create_agent
from langgraph.graph import add_messages

from api.common.rag_pipeline import (
    search_astronomy_papers,
    search_bio_papers,
    search_cs_papers,
)
from api.v1.chat.multi_agent.agents._checkpointer import get_chat_checkpointer


#################################################################################
# 작업 에이전트용 상태 스키마
#################################################################################
class _PaperWorkerState(TypedDict):
    """논문 검색 도구가 출처(sources)를 누적할 수 있도록 하는 작업 에이전트 내부 상태.

    검색 도구는 Command(update={"sources": [...]})를 반환하므로, 에이전트의
    state_schema에 sources 키가 있어야 누적이 동작한다(기존 chat_agent의 BioAgentState 패턴).
    """
    messages: Annotated[list, add_messages]
    sources: list[dict]
    web_sources: list[dict]


#################################################################################
# Agent 클래스
#################################################################################
class PaperAgent:
    """논문 검색 작업 Agent.

    bio/astronomy/cs arXiv 논문 검색 도구로 학술 질문에 답하고, 검색된 출처를 누적한다.
    인용 표시·영어 검색 규칙은 기존 chat_agent의 stream_system_prompt에서 그대로 가져왔다.
    """

    # 초기화 메소드
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.PaperAgent")
        system_prompt = """
            당신은 생명공학·유전체학(q-bio.GN), 천문학(astro-ph.EP), 컴퓨터과학(cs.NE) 논문을 다루는 연구 조력자입니다.

            - 중요: 검색 도구에 전달하는 query는 반드시 영어로 작성하세요.
                사용자가 한국어로 질문했더라도 핵심 개념을 영어 학술 용어로 번역해 검색합니다.
                예) "소행성체 형성" → "planetesimal formation"
                    "외계행성 대기" → "exoplanet atmosphere"
                    "행성 이주" → "planetary migration"

            작업 방식:
            - 질문 주제를 파악해서 알맞은 검색 도구를 사용합니다.
              · 생명공학·유전체학 → search_bio_papers
              · 천문학 → search_astronomy_papers
              · 컴퓨터과학 → search_cs_papers

            - 검색된 논문 내용을 근거로, 질문에 대한 설명을 마크다운으로 풍부하게 작성합니다.
              핵심 용어는 **굵게** 강조하고, 길면 ## 소제목으로 나눠도 좋습니다.
            - 중요: 참고한 논문을 "관련 논문" 같은 별도 목록·섹션으로 나열하지는 마세요.
              논문 출처 카드는 화면에 따로 표시되므로, 당신은 설명에 집중합니다.
            - 인용 표시(중요): 검색 도구 결과의 각 논문은 [논문 1], [논문 2], [논문 3]처럼 번호가 매겨져 있습니다.
              근거가 된 논문 번호를 [1], [2] 형식으로 붙이되, 반드시 문장 중간이 아니라
              문단(또는 목록 항목)이 완전히 끝나는 맨 끝에 모아서 붙이세요.
              · 한 문단이 여러 문장이어도, 인용은 그 문단의 마지막 문장 끝에 한 번만 모읍니다.
              · 여러 논문에 근거하면 문단 끝에 [1][2]처럼 이어서 표시합니다.
              · 문장 하나하나마다 인용을 흩뿌리지 마세요.
              · 반드시 검색 결과의 논문 번호와 일치시키세요. 없는 번호를 지어내지 마세요.
              · 근거가 검색 논문이 아닌 일반 지식이면 번호를 붙이지 않습니다.
              · 예: "유전체 시퀀싱은 DNA 서열을 결정하는 과정입니다 [1]. 최근에는 메타유전체학 연구가 활발합니다 [2]."
            - 검색 결과에 없는 내용은 지어내지 말고, 못 찾으면 "관련 논문을 찾지 못했습니다"라고 적습니다.
            - 항상 사용자가 질문한 언어로 답합니다.
        """
        # 스트리밍 에이전트(checkpointer 포함)를 같은 설정으로 재생성할 수 있도록 보관한다.
        self.model = model
        self.system_prompt = system_prompt
        self.tools = [search_bio_papers, search_astronomy_papers, search_cs_papers]
        # 비스트리밍(ainvoke) 폴백용 에이전트 — checkpointer 없음(thread_id 불필요).
        self.agent = create_agent(
            model=model,
            tools=self.tools,
            system_prompt=system_prompt,
            # 도구가 sources를 누적할 수 있도록 작업 상태 스키마를 지정한다.
            state_schema=cast(Any, _PaperWorkerState),
        )
        # 스트리밍 전용 에이전트는 running event loop가 필요하므로 lazy 생성한다.
        self._stream_agent = None

    # 에이전트 실행 메소드
    async def run(self, query: str) -> dict:
        """질문에 답하고 답변 본문과 누적된 논문 출처를 반환한다.

        Returns:
            dict: {"answer": str, "sources": list[dict]}
            (출처를 슈퍼바이저 공유 상태로 올려보내기 위해 텍스트와 함께 sources도 반환한다.)
        """
        self.logger.info("논문 검색 에이전트 실행")
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": query}],
             "sources": [], "web_sources": []}
        )
        return {
            "answer": result["messages"][-1].content,
            "sources": result.get("sources", []),
        }

    # 스트리밍 전용 에이전트 lazy 초기화
    async def _ensure_stream_agent(self):
        """공유 checkpointer를 물린 스트리밍 에이전트를 최초 1회만 생성해 재사용한다."""
        if self._stream_agent is None:
            checkpointer = await get_chat_checkpointer()
            self._stream_agent = create_agent(
                model=self.model,
                tools=self.tools,
                system_prompt=self.system_prompt,
                state_schema=cast(Any, _PaperWorkerState),
                checkpointer=checkpointer,
            )
        return self._stream_agent

    # 스트리밍 실행 메소드
    async def run_stream(
        self, query: str, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        """답변 텍스트를 토큰 단위로 흘려보낸다(대화는 checkpointer에 thread_id별로 저장).

        기존 chat_agent.run_stream의 검증된 토큰 필터링 규칙을 그대로 따른다:
        도구 호출 청크로 검색 시작을 감지해 status 이벤트를 한 번 보내고, 도구 노드
        토큰(검색 결과)과 도구 호출만 담긴 AI 토큰은 건너뛴 뒤 실제 답변 텍스트만 yield 한다.
        출처(sources)는 여기서 보내지 않고 state에 누적되며, 종료 후 get_latest_sources로 조회한다.
        """
        agent = await self._ensure_stream_agent()
        announced = False  # status 이벤트를 한 번만 보내기 위한 플래그

        try:
            async for _stream_mode, chunk in agent.astream(
                {"messages": [{"role": "user", "content": query}],
                 "sources": [], "web_sources": []},
                {"configurable": {"thread_id": conversation_id}},
                stream_mode=cast(Any, ["messages"]),
            ):
                token, metadata = chunk

                # 도구 호출 시작 감지 → status 이벤트(최초 1회)
                has_tool = False
                for tc in (getattr(token, "tool_call_chunks", None) or []):
                    if tc.get("name"):
                        has_tool = True
                for tc in (getattr(token, "tool_calls", None) or []):
                    if tc.get("name"):
                        has_tool = True
                if has_tool and not announced:
                    announced = True
                    yield {"type": "status", "data": "paper_search"}

                # 도구 노드 토큰(검색 결과)은 답변이 아니므로 건너뛴다.
                if isinstance(metadata, dict) and metadata.get("langgraph_node") == "tools":
                    continue
                # 도구 호출만 담긴 AI 토큰도 답변 텍스트가 아니므로 건너뛴다.
                if getattr(token, "tool_calls", None):
                    continue
                content = getattr(token, "content", "")
                if not content:
                    continue
                yield {"type": "token", "data": content}
        except Exception as e:
            self.logger.error(
                f"논문 스트리밍 처리 중 오류 (conversation_id={conversation_id}): {e}")
            yield {"type": "token",
                   "data": "\n\n[오류 발생] 답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}

    # 스트림 종료 후 누적 출처 조회
    async def get_latest_sources(self, conversation_id: str) -> list[dict]:
        """스트리밍 종료 후 state에 누적된 논문 출처를 arxiv_id 기준 중복 제거해 반환한다."""
        agent = await self._ensure_stream_agent()
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
