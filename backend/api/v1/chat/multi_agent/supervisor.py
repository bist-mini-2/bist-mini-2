import asyncio
import logging
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from langgraph.graph import END, START, StateGraph

from api.v1.chat.multi_agent.nodes.analysis_node import analysis_node
from api.v1.chat.multi_agent.nodes.paper_node import paper_node
from api.v1.chat.multi_agent.nodes.web_node import web_node
from api.v1.chat.multi_agent.nodes.gather_node import gather_node
from api.v1.chat.multi_agent.nodes.synthesis_node import synthesis_node
# 스트리밍에서는 그래프 대신 작업 에이전트를 직접 호출하므로, nodes 모듈에 이미 만들어진
# 싱글톤 에이전트를 재사용한다(같은 공유 checkpointer를 쓰므로 대화 연속성 유지 + 메모리 절약).
from api.v1.chat.multi_agent.nodes.analysis_node import agent as analysis_agent
from api.v1.chat.multi_agent.nodes.paper_node import agent as paper_agent
from api.v1.chat.multi_agent.nodes.web_node import agent as web_agent
from api.v1.chat.multi_agent.nodes.synthesis_node import agent as synthesis_agent
from api.v1.chat.multi_agent.state import MultiAgentState


# 조건 분기 함수 정의
def route_fun(state: MultiAgentState) -> str:
    """분석 결과(route)를 보고 다음 노드를 결정한다. 기본값은 paper."""
    return "web" if state.get("route") == "web" else "paper"


class ChatMultiAgentSupervisor:
    """슈퍼바이저 멀티 에이전트(팬아웃 + 종합).

    흐름: START → (paper_node ∥ web_node 병렬) → gather → synthesis → END
    논문·웹 두 에이전트를 병렬로 호출한 뒤, 둘의 답변을 종합(synthesis)해 하나의
    답변을 만든다(퍼플렉시티 스타일). 강사님 sec09 팬아웃+취합 패턴을 따른다.
    """

    # 초기화 메소드
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.ChatMultiAgentSupervisor")
        # 그래프(작업 흐름) 구성
        self.build_workflow()
        # 스트리밍 전용: 라우팅/답변을 직접 호출하기 위해 작업 에이전트 인스턴스를 보유한다.
        # (nodes 모듈의 싱글톤을 재사용 — 같은 공유 checkpointer로 대화가 연속된다.)
        self.analysis_agent = analysis_agent
        self.paper_agent = paper_agent
        self.web_agent = web_agent
        # 종합(synthesis) 에이전트 — run_stream에서 종합 답변 토큰 스트리밍에 사용.
        self.synthesis_agent = synthesis_agent

    # 그래프(작업 흐름) 구성 메소드 — 팬아웃 + 종합(현재 활성)
    def build_workflow(self):
        """StateGraph를 팬아웃(논문∥웹) + 종합 구조로 구성해 컴파일한다.

        흐름: START → (paper_node ∥ web_node) → gather → synthesis → END
        - START에서 paper_node·web_node로 동시에 엣지를 그어 병렬 실행한다.
        - 두 노드가 같은 gather로 엣지를 그어, 둘 다 끝날 때까지 대기 후 진행한다.
        """
        # 그래프 생성
        graph = StateGraph(MultiAgentState)

        # 그래프에 노드 추가
        graph.add_node("paper_node", paper_node)
        graph.add_node("web_node", web_node)
        graph.add_node("gather", gather_node)
        graph.add_node("synthesis", synthesis_node)

        # 그래프에 엣지 추가
        graph.add_edge(START, "paper_node")   # 병렬 분기
        graph.add_edge(START, "web_node")
        graph.add_edge("paper_node", "gather")  # 병렬 완료 대기
        graph.add_edge("web_node", "gather")
        graph.add_edge("gather", "synthesis")
        graph.add_edge("synthesis", END)

        # 그래프 컴파일
        self.work_flow = graph.compile()

    # 그래프(작업 흐름) 구성 메소드 — 기존 라우팅 버전(보존, 비활성)
    def _build_workflow_routing(self):
        """[보존] 라우팅 버전 그래프. 되돌릴 때 대비해 남겨둔다(현재 미사용).

        흐름: START → analysis → (route_fun 분기) → paper_node 또는 web_node → END
        """
        # 그래프 생성
        graph = StateGraph(MultiAgentState)

        # 그래프에 노드 추가
        graph.add_node("analysis", analysis_node)
        graph.add_node("paper_node", paper_node)
        graph.add_node("web_node", web_node)

        # 그래프에 엣지 추가
        graph.add_edge(START, "analysis")
        # 분석 결과로 분기
        graph.add_conditional_edges(
            "analysis",
            route_fun,
            # { "리턴값": "다음노드" }
            {
                "paper": "paper_node",
                "web": "web_node",
            },
        )
        graph.add_edge("paper_node", END)
        graph.add_edge("web_node", END)

        # 그래프 컴파일
        self.work_flow = graph.compile()

    # 에이전트 실행 메소드
    async def run(self, query: str) -> dict:
        """질문을 받아 논문·웹 병렬 호출 후 종합한 답변과 출처를 반환한다.

        Returns:
            dict: {"answer": str, "sources": list[dict], "web_sources": list[dict]}
        """
        # 초기 상태 생성
        initial_state = {
            "messages": [],
            "user_query": query,
            "route": "",
            "sources": [],
            "web_sources": [],
            "paper_answer": "",
            "web_answer": "",
            "final_response": "",
        }
        # 그래프 실행
        final_state = await self.work_flow.ainvoke(initial_state)
        return {
            "answer": final_state["final_response"],
            "sources": final_state.get("sources", []),
            "web_sources": final_state.get("web_sources", []),
        }

    # 스트리밍 실행 메소드 — 팬아웃 + 종합(현재 활성)
    async def run_stream(
        self, query: str, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        """논문·웹 병렬 검색 후, 종합 답변을 토큰 스트리밍한다(팬아웃+종합).

        StateGraph를 astream하지 않는다. 검색은 병렬 비스트리밍(ainvoke)으로 끝내고,
        종합(synthesis) 답변만 토큰 단위로 흘려보낸다. 검색 출처는 그래프/checkpointer가
        아니라 run의 반환 dict에서 직접 받아 지역변수로 들고 있다가 마지막에 알린다.

        이벤트:
            - {"type":"status","data":"paper_search"}   검색 시작 알림
            - {"type":"status","data":"web_search"}
            - {"type":"status","data":"synthesizing"}    종합 시작 알림
            - {"type":"token","data":...}                종합 답변 토큰
            - {"type":"sources","data":{"sources":[...],"web_sources":[...]}}  종료 직전 1회
        """
        # 1) 검색 병렬 — status 먼저 알리고 동시에 실행
        yield {"type": "status", "data": "paper_search"}
        yield {"type": "status", "data": "web_search"}

        paper_result, web_result = await asyncio.gather(
            self.paper_agent.run(query),
            self.web_agent.run(query),
            return_exceptions=True,
        )
        # 예외 방어: 실패한 쪽은 빈 결과로 처리
        if isinstance(paper_result, dict):
            paper_answer = paper_result.get("answer", "")
            sources = paper_result.get("sources", [])
        else:
            self.logger.error(f"논문 검색 실패: {paper_result}")
            paper_answer, sources = "", []
        if isinstance(web_result, dict):
            web_answer = web_result.get("answer", "")
            web_sources = web_result.get("web_sources", [])
        else:
            self.logger.error(f"웹 검색 실패: {web_result}")
            web_answer, web_sources = "", []

        # 2) 종합 스트리밍 — conversation_id를 넘겨 대화 연속성 확보
        yield {"type": "status", "data": "synthesizing"}
        async for event in self.synthesis_agent.run_stream(
            query, paper_answer, web_answer, conversation_id
        ):
            yield event

        # 3) 출처 알림 — 호출자(service)가 저장에 사용. 논문·웹 둘 다.
        yield {"type": "sources", "data": {"sources": sources, "web_sources": web_sources}}

    # 스트리밍 실행 메소드 — 기존 라우팅 버전(보존, 비활성)
    async def _run_stream_routing(
        self, query: str, conversation_id: str
    ) -> AsyncGenerator[dict, None]:
        """[보존] 라우팅 방식 스트리밍. 되돌릴 때 대비해 남겨둔다(현재 미사용).

        라우팅(ainvoke) → 선택된 작업 에이전트 스트리밍(astream)을 하나로 잇는다.

        StateGraph를 통째로 astream하지 않는다(중첩 서브그래프 토큰 추출이 복잡하므로).
        라우팅은 짧은 분류값이라 스트리밍이 불필요하므로 analysis를 ainvoke로 빠르게 호출해
        route만 정하고, 답변 토큰만 작업 에이전트의 run_stream으로 흘려보낸다(passthrough).
        출처는 스트림 종료 후 get_latest_sources(route, conversation_id)로 조회한다.

        yield 이벤트:
            - {"type": "status", "data": "paper_search"|"web_search"}  (작업 에이전트가 발생)
            - {"type": "token", "data": <텍스트 조각>}                 (작업 에이전트가 발생)
            - {"type": "route", "data": "paper"|"web"}                 (스트림 종료 직전 1회)
        """
        # 1) 라우팅: analysis를 ainvoke로 빠르게 호출(예외 시 paper로 폴백)
        try:
            route_result = await self.analysis_agent.run(query)
            route = route_result.get("route", "paper")
        except Exception as e:
            self.logger.error(f"라우팅 분석 실패, paper로 폴백: {e}")
            route = "paper"
        self.logger.info(f"스트리밍 라우팅 결정: route={route}")

        # 2) 분기: route에 따라 작업 에이전트 선택
        target = self.web_agent if route == "web" else self.paper_agent

        # 3) 답변 토큰 스트리밍 — 작업 에이전트의 이벤트를 그대로 통과시킨다.
        #    (작업 에이전트 run_stream은 내부에서 예외를 처리해 에러 토큰을 yield한다.)
        async for event in target.run_stream(query, conversation_id):
            yield event

        # 4) 최종 route 알림 — 호출자(service)가 어느 에이전트에서 출처를 꺼낼지 결정용.
        yield {"type": "route", "data": route}

    # 스트림 종료 후 누적 출처 조회
    async def get_latest_sources(self, route: str, conversation_id: str) -> dict:
        """route에 따라 해당 작업 에이전트에서 누적된 출처를 꺼내 반환한다.

        Returns:
            dict: {"sources": list[dict], "web_sources": list[dict]}
        """
        if route == "web":
            return {
                "sources": [],
                "web_sources": await self.web_agent.get_latest_web_sources(conversation_id),
            }
        return {
            "sources": await self.paper_agent.get_latest_sources(conversation_id),
            "web_sources": [],
        }

    # 종합 checkpointer에서 대화 내역 조회
    async def get_history(self, conversation_id: str) -> list[dict]:
        """종합 에이전트의 checkpointer에서 이 방의 대화(질문↔종합답변)를 반환한다.

        팬아웃 구조에선 검색(paper/web run)에 checkpointer가 없어 대화가 안 쌓이고,
        진짜 답변인 종합(synthesis)만 thread_id별로 저장된다. 따라서 synthesis
        에이전트의 checkpointer를 조회한다. 기존 chat_agent.get_history와 동일하게
        human/ai 실제 발화만 필터링한다.

        주의: synthesis 입력 user content는 "[질문]\\n{q}\\n\\n[논문 기반 답변]\\n..."
        형태로 저장된다(LLM 종합용). 화면에는 순수 질문만 보여야 하므로, user 메시지는
        "[질문]\\n" 다음부터 "[논문 기반 답변]" 전까지만 잘라 원질문으로 복원해 반환한다.
        """
        agent = await self.synthesis_agent._ensure_stream_agent()
        state = await agent.aget_state(
            {"configurable": {"thread_id": conversation_id}}
        )
        messages = state.values.get("messages", []) if state.values else []
        history = []
        for msg in messages:
            msg_type = getattr(msg, "type", None)
            content = getattr(msg, "content", "")
            if msg_type == "human":
                # 저장된 content에서 순수 질문만 복원(논문/웹 답변 텍스트 제거).
                pure_query = content.split("\n\n[논문 기반 답변]")[0]
                pure_query = pure_query.replace("[질문]\n", "").strip()
                history.append({"role": "user", "content": pure_query})
            elif msg_type == "ai" and content:
                # 도구 호출만 있는(content 비어있는) AI 메시지는 제외
                history.append({"role": "assistant", "content": content})
        return history

    # 그래프 시각화 메소드 (디버깅)
    def get_graph_image(self):
        """컴파일된 그래프 구조의 Mermaid 이미지를 PNG 바이트로 반환한다.

        Returns:
            bytes: 그래프의 PNG 바이너리 데이터.
        """
        return self.work_flow.get_graph().draw_mermaid_png()


ChatMultiAgentSupervisorDep = Annotated[
    ChatMultiAgentSupervisor, Depends(ChatMultiAgentSupervisor)
]
