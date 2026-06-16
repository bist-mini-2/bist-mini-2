from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector, HALFVEC
from api.database.config.entity_base import Base


class PaperCsEntity(Base):
    """컴퓨터 과학 논문 메타데이터 엔티티 클래스입니다.

    Attributes:
        doc_id (str): ArXiv 논문 고유 ID (Primary Key).
        title (str): 논문 제목.
        abstract (str): 논문 초록 전체 본문.
        authors (str): 저자 목록.
        journal_ref (str): 게재 학술지/저널 정보.
        doi (str): DOI (Digital Object Identifier) 식별자.
        categories (str): ArXiv 학술 카테고리 태그.
        embeddings (relationship): 관련 청크 임베딩 리스트와의 관계성.
    """
    
    __tablename__ = "paper_cs"

    doc_id = Column(String(50), primary_key=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(Text, nullable=True)
    journal_ref = Column(Text, nullable=True)
    doi = Column(String(100), nullable=True)
    categories = Column(String(100), nullable=True)

    embeddings = relationship(
        "CsEmbeddingEntity",
        back_populates="paper",
        cascade="all, delete-orphan"
    )


class CsEmbeddingEntity(Base):
    """컴퓨터 과학 논문 초록의 개별 청크 및 3072차원 임베딩 벡터를 저장하는 엔티티 클래스입니다.

    Attributes:
        chunk_id (int): 청크 고유 식별자 (Primary Key, Auto increment).
        doc_id (str): 연결된 논문 메타데이터 외래 키 (ForeignKey).
        chunk_text (str): 500자 분할된 텍스트 본문.
        embedding (Vector): 3072차원 조밀 임베딩 벡터 (pgvector).
        chunk_index (int): 논문 내에서 청크 순서 번호 (0-indexed).
        paper (relationship): 부모 논문 메타데이터 엔티티 객체.
    """
    
    __tablename__ = "cs_embeddings"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(
        String(50),
        ForeignKey("paper_cs.doc_id", ondelete="CASCADE"),
        nullable=False
    )
    chunk_text = Column(Text, nullable=False)
    embedding = Column(HALFVEC(3072), nullable=False)
    chunk_index = Column(Integer, nullable=False)

    paper = relationship("PaperCsEntity", back_populates="embeddings")

    __table_args__ = (
        Index(
            "ix_cs_embeddings_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "halfvec_cosine_ops"},
        ),
    )
