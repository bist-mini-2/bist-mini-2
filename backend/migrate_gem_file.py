"""
gem_file 테이블 생성 마이그레이션 스크립트.
실행: python migrate_gem_file.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@kosa165.iptime.org:50003/postgres"

async def migrate():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS gem_file"))
        await conn.execute(text("""
            CREATE TABLE gem_file (
                file_id     VARCHAR(36)  PRIMARY KEY,
                gem_id      VARCHAR(36)  NOT NULL REFERENCES gem(gem_id) ON DELETE CASCADE,
                filename    VARCHAR(255) NOT NULL,
                chunk_count INTEGER      NOT NULL DEFAULT 0,
                uploaded_at TIMESTAMP    DEFAULT NOW()
            )
        """))
    await engine.dispose()
    print("✅ gem_file 테이블 재생성 완료")


if __name__ == "__main__":
    asyncio.run(migrate())
