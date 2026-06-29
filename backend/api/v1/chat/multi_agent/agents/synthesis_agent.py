import logging
from typing import Any, AsyncGenerator, cast

from langchain.agents import create_agent

from api.v1.chat.multi_agent.agents._checkpointer import get_chat_checkpointer


#################################################################################
# Agent 클래스
#################################################################################
class SynthesisAgent:
    """종합(synthesis) Agent.

    같은 질문에 대한 [논문 기반 답변]과 [웹 기반 답변]을 받아, 둘을 통합한 하나의
    풍부하고 일관된 답변을 생성한다. 검색 도구 없이 LLM만 사용한다.
    """

    # 초기화 메소드
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.SynthesisAgent")
        system_prompt = """
            너는 두 출처의 답변을 종합하는 전문가다.
            같은 질문에 대해 [논문 기반 답변]과 [웹 기반 답변]이 주어진다.
            이 둘을 통합해 하나의 풍부하고 일관된 답변을 한국어로 작성하라.
            - 논문 기반 답변의 인용 표기 [1], [2] 등은 그대로 유지한다.
            - 웹 기반 답변에서 가져온 정보에는 [웹 출처 목록]의 번호를 사용해 [web1], [web2] 형식으로 인용을 단다. (예: "FDA가 승인했다[web1].")
            - 웹 인용은 반드시 [web숫자] 형식만 쓴다. [^1^]나 각주 표기는 절대 쓰지 않는다.
            - 논문 인용 [N]과 웹 인용 [webN]은 서로 다른 출처 체계이므로 혼동하지 않는다.
            - 인용은 해당 정보가 나온 출처에만 정확히 단다. 출처가 불명확하면 인용을 생략한다.
            - 웹 기반 답변의 최신 정보·동향을 자연스럽게 녹인다.
            - 중복은 합치고, 모순되면 양쪽 관점을 모두 제시한다.
            - 서론/결론 없이 본문 중심으로, 읽기 쉽게 단락을 나눠 작성한다.
        """
        # 스트리밍 에이전트(checkpointer 포함)를 같은 설정으로 재생성할 수 있도록 보관한다.
        self.model = model
        self.system_prompt = system_prompt
        # 비스트리밍(ainvoke) 폴백용 에이전트 — checkpointer 없음(thread_id 불필요).
        self.agent = create_agent(
            model=model,
            system_prompt=system_prompt,
        )
        # 스트리밍 전용 에이전트는 running event loop가 필요하므로 lazy 생성한다.
        self._stream_agent = None

    # 입력 content 구성 헬퍼 (run/run_stream 공통)
    def _build_content(
        self, query: str, paper_answer: str, web_answer: str, web_sources: list[dict] | None
    ) -> str:
        """종합 입력 content를 구성한다. [웹 출처 목록]을 번호와 함께 제시해
        LLM이 [web1], [web2] 인용을 정확히 달 수 있게 한다.
        """
        web_list_lines = []
        for i, w in enumerate(web_sources or [], start=1):
            title = w.get("title", "")
            url = w.get("url", "")
            # 도메인까지 따로 표기하지 않고 제목+전체 url을 함께 준다(LLM 참고용).
            web_list_lines.append(f"[web{i}] {title} ({url})")
        web_list = "\n".join(web_list_lines) if web_list_lines else "(웹 출처 없음)"
        return (
            f"[질문]\n{query}\n\n"
            f"[논문 기반 답변]\n{paper_answer}\n\n"
            f"[웹 기반 답변]\n{web_answer}\n\n"
            f"[웹 출처 목록]\n{web_list}"
        )

    # 에이전트 실행 메소드
    async def run(
        self, query: str, paper_answer: str, web_answer: str, web_sources: list[dict] | None = None
    ) -> str:
        """질문과 두 답변을 받아 종합한 답변 본문을 반환한다.

        web_sources 기본값 None — 그래프(synthesis_node) 등 기존 호출과 호환된다
        (그 경우 [웹 출처 목록]은 "(웹 출처 없음)"이 되고 [webN] 인용은 생략된다).
        """
        self.logger.info("종합 에이전트 실행")
        content = self._build_content(query, paper_answer, web_answer, web_sources)
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": content}]}
        )
        return result["messages"][-1].content

    # 스트리밍 전용 에이전트 lazy 초기화
    async def _ensure_stream_agent(self):
        """공유 checkpointer를 물린 스트리밍 에이전트를 최초 1회만 생성해 재사용한다.

        paper_agent의 "checkpointer 2-에이전트 분리" 패턴을 그대로 따른다. 종합 답변을
        thread_id별로 저장해 대화 연속성("방금 그거 더 자세히")을 확보한다.
        """
        if self._stream_agent is None:
            checkpointer = await get_chat_checkpointer()
            self._stream_agent = create_agent(
                model=self.model,
                system_prompt=self.system_prompt,
                checkpointer=checkpointer,
            )
        return self._stream_agent

    # 스트리밍 실행 메소드
    async def run_stream(
        self,
        query: str,
        paper_answer: str,
        web_answer: str,
        web_sources: list[dict] | None,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """종합 답변을 토큰 스트리밍하며, 질문↔답변을 thread_id별로 checkpointer에 저장한다.

        synthesis 에이전트는 도구가 없으므로 모든 AI 토큰이 답변 본문이다
        (paper/web run_stream과 달리 도구 토큰 필터링이 불필요해 단순하다).
        같은 conversation_id로 호출하면 이전 대화 messages가 add_messages 리듀서로
        자동 누적되어 LLM에 함께 전달되므로, 별도 처리 없이 대화 맥락이 이어진다.
        web_sources를 받아 [web1] 형식 인용을 LLM이 정확히 달 수 있게 한다.
        """
        agent = await self._ensure_stream_agent()
        content = self._build_content(query, paper_answer, web_answer, web_sources)
        try:
            # stream_mode는 기존 paper_agent.run_stream과 동일한 list 형태로 맞춘다.
            async for _stream_mode, chunk in agent.astream(
                {"messages": [{"role": "user", "content": content}]},
                {"configurable": {"thread_id": conversation_id}},
                stream_mode=cast(Any, ["messages"]),
            ):
                token, _metadata = chunk
                text = getattr(token, "content", "")
                if text:
                    yield {"type": "token", "data": text}
        except Exception as e:
            self.logger.error(
                f"종합 스트리밍 실패 (conversation_id={conversation_id}): {e}")
            yield {"type": "token", "data": "\n\n(종합 중 오류가 발생했습니다.)"}
