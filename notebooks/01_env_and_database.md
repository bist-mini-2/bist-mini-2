# 📖 [01] 환경 & DB 연결 기초

이 노트북은 **Paper Agent** 백엔드에서 환경 변수를 로드하고, PostgreSQL 데이터베이스에 비동기 커넥션(`AsyncSession`)을 형성하며, pgvector 확장 모듈의 상태를 점검하는 독립 실행형 튜토리얼입니다.

---

## 💡 3분 배경지식: FastAPI & SQLAlchemy 비동기 설계
1. **왜 비동기(async/await)인가?**
   - 학술 플랫폼 특성상 대규모 임베딩 연산이나 LLM API 통신, 대용량 RAG 검색 등으로 인해 DB 쿼리 대기 시간이 길어질 수 있습니다. 동기식(Sync) I/O는 DB 응답을 기다리는 동안 스레드가 차단되지만, 비동기(Async) I/O는 대기하는 동안 다른 사용자의 요청을 처리할 수 있어 처리량(Throughput)이 대폭 향상됩니다.
2. **SQLAlchemy AsyncSession**:
   - SQLAlchemy 2.0부터는 `asyncpg` 또는 `psycopg` 비동기 드라이버를 통해 비동기 세션을 공식 지원합니다. `await db.execute()`와 같이 세션 수명 주기 전체를 비동기식으로 제어합니다.
3. **pgvector 확장**:
   - PostgreSQL 상에서 벡터 유사도 검색(Cosine Distance 등)을 가능케 해주는 모듈입니다. RAG 파이프라인의 핵심 토대입니다.

---

## 🐳 Docker Compose를 이용한 pgvector DB 실행
로컬에 pgvector가 내장된 PostgreSQL이 구동되지 않은 경우, 터미널에서 다음 명령어를 실행하여 켜줍니다.
```bash
docker run -d --name paper-agent-db -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=postgres pgvector/pgvector:17-pg17
```

### 1. 환경 변수 설정 및 settings 모듈 로드

```python
import sys
import os

# 백엔드 모듈 경로를 파이썬 검색 경로에 추가
sys.path.append(os.path.abspath("../backend"))

from api.common.config import settings

print("=== 환경 설정 값 확인 ===")
print(f"DATABASE_URL (비동기): {settings.DATABASE_URL}")
print(f"PGVECTOR_URL (임베딩용): {settings.PGVECTOR_URL}")
print(f"OpenAI API Key 존재 여부: {bool(settings.OPENAI_API_KEY)}")
```

### 2. SQLAlchemy AsyncSession을 이용한 비동기 연결 테스트

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

async def test_db_connection():
    # 1. 비동기 DB 엔진 생성
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    # 2. 세션 팩토리 정의
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    print("데이터베이스 연결을 시도합니다...")
    async with async_session() as session:
        # 3. 간단한 SQL 문 실행
        result = await session.execute(text("SELECT 1"))
        val = result.scalar()
        print(f"연결 성공! SELECT 1 결과값: {val}")
        
    # 4. 엔진 리소스 해제
    await engine.dispose()

# 주피터 환경의 이벤트 루프에서 실행
await test_db_connection()
```

### 3. pgvector 확장 활성화 여부 검증

```python
async def check_pgvector_extension():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine)
    
    async with async_session() as session:
        # pgvector 익스텐션 등록 여부 확인 쿼리
        result = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
        ext = result.scalar()
        
        if ext == "vector":
            print("✅ pgvector 확장 모듈이 데이터베이스에 정상 활성화되어 있습니다.")
        else:
            print("❌ pgvector 확장을 찾을 수 없습니다. 활성화를 시도합니다...")
            try:
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await session.commit()
                print("✅ pgvector 확장을 성공적으로 생성 및 활성화했습니다.")
            except Exception as e:
                print(f"❌ pgvector 확장 생성 실패. 권한을 확인하세요: {e}")
                
    await engine.dispose()

await check_pgvector_extension()
```

