import logging

from langchain.agents import create_agent
from pydantic import BaseModel, Field


#################################################################################
# 구조화된 출력 스키마
#################################################################################
class SearchQuery(BaseModel):
    """이미지 분석으로 생성한 검색 쿼리 스키마."""
    query: str = Field(
        description="이미지와 질문에서 도출한 학술 논문 검색용 한국어 쿼리(키워드 중심)."
    )


#################################################################################
# Agent 클래스
#################################################################################
class ImageAgent:
    """이미지 분석 Agent.

    사용자가 올린 이미지(그래프/도표 등)와 질문을 함께 분석해, 논문·웹 검색에
    사용할 검색 쿼리 텍스트를 생성한다. gpt-4o-mini의 멀티모달(비전) 능력을 쓰며
    별도 비전 모델은 사용하지 않는다. analysis_agent의 구조화 출력 패턴을 따른다.
    """

    # 초기화 메소드
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.ImageAgent")
        system_prompt = """
            당신은 사용자가 올린 이미지(그래프, 도표, 다이어그램, 수식 등)와 질문을 함께
            분석해, 학술 논문 검색에 사용할 검색 쿼리를 생성하는 전문가입니다.

            작업 방식:
            - 이미지에서 보이는 핵심 주제·개념·기법을 파악합니다.
              (그래프 종류, 축 라벨, 데이터 형태, 표시된 용어 등)
            - 사용자의 질문 의도와 합쳐, 관련 논문을 찾기에 적합한 검색 쿼리를 만듭니다.
            - 쿼리는 한국어로, 핵심 개념을 담은 키워드 중심으로 작성합니다.
              (완전한 문장보다 검색에 적합한 핵심어 나열에 가깝게)
              예) "단일세포 RNA 시퀀싱 UMAP 클러스터링 세포 유형"
                  "외계행성 통과 광도곡선 검출"
            - 이미지만으로 주제가 불분명하면, 질문 내용을 더 비중 있게 반영합니다.

            query에는 검색 쿼리 텍스트만 담으세요.
        """
        self.agent = create_agent(
            model=model,
            system_prompt=system_prompt,
            response_format=SearchQuery,
        )

    # 에이전트 실행 메소드
    async def run(self, image_data_url: str, query: str) -> dict:
        """이미지(data URL)와 질문을 분석해 검색 쿼리를 dict로 반환한다.

        Args:
            image_data_url: "data:image/png;base64,..." 형식의 이미지 data URL 통째.
            query: 사용자 질문 텍스트.

        Returns:
            dict: {"query": "<생성된 검색 쿼리>"}
        """
        self.logger.info("이미지 분석 에이전트 실행")
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": [
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]}]}
        )
        analysis: SearchQuery = result["structured_response"]
        return analysis.model_dump()
