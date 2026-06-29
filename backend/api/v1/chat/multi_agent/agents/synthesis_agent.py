import logging

from langchain.agents import create_agent


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
            - 웹 기반 답변의 최신 정보·동향을 자연스럽게 녹인다.
            - 중복은 합치고, 모순되면 양쪽 관점을 모두 제시한다.
            - 서론/결론 없이 본문 중심으로, 읽기 쉽게 단락을 나눠 작성한다.
        """
        # 도구 없이 LLM만 사용하는 종합 에이전트.
        self.agent = create_agent(
            model=model,
            system_prompt=system_prompt,
        )

    # 에이전트 실행 메소드
    async def run(self, query: str, paper_answer: str, web_answer: str) -> str:
        """질문과 두 답변을 받아 종합한 답변 본문을 반환한다."""
        self.logger.info("종합 에이전트 실행")
        content = (
            f"[질문]\n{query}\n\n"
            f"[논문 기반 답변]\n{paper_answer}\n\n"
            f"[웹 기반 답변]\n{web_answer}"
        )
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": content}]}
        )
        return result["messages"][-1].content
