# Bist Mini 2 - Backend Presentation Script (발표 대본)

본 문서는 `Bist Mini 2` 백엔드 프로젝트의 핵심 파이프라인인 **공통 RAG 파이프라인(Common RAG Pipeline)**과 **3대 핵심 비즈니스 도메인(Chat, Gems, Research Gap)**의 구현 세부사항과 동작 원리를 발표할 수 있도록 구성한 발표 대본입니다. 발표자가 보면서 말하기 편하도록 **핵심 소스 코드 조각(Markdown Code Block)**을 각 슬라이드마다 직접 포함하고 있습니다.

---

## 🖥️ Slide 1: 발표 오프닝 및 백엔드 아키텍처 개요
**[발표자]**
> 안녕하세요. `Bist Mini 2` 백엔드 파트 발표를 맡은 [발표자 이름]입니다.
> 
> 저희 시스템은 여러 도메인의 학술 논문 데이터를 기반으로 연구를 돕는 RAG(Retrieval-Augmented Generation) 시스템입니다. 
> 오늘 발표에서는 저희 백엔드 구현의 가장 핵심이 되는 **공통 RAG 파이프라인**과, 이를 활용한 **3대 핵심 비즈니스 기능(대화형 Chat, 커스텀 비서 Gems, 백그라운드 Research Gap 분석)**을 중심으로 소스 코드 수준에서 동작 원리를 설명해 드리겠습니다.
> 
> 저희 백엔드는 **FastAPI**를 바탕으로, 비동기 트랜잭션과 에이전트 체크포인팅을 다루기 위해 **Controller - Service - DAO - Entity** 레이어드 아키텍처를 견고하게 구축하였습니다.

---

## 🖥️ Slide 2: 공통 RAG 파이프라인 및 LangGraph 연동 툴
#### 📄 대상 코드: [api/common/rag_pipeline.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/rag_pipeline.py)

**[발표자]**
> 첫 번째로, 저희 서비스의 심장부라고 할 수 있는 **공통 RAG 파이프라인**입니다.
> 
> 저희는 생명공학(`bio`), 컴퓨터과학(`cs`), 천문학(`astronomy`)이라는 3대 학술 도메인 컬렉션을 단일 데이터베이스 내에서 관리하고 있습니다.
> RAG 검색을 전담하는 **`CommonRagPipeline`** 클래스는 pgvector 비동기 드라이버를 래핑하여 유사도 연산을 통합 수행합니다.
> 
> 아래 코드의 **`similarity_search`** 메소드를 보시면, 요청된 도메인에 매핑된 pgvector 컬렉션에 대해 비동기 유사도 검색(`asimilarity_search_with_score`)을 수행하고, 계산된 거리 점수를 직관적인 유사도 점수(`1.0 - score`)로 가공해 상위 k개의 매칭 청크 리스트를 빌드하여 반환합니다.

```python
# backend/api/common/rag_pipeline.py 중 일부

class CommonRagPipeline:
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.CommonRagPipeline")
        self._embeddings = None

    def get_embeddings(self):
        """임베딩 인스턴스를 지연 로딩(Lazy Loading) 방식으로 공유합니다."""
        if self._embeddings is None:
            self._embeddings = init_embeddings(model=EMBED_MODEL)
        return self._embeddings

    async def similarity_search(self, domain: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """지정된 도메인 컬렉션에서 질의어와 유사도가 높은 문서를 검색합니다."""
        if domain not in DOMAIN_COLLECTIONS:
            raise ValueError(f"지원하지 않는 도메인입니다: {domain}")

        collection_name = DOMAIN_COLLECTIONS[domain]
        vectorstore = PGVector(
            embeddings=self.get_embeddings(),
            collection_name=collection_name,
            connection=CONNECTION,
            async_mode=True,
        )

        # 비동기로 pgvector 코사인 유사성 검색
        results = await vectorstore.asimilarity_search_with_score(query, k=k)

        formatted_results = []
        for doc, score in results:
            meta = doc.metadata or {}
            arxiv_id = meta.get("arxiv_id") or meta.get("doc_id") or ""
            title = meta.get("title", "")
            similarity = round(1.0 - score, 4)  # 거리값을 유사도 점수로 변환

            formatted_results.append({
                "doc_id": arxiv_id,
                "title": title,
                "text_chunk": doc.page_content,
                "score": similarity
            })
        return formatted_results
```

> 이 파이프라인은 싱글톤 인스턴스인 `common_rag_pipeline` 형태로 메모리에 유지되며, LangGraph 에이전트 노드가 활용할 수 있도록 아래의 `@tool` 기반 함수들과 직접 바인딩됩니다.
> 검색된 결과는 상태 그래프의 `messages`와 출처 정보를 담는 `sources`에 누적 업데이트될 수 있도록 LangGraph `Command` 흐름 제어 객체로 싸여 리턴됩니다.

```python
# backend/api/common/rag_pipeline.py (LangGraph 툴 함수 정의 예시)

@tool
async def search_bio_papers(query: str, runtime: ToolRuntime, k: int = 3) -> Command:
    """생명공학·유전체학(q-bio.GN) 논문 데이터베이스에서 관련 내용을 검색하는 툴입니다."""
    results = await common_rag_pipeline.similarity_search("bio", query, k=k)

    if not results:
        msg = f"q-bio.GN 논문에서 '{query}'와 관련된 내용을 찾을 수 없습니다."
        return Command(update={
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        })

    output_lines = [f"검색 결과: '{query}' (q-bio.GN 논문)\n", "=" * 80]
    sources = []
    for idx, r in enumerate(results, 1):
        arxiv_id = r["doc_id"]
        title = r["title"]
        score = r["score"]
        output_lines.append(f"\n[논문 {idx}] (유사도: {score:.4f}) / arXiv ID: {arxiv_id}")
        output_lines.append(f"내용: {r['text_chunk']}\n")
        
        snippet = " ".join((r["text_chunk"] or "").split())
        if len(snippet) > 160:
            snippet = snippet[:160] + "…"
        sources.append({"arxiv_id": arxiv_id, "title": title, "summary": snippet})

    return Command(update={
        "messages": [ToolMessage(content="\n".join(output_lines), tool_call_id=runtime.tool_call_id)],
        "sources": sources  # LangGraph State 내의 sources 목록으로 자동 병합
    })
```

---

## 🖥️ Slide 3: 대표 기능 1 — LangGraph RAG 챗봇 대화 세션 관리
#### 📄 대상 코드: [chat/chat_agent.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/chat_agent.py) / [chat/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/services.py)

**[발표자]**
> 두 번째는 대표 기능 중 첫 번째인 **대화방 형태의 RAG 챗봇 기능**입니다.
> 사용자와 주고받는 대화 내역이 유실되지 않도록 LangGraph의 영구 저장소 체크포인터인 `AsyncPostgresSaver`를 연동했습니다.
> 
> **`ChatAgent`** 클래스의 **`_initialize`** 메소드는 다중 요청 상황에서 중복 생성을 방지하기 위한 비동기 락(`self._init_lock`) 하에 동작하며, 데이터베이스에 대화 내역 저장을 위한 checkpoints 테이블이 없을 경우에만 `setup()`을 구동하도록 멱등성을 보장합니다.
> 
> **`run`** 메소드는 세션 ID(`conversation_id`)를 런타임에 `thread_id`로 매핑하여 호출함으로써, 이전의 대화 흐름을 영구 저장소에서 자동 복원하여 답변 맥락을 기억하도록 제어합니다. 또한, 출력 형식의 일관성을 위해 Pydantic 모델인 `BioAnswer`로 구조화된 답변 포맷을 강제합니다.

```python
# backend/api/v1/chat/chat_agent.py 중 일부

class ChatAgent:
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.model = model
        self.checkpointer = None
        self.agent = None
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """비동기 Lazy 방식을 활용해 체크포인터 테이블을 멱등하게 자동 생성하고 에이전트를 결합합니다."""
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            if chat_psycopg_pool.closed:
                await chat_psycopg_pool.open()
            
            # 1. Postgres 기반의 체크포인터 생성
            self.checkpointer = AsyncPostgresSaver(cast(Any, chat_psycopg_pool))
            
            # 2. RAG 전용 LLM 에이전트 생성
            self.agent = create_agent(
                model=self.model,
                tools=[search_bio_papers, search_astronomy_papers, search_cs_papers],
                system_prompt=self.system_prompt,
                checkpointer=self.checkpointer,
                state_schema=cast(Any, BioAgentState),
                response_format=BioAnswer  # 구조화 출력 정의
            )

            # checkpoints 테이블이 없을 때만 새롭게 빌드
            async with chat_psycopg_pool.connection() as conn:
                cur = await conn.execute(
                    "SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='checkpoints'"
                )
                exists = await cur.fetchone()
            if not exists:
                await self.checkpointer.setup()

            self._initialized = True

    async def run(self, message: str, conversation_id: str) -> dict:
        """이전 대화 이력을 자동으로 데이터베이스에서 복원해 답변을 도출합니다."""
        await self._initialize()
        assert self.agent is not None
        
        result = await self.agent.ainvoke(
            {
                "messages": [{"role": "user", "content": message}],
                "sources": [],
            },
            {"configurable": {"thread_id": conversation_id}},  # thread_id를 통해 세션 복원
        )
        
        structured = result.get("structured_response")
        return {
            "answer": structured.explanation if structured else result["messages"][-1].content,
            "papers": [p.model_dump() for p in structured.papers] if structured else [],
            "sources": result.get("sources", [])
        }
```

> 이렇게 에이전트가 완성되면 비즈니스 레이어인 **`ChatService`**가 이 답변을 가공하고, 질문 답변의 신뢰 근거가 된 논문 출처 리스트를 `chat_source` 테이블에 턴 단위 메시지 번호와 유기적으로 매핑해 저장합니다.
> 이를 통해, 사용자가 방을 나갔다가 다시 들어왔을 때, 이전의 대화 내역뿐만 아니라 당시 답변 아래에 달려있던 출처 카드까지 완벽히 복원할 수 있습니다.

```python
# backend/api/v1/chat/services.py 중 일부

class ChatService:
    def __init__(self, chat_session_dao: ChatSessionDaoDep, chat_agent: ChatAgentDep) -> None:
        self.chat_session_dao = chat_session_dao
        self.chat_agent = chat_agent

    async def send_message(self, member_id: str, session_id: str, message: str) -> dict:
        """사용자 메시지를 받아 RAG를 거쳐 답변을 제공하고 출처 목록을 영구 저장합니다."""
        await self._get_owned_session(member_id, session_id)
        
        # 1. 챗봇 에이전트 구동
        result = await self.chat_agent.run(message, session_id)

        # 2. 답변의 논문 출처 정보를 chat_source 테이블에 삽입
        if result.get("sources"):
            history = await self.chat_agent.get_history(session_id)
            assistant_index = len(history) - 1  # 답변이 기록된 메시지 리스트 상의 인덱스
            
            await self.chat_session_dao.insert_sources(
                session_id, assistant_index, result["sources"]
            )

        return result
```

---

## 🖥️ Slide 4: 대표 기능 2 — 사용자 정의 RAG 비서 (Gems)
#### 📄 대상 코드: [gems/gem_agent.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/gem_agent.py) / [gems/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/services.py)

**[발표자]**
> 세 번째는 대표 기능 중 두 번째인 **사용자 정의 RAG 비서(Gems)** 기능입니다.
> 사용자는 원하는 논문 데이터 소스(생명공학/컴퓨터과학/천문학 등)를 선택하고, 본인의 입맛에 맞는 시스템 프롬프트 가이드라인(페르소나 지침)을 결합하여 세상에 단 하나뿐인 특화 연구 비서를 개설할 수 있습니다.
> 
> 핵심 로직은 **`GemAgent`** 클래스의 **`_build_system_prompt`**와 **`_build_agent`** 메소드입니다.
> 
> 사용자가 입력한 지침 텍스트에, 백엔드 시스템에서 해당 데이터소스 툴을 바인딩할 수 있도록 유도하는 프롬프트를 자동으로 조립합니다.
> 특히, **"사용자가 한글로 질문을 던지더라도, RAG 엔진에 넘길 검색 파라미터는 반드시 영어 학술 핵심 용어로 자동 번역 및 치환해서 탐색할 것"**이라는 상세 규칙을 결합함으로써 RAG의 한글 검색 성능 저하 한계를 멋지게 돌파했습니다.

```python
# backend/api/v1/gems/gem_agent.py 중 일부

class GemAgent:
    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.model = model
        self.checkpointer = None
        self._initialized = False

    def _build_system_prompt(self, db_sources: list[str], persona_prompt: str) -> str:
        """사용자가 지정한 페르소나 지침과 선택한 데이터소스 가이드를 동적으로 합성합니다."""
        tool_lines = "\n".join(f"  · {_TOOL_CALL_DESC[src]}" for src in db_sources if src in _TOOL_CALL_DESC)
        
        return f"""{persona_prompt}

작업 방식:
- 질문 주제를 파악해서 아래 검색 도구 중 알맞은 것을 반드시 호출합니다.
{tool_lines}
- 중요: 검색 도구에 전달하는 query는 반드시 영어로 작성하세요.
  사용자가 한국어로 질문했더라도 핵심 개념을 영어 학술 용어로 번역해 검색합니다.
  예) "소행성체 형성" → "planetesimal formation"
- 검색된 논문 내용을 근거로, explanation에 질문에 대한 설명을 마크다운으로 풍부하게 작성합니다.
- papers에는 답변의 근거가 된 논문 각각을 정리합니다.
- 답변은 항상 사용자가 질문한 언어로 작성합니다.
"""

    def _build_agent(self, db_sources: list[str], system_prompt: str):
        """런타임 시점에 사용자가 설정한 소스에 맞춰 툴 목록을 다이내믹 바인딩하여 전용 에이전트를 빌드합니다."""
        tools = [_TOOL_MAP[src] for src in db_sources if src in _TOOL_MAP]
        if not tools:
            tools = [search_bio_papers]

        full_system_prompt = self._build_system_prompt(db_sources, system_prompt)

        return create_agent(
            model=self.model,
            tools=tools,
            system_prompt=full_system_prompt,
            checkpointer=self.checkpointer,
            state_schema=cast(Any, GemAgentState),
            response_format=GemAnswer
        )
```

> 대화가 시작될 때는 사용자의 요청에 포함된 `gem_id`를 기반으로 `GemService`에서 DB의 비서 설정 정보를 조회한 뒤, 비서의 지침 정보를 추출하여 즉석에서 에이전트 인스턴스를 동적으로 생성하고 비동기 대화 루틴을 밟게 됩니다.

```python
# backend/api/v1/gems/gem_agent.py (대화 실행부)

    async def run(self, message: str, thread_id: str, db_sources: list[str], system_prompt: str) -> dict:
        """지정된 Gem 비서의 페르소나와 툴 사양을 토대로 독립된 대화 턴을 진행합니다."""
        await self._initialize()
        
        # 1. 해당 Gem 사양에 맞는 맞춤형 에이전트 동적 생성
        agent = self._build_agent(db_sources, system_prompt)
        
        # 2. 지정된 thread_id(대화 세션)로 실행
        result = await agent.ainvoke(
            {
                "messages": [{"role": "user", "content": message}],
                "sources": [],
            },
            {"configurable": {"thread_id": thread_id}},
        )
        
        structured = result.get("structured_response")
        return {
            "answer": structured.explanation if structured else result["messages"][-1].content,
            "papers": [p.model_dump() for p in structured.papers] if structured else [],
            "sources": result.get("sources", [])
        }
```

---

## 🖥️ Slide 5: 대표 기능 3 — 대규모 비동기 연구 공백 분석 (Research Gap)
#### 📄 대상 코드: [research_gap/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/services.py)

**[발표자]**
> 마지막으로 대표 기능 중 세 번째인 **대규모 연구 공백(Research Gap) 분석** 기능입니다.
> 
> 대규모 분석은 LLM 호출이 연속적으로 일어나며 30초 이상의 시간이 소요되므로, 동기적으로 응답을 대기하게 되면 서버의 이벤트 루프가 멈춰 다른 유저들이 서버 마비 상태를 경험하게 됩니다.
> 
> 이를 해결하고자 저희는 **비동기 백그라운드 태스크(FastAPI BackgroundTasks)** 방식을 구축했습니다.
> 사용자가 특정 분야에 대한 연구 공백 분석을 요청하면, **`start_analysis`** 메소드는 우선 DB에 고유 태스크 ID와 함께 진행 상태를 PENDING으로 즉시 생성한 후, 백그라운드 대기열에 핵심 연산 루틴인 **`run_batch_analysis`**를 던지고 사용자에게는 작업 ID를 즉각 리턴합니다.

```python
# backend/api/v1/research_gap/services.py 중 일부

class ResearchGapService:
    def __init__(self, research_gap_dao: ResearchGapDaoDep) -> None:
        self.research_gap_dao = research_gap_dao

    async def start_analysis(self, domain: str, query: str, background_tasks, mid: str) -> str:
        """작업 요청 시 비차단(Non-blocking) 방식으로 UUID 태스크를 즉각 발행하고, 백그라운드 스레드를 예약합니다."""
        target_domain = domain.lower().strip()
        
        import uuid
        task_id = str(uuid.uuid4())
        
        # 1. 상태 데이터 생성 (PENDING)
        await self.research_gap_dao.create_task(task_id, target_domain, query, mid)
        
        # 2. 백그라운드 태스크 등록 및 비차단 즉시 반환
        background_tasks.add_task(self.run_batch_analysis, task_id, target_domain, query, mid)
        
        return task_id
```

> 백그라운드에서 백엔드 워커가 호출하는 **`run_batch_analysis`** 메소드는 독립적인 DB 커넥션 트랜잭션을 맺고 수행됩니다.
> 
> 1단계로 RAG 검색 엔진에 k=25 수준으로 대량 쿼리를 수행해 관련 학술 텍스트를 대량 확보한 다음, 중복 가공 과정을 거쳐 신뢰도가 가장 우수한 **최대 4개의 고유 논문**으로 최종 정밀 분석군을 축약합니다.
> 
> 2단계로 각 논문에 대해 `gpt-4o-mini` 모델의 Structured Output 기술을 활용해 각 논문의 구체적인 '해결 기법'과 '한계점'을 정확히 축출합니다. 특히, **해당 한계점이 거짓이 아님을 증명하기 위해 논문 원본의 구절을 한 자도 훼손하지 않고 긁어오는 영문 원문 인용 필드(`source_quote`)**를 함께 수집합니다.
> 
> 3단계로 추출된 개별 연구 한계점 매트릭스를 context로 삼아, 학계에 남겨진 공통된 한계점(`common_limitations`)과 이를 극복하여 새로운 논문을 투고할 수 있는 **3개의 혁신적 추천 연구 로드맵 방향성(`suggested_directions`)**을 최종 도출하여 기록합니다.
> 
> 작업이 완료되면 **SSE 실시간 알림 브로드캐스터**(`notification_broadcaster`)를 흔들어 대기 중인 사용자의 브라우저 화면에 실시간으로 완료 푸시 알림을 쏴주는 이벤트 구조를 완성했습니다.

```python
# backend/api/v1/research_gap/services.py (백그라운드 코어 배치 연산 루틴)

    async def run_batch_analysis(self, task_id: str, domain: str, query: str, mid: str) -> None:
        """대규모 RAG 검색, 문헌 축약, 개별 한계점 추출, 공통 공백 분석 및 추천 로드맵 도출 과정을 백그라운드에서 안전하게 실행합니다."""
        # 1. RUNNING 상태 갱신 (10%)
        async with session_maker() as session:
            dao = ResearchGapDao(session)
            await dao.update_task_progress(task_id, "RUNNING", 10)
            await session.commit()

        try:
            # 2. RAG 대량 탐색 (k=25) 후 고유 4개 문헌으로 압축 (30%)
            results = await common_rag_pipeline.similarity_search(domain, query, k=25)
            temp_papers = {}
            for r in results:
                arxiv_id = r["doc_id"]
                if arxiv_id and arxiv_id not in temp_papers:
                    temp_papers[arxiv_id] = {
                        "arxiv_id": arxiv_id,
                        "title": r["title"],
                        "chunks": [r["text_chunk"]]
                    }
            
            papers_list = list(temp_papers.values())[:4]  # 최대 4개 고유 문헌

            # 3. 개별 논문의 해결 기법 및 한계점(verbatim source_quote 포함) 추출 (60%)
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0).with_structured_output(PaperAnalysisResult)
            analyzed_papers = []
            for paper in papers_list:
                full_text = "\n".join(paper["chunks"])
                prompt = ChatPromptTemplate.from_template("다음 학술 논문 텍스트에서 한계점과 해결 기법을 추출하세요:\n\n{text}")
                res = await llm.ainvoke(prompt.format_messages(text=full_text))
                
                analyzed_papers.append({
                    "arxiv_id": paper["arxiv_id"],
                    "title": paper["title"],
                    "contributions": res.contributions[:2],  # 최대 2개
                    "limitations": res.limitations[:2]        # 최대 2개
                })

            # 4. 종합 공백 및 혁신 연구 로드맵 방향성 도출 (80%)
            matrix_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2).with_structured_output(ResearchGapMatrix)
            matrix_prompt = ChatPromptTemplate.from_template("종합 논문 분석 매트릭스를 기반으로 공통 한계점과 3개 로드맵 방향성을 수립하세요:\n\n{matrix}")
            final_matrix = await matrix_llm.ainvoke(matrix_prompt.format_messages(matrix=json.dumps(analyzed_papers, indent=2)))

            # 5. DB 결과 갱신 및 완료 업데이트 (100%)
            async with session_maker() as session:
                dao = ResearchGapDao(session)
                task = await dao.get_task(task_id, mid=mid)
                task.result = final_matrix.model_dump()
                task.status = "COMPLETED"
                task.progress = 100
                await session.commit()

            # 6. SSE 알림 브로드캐스팅을 통한 실시간 푸시 발송
            await notification_broadcaster.broadcast(
                mid=mid,
                message=f"'{query}'에 대한 연구 공백 분석이 성공적으로 완료되었습니다.",
                notification_type="RESEARCH_GAP",
                related_id=task_id
            )

        except Exception as e:
            # 예외 발생 시 FAIL 기록 및 사용자 고지
            async with session_maker() as session:
                dao = ResearchGapDao(session)
                await dao.update_task_error(task_id, str(e))
                await session.commit()
```

---

## 🖥️ Slide 6: 발표 마무리 및 질의응답 (Q&A)
**[발표자]**
> 이상으로 `Bist Mini 2` 백엔드 프로젝트의 RAG 핵심 파이프라인과 3대 비즈니스 도메인의 아키텍처 및 소스 코드 발표를 마치겠습니다.
> 
> 저희는 단순히 LLM API를 단순 중개하는 것을 넘어,
> 1. 대규모 pgvector 데이터소스를 유연하게 지향하는 **싱글톤 RAG 검색 파이프라인**,
> 2. 이전 대화 턴과 참고 문헌 출처까지 영구 복원하는 **체크포인팅 챗봇 엔진**,
> 3. 한글 질문을 정교한 영어 키워드로 치환해 RAG 성능을 극대화한 **동적 Gems 비서**,
> 4. 무거운 분석 연산으로부터 사용자 대기 시간을 차단하고 완료 즉시 푸시를 날리는 **비동기 백그라운드 Research Gap 엔진**까지 
> 
> 실질적이고 견고한 대학원 연구 조력 플랫폼으로서의 완성도 높은 인프라를 완성했습니다.
> 경청해 주셔서 감사합니다. 질문이 있으시면 성심껏 답변해 드리겠습니다.
