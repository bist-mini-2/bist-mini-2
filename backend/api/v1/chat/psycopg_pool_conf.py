from psycopg_pool import AsyncConnectionPool

# AsyncPostgresSaver(대화 기록 저장)용 psycopg 풀.
# 공용 dbsession.py는 asyncpg 기반이라 호환 안 되므로 psycopg 풀을 별도 생성.
# open=False로 생성되므로, checkpointer.setup() 전에 chat_agent에서 직접 open() 한다.
chat_psycopg_pool = AsyncConnectionPool(
    "postgresql://postgres:postgres@kosa165.iptime.org:50003/postgres",
    min_size=1,
    max_size=3,
    kwargs={"autocommit": True},
    open=False,
)
