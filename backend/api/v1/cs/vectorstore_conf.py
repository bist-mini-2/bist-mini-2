# LangChain PGVector 전용 설정 (CS 도메인).

from api.common.config import settings

COLLECTION_NAME = "cs-NE"
CONNECTION = settings.PGVECTOR_URL
EMBED_MODEL = "openai:text-embedding-3-large"
