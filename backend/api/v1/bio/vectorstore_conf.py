# LangChain PGVector 전용 설정.
# 프로젝트 공용 engine은 asyncpg 기반이라 PGVector(psycopg v3)와 호환되지 않으므로
# connection string을 별도로 관리한다.

COLLECTION_NAME = "q-bio-GN"
CONNECTION = "postgresql+psycopg_async://postgres:postgres@kosa165.iptime.org:50003/postgres"
EMBED_MODEL = "openai:text-embedding-3-large"
