import logging
from typing import Annotated, Any
from fastapi import Depends
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from langchain.embeddings import init_embeddings
from langchain_postgres import PGVector

from api.common.config import settings
from api.v1.cs.dao import CsDaoDep
from api.v1.cs.embedding import embedding_helper
from api.v1.cs.handler import LlmLoggingHandler
from api.v1.cs.tools import search_cs_papers
from api.v1.cs.vectorstore_conf import COLLECTION_NAME, CONNECTION, EMBED_MODEL


class CsService:
    """컴퓨터 과학(CS) 도메인의 RAG 유사도 검색 및 임베딩 처리 비즈니스 로직을 처리합니다."""

    def __init__(self, cs_dao: CsDaoDep) -> None:
        self.logger = logging.getLogger(f"{__name__}.CsService")
        self.cs_dao = cs_dao
        self._agents = {}

    def _get_agent(self, llm_model: str) -> Any:
        """지정된 LLM 모델에 대한 에이전트 컴파일 인스턴스를 가져오거나 생성합니다.

        Args:
            llm_model (str): 사용할 OpenAI LLM 모델명.

        Returns:
            Any: CompiledStateGraph 에이전트 인스턴스.

        Raises:
            BusinessException: 지원하지 않는 모델명이 전달된 경우.
        """
        allowed_models = {"gpt-4o-mini", "gpt-4o"}
        if llm_model not in allowed_models:
            from api.common.exceptions import BusinessException
            raise BusinessException(f"지원하지 않는 LLM 모델입니다: {llm_model}")

        if llm_model not in self._agents:
            self.logger.info(f"LLM 모델 {llm_model} 에 대한 신규 에이전트 컴파일을 수행합니다.")
            llm = ChatOpenAI(
                model=llm_model,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0,
                callbacks=[LlmLoggingHandler()]
            )
            # 모듈 레벨 툴 목록 정의
            tools = [search_cs_papers]
            self._agents[llm_model] = create_agent(llm, tools)

        return self._agents[llm_model]

    async def search_similar_papers(self, query: str, top_k: int) -> list[dict]:
        """질의어(Query)를 임베딩으로 변환한 뒤, 유사도가 높은 상위 논문 청크 목록을 검색합니다.

        Args:
            query (str): 사용자의 질의 텍스트.
            top_k (int): 반환할 상위 결과 개수.

        Returns:
            list[dict]: 매칭된 유사 청크 딕셔너리 목록.
        """
        self.logger.info("search_similar_papers 실행 (PGVector 활용)")
        vectorstore = PGVector(
            embeddings=init_embeddings(model=EMBED_MODEL),
            collection_name=COLLECTION_NAME,
            connection=CONNECTION,
            async_mode=True,
        )
        results = await vectorstore.asimilarity_search_with_score(query, k=top_k)

        formatted = []
        for doc, score in results:
            formatted.append({
                "doc_id": doc.metadata.get("arxiv_id") or doc.metadata.get("doc_id") or "",
                "title": doc.metadata.get("title", ""),
                "text_chunk": doc.page_content,
                "score": round(1.0 - float(score), 4)
            })

        return formatted

    async def answer_question_with_rag(
        self, query: str, top_k: int, llm_model: str = "gpt-4o-mini"
    ) -> dict[str, Any]:
        """RAG 파이프라인을 활용하여 질의에 대한 유사 논문 출처를 찾고, 이를 참고하여 답변을 생성합니다.

        Args:
            query (str): 사용자의 질문 텍스트.
            top_k (int): 참고할 유사 논문 청크 상위 개수.
            llm_model (str, optional): 사용할 OpenAI LLM 모델명. Defaults to "gpt-4o-mini".

        Returns:
            dict[str, Any]: 생성된 답변과 참고한 논문 청크 딕셔너리 리스트를 포함하는 딕셔너리.
        """
        self.logger.info("answer_question_with_rag 실행")

        # 모델 유효성 사전 검사 (DB 조회 전 조기 처리)
        allowed_models = {"gpt-4o-mini", "gpt-4o"}
        if llm_model not in allowed_models:
            from api.common.exceptions import BusinessException
            raise BusinessException(f"지원하지 않는 LLM 모델입니다: {llm_model}")

        # 1. 유사 논문 청크 검색
        sources = await self.search_similar_papers(query, top_k)

        # 2. 콘텍스트 생성
        context_parts = []
        for idx, src in enumerate(sources):
            context_parts.append(
                f"[Document {idx + 1}]\n"
                f"Title: {src['title']}\n"
                f"Content: {src['text_chunk']}\n"
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

        return {
            "answer": answer_text,
            "sources": sources
        }

    async def run_agent_with_rag_tool(
        self, query: str, llm_model: str = "gpt-4o-mini"
    ) -> dict[str, Any]:
        """RAG 파이프라인을 툴(Tool)로 정의하고, LangGraph React Agent를 통해 에이전트 답변을 생성합니다.

        Args:
            query (str): 사용자의 질문 텍스트.
            llm_model (str, optional): 사용할 OpenAI LLM 모델명. Defaults to "gpt-4o-mini".

        Returns:
            dict[str, Any]: 생성된 답변과 실행된 툴 정보 목록이 담긴 딕셔너리.
        """
        self.logger.info("run_agent_with_rag_tool 실행")

        # 1. 캐시된 Agent 구성 (매 요청 시 컴파일 방지 및 모델 검증 내장)
        agent = self._get_agent(llm_model)
        
        # 2. Agent 실행 (config를 전달하여 cs_service 의존성 주입)
        response = await agent.ainvoke(
            {"messages": [("user", query)]},
            config={"configurable": {"cs_service": self}}
        )
        
        messages = response["messages"]
        final_answer = messages[-1].content
        
        # 3. 사용된 툴 콜(Tool Calls) 및 RAG 출처(artifact) 수집
        tool_calls = []
        sources = []
        for msg in messages:
            # ToolMessage에서 artifact 필드에 담긴 RAG 출처 추출
            if getattr(msg, "type", None) == "tool" and hasattr(msg, "artifact") and msg.artifact:
                if isinstance(msg.artifact, list):
                    sources.extend(msg.artifact)

            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "name": tc.get("name"),
                        "args": tc.get("args"),
                        "id": tc.get("id")
                    })
                    
        return {
            "answer": str(final_answer).strip(),
            "sources": sources,
            "tool_calls": tool_calls
        }


CsServiceDep = Annotated[CsService, Depends(CsService)]
