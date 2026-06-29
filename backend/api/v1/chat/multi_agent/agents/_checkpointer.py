"""paper/web 작업 에이전트가 공유하는 단일 AsyncPostgresSaver 제공 모듈.

paper_agent와 web_agent는 같은 대화방(thread_id=session_id)의 기록을 공유해야 하므로,
하나의 checkpointer 인스턴스를 두 에이전트가 함께 사용한다. 기존 chat_agent._initialize의
psycopg_pool + AsyncPostgresSaver + 멱등 setup 패턴을 그대로 따른다.

checkpoints 테이블은 chat_agent와 같은 DB를 공유하지만, 이미 테이블이 존재하면 setup()을
건너뛰어 중복 setup으로 인한 hang을 방지한다(멱등 처리).
"""
import asyncio
import logging
from typing import Any, cast

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from api.database.config.psycopg_pool import psycopg_pool as chat_psycopg_pool

logger = logging.getLogger(__name__)

# 모듈 레벨 싱글톤 — 최초 1회만 생성해 paper/web 에이전트가 공유한다.
_checkpointer: AsyncPostgresSaver | None = None
_init_lock = asyncio.Lock()


async def get_chat_checkpointer() -> AsyncPostgresSaver:
    """공유 checkpointer를 lazy 초기화하여 반환한다(running event loop 안에서 호출).

    psycopg_pool은 open=False로 생성되므로 setup 전에 풀을 연다. checkpoints 테이블이
    이미 있으면 setup()을 건너뛴다(chat_agent와 동일한 멱등 처리).
    """
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    async with _init_lock:
        if _checkpointer is not None:
            return _checkpointer

        if chat_psycopg_pool.closed:
            await chat_psycopg_pool.open()

        checkpointer = AsyncPostgresSaver(cast(Any, chat_psycopg_pool))

        # checkpoints 테이블이 이미 있으면 setup()을 건너뛴다(중복 setup hang 방지).
        async with chat_psycopg_pool.connection() as conn:
            cur = await conn.execute(
                "SELECT 1 FROM pg_tables "
                "WHERE schemaname='public' AND tablename='checkpoints'"
            )
            exists = await cur.fetchone()
            if not exists:
                # checkpoints가 없는데 migration 테이블만 있으면 setup()이 테이블을 만들지 않으므로
                # 관련 테이블을 일괄 삭제해 setup()이 처음부터 깨끗이 생성하도록 유도한다.
                await conn.execute(
                    "DROP TABLE IF EXISTS checkpoint_migrations, checkpoint_blobs, "
                    "checkpoint_writes CASCADE;"
                )
        if not exists:
            await checkpointer.setup()

        _checkpointer = checkpointer
        logger.info("멀티 에이전트 공유 checkpointer 초기화 완료")
        return _checkpointer
