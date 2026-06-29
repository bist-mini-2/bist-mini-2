import logging
from typing import Annotated, Any, AsyncGenerator, TypedDict, cast

from langchain.agents import create_agent
from langgraph.graph import add_messages

from api.common.tools import get_current_datetime, search_web
from api.v1.chat.multi_agent.agents._checkpointer import get_chat_checkpointer


#################################################################################
# 작업 에이전트용 상태 스키마
#################################################################################
class _WebWorkerState(TypedDict):
    """웹 검색 도구가 출처(web_sources)를 누적할 수 있도록 하는 작업 에이전트 내부 상태.

    search_web은 Command(update={"web_sources": [...]})를 반환하므로, 에이전트의
    state_schema에 web_sources 키가 있어야 누적이 동작한다.
    """
    messages: Annotated[list, add_messages]
    sources: list[dict]
    web_sources: list[dict]


#################################################################################
# Agent 클래스
#################################################################################
class WebAgent:
    """웹 검색 작업 Agent.

    최신 동향·일반 상식 등 논문 범위 밖 질문을 웹 검색으로 답하고, 웹 출처를 누적한다.
    """

    # 초기화 메소드
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.WebAgent")
        system_prompt = """
            당신은 웹 검색으로 최신 정보를 찾아 답하는 연구 조력자입니다.

            작업 방식:
            - search_web 도구로 질문과 관련된 최신 정보를 검색해 근거로 삼아 답합니다.
            - '오늘', '지금', '현재', '최근' 등 현재 시점이 필요한 질문이면
              get_current_datetime 도구로 현재 날짜·시각을 먼저 확인하세요.
            - 검색 결과를 바탕으로 마크다운으로 자연스럽고 풍부하게 설명합니다.
              핵심 용어는 **굵게** 강조해도 좋습니다.
            - 참고한 출처(웹사이트, 기사 등)를 답변에 자연스럽게 언급하세요.
            - 검색 결과에 없는 내용은 지어내지 마세요.
            - 항상 사용자가 질문한 언어로 답합니다.
        """
        # 스트리밍 에이전트(checkpointer 포함)를 같은 설정으로 재생성할 수 있도록 보관한다.
        self.model = model
        self.system_prompt = system_prompt
        self.tools = [search_web, get_current_datetime]
        # 비스트리밍(ainvoke) 폴백용 에이전트 — checkpointer 없음(thread_id 불필요).
        self.agent = create_agent(
            model=model,
            tools=self.tools,
            system_prompt=system_prompt,
            # 도구가 web_sources를 누적할 수 있도록 작업 상태 스키마를 지정한다.
            state_schema=cast(Any, _WebWorkerState),
        )
        # 스트리밍 전용 에이전트는 running event loop가 필요하므로 lazy 생성한다.
        self._stream_agent = None

    # 에이전트 실행 메소드
    async def run(self, query: str) -> dict:
        """질문에 답하고 답변 본문과 누적된 웹 출처를 반환한다.

        Returns:
            dict: {"answer": str, "web_sources": list[dict]}
        """
        self.logger.info("웹 검색 에이전트 실행")
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": query}],
             "sources": [], "web_sources": []}
        )
        return {
            "answer": result["messages"][-1].content,
            "web_sources": result.get("web_sources", []),
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
                state_schema=cast(Any, _WebWorkerState),
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
        출처(web_sources)는 여기서 보내지 않고 state에 누적되며, 종료 후 get_latest_web_sources로 조회한다.
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
                    yield {"type": "status", "data": "web_search"}

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
                f"웹 스트리밍 처리 중 오류 (conversation_id={conversation_id}): {e}")
            yield {"type": "token",
                   "data": "\n\n[오류 발생] 답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}

    # 스트림 종료 후 누적 웹 출처 조회
    async def get_latest_web_sources(self, conversation_id: str) -> list[dict]:
        """스트리밍 종료 후 state에 누적된 웹 출처를 url 기준 중복 제거해 반환한다."""
        agent = await self._ensure_stream_agent()
        state = await agent.aget_state(
            {"configurable": {"thread_id": conversation_id}}
        )
        raw = state.values.get("web_sources", []) if state.values else []
        seen = set()
        unique = []
        for s in raw:
            if s["url"] not in seen:
                seen.add(s["url"])
                unique.append(s)
        return unique
