import asyncio
import json
import logging
from typing import Annotated, Optional, AsyncGenerator
from fastapi import Depends
from sqlalchemy import select
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from api.common.config import settings
from api.database.config.dbsession import session_maker
from api.v1.research_gap.dao import ResearchGapDaoDep, ResearchGapDao
from api.v1.research_gap.embedding import embedding_helper
from api.v1.notification.notifier import notification_broadcaster

from api.v1.cs.entity import CsEmbeddingEntity
from api.v1.research_gap.models import PaperAnalysisResult, ResearchGapMatrix


class ResearchGapService:
    """대규모 문헌 비교 및 학계 연구 공백(Research Gap) 분석을 수행하는 서비스입니다."""

    def __init__(self, research_gap_dao: ResearchGapDaoDep) -> None:
        self.logger = logging.getLogger(f"{__name__}.ResearchGapService")
        self.research_gap_dao = research_gap_dao

    async def get_task_status(self, task_id: str, mid: str) -> dict:
        """태스크 ID로 현재 배치 분석 작업의 진행 상태를 조회합니다.

        Args:
            task_id (str): 태스크 고유 ID.
            mid (str): 사용자의 식별자 ID.

        Returns:
            dict: 태스크 상태 필드가 정의된 딕셔너리.

        Raises:
            TaskNotFoundError: 요청한 분석 배치 태스크를 찾을 수 없을 때.
        """
        task = await self.research_gap_dao.get_task(task_id, mid=mid)
        if not task:
            from api.common.exceptions import TaskNotFoundError
            raise TaskNotFoundError(
                message=f"요청하신 태스크 ID를 찾을 수 없습니다: {task_id}"
            )
        return {
            "task_id": task.task_id,
            "domain": task.domain,
            "query": task.query,
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }

    async def get_task_result(self, task_id: str, mid: str) -> dict:
        """태스크 ID로 완료된 배치 분석의 최종 결과 데이터를 조회합니다.

        Args:
            task_id (str): 태스크 고유 ID.
            mid (str): 사용자의 식별자 ID.

        Returns:
            dict: 최종 분석 매트릭스 및 연구 공백 제안 리포트 또는 에러 상세.

        Raises:
            TaskNotFoundError: 요청한 분석 배치 태스크를 찾을 수 없을 때.
        """
        task = await self.research_gap_dao.get_task(task_id, mid=mid)
        if not task:
            from api.common.exceptions import TaskNotFoundError
            raise TaskNotFoundError(
                message=f"요청하신 태스크 ID를 찾을 수 없습니다: {task_id}"
            )
        return {
            "task_id": task.task_id,
            "status": task.status,
            "progress": task.progress,
            "result": task.result,
            "translated_result": task.translated_result,
            "error_message": task.error_message
        }

    async def start_analysis(self, domain: str, query: str, background_tasks, mid: str) -> str:
        """분석 요청을 받아 유효성을 확인한 뒤 새 태스크를 생성하고 백그라운드 배치 연산을 예약합니다.

        Args:
            domain (str): 학술 도메인 (cs).
            query (str): 분석할 기술/키워드.
            background_tasks: FastAPI BackgroundTasks 객체.
            mid (str): 사용자의 식별자 ID.

        Returns:
            str: 생성된 태스크 고유 ID (UUID).
        
        Raises:
            BusinessException: 지원하지 않는 도메인이 입력되었을 경우.
        """
        target_domain = domain.lower().strip()
        if target_domain != "cs":
            from api.common.exceptions import BusinessException
            raise BusinessException(
                message="지원되지 않는 도메인입니다. 현재는 'cs' 도메인만 분석을 지원합니다.",
                error_code="UNSUPPORTED_DOMAIN"
            )

        import uuid
        task_id = str(uuid.uuid4())
        
        # 1. 태스크 생성 (PENDING)
        await self.research_gap_dao.create_task(task_id, target_domain, query, mid)
        
        # 2. 백그라운드 배치 작업 실행 등록
        background_tasks.add_task(self.run_batch_analysis, task_id, target_domain, query, mid)
        
        return task_id


    async def run_batch_analysis(self, task_id: str, domain: str, query: str, mid: str) -> None:
        """백그라운드에서 실행되는 비동기 분석 배치 처리 코어 로직입니다.

        독자적인 DB 세션을 생성하여 단계별 상태 및 진행률을 커밋하고 완료 시 SSE 이벤트를 방출합니다.
        """
        self.logger.info(f"Background batch task {task_id} started (mid={mid}, domain={domain}, query={query})")

        # 1. RUNNING 상태로 업데이트 (10%)
        async with session_maker() as session:
            dao = ResearchGapDao(session)
            await dao.update_task_progress(task_id, "RUNNING", 10)
            await session.commit()

        try:
            # 2. 쿼리 임베딩 인코딩 수행
            self.logger.info("Encoding query vector...")
            query_vector = embedding_helper.encode(query)

            # 3. DB 세션에서 유사 논문 리스트 검색 (Top 5) (30%)
            papers_list = []
            async with session_maker() as session:
                if domain == "cs":
                    # cs_embeddings 단일 테이블 쿼리 및 cmetadata 로드
                    stmt = (
                        select(
                            CsEmbeddingEntity.cmetadata,
                            CsEmbeddingEntity.document.label("content")
                        )
                        .order_by(CsEmbeddingEntity.embedding.cosine_distance(query_vector).asc())
                        .limit(5)
                    )
                    result = await session.execute(stmt)
                    raw_rows = result.mappings().all()
                    
                    for row in raw_rows:
                        meta = row["cmetadata"] or {}
                        papers_list.append({
                            "arxiv_id": meta.get("arxiv_id") or meta.get("doc_id") or "",
                            "title": meta.get("title", ""),
                            "content": row["content"]
                        })
                else:
                    raise ValueError(f"지원하지 않는 도메인입니다: {domain}")

            if not papers_list:
                raise ValueError("검색된 관련 논문 자료가 없습니다. 데이터베이스 적재 상태 또는 키워드를 확인해 주세요.")

            # RUNNING 상태로 업데이트 (40%)
            async with session_maker() as session:
                dao = ResearchGapDao(session)
                await dao.update_task_progress(task_id, "RUNNING", 40)
                await session.commit()

            # 4. LLM을 활용한 개별 논문 분석 (Problems Solved / Limitations) (60%)
            self.logger.info(f"Analyzing {len(papers_list)} papers with LLM Structured Output...")
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0
            )
            structured_llm = llm.with_structured_output(PaperAnalysisResult)

            analyzed_papers = []
            for paper in papers_list:
                paper_id = paper["arxiv_id"]
                title = paper["title"]
                content = paper["content"]

                prompt = ChatPromptTemplate.from_messages([
                    ("system", (
                        "You are an academic researcher analyzing a scientific paper abstract.\n"
                        "Extract the problems solved (or core methodologies proposed) and the limitations (or future gaps) "
                        "discussed in the provided text.\n"
                        "Response must be in English and structured in the requested format."
                    )),
                    ("user", "Title: {title}\nArXiv ID: {arxiv_id}\n\nContent:\n{content}")
                ])

                chain = prompt | structured_llm
                result_obj = await chain.ainvoke({
                    "title": title,
                    "arxiv_id": paper_id,
                    "content": content
                })

                if not isinstance(result_obj, PaperAnalysisResult):
                    raise TypeError(f"Expected PaperAnalysisResult, got {type(result_obj)}")

                analyzed_papers.append(result_obj)

            # RUNNING 상태로 업데이트 (80%)
            async with session_maker() as session:
                dao = ResearchGapDao(session)
                await dao.update_task_progress(task_id, "RUNNING", 80)
                await session.commit()

            # 5. 연구 공백 추론 및 AI 추천 연구 주제 합성 (95%)
            self.logger.info("Synthesizing Research Gap Matrix and Proposing Research Directions...")
            matrix_data = "\n\n".join([
                f"Paper: {p.title} (ID: {p.arxiv_id})\n"
                f"- Solved: {', '.join(p.problems_solved)}\n"
                f"- Limitations: {', '.join(p.limitations)}"
                for p in analyzed_papers
            ])

            synthesis_prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a visionary research scientist overseeing the research gap matrix of a specific domain.\n"
                    "Review the analysis results of multiple papers, identify the common limitations (underlying gaps), "
                    "and propose 3 highly innovative and concrete future research topics (suggested directions) to address those gaps.\n"
                    "Respond in English. Structure the response strictly according to the format."
                )),
                ("user", "Research Gap Matrix:\n{matrix_data}\n\nTarget Domain: {domain}\nTarget Query/Topic: {query}")
            ])

            synthesis_llm = llm.with_structured_output(ResearchGapMatrix)
            final_report = await (synthesis_prompt | synthesis_llm).ainvoke({
                "matrix_data": matrix_data,
                "domain": domain,
                "query": query
            })

            if not isinstance(final_report, ResearchGapMatrix):
                raise TypeError(f"Expected ResearchGapMatrix, got {type(final_report)}")

            # 6. COMPLETED 상태로 업데이트 및 결과 저장 (100%)
            async with session_maker() as session:
                dao = ResearchGapDao(session)
                await dao.update_task_progress(
                    task_id,
                    "COMPLETED",
                    100,
                    result=final_report.model_dump()
                )
                await session.commit()

            self.logger.info(f"Batch task {task_id} completed successfully.")

            import uuid
            notif_id = str(uuid.uuid4())
            notif_title = "연구 공백 분석 완료"
            notif_msg = f"[{domain.upper()}] \"{query}\" 주제의 문헌 비교 분석이 완료되었습니다."
            notif_type = "success"

            # DB에 알림 저장
            async with session_maker() as session:
                from api.v1.notification.dao import NotificationDao
                notif_dao = NotificationDao(session)
                await notif_dao.create_notification(
                    id=notif_id,
                    mid=mid,
                    title=notif_title,
                    message=notif_msg,
                    type=notif_type,
                    task_id=task_id
                )
                await session.commit()

            # 7. SSE 완료 브로드캐스트 전송
            await notification_broadcaster.broadcast({
                "id": notif_id,
                "event": "task_completed",
                "task_id": task_id,
                "domain": domain,
                "query": query,
                "status": "COMPLETED",
                "progress": 100,
                "mid": mid,
                "title": notif_title,
                "message": notif_msg,
                "type": notif_type
            })

        except Exception as e:
            self.logger.error(f"Error executing batch analysis task {task_id}: {e}", exc_info=True)
            async with session_maker() as session:
                dao = ResearchGapDao(session)
                await dao.update_task_progress(
                    task_id,
                    "FAILED",
                    100,
                    error_message=str(e)
                )
                await session.commit()

            import uuid
            notif_id = str(uuid.uuid4())
            notif_title = "연구 공백 분석 실패"
            notif_msg = f"[{domain.upper()}] \"{query}\" 분석 중 에러가 발생했습니다: {str(e)}"
            notif_type = "danger"

            # DB에 알림 저장
            async with session_maker() as session:
                from api.v1.notification.dao import NotificationDao
                notif_dao = NotificationDao(session)
                await notif_dao.create_notification(
                    id=notif_id,
                    mid=mid,
                    title=notif_title,
                    message=notif_msg,
                    type=notif_type,
                    task_id=task_id
                )
                await session.commit()

            # SSE 실패 브로드캐스트 전송
            await notification_broadcaster.broadcast({
                "id": notif_id,
                "event": "task_failed",
                "task_id": task_id,
                "domain": domain,
                "query": query,
                "status": "FAILED",
                "progress": 100,
                "error_message": str(e),
                "mid": mid,
                "title": notif_title,
                "message": notif_msg,
                "type": notif_type
            })

    async def translate_matrix(self, task_id: str, mid: str) -> dict:
        """주어진 태스크 ID의 영문 분석 결과를 한국어로 번역하고 DB에 캐싱합니다.

        이미 번역된 결과가 존재하는 경우 DB에서 바로 반환합니다.

        Args:
            task_id (str): 태스크 고유 ID.
            mid (str): 사용자의 식별자 ID.

        Returns:
            dict: 한국어로 번역된 분석 결과 객체 딕셔너리.
        """
        # 1. DB에서 태스크 정보 로드 및 검증
        task = await self.research_gap_dao.get_task(task_id, mid=mid)
        if not task:
            from api.common.exceptions import TaskNotFoundError
            raise TaskNotFoundError(
                message=f"요청하신 태스크 ID를 찾을 수 없습니다: {task_id}"
            )
            
        # 2. 이미 번역된 결과가 있다면 바로 반환 (Cache Hit)
        if task.translated_result:
            self.logger.info(f"Returning cached translation for task: {task_id}")
            return task.translated_result

        # 3. 영문 분석 결과가 아직 없는 경우 예외 처리
        if not task.result or task.status != "COMPLETED":
            from api.common.exceptions import BusinessException
            raise BusinessException(
                message="분석이 아직 완료되지 않았거나 결과가 존재하지 않아 번역을 진행할 수 없습니다.",
                error_code="TRANSLATION_NOT_READY"
            )

        # 4. LLM을 통해 번역 수행
        from api.v1.research_gap.models import ResearchGapMatrix
        matrix = ResearchGapMatrix.model_validate(task.result)
        
        self.logger.info(f"Translating ResearchGapMatrix for task {task_id} to Korean...")
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert academic translator specializing in computer science.\n"
                "Translate the given Research Gap Matrix (including paper titles, problems solved, limitations, common limitations, and suggested directions) into natural and professional Korean.\n"
                "Maintain the academic context and terminology accurately (e.g. keep common technical terms like RAG, LLM, prompt caching in English or use standard Korean translations).\n"
                "Response must be structured in the requested format."
            )),
            ("user", "{matrix_json}")
        ])
        
        structured_llm = llm.with_structured_output(ResearchGapMatrix)
        chain = prompt | structured_llm
        
        translated = await chain.ainvoke({
            "matrix_json": json.dumps(matrix.model_dump(), ensure_ascii=False)
        })
        
        if not isinstance(translated, ResearchGapMatrix):
            raise TypeError(f"Expected ResearchGapMatrix, got {type(translated)}")
            
        translated_dict = translated.model_dump()
        
        # 5. DB에 번역본 저장 및 커밋
        async with session_maker() as session:
            from api.v1.research_gap.dao import ResearchGapDao
            dao = ResearchGapDao(session)
            await dao.update_task_translation(task_id, translated_dict)
            await session.commit()
            
        return translated_dict

    async def list_user_tasks(self, mid: str) -> list[dict]:
        """주어진 사용자 ID가 요청한 모든 분석 태스크 정보 목록을 조회합니다.

        Args:
            mid (str): 사용자의 식별자 ID.

        Returns:
            list[dict]: 사용자 소유의 태스크 정보 딕셔너리 리스트.
        """
        tasks = await self.research_gap_dao.list_tasks(mid=mid)
        return [
            {
                "task_id": t.task_id,
                "domain": t.domain,
                "query": t.query,
                "status": t.status,
                "progress": t.progress,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            }
            for t in tasks
        ]


ResearchGapServiceDep = Annotated[ResearchGapService, Depends(ResearchGapService)]
