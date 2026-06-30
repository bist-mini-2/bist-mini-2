import logging

from api.v1.chat.multi_agent.agents.synthesis_agent import SynthesisAgent
from api.v1.chat.multi_agent.state import MultiAgentState


logger = logging.getLogger(__name__)

# 모듈 싱글톤 에이전트 생성
agent = SynthesisAgent()


# 종합 노드 정의 (얇은 래퍼)
async def synthesis_node(state: MultiAgentState) -> dict:
    logger.info("종합 노드 실행")
    # 논문 답변 + 웹 답변을 받아 하나의 종합 답변 생성
    answer = await agent.run(
        state["user_query"],
        state.get("paper_answer", ""),
        state.get("web_answer", ""),
    )
    # 상태 업데이트: 최종 답변 저장
    return {"final_response": answer}
