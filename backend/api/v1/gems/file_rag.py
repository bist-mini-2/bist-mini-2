"""Gem별 사용자 업로드 파일의 텍스트 추출, 임베딩, pgvector 저장/검색을 담당하는 모듈입니다."""

import io
import logging
from typing import Any, Dict, List

import pdfplumber
from docx import Document as DocxDocument
from langchain.embeddings import init_embeddings
from langchain_postgres import PGVector

from api.common.config import settings

logger = logging.getLogger(__name__)

EMBED_MODEL = "openai:text-embedding-3-large"
CONNECTION = settings.PGVECTOR_URL
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".docx", ".doc"}


def _collection_name(gem_id: str) -> str:
    """Gem별 pgvector 컬렉션 이름을 반환합니다."""
    return f"gem_{gem_id}_files"


def _extract_text(filename: str, file_bytes: bytes) -> str:
    """파일 형식에 따라 텍스트를 추출합니다.

    Args:
        filename: 원본 파일명 (확장자 판별에 사용).
        file_bytes: 파일 바이너리 데이터.

    Returns:
        추출된 텍스트 문자열.
    """
    fname = filename.lower()

    if fname.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(p for p in pages if p.strip())

    if fname.endswith(".docx") or fname.endswith(".doc"):
        doc = DocxDocument(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    # TXT / MD / CSV 등 텍스트 계열
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore")


def _chunk_text(text: str) -> List[str]:
    """텍스트를 고정 크기 청크로 분할합니다 (CHUNK_OVERLAP 만큼 겹침).

    Args:
        text: 원본 텍스트.

    Returns:
        청크 문자열 리스트.
    """
    if not text.strip():
        return []

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP

    return chunks


class GemFileRag:
    """Gem별 업로드 파일의 RAG 파이프라인을 관리합니다."""

    def __init__(self) -> None:
        self._embeddings = None

    def get_embeddings(self):
        """임베딩 모델 인스턴스를 지연 초기화로 반환합니다."""
        if self._embeddings is None:
            self._embeddings = init_embeddings(model=EMBED_MODEL)
        return self._embeddings

    def _get_vectorstore(self, gem_id: str) -> PGVector:
        return PGVector(
            embeddings=self.get_embeddings(),
            collection_name=_collection_name(gem_id),
            connection=CONNECTION,
            async_mode=True,
        )

    async def process_and_store(
        self, gem_id: str, filename: str, file_bytes: bytes
    ) -> int:
        """파일에서 텍스트를 추출하고 청킹 후 pgvector에 저장합니다.

        Args:
            gem_id: 대상 Gem의 고유 ID.
            filename: 업로드된 파일명.
            file_bytes: 파일 바이너리 데이터.

        Returns:
            저장된 청크 수. 텍스트를 추출할 수 없으면 0.
        """
        text = _extract_text(filename, file_bytes)
        chunks = _chunk_text(text)

        if not chunks:
            logger.warning(f"파일 '{filename}'에서 텍스트를 추출하지 못했습니다.")
            return 0

        vectorstore = self._get_vectorstore(gem_id)
        metadatas = [{"filename": filename, "chunk_index": i} for i in range(len(chunks))]
        await vectorstore.aadd_texts(chunks, metadatas=metadatas)

        logger.info(f"Gem '{gem_id}' | 파일 '{filename}' → {len(chunks)}개 청크 저장 완료")
        return len(chunks)

    async def search(self, gem_id: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Gem의 업로드 파일 컬렉션에서 유사 청크를 검색합니다.

        Args:
            gem_id: 검색할 Gem ID.
            query: 검색 쿼리 텍스트.
            k: 반환할 최대 청크 수.

        Returns:
            각 청크의 filename, chunk_index, text_chunk, score를 담은 딕셔너리 리스트.
        """
        vectorstore = self._get_vectorstore(gem_id)
        results = await vectorstore.asimilarity_search_with_score(query, k=k)

        return [
            {
                "filename": (doc.metadata or {}).get("filename", ""),
                "chunk_index": (doc.metadata or {}).get("chunk_index", 0),
                "text_chunk": doc.page_content,
                "score": round(1.0 - score, 4),
            }
            for doc, score in results
        ]

    async def delete_collection(self, gem_id: str) -> None:
        """Gem의 파일 임베딩 컬렉션 전체를 삭제합니다. Gem 삭제 시 호출합니다.

        Args:
            gem_id: 삭제할 Gem ID.
        """
        try:
            vectorstore = self._get_vectorstore(gem_id)
            await vectorstore.adelete_collection()
            logger.info(f"Gem '{gem_id}' 파일 컬렉션 삭제 완료")
        except Exception as exc:
            logger.warning(f"Gem '{gem_id}' 파일 컬렉션 삭제 실패 (무시): {exc}")


# 싱글톤 인스턴스
gem_file_rag = GemFileRag()
