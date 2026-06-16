import logging
from typing import Annotated
from fastapi import Depends
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langgraph.prebuilt import create_react_agent

from api.common.config import settings
from api.v1.cs.dao import CsDaoDep
from api.v1.cs.embedding import embedding_helper
from api.v1.cs.models import (
    SimilaritySearchResult,
    SimilaritySearchResponse,
    CsRagQueryResponse,
    CsAgentQueryResponse,
)


@tool
async def search_cs_papers(
    search_query: str,
    config: RunnableConfig
) -> str:
    """컴퓨터 과학(Neural and Evolutionary Computing, cs.NE 카테고리) 관련 학술 논문 데이터베이스에서 검색을 수행합니다.
    인공신경망, 진화 컴퓨팅, 유전 알고리즘, 신경망 학습 다이내믹스 등의 개념에 대한 질문에 대답하거나 참고 자료가 필요할 때 이 툴을 사용하세요.
    입력값(search_query)은 검색어 텍스트여야 합니다.
    """
    cs_service: "CsService" = config.get("configurable", {}).get("cs_service")
    if not cs_service:
        return "오류: cs_service가 설정에 제공되지 않았습니다."

    search_res = await cs_service.search_similar_papers(search_query, top_k=3)
    if not search_res.results:
        return "검색 결과가 데이터베이스에 존재하지 않습니다."
        
    formatted_results = []
    for idx, item in enumerate(search_res.results):
        formatted_results.append(
            f"[문서 {idx+1}]\n논문 ID: {item.doc_id}\n제목: {item.title}\n내용 청크: {item.text_chunk}\n"
        )
    return "\n".join(formatted_results)


class LlmLoggingHandler(BaseCallbackHandler):
    """LLM의 프롬프트 입출력 내역을 표준 로거로 수집하고 기록하는 커스텀 콜백 핸들러입니다."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("api.v1.cs.llm")

    def on_llm_start(
        self, serialized: dict, prompts: list[str], **kwargs
    ) -> None:
        """LLM 호출 시작 시 프롬프트를 로깅합니다.

        Args:
            serialized (dict): 모델 직렬화 객체 정보.
            prompts (list[str]): 입력 프롬프트 리스트.
            **kwargs: 추가 키워드 인자.
        """
        for prompt in prompts:
            self.logger.info(f"[LLM INPUT PROMPT]\n{prompt}")

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 응답 완료 시 생성 결과를 로깅합니다.

        Args:
            response (LLMResult): LLM 생성 결과 객체.
            **kwargs: 추가 키워드 인자.
        """
        for generation in response.generations:
            for g in generation:
                self.logger.info(f"[LLM OUTPUT ANSWER]\n{g.text}")


class CsService:
    """컴퓨터 과학(CS) 도메인의 RAG 유사도 검색 및 임베딩 처리 비즈니스 로직을 처리합니다."""

    def __init__(self, cs_dao: CsDaoDep) -> None:
        self.logger = logging.getLogger(f"{__name__}.CsService")
        self.cs_dao = cs_dao

    async def search_similar_papers(self, query: str, top_k: int) -> SimilaritySearchResponse:
        """질의어(Query)를 임베딩으로 변환한 뒤, 유사도가 높은 상위 논문 청크 목록을 검색합니다.

        Args:
            query (str): 사용자의 질의 텍스트.
            top_k (int): 반환할 상위 결과 개수.

        Returns:
            SimilaritySearchResponse: 매칭된 유사 청크 목록을 포함한 DTO 응답 객체.
        """
        self.logger.info("search_similar_papers 실행")
        # 1. 쿼리 텍스트 임베딩 생성 (싱글톤 helper 활용)
        query_vector = embedding_helper.encode(query)

        # 2. DAO를 통해 유사도 높은 청크들 조회
        raw_results = await self.cs_dao.select_similar_chunks(query_vector, top_k)

        # 3. DTO 리스트로 결과 변환
        results_list = []
        for doc_id, title, chunk_text, score in raw_results:
            results_list.append(
                SimilaritySearchResult(
                    doc_id=doc_id,
                    title=title,
                    text_chunk=chunk_text,
                    score=score
                )
            )

        return SimilaritySearchResponse(results=results_list)

    async def answer_question_with_rag(
        self, query: str, top_k: int, llm_model: str = "gpt-4o-mini"
    ) -> CsRagQueryResponse:
        """RAG 파이프라인을 활용하여 질의에 대한 유사 논문 출처를 찾고, 이를 참고하여 답변을 생성합니다.

        Args:
            query (str): 사용자의 질문 텍스트.
            top_k (int): 참고할 유사 논문 청크 상위 개수.
            llm_model (str, optional): 사용할 OpenAI LLM 모델명. Defaults to "gpt-4o-mini".

        Returns:
            CsRagQueryResponse: 생성된 답변과 참고한 논문 청크 출처 리스트 DTO.
        """
        self.logger.info("answer_question_with_rag 실행")

        # 1. 유사 논문 청크 검색
        search_response = await self.search_similar_papers(query, top_k)
        sources = search_response.results

        # 2. 콘텍스트 생성
        context_parts = []
        for idx, src in enumerate(sources):
            context_parts.append(
                f"[Document {idx + 1}]\n"
                f"Title: {src.title}\n"
                f"Content: {src.text_chunk}\n"
            )
        context = "\n".join(context_parts)

        # 3. LLM 프롬프트 빌드 및 실행
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert AI assistant specialized in Computer Science, specifically in "
                "Neural and Evolutionary Computing (cs.NE).\n"
                "Your task is to answer the user's question as accurately as possible based on the provided "
                "scientific paper context.\n\n"
                "Constraints:\n"
                "- Write the response in Korean.\n"
                "- Make your response polite, professional, and well-structured.\n"
                "- Base your answer primarily on the provided context. If the context does not contain "
                "enough information to answer, formulate a reasonable answer using your general knowledge, "
                "but clearly mention that it was not found in the retrieved documents."
            )),
            ("user", "Context:\n{context}\n\nQuestion: {question}")
        ])

        # ChatOpenAI 인스턴스 획득 (API Key는 settings에서 주입)
        llm = ChatOpenAI(
            model=llm_model,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.2,
            callbacks=[LlmLoggingHandler()]
        )

        # 프롬프트 구성 및 비동기 호출 실행
        chain = prompt_template | llm
        llm_response = await chain.ainvoke({
            "context": context,
            "question": query
        })

        answer_text = str(llm_response.content).strip()

        return CsRagQueryResponse(
            answer=answer_text,
            sources=sources
        )

    async def run_agent_with_rag_tool(
        self, query: str, llm_model: str = "gpt-4o-mini"
    ) -> CsAgentQueryResponse:
        """RAG 파이프라인을 툴(Tool)로 정의하고, LangGraph React Agent를 통해 에이전트 답변을 생성합니다.

        Args:
            query (str): 사용자의 질문 텍스트.
            llm_model (str, optional): 사용할 OpenAI LLM 모델명. Defaults to "gpt-4o-mini".

        Returns:
            CsAgentQueryResponse: 생성된 답변과 실행된 툴 정보 목록이 담긴 응답 DTO.
        """
        self.logger.info("run_agent_with_rag_tool 실행")

        # 1. 모듈 레벨 툴 목록 정의
        tools = [search_cs_papers]

        # 2. Agent 구성
        llm = ChatOpenAI(
            model=llm_model,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0,
            callbacks=[LlmLoggingHandler()]
        )
        
        agent = create_react_agent(llm, tools)
        
        # 3. Agent 실행 (config를 전달하여 cs_service 의존성 주입)
        response = await agent.ainvoke(
            {"messages": [("user", query)]},
            config={"configurable": {"cs_service": self}}
        )
        
        messages = response["messages"]
        final_answer = messages[-1].content
        
        # 4. 사용된 툴 콜(Tool Calls) 수집
        tool_calls = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "name": tc.get("name"),
                        "args": tc.get("args"),
                        "id": tc.get("id")
                    })
                    
        return CsAgentQueryResponse(
            answer=str(final_answer).strip(),
            tool_calls=tool_calls
        )


CsServiceDep = Annotated[CsService, Depends(CsService)]
