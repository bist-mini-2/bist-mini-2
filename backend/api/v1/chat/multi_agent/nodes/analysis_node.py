import logging

from api.v1.chat.multi_agent.agents.analysis_agent import AnalysisAgent
from api.v1.chat.multi_agent.state import MultiAgentState


logger = logging.getLogger(__name__)

# 모듈 싱글톤 에이전트 생성
agent = AnalysisAgent()


# 라우팅 분석 노드 정의 (얇은 래퍼)
async def analysis_node(state: MultiAgentState) -> dict:
    logger.info("라우팅 분석 노드 실행")
    # 상태에서 사용자 질문 꺼내기
    query = state["user_query"]
    # 에이전트를 실행해 라우팅 결과 얻기
    result = await agent.run(query)
    logger.info(f"라우팅 결정: route={result['route']} reason={result['reason']}")
    # 상태 업데이트: 라우팅 결과 저장
    return {"route": result["route"]}
