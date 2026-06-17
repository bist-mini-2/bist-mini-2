import logging
from typing import Annotated, Optional
from fastapi import Depends
from sqlalchemy import select
from api.database.config.dbsession import OrmSessionDep
from api.v1.research_gap.entity import ResearchGapTaskEntity


class ResearchGapDao:
    """대규모 문헌 비교 분석 태스크의 DB 상태 관리를 수행하는 데이터 액세스 객체(DAO)입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        self.logger = logging.getLogger(f"{__name__}.ResearchGapDao")
        self.orm_session = orm_session

    async def create_task(
        self, task_id: str, domain: str, query: str, mid: str
    ) -> ResearchGapTaskEntity:
        """새로운 분석 배치 태스크를 PENDING 상태로 생성합니다.

        Args:
            task_id (str): 생성할 태스크 고유 ID.
            domain (str): 학술 분야 (cs).
            query (str): 검색 질의어.
            mid (str): 사용자의 식별자 ID.

        Returns:
            ResearchGapTaskEntity: 생성된 태스크 ORM 객체.
        """
        self.logger.info(f"create_task: {task_id} (mid={mid}, domain={domain}, query={query})")
        task = ResearchGapTaskEntity(
            task_id=task_id,
            mid=mid,
            domain=domain,
            query=query,
            status="PENDING",
            progress=0
        )
        self.orm_session.add(task)
        await self.orm_session.flush()
        return task

    async def get_task(self, task_id: str, mid: Optional[str] = None) -> Optional[ResearchGapTaskEntity]:
        """주어진 ID에 해당하는 분석 태스크를 조회합니다.

        Args:
            task_id (str): 태스크 고유 ID.
            mid (Optional[str]): 소유자 조회를 위한 사용자 ID.

        Returns:
            Optional[ResearchGapTaskEntity]: 매칭된 태스크 ORM 객체 또는 None.
        """
        self.logger.info(f"get_task: {task_id} (mid={mid})")
        stmt = select(ResearchGapTaskEntity).where(ResearchGapTaskEntity.task_id == task_id)
        if mid is not None:
            stmt = stmt.where(ResearchGapTaskEntity.mid == mid)
        result = await self.orm_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_task_progress(
        self,
        task_id: str,
        status: str,
        progress: int,
        result: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> Optional[ResearchGapTaskEntity]:
        """분석 태스크의 진행도 및 상태를 갱신합니다.

        Args:
            task_id (str): 태스크 고유 ID.
            status (str): 새 작업 상태 (RUNNING, COMPLETED, FAILED).
            progress (int): 새 진행율 (0 ~ 100).
            result (Optional[dict]): 분석 완료 시 저장할 JSON 결과 데이터.
            error_message (Optional[str]): 실패 시 기록할 에러 메시지.

        Returns:
            Optional[ResearchGapTaskEntity]: 갱신된 태스크 ORM 객체 또는 None.
        """
        self.logger.info(f"update_task_progress: {task_id} (status={status}, progress={progress})")
        task = await self.get_task(task_id)
        if task:
            task.status = status
            task.progress = progress
            if result is not None:
                task.result = result
            if error_message is not None:
                task.error_message = error_message
            await self.orm_session.flush()
        return task


ResearchGapDaoDep = Annotated[ResearchGapDao, Depends(ResearchGapDao)]
