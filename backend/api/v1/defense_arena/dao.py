"""보안 격리 세션 및 모의 디펜스 대화 이력의 데이터베이스 CRUD 작업을 전담하는 DAO 모듈입니다."""

import logging
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select, and_
from api.database.config.dbsession import OrmSessionDep
from api.v1.defense_arena.entity import DefenseArenaSessionEntity, DefenseHistoryEntity, DefenseArenaChunkEntity


class DefenseArenaDao:
    """defense_arena_session 및 defense_history 테이블에 대한 ORM 작업을 처리하는 DAO입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        """DefenseArenaDao 인스턴스를 초기화하고 ORM 세션을 주입합니다.

        Args:
            orm_session (OrmSessionDep): 데이터베이스 ORM 세션 의존성.
        """
        self.logger = logging.getLogger(f"{__name__}.DefenseArenaDao")
        self.orm_session = orm_session

    async def create_session(self, session: DefenseArenaSessionEntity) -> DefenseArenaSessionEntity:
        """새로운 보안 격리 세션을 생성합니다."""
        self.orm_session.add(session)
        await self.orm_session.flush()
        await self.orm_session.refresh(session)
        return session

    async def get_session(self, session_id: str) -> DefenseArenaSessionEntity | None:
        """세션 ID로 보안 격리 세션을 조회합니다."""
        return await self.orm_session.get(DefenseArenaSessionEntity, session_id)

    async def update_session_activity(self, session_id: str) -> None:
        """세션의 마지막 활동 시각을 현재 시각으로 업데이트하여 만료 타이머를 연장합니다."""
        session = await self.get_session(session_id)
        if session:
            session.updated_at = datetime.now()
            await self.orm_session.flush()

    async def delete_session(self, session_id: str) -> bool:
        """세션을 삭제합니다. CASCADE에 의해 연관된 모의 디펜스 이력 및 텍스트 청크도 함께 삭제됩니다."""
        session = await self.get_session(session_id)
        if session:
            await self.orm_session.delete(session)
            await self.orm_session.flush()
            return True
        return False

    async def update_session(self, session: DefenseArenaSessionEntity) -> DefenseArenaSessionEntity:
        """세션 상세 정보(예: 분석 피어 리뷰/가설 검증 리포트 캐싱)를 저장합니다."""
        merged = await self.orm_session.merge(session)
        await self.orm_session.flush()
        await self.orm_session.refresh(merged)
        return merged

    async def delete_chunks(self, session_id: str) -> None:
        """세션에 연관된 pgvector 청크만 지웁니다. (만료 세션 보관용 파일 파쇄 단계)"""
        result = await self.orm_session.execute(
            select(DefenseArenaChunkEntity).where(DefenseArenaChunkEntity.session_id == session_id)
        )
        chunks = result.scalars().all()
        for chunk in chunks:
            await self.orm_session.delete(chunk)
        await self.orm_session.flush()

    async def list_user_sessions(self, member_id: str) -> list[DefenseArenaSessionEntity]:
        """사용자의 디펜스 아레나 세션 히스토리 목록을 최신순으로 조회합니다."""
        result = await self.orm_session.execute(
            select(DefenseArenaSessionEntity)
            .where(DefenseArenaSessionEntity.member_id == member_id)
            .order_by(DefenseArenaSessionEntity.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_expired_sessions(self, expire_minutes: int = 30) -> list[DefenseArenaSessionEntity]:
        """마지막 활동(updated_at) 이후 지정한 시간(분)이 지나고 아직 청크가 소거되지 않은 만료 세션 목록을 조회합니다."""
        threshold = datetime.now() - timedelta(minutes=expire_minutes)
        result = await self.orm_session.execute(
            select(DefenseArenaSessionEntity)
            .where(and_(
                DefenseArenaSessionEntity.updated_at <= threshold,
                DefenseArenaSessionEntity.chunk_count > 0
            ))
        )
        return list(result.scalars().all())


    async def insert_chunks(self, chunks: list[DefenseArenaChunkEntity]) -> None:
        """분할된 텍스트 및 임베딩 벡터 리스트를 일괄 추가합니다."""
        self.orm_session.add_all(chunks)
        await self.orm_session.flush()

    async def similarity_search_in_session(self, session_id: str, query_vector: list[float], k: int = 3) -> list[tuple[DefenseArenaChunkEntity, float]]:
        """세션 내부 텍스트 청크에서 코사인 유사도가 가장 높은 상위 k개의 청크를 반환합니다.

        Returns:
            list[tuple[DefenseArenaChunkEntity, float]]: (청크 엔티티, 유사도 점수) 리스트
        """
        # 코사인 거리(0=동일, 2=반대)를 구하고 오름차순으로 정렬
        distance_col = DefenseArenaChunkEntity.embedding.cosine_distance(query_vector)
        result = await self.orm_session.execute(
            select(DefenseArenaChunkEntity, distance_col)
            .where(DefenseArenaChunkEntity.session_id == session_id)
            .order_by(distance_col.asc())
            .limit(k)
        )
        # 유사도 = 1.0 - 거리
        return [(row[0], round(1.0 - float(row[1]), 4)) for row in result.all()]

    async def insert_defense_history(self, history: DefenseHistoryEntity) -> DefenseHistoryEntity:
        """새로운 모의 디펜스 대화 이력 레코드를 저장합니다."""
        self.orm_session.add(history)
        await self.orm_session.flush()
        await self.orm_session.refresh(history)
        return history

    async def get_defense_history(self, session_id: str) -> list[DefenseHistoryEntity]:
        """특정 세션에서 오고 간 디펜스 대화 내역 목록을 턴 순서대로 조회합니다."""
        result = await self.orm_session.execute(
            select(DefenseHistoryEntity)
            .where(DefenseHistoryEntity.session_id == session_id)
            .order_by(DefenseHistoryEntity.turn.asc())
        )
        return list(result.scalars().all())

    async def get_defense_history_by_turn(self, session_id: str, turn: int) -> DefenseHistoryEntity | None:
        """특정 세션의 특정 턴 디펜스 이력을 조회합니다."""
        result = await self.orm_session.execute(
            select(DefenseHistoryEntity)
            .where(and_(
                DefenseHistoryEntity.session_id == session_id,
                DefenseHistoryEntity.turn == turn
            ))
        )
        return result.scalar_one_or_none()

    async def update_defense_history(self, history: DefenseHistoryEntity) -> DefenseHistoryEntity:
        """디펜스 이력(예: 사용자의 답변 및 획득한 평점 피드백)을 업데이트합니다."""
        merged = await self.orm_session.merge(history)
        await self.orm_session.flush()
        await self.orm_session.refresh(merged)
        return merged


DefenseArenaDaoDep = Annotated[DefenseArenaDao, Depends(DefenseArenaDao)]
