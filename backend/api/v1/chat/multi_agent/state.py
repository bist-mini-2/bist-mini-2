from typing import Annotated, TypedDict
from langgraph.graph import add_messages


class MultiAgentState(TypedDict):
    """슈퍼바이저 멀티 에이전트가 공유하는 상태.

    강사님 sec09 ShareState 패턴을 따르되, 기존 채팅의 sources/web_sources를
    유지해 인용·출처 저장 기능을 그대로 살린다.
    """
    messages: Annotated[list, add_messages]   # 대화 메시지 누적
    user_query: str         # 사용자 원본 질문
    route: str              # 라우팅 결정 ("paper" 또는 "web")
    sources: list[dict]     # 논문 검색 출처 누적 (인용/카드용)
    web_sources: list[dict] # 웹 검색 출처 누적
    paper_answer: str       # 논문 에이전트 답변(종합 입력용)
    web_answer: str         # 웹 에이전트 답변(종합 입력용)
    final_response: str     # 최종 답변 본문