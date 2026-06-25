import asyncio
import json
import logging
import operator
from typing import Annotated, Any, cast, AsyncGenerator

from fastapi import Depends
from langchain.agents import create_agent, AgentState
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from api.common.rag_pipeline import (
    search_bio_papers,
    search_cs_papers,
    search_astronomy_papers,
)
from api.database.config.psycopg_pool import psycopg_pool as chat_psycopg_pool


class GemAgentState(AgentState):
    """Gem 에이전트의 대화 상태 및 검색된 출처 목록을 저장하는 상태 정의 딕셔너리입니다.

    AgentState를 상속하여 messages / jump_to / structured_response 필드를 포함하며,
    sources 필드는 operator.add reducer로 여러 툴 호출 결과를 누적합니다.
    """
    sources: Annotated[list[dict], operator.add]   # 검색된 논문 출처 누적


logger = logging.getLogger(__name__)

# db_sources 값 → 실제 tool 매핑
_TOOL_MAP = {
    "bio": search_bio_papers,
    "cs": search_cs_papers,
    "astronomy": search_astronomy_papers,
}

# db_sources 값 → 시스템 프롬프트 내 툴 호출 안내 문구
_TOOL_CALL_DESC = {
    "bio": "생명공학·유전체학(유전자, DNA, 시퀀싱, 단백질 등) 관련 질문 → search_bio_papers",
    "cs": "컴퓨터과학(신경망, 딥러닝, 진화 알고리즘, 머신러닝 등) 관련 질문 → search_cs_papers",
    "astronomy": "천문학(외계행성, 행성, 천체물리, 우주 등) 관련 질문 → search_astronomy_papers",
}

_FILE_TOOL_DESC = "사용자가 업로드한 파일 내용 검색 → search_gem_files (업로드 파일에서 답을 찾을 수 있을 때 반드시 호출)"


def _make_file_search_tool(gem_id: str):
    """gem_id를 캡처한 동적 파일 검색 툴을 생성합니다."""
    from api.v1.gems.file_rag import gem_file_rag  # 순환 임포트 방지를 위해 지연 임포트

    @tool
    async def search_gem_files(query: str, runtime: ToolRuntime, k: int = 10) -> Command:
        """사용자가 이 Gem에 업로드한 파일 내용에서 관련 정보를 검색합니다.

        업로드 파일 기반 질문이거나 추가 맥락이 필요할 때 이 도구를 호출하세요.

        Args:
            query: 검색할 핵심 키워드 또는 질문 (영어 권장).
            runtime: LangGraph 툴 런타임 컨텍스트.
            k: 반환할 상위 청크 수. 기본값은 3.
        """
        results = await gem_file_rag.search(gem_id, query, k=k)

        if results is None or not results:
            msg = f"업로드된 파일에서 '{query}'와 관련된 내용을 찾지 못했습니다."
            return Command(update={
                "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
            })

        output_lines = [f"업로드 파일 검색 결과: '{query}'\n", "=" * 80]
        file_sources = []
        seen_files: set[str] = set()
        for idx, r in enumerate(results, 1):
            output_lines.append(f"\n[파일 {idx}] {r['filename']} (유사도: {r['score']:.4f})")
            output_lines.append(f"\n내용:\n{r['text_chunk']}\n")
            output_lines.append("-" * 80)
            # 파일명 기준 중복 제거 후 sources에 추가 (type: "file" 표시)
            if r["filename"] not in seen_files:
                seen_files.add(r["filename"])
                snippet = " ".join((r["text_chunk"] or "").split())
                if len(snippet) > 160:
                    snippet = snippet[:160].rstrip() + "…"
                file_sources.append({
                    "type": "file",
                    "arxiv_id": "",
                    "title": r["filename"],
                    "summary": snippet,
                    "score": round(r["score"], 4),
                })

        return Command(update={
            "messages": [ToolMessage(content="\n".join(output_lines), tool_call_id=runtime.tool_call_id)],
            "sources": file_sources,
        })

    return search_gem_files


class GemPaperRef(BaseModel):
    """답변 근거가 된 논문 한 편."""
    arxiv_id: str = Field(description="논문의 arXiv ID (예: 2504.10388)")
    title: str = Field(description="논문 제목")
    summary: str = Field(description="이 논문이 질문과 어떻게 관련되는지 한 문장 요약")


class GemAnswer(BaseModel):
    """Gem RAG 답변 구조."""
    explanation: str = Field(
        description=(
            "질문에 대한 자연스러운 설명. 논문을 번호로 나열하지 말고 "
            "질문에 직접 답하는 서술형 마크다운으로 작성한다. "
            "핵심 용어는 **굵게** 강조하고, 내용이 길면 ## 소제목으로 구조를 나눠도 좋다."
        )
    )
    papers: list[GemPaperRef] = Field(
        default_factory=list,
        description="답변 근거가 된 논문 목록"
    )


class GemAgent:
    """Gem 전용 에이전트.

    db_sources 목록에 해당하는 RAG 도구만 선택적으로 탑재하고,
    사용자가 지정한 system_prompt를 페르소나로 바인딩한다.
    응답은 chat_agent와 동일한 구조화 출력(explanation + papers)으로 강제한다.
    대화 이력은 AsyncPostgresSaver가 thread_id별로 영구 저장한다.
    chat_psycopg_pool을 재사용하므로 별도 풀을 생성하지 않는다.
    """

    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger(f"{__name__}.GemAgent")
        self.model = model
        self.checkpointer = None
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """최초 1회 psycopg 풀 확인 후 checkpointer를 생성한다."""
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            if chat_psycopg_pool.closed:
                await chat_psycopg_pool.open()
            self.checkpointer = AsyncPostgresSaver(cast(Any, chat_psycopg_pool))

            async with chat_psycopg_pool.connection() as conn:
                cur = await conn.execute(
                    "SELECT 1 FROM pg_tables "
                    "WHERE schemaname='public' AND tablename='checkpoints'"
                )
                exists = await cur.fetchone()
                if not exists:
                    await conn.execute(
                        "DROP TABLE IF EXISTS checkpoint_migrations, checkpoint_blobs, checkpoint_writes CASCADE;"
                    )
            if not exists:
                assert self.checkpointer is not None
                await self.checkpointer.setup()

            self._initialized = True
            self.logger.info("GemAgent checkpointer 초기화 완료")

    def _build_system_prompt(
        self, db_sources: list[str], persona_prompt: str, has_files: bool = False, streaming: bool = False
    ) -> str:
        """선택된 db_sources + 파일 유무에 맞는 툴 호출 지침 + 페르소나를 합쳐 시스템 프롬프트를 생성한다."""
        tool_lines = "\n".join(
            f"  · {_TOOL_CALL_DESC[src]}"
            for src in db_sources
            if src in _TOOL_CALL_DESC
        )
        if has_files:
            tool_lines += f"\n  · {_FILE_TOOL_DESC}"

        if streaming:
            return f"""{persona_prompt}

작업 방식:
- 질문 주제를 파악해서 아래 검색 도구 중 알맞은 것을 반드시 호출합니다.
{tool_lines}
- 중요: 검색 도구에 전달하는 query는 반드시 영어로 작성하세요.
  사용자가 한국어로 질문했더라도 핵심 개념을 영어 학술 용어로 번역해 검색합니다.
- 검색된 내용을 근거로 질문에 대한 답변을 마크다운으로 풍부하게 작성합니다.
  핵심 용어는 **굵게** 강조하고, 길면 ## 소제목으로 구조를 나눠도 좋습니다.
- 중요: 참고한 논문 목록을 본문에 나열하거나 별도 섹션을 만들지 마세요. 설명에만 집중합니다.
- 검색 결과에 없는 내용은 지어내지 말고 "관련 내용을 찾지 못했습니다"라고 적습니다.
- 답변은 항상 사용자가 질문한 언어로 작성합니다(한국어 질문이면 한국어로).
"""

        return f"""{persona_prompt}

작업 방식:
- 질문 주제를 파악해서 아래 검색 도구 중 알맞은 것을 반드시 호출합니다.
{tool_lines}
- 중요: 검색 도구에 전달하는 query는 반드시 영어로 작성하세요.
  사용자가 한국어로 질문했더라도 핵심 개념을 영어 학술 용어로 번역해 검색합니다.
  예) "소행성체 형성" → "planetesimal formation"
      "외계행성 대기" → "exoplanet atmosphere"
      "행성 이주" → "planetary migration"
- 검색된 내용을 근거로, explanation에 질문에 대한 설명을 마크다운으로 풍부하게 작성합니다.
  핵심 용어는 **굵게** 강조하고, 내용이 길면 ## 소제목으로 구조를 나눠도 좋습니다.
  질문에 맞춰 설명 길이를 조절합니다.
  단, 개별 논문을 "1. 2. 3."처럼 번호로 나열하지는 마세요. 논문 하나하나는 papers가 담당합니다.
- papers에는 답변의 근거가 된 논문 각각을 정리합니다(제목, arxiv_id, 한 줄 요약).
  업로드 파일에서 얻은 내용의 경우 arxiv_id를 빈 문자열("")로, title을 파일명으로 설정합니다.
- 검색 결과에 없는 내용은 지어내지 말고, explanation에 "관련 내용을 찾지 못했습니다"라고 적습니다.
- 답변은 항상 사용자가 질문한 언어로 작성합니다(한국어 질문이면 한국어로).
"""

    def _build_agent(
        self,
        db_sources: list[str],
        system_prompt: str,
        gem_id: str | None = None,
        has_files: bool = False,
    ):
        """db_sources + 파일 유무에 맞는 tool 목록과 system_prompt로 agent를 동적으로 생성한다."""
        tools = [_TOOL_MAP[src] for src in db_sources if src in _TOOL_MAP]
        if not tools:
            tools = [search_bio_papers]

        if has_files and gem_id:
            tools.append(_make_file_search_tool(gem_id))

        full_system_prompt = self._build_system_prompt(db_sources, system_prompt, has_files)

        return create_agent(
            model=self.model,
            tools=tools,
            system_prompt=full_system_prompt,
            checkpointer=self.checkpointer,
            state_schema=GemAgentState,
            response_format=GemAnswer,
        )

    def _build_stream_agent(
        self,
        db_sources: list[str],
        system_prompt: str,
        gem_id: str | None = None,
        has_files: bool = False,
    ):
        """스트리밍 전용 에이전트 — response_format 없이 마크다운 텍스트를 직접 출력한다."""
        tools = [_TOOL_MAP[src] for src in db_sources if src in _TOOL_MAP]
        if not tools:
            tools = [search_bio_papers]

        if has_files and gem_id:
            tools.append(_make_file_search_tool(gem_id))

        full_system_prompt = self._build_system_prompt(db_sources, system_prompt, has_files, streaming=True)

        return create_agent(
            model=self.model,
            tools=tools,
            system_prompt=full_system_prompt,
            checkpointer=self.checkpointer,
            state_schema=GemAgentState,
            # response_format 없음 — 스트리밍은 JSON 완성 전까지 파싱 불가
        )

    async def run_stream(
        self,
        message: str,
        thread_id: str,
        db_sources: list[str],
        system_prompt: str,
        gem_id: str | None = None,
        has_files: bool = False,
    ) -> AsyncGenerator[dict, None]:
        """토큰 단위 스트리밍으로 메시지를 처리한다. 채팅허브와 동일한 방식."""
        await self._initialize()
        agent = self._build_stream_agent(db_sources, system_prompt, gem_id=gem_id, has_files=has_files)

        _TOOL_STATUS = {
            "search_bio_papers": "paper_search",
            "search_cs_papers": "paper_search",
            "search_astronomy_papers": "paper_search",
            "search_gem_files": "file_search",
        }
        announced_tools: set[str] = set()
        config = {"configurable": {"thread_id": thread_id}}
        captured_sources: list[dict] = []

        async for stream_mode, chunk in agent.astream(
            {"messages": [{"role": "user", "content": message}], "sources": []},
            config,
            stream_mode=cast(Any, ["messages", "values"]),
        ):
            # values 모드: 매 스텝 후 전체 state — sources 캡처
            if stream_mode == "values":
                if isinstance(chunk, dict):
                    sv = chunk.get("sources")
                    if sv:
                        captured_sources = list(sv)
                continue

            # messages 모드
            token, metadata = chunk

            # 도구 호출 감지 → status 이벤트 (첫 등장 1회)
            names: list[str] = []
            for tc in (getattr(token, "tool_call_chunks", None) or []):
                if tc.get("name"):
                    names.append(tc["name"])
            for tc in (getattr(token, "tool_calls", None) or []):
                if tc.get("name"):
                    names.append(tc["name"])
            for name in names:
                if name not in announced_tools:
                    announced_tools.add(name)
                    yield {"type": "status", "data": _TOOL_STATUS.get(name, "tool")}

            # 도구 노드 결과 토큰 / 도구 호출만 담은 AI 토큰은 답변이 아니므로 스킵
            if isinstance(metadata, dict) and metadata.get("langgraph_node") == "tools":
                continue
            if getattr(token, "tool_calls", None):
                continue

            content = getattr(token, "content", "")
            if content:
                yield {"type": "token", "data": content}

        # 스트리밍 완료 후 캡처한 sources를 papers 이벤트로 방출
        if captured_sources:
            seen: set[str] = set()
            unique: list[dict] = []
            for s in captured_sources:
                key = s.get("arxiv_id") or s.get("title", "")
                if key and key not in seen:
                    seen.add(key)
                    unique.append(s)
            if unique:
                yield {"type": "papers", "data": unique}

    async def run(
        self,
        message: str,
        thread_id: str,
        db_sources: list[str],
        system_prompt: str,
        gem_id: str | None = None,
        has_files: bool = False,
    ) -> dict:
        """메시지를 처리하여 answer와 sources를 반환한다(대화 기록 자동 저장/복원)."""
        await self._initialize()
        agent = self._build_agent(db_sources, system_prompt, gem_id=gem_id, has_files=has_files)
        try:
            result = await agent.ainvoke(
                {
                    "messages": [{"role": "user", "content": message}],
                    "sources": [],
                },
                {"configurable": {"thread_id": thread_id}},
            )

            # 구조화 출력 추출 (chat_agent와 동일한 방식)
            structured = result.get("structured_response")
            if structured:
                answer = structured.explanation
                papers = [p.model_dump() for p in structured.papers]
            else:
                # response_format 미지원 시 LLM이 JSON 문자열을 그대로 content에 넣는 경우 파싱
                raw_content = result["messages"][-1].content
                try:
                    parsed = json.loads(raw_content)
                    answer = parsed.get("explanation", raw_content)
                    papers = parsed.get("papers", [])
                except (json.JSONDecodeError, AttributeError):
                    answer = raw_content
                    papers = []

            seen = set()
            unique_sources = []
            for s in result.get("sources", []):
                key = s.get("arxiv_id") or s.get("doc_id", "")
                if key not in seen:
                    seen.add(key)
                    unique_sources.append(s)

            return {
                "answer": answer,
                "papers": papers,
                "sources": unique_sources,
            }
        except Exception as e:
            self.logger.error(f"Gem 대화 처리 실패 (thread_id={thread_id}): {e}")
            return {
                "answer": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "papers": [],
                "sources": [],
            }

    async def get_history(
        self,
        thread_id: str,
        db_sources: list[str],
        system_prompt: str,
        gem_id: str | None = None,
        has_files: bool = False,
    ) -> list[dict]:
        """대화 스레드의 user/assistant 메시지 내역을 순서대로 반환한다."""
        await self._initialize()
        agent = self._build_agent(db_sources, system_prompt, gem_id=gem_id, has_files=has_files)
        state = await agent.aget_state(
            {"configurable": {"thread_id": thread_id}}
        )
        messages = state.values.get("messages", []) if state.values else []

        history = []
        for msg in messages:
            msg_type = getattr(msg, "type", None)
            content = getattr(msg, "content", "")
            if msg_type == "human":
                history.append({"role": "user", "content": content})
            elif msg_type == "ai" and content:
                # JSON 문자열로 저장된 경우 explanation만 추출
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict) and "explanation" in parsed:
                        content = parsed["explanation"]
                except (json.JSONDecodeError, TypeError):
                    pass
                history.append({"role": "assistant", "content": content})
        return history

    async def clear_history(self, thread_id: str) -> None:
        """대화 스레드의 모든 기록을 삭제한다."""
        await self._initialize()
        assert self.checkpointer is not None
        await self.checkpointer.adelete_thread(thread_id)


# 싱글톤 인스턴스
_gem_agent = GemAgent()


def get_gem_agent() -> GemAgent:
    """GemAgent 싱글톤 인스턴스를 반환하는 의존성 제공자."""
    return _gem_agent


GemAgentDep = Annotated[GemAgent, Depends(get_gem_agent)]
