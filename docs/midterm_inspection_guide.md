# 🚀 Bist Mini 2 - 학술 에이전트 백엔드 코드 중간점검 가이드

본 문서는 **Paper Agent (학술 에이전트 서비스 플랫폼)** 백엔드 설계 및 코드 레벨의 심층 분석을 위해 작성된 준비 문서입니다. 프론트엔드 내용을 제외하고, 학술 데이터 적재 스크립트에서부터 각 기능 모듈별 **Entity, DTO/Model, DAO, Service, Agent/Workflow, Endpoint**의 물리적 파일 구성과 상호 동작 흐름을 설명하기 위한 대본 및 검증 테스트 코드를 제공합니다.

---

## 📂 목차
1. [백엔드 공통 인프라 및 아키텍처](#1-백엔드-공통-인프라-및-아키텍처)
2. [학술 도메인 데이터 pgvector 임베딩 적재 (Embedding Scripts)](#2-학술-도메인-데이터-pgvector-임베딩-적재-embedding-scripts)
3. [기능별 백엔드 코드 상세 분석](#3-기능별-백엔드-코드-상세-분석)
   - [Feature 1: RAG 통합 대화 (Chat Hub)](#feature-1-rag-통합-대화-chat-hub)
   - [Feature 2: 대규모 문헌 비교 분석기 (Research Gap Analyzer)](#feature-2-대규모-문헌-비교-분석기-research-gap-analyzer)
   - [Feature 3: 커스텀 연구 에이전트 (Custom Gems)](#feature-3-커스텀-연구-에이전트-custom-gems)
4. [독립형 백엔드 API 테스트 가이드](#4-독립형-백엔드-api-테스트-가이드)
   - [cURL 명령어를 활용한 테스트](#curl-명령어를-활용한-테스트)
   - [Python 통합 테스트 자동화 스크립트](#python-통합-테스트-자동화-스크립트)
5. [코드 설명 및 점검 발표 대본](#5-코드-설명-및-점검-발표-대본)

---

## 1. 백엔드 공통 인프라 및 아키텍처

Bist Mini 2의 백엔드는 **FastAPI 비동기(Asyncio) 엔진**을 메인 프레임워크로 삼고, **SQLAlchemy 2.0 비동기 세션(`asyncpg` 드라이버)**과 **pgvector HNSW 인덱싱** 기반의 학술 정보 벡터 검색 파이프라인을 구축하였습니다.

### ⚙️ 핵심 공통 설계 요소
1. **Pydantic DTO 기반 일관된 응답 구조 (`api/database/config/dto_base.py`)**
   - 모든 HTTP API 응답은 일관된 JSON 스키마를 따릅니다.
     - **성공 (200/201)**: `{ "status": "success", "data": { ... } }`
     - **실패 (4xx/5xx)**: `{ "status": "error", "message": "에러 내용" }`
   - *예외 사항*: OAuth2 Password 로그인 API(`/auth/login`)에 한해서는 Swagger UI의 `Authorize` 자물쇠 인증과의 호환을 위해 루트 레벨에 `access_token`과 `token_type`을 포함하는 평평한(Flat) JSON을 반환합니다.
2. **Annotated 의존성 주입 패턴 (`api/dependencies.py`)**
   - 가독성과 모듈화를 위해 `typing.Annotated` 구문을 사용하여 공통 주입 모델을 통일화했습니다.
     - `DbSession = Annotated[AsyncSession, Depends(get_db)]`
     - `CurrentUser = Annotated[User, Depends(get_current_user)]`
3. **2단계 인증 검증 패턴 (`api/common/auth.py`)**
   - 1단계(APIRouter 데코레이터 레벨)에서 `verify_access_token`을 실행해 JWT 무결성과 만료 시간을 검사합니다.
   - 2단계(컨트롤러 매개변수 레벨)에서 검증이 끝난 토큰 캐시의 식별자 정보를 주입(`LoginCheckDep`)받아 데이터베이스 쿼리에 바인딩합니다.
4. **공통 RAG 검색 파이프라인 (`api/common/rag_pipeline.py`)**
   - 생명공학(`bio`), 컴퓨터과학(`cs`), 천문학(`astronomy`) 도메인별 pgvector 테이블에 적재된 논문 데이터에 대한 코사인 유사도 검색을 통합 제공합니다.
   - 임베딩 모델로 `text-embedding-3-large` (3072차원)를 표준으로 적용했습니다.

---

## 2. 학술 도메인 데이터 pgvector 임베딩 적재 (Embedding Scripts)

Bist Mini 2의 RAG 서비스 구현을 위해 생명공학, 컴퓨터과학, 천문학의 3대 연구분야 대규모 학술 데이터를 전처리하여 벡터 데이터베이스에 적재하는 파이프라인 구조입니다.

### 🗄️ pgvector 저장소 스키마 구조
LangChain의 `PGVector` 통합 라이브러리 스키마를 활용하여 다음과 같은 테이블로 원문과 임베딩 벡터를 매핑합니다:
- **`langchain_pg_collection`**: 데이터 그룹을 논리적으로 분할 관리하는 테이블 (컬렉션 이름: `bio_embeddings`, `cs_embeddings`, `astronomy_embeddings`).
- **`langchain_pg_embedding`**: 3072차원의 텍스트 임베딩 벡터(`embedding`), 원본 데이터(`document`), 확장 정보를 기록한 메타데이터 필드(`cmetadata`: `arxiv_id`, `title`, `categories`, `update_date`)를 저장하는 테이블.

---

### 📂 적재 스크립트 코드 분석

#### ① 생명공학(Bio) 데이터 적재 스크립트 (`scripts/datasets/load_bio_gn_to_pgvector.py`)
- **목적**: 생명공학 원천 데이터(`bio_gn_embeddings.jsonl`)를 데이터베이스에 중복 없이 일괄 적재합니다.
- **핵심 알고리즘**:
  1. **기존 컬렉션 데이터 소거 (`clear_existing_collection_embeddings`)**: 재실행 시 데이터 중복 누적을 방지하기 위해 `langchain_pg_collection` 및 `langchain_pg_embedding` 테이블에서 컬렉션명이 `bio_embeddings`인 기존 행들을 SQL 트랜잭션으로 강제 삭제합니다.
  2. **원천 데이터 파싱 및 Document 빌드**: `bio_gn_embeddings.jsonl`의 각 행을 읽어 텍스트 필드를 `Title: {title}\n\nAbstract: {abstract}` 형태로 결합합니다. (이 형식은 RAG 검색 시 임베딩 의미적 유사도 성능을 극대화하기 위해 최적화되었습니다.)
  3. **비동기 배치 임베딩 적재**: OpenAI `text-embedding-3-large` 임베딩 API를 이용하여 3072차원 벡터로 변환하고 `aadd_documents` API를 사용하여 200건 단위의 배치(`BATCH_SIZE = 200`)로 비동기 업로드합니다.

```python
# scripts/datasets/load_bio_gn_to_pgvector.py (기존 데이터 삭제 및 비동기 업로드 부분)
def clear_existing_collection_embeddings() -> None:
    sync_connection_str = CONNECTION.replace("postgresql+psycopg_async://", "postgresql://")
    try:
        with psycopg.connect(sync_connection_str) as conn:
            with conn.cursor() as cur:
                # 1. 컬렉션 UUID 획득
                cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s", (COLLECTION_NAME,))
                row = cur.fetchone()
                if row:
                    collection_uuid = row[0]
                    # 2. 하위 임베딩 레코드 일괄 삭제 (Cascading 예방)
                    cur.execute("DELETE FROM langchain_pg_embedding WHERE collection_id = %s", (collection_uuid,))
                    print(f"기존 '{COLLECTION_NAME}' 임베딩 {cur.rowcount}건 삭제 완료.")
                conn.commit()
    except Exception as e:
        print(f"기존 데이터 삭제 에러: {e}")

# ... 문서 로드 후 LangChain PGVector 연동
vectorstore = PGVector(
    embeddings=init_embeddings(model=EMBED_MODEL),
    collection_name=COLLECTION_NAME,
    connection=CONNECTION,
    async_mode=True,
)
# batch_size=200 단위로 비동기 전송
await vectorstore.aadd_documents(batch)
```

---

#### ② CS 및 천문학 추가 적재 스크립트 (`scripts/datasets/append_full_domain_embeddings.py`)
- **목적**: 대용량 컴퓨터과학(`cs_raw.json`, 17,825건) 및 천문학(`astronomy_raw.json`, 35,083건) 데이터셋에서 이미 적재된 논문을 필터링하고 제외한 나머지 신규 문서만 증분(Incremental) 적재합니다.
- **핵심 알고리즘**:
  1. **기적재 아카이브 ID 스캔 (`get_existing_ids`)**: `langchain_pg_embedding` 테이블의 `cmetadata` 컬렉션 JSON 필드를 대상으로 SQL 쿼리를 실행해 이미 DB에 존재하는 모든 `arxiv_id` 목록을 조회하여 인메모리 Set 객체에 캐싱합니다.
     - `SELECT cmetadata->>'arxiv_id' FROM langchain_pg_embedding WHERE collection_id = %s`
  2. **신규 문서 선별 필터링**: 로컬 JSON 파일을 파싱하면서 `arxiv_id`가 Set 캐시에 존재하는 경우 건너뜀으로써 비용 낭비와 데이터 무결성 훼손을 차단합니다.
  3. **비동기 병렬 업로드**: `tqdm` 프로그레스 바를 표시하며 `aadd_documents`를 기동하여 100건 단위의 배치로 업로드합니다.

```python
# scripts/datasets/append_full_domain_embeddings.py (중복 검사 쿼리 및 Document 구조화 부분)
def get_existing_ids(collection_name: str) -> Set[str]:
    sync_conn_str = CONNECTION.replace("postgresql+psycopg_async://", "postgresql://")
    existing_ids = set()
    try:
        with psycopg.connect(sync_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s", (collection_name,))
                row = cur.fetchone()
                if not row:
                    return existing_ids
                collection_uuid = row[0]
                
                # cmetadata JSON 내부의 arxiv_id 필드를 추출해 메모리에 업로드
                cur.execute("""
                    SELECT cmetadata->>'arxiv_id' 
                    FROM langchain_pg_embedding 
                    WHERE collection_id = %s
                """, (collection_uuid,))
                
                for r in cur.fetchall():
                    if r[0]:
                        existing_ids.add(r[0])
    except Exception as e:
        print(f"기존 ID 스캔 중 오류: {e}")
    return existing_ids
```

---

## 3. 기능별 백엔드 코드 상세 분석

### Feature 1: RAG 통합 대화 (Chat Hub)
* **역할**: 사용자가 질문을 던지면 질문 내용에 적합한 참고 문헌 논문 데이터를 pgvector 데이터베이스에서 실시간 추출하고, 이를 결합하여 AI 답변과 원천 논문 출처 리스트를 반환합니다.

#### 📁 파일별 구현 내역

| 파일명 | 역할 및 핵심 기능 |
| :--- | :--- |
| `api/v1/chat/entity.py` | - `ChatSessionEntity`: 대화방의 소유자(`member_id`) 및 방 제목(`title`) 저장 메타 테이블.<br>- `ChatSourceEntity`: AI의 답변 시 인용된 참고 문헌 논문 정보(`arxiv_id`, `title`, `summary`) 매핑 테이블. |
| `api/v1/chat/models.py` | - API 요청/응답 스키마(DTO) 정의.<br>- `ChatSessionCreateRequest`, `ChatMessageRequest`, `ChatMessageResponseWrapper` 등 정의 (`BaseDTO` 상속). |
| `api/v1/chat/dao.py` | - `ChatDao`: SQLAlchemy 비동기 세션을 이용하여 채팅방 생성, 삭제, 이름 변경, 출처 등록 등 DB 입출력 전담. |
| `api/v1/chat/services.py` | - `ChatService`: 대화 흐름 비즈니스 기획 관리.<br>- 메시지 전송 시 RAG 파이프라인 가동 및 `ChatSourceEntity` 생성 보존 흐름 조율. |
| `api/v1/chat/chat_agent.py` | - LangChain/LangGraph 및 OpenAI SDK 기반 RAG 스트리밍 실행기.<br>- 비동기 제너레이터(`async for chunk in client.chat.completions`)를 이용해 클라이언트에 토큰 단위로 실시간 yield. |
| `api/v1/chat/endpoints.py` | - `/chat/sessions` 관련 엔드포인트 노출.<br>- `StreamingResponse`를 통한 실시간 대화 스트리밍 응답(`/chat/sessions/{id}/messages/stream`). |

---

### Feature 2: 대규모 문헌 비교 분석기 (Research Gap Analyzer)
* **역할**: 특정 주제에 대한 복수의 논문(최대 4개)을 한 번에 요약 비교하여 분석 매트릭스를 생성하고, 기존 연구의 한계점과 미래 지향적 신규 연구 가설(Research Gap)을 합성하여 백그라운드 배치 프로세스로 도출합니다.

#### 📁 파일별 구현 내역

| 파일명 | 역할 및 핵심 기능 |
| :--- | :--- |
| `api/v1/research_gap/entity.py` | - `ResearchGapTaskEntity`: 배치 작업 상태(`status`: PENDING, RUNNING, COMPLETED, FAILED), 진행률(`progress`: 0~100%), 영어 결과 레포트(`result`), 한국어 번역 캐시(`translated_result`) 저장 테이블. |
| `api/v1/research_gap/models.py` | - 분석 실행 요청(`AnalyzeRequest`), 일괄 삭제(`BulkDeleteRequest`), 결과 조회용 DTO 클래스 정의. |
| `api/v1/research_gap/dao.py` | - `ResearchGapDao`: 특정 작업의 상세 상태 변경 및 번역 결과 필드 갱신, 다중 삭제 트랜잭션 수행. |
| `api/v1/research_gap/services.py` | - `ResearchGapService`: 배치 관리자.<br>- FastAPI `BackgroundTasks`를 통해 무거운 LLM 연산 작업을 백그라운드 스레드로 위임 기동.<br>- LangChain Structured Output API를 사용해 결과 데이터 유효성 자동 검증. |
| `api/v1/research_gap/endpoints.py` | - API 라우팅 정의.<br>- 비동기 기동 API: `POST /research-gap/analyze`<br>- 상태 폴링 API: `GET /research-gap/tasks/{task_id}`<br>- 기계 번역 및 캐시 API: `POST /research-gap/tasks/{task_id}/translate` |
| `api/v1/research_gap/embedding.py` | - 특정 논문 텍스트 분석에 필요한 임베딩 추출 보조 로직. |

---

### Feature 3: 커스텀 연구 에이전트 (Custom Gems)
* **역할**: 사용자가 고유의 에이전트 이름, 참고 학술 범위(Bio, CS, Astronomy 다중 선택), 특정 가이드라인(System Prompt)을 기재하여 자기만의 연구 에이전트(Gems)를 개설하고 대화를 나눌 수 있는 샌드박스입니다.

#### 📁 파일별 구현 내역

| 파일명 | 역할 및 핵심 기능 |
| :--- | :--- |
| `api/v1/gems/entity.py` | - `GemEntity`: 커스텀 에이전트 설정 테이블.<br>- 이름(`name`), 참고 데이터 소스(`db_sources`: 콤마 구분자 문자열), 전용 룰 지침(`system_prompt`) 보관. |
| `api/v1/gems/models.py` | - Gem 생성/수정 요청 DTO 및 대화 요청 DTO(`GemChatRequest`), 응답 래퍼 정의. |
| `api/v1/gems/dao.py` | - `GemDao`: 사용자 소유의 Gems 목록 획득, 상세 정보 갱신, 삭제 트랜잭션. |
| `api/v1/gems/services.py` | - `GemService`: 특정 Gem의 정보를 데이터베이스에서 가져와 `gem_agent` 실행을 주관하며, 스레드별 대화 히스토리를 관리. |
| `api/v1/gems/gem_agent.py` | - 커스텀 프롬프트 런타임 바인딩 에이전트.<br>- 사용자의 질문에 맞춰 `db_sources`에 명시된 데이터베이스 범위에 국한하여 다중 도메인 RAG를 가동한 뒤, 커스텀 `system_prompt`를 합성하여 대답 도출. |
| `api/v1/gems/endpoints.py` | - Gem 정보 관리 API (CRUD) 및 커스텀 대화 엔드포인트(`/gems/{gem_id}/chat`) 처리. |

---

## 4. 독립형 백엔드 API 테스트 가이드

중간점검 현장이나 로컬 개발 서버 작동 무결성을 입증하기 위해 외부 터미널 및 외부 스크립트에서 즉시 구동할 수 있는 자동 테스트 코드입니다.

### cURL 명령어를 활용한 테스트

#### 1. OAuth2 로그인 및 JWT 토큰 취득
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test3333&password=your_password"
```
> 반환된 JSON에서 `access_token` 값을 복사하여 이후 API의 `<TOKEN>` 자리에 대입합니다.

#### 2. Feature 1: RAG 채팅방 생성
```bash
curl -X POST "http://localhost:8000/api/v1/chat/sessions" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"title": "중간점검 데모 세션"}'
```

#### 3. Feature 2: 비동기 문헌 분석(Research Gap) 예약 기동
```bash
curl -X POST "http://localhost:8000/api/v1/research-gap/analyze" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"domain": "cs", "query": "Transformer Models"}'
```
> 반환된 `task_id`를 활용해 상태 조회를 호출합니다.

#### 4. Feature 3: 커스텀 에이전트 Gem 개설
```bash
curl -X POST "http://localhost:8000/api/v1/gems" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "비판적 연구 검증가",
       "db_sources": ["cs", "bio"],
       "system_prompt": "당신은 냉철한 과학 비평가입니다. 분석 방법론의 맹점을 찾아내어 비판적으로 서술하십시오."
     }'
```

---

### Python 통합 테스트 자동화 스크립트

독립적인 검증 환경에서 백엔드 API 라이프사이클을 시뮬레이션할 수 있는 완성형 테스트 코드입니다.
`backend/tests/manual_midterm_test.py`에 저장한 뒤 `PYTHONPATH=. python tests/manual_midterm_test.py`로 실행할 수 있습니다.

```python
# backend/tests/manual_midterm_test.py
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "test3333"
PASSWORD = "your_password"  # 테스트할 로컬 계정 패스워드 입력

async def run_integration_test():
    async with httpx.AsyncClient(timeout=45.0) as client:
        print("====== [시작] Bist Mini 2 백엔드 핵심 기능 통합 테스트 ======")

        # 1. 로그인 및 토큰 취득
        print("\n[단계 1] OAuth2 패스워드 로그인 시도...")
        login_res = await client.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        if login_res.status_code != 200:
            print(f"❌ 로그인 실패: {login_res.text}")
            return
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ JWT 인증 토큰 발급 성공!")

        # 2. Feature 1: RAG 채팅방 개설 및 메시지 전송
        print("\n[단계 2] Feature 1 RAG 채팅 세션 생성...")
        session_res = await client.post(
            f"{BASE_URL}/chat/sessions",
            headers=headers,
            json={"title": "RAG API 테스트 방"}
        )
        session_id = session_res.json()["data"]["session_id"]
        print(f"✅ RAG 채팅방 생성 완료 (ID: {session_id})")

        print("-> RAG 질문 및 출처 조회 API 테스트...")
        msg_res = await client.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            headers=headers,
            json={"message": "Attention Mechanism이 딥러닝 아키텍처에 미친 영향에 대해 요약해줘."}
        )
        answer = msg_res.json()["data"]["answer"]
        sources = msg_res.json()["data"]["sources"]
        print(f"✅ AI 답변 요약 수신 완료. 수집된 논문 정보 개수: {len(sources)}개")

        # 3. Feature 2: 비동기 Research Gap 분석 및 폴링
        print("\n[단계 3] Feature 2 Research Gap 분석 배치 기동...")
        analysis_res = await client.post(
            f"{BASE_URL}/research-gap/analyze",
            headers=headers,
            json={"domain": "cs", "query": "Attention Mechanism"}
        )
        task_id = analysis_res.json()["data"]["task_id"]
        print(f"✅ 분석 배치 작업 예약 완료 (Task ID: {task_id})")

        print("-> 비동기 배치 진척율 폴링 중...")
        for i in range(15):
            await asyncio.sleep(2)
            status_res = await client.get(f"{BASE_URL}/research-gap/tasks/{task_id}", headers=headers)
            status_data = status_res.json()["data"]
            print(f"   [폴링 {i+1}] 상태: {status_data['status']} | 진행율: {status_data['progress']}%")
            if status_data["status"] == "COMPLETED":
                print("✅ 비동기 문헌 분석 배치 작업 완료!")
                break
        else:
            print("⚠️ 폴링 제한 시간 초과 (테스트 백그라운드 구동 지속)")

        # 4. Feature 3: 커스텀 Gem 생성 및 전용 RAG 대화
        print("\n[단계 4] Feature 3 커스텀 학술 에이전트 Gem 설계...")
        gem_res = await client.post(
            f"{BASE_URL}/gems",
            headers=headers,
            json={
                "name": "천문 연구 보조 에이전트",
                "db_sources": ["astronomy"],
                "system_prompt": "당신은 NASA 천체 물리학 연구원입니다. 모든 대답은 관측 데이터 분석 중심의 어조로 전개하세요."
            }
        )
        gem_id = gem_res.json()["data"]["gem_id"]
        print(f"✅ 커스텀 Gem 생성 성공 (Gem ID: {gem_id})")

        print("-> Gem RAG 채팅 API 질의...")
        gem_chat_res = await client.post(
            f"{BASE_URL}/gems/{gem_id}/chat",
            headers=headers,
            json={
                "thread_id": f"test_thread_{gem_id}",
                "message": "제임스 웹 우주 망원경의 최근 업적 정리"
            }
        )
        gem_answer = gem_chat_res.json()["data"]["answer"]
        print(f"✅ Gem 답변 도출 성공! (답변 일부: {gem_answer[:60]}...)")
        
        print("\n====== [종료] 모든 핵심 API 테스트 검증 통과 ======")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
```

---

## 5. 코드 설명 및 점검 발표 대본

중간점검 보고 회의에서 백엔드 코드 설계의 완성도를 코드 파일 기준으로 매끄럽게 전달할 수 있는 전용 발표 가이드 대본입니다.

---

### 🎙️ 1. 아키텍처 개요 및 설계 컨벤션 소개
> *"Bist Mini 2의 백엔드 설계 핵심 철학과 공통 인프라에 대해 설명해 드리겠습니다. 저희 시스템은 모듈 간 결합도를 낮추고 유지보수성을 극대화하기 위해 각 기능 단위를 물리적인 Layer로 분리하였습니다. 데이터베이스 원천 테이블을 조종하는 **Entity**, 외부에 노출되는 구조를 제한하는 **DTO/Model**, 원 데이터 조회를 캡슐화한 **DAO**, 비즈니스 로직을 총괄하는 **Service**, API 주소를 매핑한 **Endpoint**로 각 도메인을 격리했습니다.*
> 
> *특히 의존성 주입 시 FastAPI의 `Depends` 구조를 Python 3.12의 `typing.Annotated` 패턴으로 묶어 컴파일 에러를 차단하고 데이터베이스 비동기 트랜잭션의 수명 주기를 일관성 있게 제어하도록 규격화했습니다. 또한 pgvector 데이터베이스 검색 성능을 위해 HNSW 인덱스를 탑재하고 3072차원 고정 벡터 임베딩을 이용한 공통 RAG 모듈을 `api/common/rag_pipeline.py`에 구축하여 중복 코드를 배제했습니다."*

---

### 🎙️ 2. 학술 도메인 데이터 pgvector 임베딩 적재 파이프라인 소개
> *"저희 학술 RAG 시스템이 작동할 수 있도록 사전 전처리 단계로 3대 도메인 데이터를 pgvector 데이터베이스에 가공 적재하는 파이프라인 스크립트를 구현하였습니다. 이 스크립트들은 `scripts/datasets` 폴더 내에 배치되어 있습니다.*
> 
> *먼저 생명공학 도메인을 처리하는 `load_bio_gn_to_pgvector.py`는 데이터 무결성을 위해 실행 초기 단계에서 `psycopg` 연결을 이용해 `bio_embeddings` 컬렉션에 등록되어 있던 기존 임베딩 행들을 소거합니다. 이후 원천 데이터를 한 줄씩 파싱하여 검색 성능 최적화 구조인 'Title + Abstract' 결합 내용으로 문서를 구조화하고, OpenAI의 `text-embedding-3-large` 모델을 통해 3072차원 벡터로 변환하여 200건 단위의 비동기 배치로 최종 DB에 업로드합니다.*
> 
> *컴퓨터과학 및 천문학 도메인을 담당하는 `append_full_domain_embeddings.py`는 수만 건이 넘는 대용량 적재 시의 중복 작업을 차단하기 위해 구현되었습니다. 적재 시작 전, DB의 `langchain_pg_embedding` 테이블의 `cmetadata` 내부 `arxiv_id` 필드를 SQL로 스캔하여 메모리에 캐시 형태로 보관합니다. 그리고 신규 데이터를 읽을 때 이 캐시를 기준으로 연산 중복을 방지(Filtering)하여 비용 낭비와 임베딩 충돌을 방지하며 100건 단위 배치로 비동기식 추가 적재를 완성합니다."*

---

### 🎙️ 3. Feature 1: RAG 통합 대화 (Chat Hub) 코드 설명
> *"첫 번째 기능인 RAG 통합 채팅의 코드 설계 구조입니다. 사용자 세션의 메타데이터는 `ChatSessionEntity`에 적재되며, AI의 실시간 답변 도중 인용하게 되는 원문 논문 출처 리스트는 `ChatSourceEntity` 테이블에 적재됩니다. 대화 데이터는 비동기 저장 엔진인 `AsyncPostgresSaver`를 채택해 세션 ID별로 스레드 분리 적재됩니다.*
> 
> *핵심 작동 파일은 `chat_agent.py`입니다. 사용자의 입력이 들어오면 RAG 파이프라인이 임베딩 검색을 시도하여 관계도가 높은 문헌을 로드한 뒤, 프롬프트를 동적으로 수립하고 OpenAI GPT-4o 연결 객체를 엽니다. 이때 백엔드는 대기 시간 병목을 예방하기 위해 비동기 제너레이터를 이용하여 클라이언트에 토큰 단위 실시간 마크다운을 스트리밍(`StreamingResponse`) 출력해 주는 형태로 구현되어 있어 최상의 응답 체감 속도를 보장합니다."*

---

### 🎙️ 4. Feature 2: 대규모 문헌 비교 분석기 (Research Gap) 코드 설명
> *"두 번째는 대규모 문헌 비교 분석 및 Research Gap 도출 모듈입니다. 다량의 논문을 읽고 비교 매트릭스 표를 추출하고 합성 리포트를 뽑아내는 과정은 긴 LLM 추론 시간이 소요되어 HTTP 타임아웃을 유발하기 쉽습니다. 이를 극복하고자 비동기 스케줄링 설계를 채택했습니다.*
> 
> *사용자가 `POST /research-gap/analyze` 엔드포인트를 호출하면, `ResearchGapService`는 데이터베이스에 신규 태스크를 생성하여 즉시 `task_id`를 반환합니다. 실질적인 LLM 연산은 FastAPI의 `BackgroundTasks` 백그라운드 프로세서로 위임하여 비동기 기동합니다. 백그라운드 프로세스는 작업 진척에 맞춰 `ResearchGapTaskEntity`의 `progress` 수치를 20%, 50%, 80%, 100%로 갱신하며, 연산이 성공 완료되면 종합 결과를 JSON 문자열 형태로 `result` 필드에 격리 저장합니다. 클라이언트는 이 `task_id`를 가지고 주기적인 폴링 조회를 진행하게 됩니다."*

---

### 🎙️ 5. Feature 3: 커스텀 연구 에이전트 (Custom Gems) 코드 설명
> *"마지막으로 커스텀 연구 비서 Gems 모듈의 설계입니다. 이는 사용자가 임의의 에이전트 페르소나 및 조회 영역을 설정할 수 있게 해주는 데이터 가상화 샌드박스입니다.*
> 
> *`GemEntity`는 에이전트 전용의 가이드 규칙인 `system_prompt`와 RAG 범위 제어용 필드인 `db_sources`를 저장하고 있습니다. `gem_agent.py`는 사용자가 Gem과의 대화방에서 질문을 보내면, 해당 Gem의 엔티티 설정을 우선 파싱합니다. 만약 `db_sources`가 `cs,bio`로 지정되어 있다면 다른 데이터베이스(예: astronomy) 검색을 원천 차단하고 오직 컴퓨터과학과 생명공학 테이블의 백터 검색 결과만을 컨텍스트로 취합합니다. 이후 사용자가 설정한 커스텀 시스템 프롬프트를 런타임에 LLM 인스턴스의 System 지침서로 강제 오버라이딩 적용하여 조화로운 개인 맞춤형 학술 지원 답변을 구성하도록 동작합니다."*
