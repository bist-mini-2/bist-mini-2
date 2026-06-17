from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import HALFVEC

from api.database.config.entity_base import Base


class CsCollectionEntity(Base):
    """컴퓨터 과학 논문 컬렉션 테이블 엔티티 클래스입니다 (langchain_postgres 컬렉션 구조 매핑)."""

    __tablename__ = "cs_collections"

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    cmetadata = Column(JSON, nullable=True)

    embeddings = relationship(
        "CsEmbeddingEntity",
        back_populates="collection",
        cascade="all, delete-orphan"
    )


class CsEmbeddingEntity(Base):
    """컴퓨터 과학 논문 임베딩 벡터 및 메타데이터를 저장하는 엔티티 클래스입니다 (langchain_postgres 임베딩 구조 매핑)."""

    __tablename__ = "cs_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True)
    collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cs_collections.uuid", ondelete="CASCADE"),
        nullable=True
    )
    embedding = Column(HALFVEC(3072), nullable=False)
    document = Column(Text, nullable=False)
    cmetadata = Column(JSON, nullable=True)
    custom_id = Column(String, nullable=True)

    collection = relationship("CsCollectionEntity", back_populates="embeddings")

    __table_args__ = (
        Index(
            "ix_cs_embeddings_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "halfvec_cosine_ops"},
        ),
    )
