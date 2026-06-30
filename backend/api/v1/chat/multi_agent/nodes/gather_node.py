import logging

from api.v1.chat.multi_agent.state import MultiAgentState


logger = logging.getLogger(__name__)


# 병렬 실행 완료 대기 노드 정의 (paper_node·web_node가 모두 끝나야 진입)
async def gather_node(state: MultiAgentState) -> dict:
    logger.info("병렬 실행 완료 대기 노드 실행")
    # 상태 변경 없이 합류만 한다(로깅용).
    logger.info(f"paper_answer 길이: {len(state.get('paper_answer', ''))}")
    logger.info(f"web_answer 길이: {len(state.get('web_answer', ''))}")
    return {}
