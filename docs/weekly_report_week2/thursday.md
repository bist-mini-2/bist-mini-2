## **📝 이번 주 실제 개발 내용 요약 (목요일)**
- **Stage-2 Full-Text RAG 아키텍처 및 파이프라인 단일 공통화**:
	- 3개 학술 도메인(cs, bio, astronomy)의 파편화된 RAG 검색 로직과 에이전트 툴들을 공통 모듈인 `rag_pipeline.py`로 단일 통합했습니다.
	- 단순히 논문 초록(Abstract)만 검색하는 기존 RAG의 정보 한계를 넘어서기 위해, 실제 논문의 전체 본문(Full-Text)을 RAG 검색 영역으로 삼는 **Stage-2 Full-Text RAG** 메커니즘을 설계했습니다.
- **온디맨드 실시간 텍스트 청킹 및 pgvector 적재 (On-Demand Vectorization)**:
	- 사용자가 특정 논문을 지정하여 분석 대화를 시작할 때, 해당 논문이 아직 벡터 데이터베이스에 없을 경우 `paper_cache_service`를 거쳐 논문 원본 본문을 실시간 수집(크롤링/캐시)한 후 500자 단위(오버랩 100자)로 청킹하여 pgvector의 전용 본문 테이블(`paper_full_text_embeddings`)에 즉각 적재하는 실시간 임베딩 파이프라인을 구현했습니다.
- **메타데이터 필터를 활용한 타겟팅 논문 정밀 유사도 검색**:
	- 전체 논문 풀에서 검색하여 불필요한 노이즈가 유입되는 것을 방어하기 위해, RAG 검색 시 해당 대화에서 지정한 논문 ID 목록(`paper_ids`)에 대해서만 메타데이터 필터(`filter={"paper_id": clean_id}`)를 주입하여 정밀 검색하고 코사인 유사도 점수로 통합 정렬 후 최종 컨텍스트로 공급하는 로직을 완성했습니다.

---

## **💻 핵심 코드 예제 및 상세 해설**

### **1. 온디맨드 벡터화 및 필터링 RAG 검색 (\\[rag_pipeline.py\\](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/rag_pipeline.py))**
특정 논문들을 실시간으로 임베딩 적재하고 해당 논문 ID 범위 내에서만 정밀 유사도 검색을 수행하는 이중 RAG 처리 코드입니다.
```python
from sqlalchemy import select
from langchain_postgres import PGVector
from api.common.entities import PaperFullTextCacheEntity
from api.common.paper_cache_service import paper_cache_service

async def get_full_text_context(
    self,
    db: AsyncSession,
    paper_ids: List[str],
    query: str,
    domain: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    self.logger.info(f"Stage-2 Full-Text RAG: paper_ids={paper_ids}, query='{query}'")
    
    # 1. 미임베딩 논문 확인 및 온디맨드 실시간 벡터화
    for pid in paper_ids:
        clean_id = pid.strip()
        if not clean_id:
            continue

        # paper_cache_service를 통해 논문 본문 원문 획득 (캐시 미스 시 자동 크롤링)
        try:
            full_text = await paper_cache_service.get_paper_full_text(db, clean_id, domain)
        except Exception as e:
            self.logger.error(f"논문 {clean_id} 본문 로드 실패: {e}")
            continue

        # DB 엔티티 조회를 통해 이미 벡터화되었는지 플래그 검증
        query_db = select(PaperFullTextCacheEntity).where(PaperFullTextCacheEntity.paper_id == clean_id)
        db_res = await db.execute(query_db)
        paper_entity = db_res.scalar_one_or_none()

        # 벡터화되지 않은 신규 논문의 경우, 실시간 청킹 및 pgvector 임베딩 적재 수행
        if paper_entity and not paper_entity.is_vectorized:
            self.logger.info(f"논문 {clean_id} 본문 벡터화 진행 중...")
            
            # 본문 커스텀 청킹 (500자 크기, 100자 오버랩)
            chunks = self._chunk_text_custom(full_text, chunk_size=500, overlap=100)
            
            if chunks:
                vectorstore = PGVector(
                    embeddings=self.get_embeddings(),
                    collection_name="paper_full_text_embeddings",
                    connection=CONNECTION,
                    async_mode=True,
                )
                metadatas = [
                    {
                        "paper_id": clean_id,
                        "title": paper_entity.title or f"arXiv Paper {clean_id}",
                        "chunk_index": i
                    }
                    for i in range(len(chunks))
                ]
                # pgvector에 청크 텍스트 및 메타데이터 일괄 등록
                await vectorstore.aadd_texts(chunks, metadatas=metadatas)

            # 벡터화 완료 상태를 DB에 기록하여 다음 대화 시 연산 중복을 차단합니다 (Lazy-Indexing).
            paper_entity.is_vectorized = True
            db.add(paper_entity)
            await db.commit()

    # 2. 지정된 논문 ID(paper_ids)에 매핑되는 메타데이터 필터 기반 RAG 검색
    all_chunks = []
    vectorstore = PGVector(
        embeddings=self.get_embeddings(),
        collection_name="paper_full_text_embeddings",
        connection=CONNECTION,
        async_mode=True,
    )

    for pid in paper_ids:
        clean_id = pid.strip()
        if not clean_id:
            continue
        try:
            # 타겟 논문에 대해서만 필터를 걸어 유사도 검색 실행 (속도 및 정확도 향상)
            results = await vectorstore.asimilarity_search_with_score(
                query, k=k, filter={"paper_id": clean_id}
            )
            for doc, score in results:
                all_chunks.append((doc, score))
        except Exception as e:
            self.logger.error(f"논문 {clean_id} RAG 검색 에러: {e}")

    # 3. 코사인 유사도 점수(1.0 - distance) 기준으로 상위 k개 정렬 및 리턴
    all_chunks.sort(key=lambda x: round(1.0 - x[1], 4), reverse=True)
    
    return [
        {
            "paper_id": doc.metadata.get("paper_id", ""),
            "title": doc.metadata.get("title", ""),
            "text_chunk": doc.page_content,
            "score": round(1.0 - score, 4)
        }
        for doc, score in all_chunks[:k]
    ]
```

### **🔍 주요 구문 및 설계 해설:**
- **`filter={"paper_id": clean_id}`**: pgvector 인덱스 탐색 범위를 특정 논문 한 편으로 제약하여, 대규모 논문 데이터베이스 환경에서도 하드웨어 디스크 연산 부담을 줄이고 정확한 컨텍스트 매칭을 보장합니다.
- **Lazy-Indexing (지연 벡터화)**: 논문 수집 시점에 모든 논문을 벡터화하려면 서버에 막대한 임베딩 API 비용과 지연이 생깁니다. 대화에서 사용자가 실제로 읽어들이기를 원할 때만 **온디맨드(On-demand)**로 작업을 수행하여 자원을 극도로 절약합니다.
