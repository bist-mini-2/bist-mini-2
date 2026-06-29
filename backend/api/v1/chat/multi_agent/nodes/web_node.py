import logging

from api.v1.chat.multi_agent.agents.web_agent import WebAgent
from api.v1.chat.multi_agent.state import MultiAgentState


logger = logging.getLogger(__name__)

# 모듈 싱글톤 에이전트 생성
agent = WebAgent()


# 웹 검색 노드 정의 (얇은 래퍼)
async def web_node(state: MultiAgentState) -> dict:
    logger.info("웹 검색 노드 실행")
    # 에이전트를 실행해 답변과 웹 출처 얻기
    result = await agent.run(state["user_query"])
    # 상태 업데이트: 웹 답변(종합 입력용)과 웹 출처 저장.
    # 병렬 실행이므로 paper_node와 같은 final_response를 쓰면 서로 덮어쓴다 → 별도 필드에 저장.
    return {
        "web_answer": result["answer"],
        "web_sources": result["web_sources"],
    }
