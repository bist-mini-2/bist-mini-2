import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from langchain.tools import ToolRuntime
from langchain_core.documents import Document
from typing import Any, cast

from api.common.rag_pipeline import (
    common_rag_pipeline,
    search_bio_papers,
    search_cs_papers,
    search_astronomy_papers
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


# =====================================================================
# RAG Similarity Search Class Tests
# =====================================================================

@pytest.mark.anyio
async def test_common_rag_pipeline_similarity_search_success():
    """CommonRagPipeline이 PGVector와 코사인 유사도를 올바르게 계산하고 결과를 반환하는지 검증합니다."""
    with patch("api.common.rag_pipeline.PGVector") as mock_pgvector:
        mock_instance = mock_pgvector.return_value
        
        # PGVector는 (Document, distance)의 튜플 리스트를 반환함
        mock_doc = Document(
            page_content="Mocked Abstract Text",
            metadata={"arxiv_id": "2406.12345", "title": "Test Title"}
        )
        # distance가 0.05 이면 코사인 유사도는 1.0 - 0.05 = 0.95
        mock_instance.asimilarity_search_with_score = AsyncMock(return_value=[(mock_doc, 0.0500)])
        
        results = await common_rag_pipeline.similarity_search("cs", "neural network", k=1)
        
        assert len(results) == 1
        assert results[0]["doc_id"] == "2406.12345"
        assert results[0]["title"] == "Test Title"
        assert results[0]["text_chunk"] == "Mocked Abstract Text"
        assert results[0]["score"] == 0.95


@pytest.mark.anyio
async def test_common_rag_pipeline_invalid_domain():
    """지원하지 않는 도메인 입력 시 ValueError가 발생하는지 검증합니다."""
    with pytest.raises(ValueError) as excinfo:
        await common_rag_pipeline.similarity_search("invalid_domain", "query")
    assert "지원하지 않는 도메인입니다" in str(excinfo.value)


# =====================================================================
# RAG Agent Tools Tests
# =====================================================================

@pytest.mark.anyio
@patch("api.common.rag_pipeline.common_rag_pipeline.similarity_search")
async def test_search_bio_papers_tool_success(mock_search):
    """search_bio_papers 툴이 모든 결과를 정상 응답으로 반환하는지 테스트합니다."""
    mock_search.return_value = [
        {"doc_id": "bio-1", "title": "Bio Title 1", "text_chunk": "Content 1", "score": 0.40},
        {"doc_id": "bio-2", "title": "Bio Title 2", "text_chunk": "Content 2", "score": 0.30},
    ]
    
    mock_runtime = MagicMock(spec=ToolRuntime)
    mock_runtime.tool_call_id = "bio_call_id"
    
    command = await cast(Any, search_bio_papers).coroutine(
        query="genomics",
        runtime=mock_runtime,
        k=2
    )
    
    assert "messages" in command.update
    assert len(command.update["messages"]) == 1
    content = command.update["messages"][0].content
    assert "Bio Title 1" in content
    assert "Bio Title 2" in content  # 필터링 안 됨
    assert len(command.update["sources"]) == 2
    assert command.update["sources"][0]["arxiv_id"] == "bio-1"
    assert command.update["sources"][1]["arxiv_id"] == "bio-2"


@pytest.mark.anyio
@patch("api.common.rag_pipeline.common_rag_pipeline.similarity_search")
async def test_search_bio_papers_tool_empty(mock_search):
    """검색 결과가 없을 때의 search_bio_papers 툴 대체 메시지 반환을 검증합니다."""
    mock_search.return_value = []
    
    mock_runtime = MagicMock(spec=ToolRuntime)
    mock_runtime.tool_call_id = "bio_call_id"
    
    command = await cast(Any, search_bio_papers).coroutine(
        query="genomics",
        runtime=mock_runtime,
        k=1
    )
    
    content = command.update["messages"][0].content
    assert "찾을 수 없습니다" in content


@pytest.mark.anyio
@patch("api.common.rag_pipeline.common_rag_pipeline.similarity_search")
async def test_search_cs_papers_tool_success(mock_search):
    """search_cs_papers 툴이 검색 결과를 올바르게 반환하는지 테스트합니다."""
    mock_search.return_value = [
        {"doc_id": "cs-1", "title": "CS Title 1", "text_chunk": "CS Content 1", "score": 0.85},
    ]
    
    mock_runtime = MagicMock(spec=ToolRuntime)
    mock_runtime.tool_call_id = "cs_call_id"
    
    command = await cast(Any, search_cs_papers).coroutine(
        query="neural network",
        runtime=mock_runtime,
        k=1
    )
    
    content = command.update["messages"][0].content
    assert "CS Title 1" in content
    assert command.update["sources"][0]["arxiv_id"] == "cs-1"


@pytest.mark.anyio
@patch("api.common.rag_pipeline.common_rag_pipeline.similarity_search")
async def test_search_astronomy_papers_tool_success(mock_search):
    """search_astronomy_papers 툴이 검색 결과를 올바르게 반환하는지 테스트합니다."""
    mock_search.return_value = [
        {"doc_id": "astro-1", "title": "Astro Title 1", "text_chunk": "Astro Content 1", "score": 0.90},
    ]
    
    mock_runtime = MagicMock(spec=ToolRuntime)
    mock_runtime.tool_call_id = "astro_call_id"
    
    command = await cast(Any, search_astronomy_papers).coroutine(
        query="mars atmosphere",
        runtime=mock_runtime,
        k=1
    )
    
    content = command.update["messages"][0].content
    assert "Astro Title 1" in content
    assert command.update["sources"][0]["arxiv_id"] == "astro-1"
