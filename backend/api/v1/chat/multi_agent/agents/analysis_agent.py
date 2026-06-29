import logging

from langchain.agents import create_agent
from pydantic import BaseModel, Field


#################################################################################
# 구조화된 출력 스키마
#################################################################################
class RouteResult(BaseModel):
    """라우팅 분석 결과 스키마."""
    route: str = Field(description="처리 경로. 반드시 'paper' 또는 'web' 중 하나.")
    reason: str = Field(description="해당 경로로 결정한 이유 한 줄 설명.")


#################################################################################
# Agent 클래스
#################################################################################
class AnalysisAgent:
    """라우팅 분석 Agent.

    사용자 질문을 분석해 논문 검색(paper)으로 답할지 웹 검색(web)으로 답할지 결정한다.
    강사님 sec09 AnalysisAgent 패턴을 따라 response_format으로 구조화 출력을 받는다.
    """

    # 초기화 메소드
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        # 로거 설정
        self.logger = logging.getLogger(f"{__name__}.AnalysisAgent")
        # 라우팅 기준을 담은 시스템 프롬프트
        system_prompt = """
            당신은 사용자 질문을 분석해 적절한 처리 경로를 결정하는 라우팅 전문가입니다.
            질문을 읽고 'paper' 또는 'web' 중 하나로 분류하세요.

            - paper: arXiv 논문으로 답할 수 있는 학술·과학·기술 주제.
                · 생명공학·유전체학 (유전자, DNA, 시퀀싱, 유전체, CRISPR, 유전자 편집,
                  단백질, 분자생물학 등)
                · 천문학 (외계행성, 행성, 천체물리, 항성, 은하 등)
                · 컴퓨터과학 (신경망, 딥러닝, 진화 알고리즘, 머신러닝 등)
                위 분야의 '개념·원리·메커니즘·연구'를 묻는 질문은 일반 상식처럼 보여도
                반드시 paper로 분류합니다.
            - web: 위 학술 분야에 속하지 않는, 시점·시사·생활 정보 질문.
                · 오늘 날씨, 환율, 주가, 스포츠 경기 결과, 뉴스, 특정 인물·제품의 최신 소식 등.

            판단 기준:
            - 생명공학·천문학·컴퓨터과학의 과학적 개념을 묻는다면 → paper.
            - 그 분야 밖이거나, '오늘/지금/최근'의 실시간 정보가 필요하면 → web.
            예시:
            - "CRISPR 유전자 편집이 뭐야?" → paper
            - "외계행성은 어떻게 찾아?" → paper
            - "트랜스포머 어텐션 원리 설명해줘" → paper
            - "오늘 한국 날씨 어때?" → web
            - "최근 AI 업계 뉴스 알려줘" → web

            route 값은 반드시 'paper' 또는 'web' 중 하나여야 합니다.
            reason에는 그렇게 판단한 이유를 한 줄로 적으세요.
        """
        self.agent = create_agent(
            model=model,
            system_prompt=system_prompt,
            response_format=RouteResult,
        )

    # 에이전트 실행 메소드
    async def run(self, query: str) -> dict:
        """질문을 분석해 라우팅 결과를 dict로 반환한다({"route": ..., "reason": ...})."""
        self.logger.info("라우팅 분석 에이전트 실행")
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]}
        )
        # 구조화된 분석 결과 추출
        analysis: RouteResult = result["structured_response"]
        return analysis.model_dump()
