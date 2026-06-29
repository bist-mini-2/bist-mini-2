## **📝 이번 주 실제 개발 내용 요약 (금요일)**
- **전문 심사위원단 피어리뷰(Peer Review) 멀티에이전트 시뮬레이션**:
	- 논문 기밀 유지를 지원하는 격리 구역 내에서 업로드된 파일 본문을 바탕으로, 방법론 에이전트(Methodology), 독창성 에이전트(Novelty), 구조/스타일 에이전트(Academic Style)의 3대 전문 LLM 에이전트 심사 시뮬레이션을 구현하여 피드백 및 정량적 가중 점수를 합성합니다.
- **자기 일관성(Self-Consistency) 기반 RAG 가설 다수결 투표 검증**:
	- 사용자가 제출한 학술 가설의 정합성을 검증하기 위해 관련 팩트 청크를 RAG로 인출한 후, 다소 높은 온도의 3회 독립적 LLM 투표 추론을 가동하고 다수결(Majority Voting - SUPPORT / REFUTE / INSUFFICIENT_EVIDENCE)로 최종 검증 판정을 내리는 자기 일관성 추론 파이프라인을 구축했습니다.
- **턴제 실시간 채점 모의 구두 디펜스 및 평가 리포트 합성**:
	- 심사위원단 에이전트들의 공격적 질문에 대답하는 턴제(총 3턴) 구두 디펜스 세션을 구현했습니다.
	- 사용자의 실시간 답변을 논리성, 근거 인용, 한계 수용, 태도의 4가지 루브릭 지표로 엄격하게 실시간 채점하고, 디펜스가 끝나면 전체 세션 로그를 종합 분석하여 최종 개정 권고안(Minor/Major Revision, Reject) 리포트를 렌더링하도록 제작했습니다.
- **30분 미활동 만료 세션 이중 소거(Double-Wipe Out) 스케줄러**:
	- 기밀 문서가 서버 공간이나 pgvector DB에 방치되는 위험을 방어하기 위해 미활동 기준 30분 만료 시, 로컬 파일 디렉토리를 물리 삭제하고 DB의 vector 청크 테이블을 cascade 삭제하는 가비지 컬렉터 스케줄러를 도입했습니다. 보관함 저장 설정 여부에 따라 이중 소거 정책(CASCADE vs 파일/청크만 소거하고 히스토리 보존)을 세밀하게 분기했습니다.

---

## **💻 핵심 코드 예제 및 상세 해설**

### **1. Self-Consistency 기반 가설 검증 및 다수결 투표 (\\[services.py\\](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/services.py))**
온도 조절을 통한 다양성 확보와 Majority Voting 기법을 사용하여 가설을 신뢰성 높게 자동 검증하는 로직입니다.
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from api.v1.defense_arena.models import HypothesisVoteItem, HypothesisVerificationResult

async def verify_hypothesis(self, session_id: str, hypothesis: str, mid: str) -> HypothesisVerificationResult:
    # 1. 가설 임베딩 후 격리 세션 내 논문 유사 Fact 청크 5개 수집
    hypo_vector = embedding_helper.encode(hypothesis)
    search_results = await self.defense_arena_dao.similarity_search_in_session(session_id, hypo_vector, k=5)
    citations = [r[0].text_chunk for r in search_results]
    citations_context = "\n\n".join([f"[Fact {i+1}]: {c}" for i, c in enumerate(citations)])

    detailed_votes = []
    support_count, refute_count, insufficient_count = 0, 0, 0

    # 2. [Self-Consistency]: 온도를 다르게 주어 3회 독립 LLM 투표 추론 수행
    for i in range(3):
        # 온도를 점진적으로 다르게 설정하여 미묘한 추론 관점 변화 유도
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5 + (i * 0.1))
        structured_llm = llm.with_structured_output(HypothesisVoteItem)

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "Evaluate the hypothesis based ONLY on the provided facts.\n"
                "Verdict: 'SUPPORT', 'REFUTE', or 'INSUFFICIENT_EVIDENCE'."
            )),
            ("user", "Hypothesis: {hypothesis}\n\nFacts:\n{context}")
        ])

        vote_item = await (prompt | structured_llm).ainvoke({
            "hypothesis": hypothesis,
            "context": citations_context
        })
        detailed_votes.append(vote_item)
        
        v = vote_item.vote.upper().strip()
        if v == "SUPPORT":
            support_count += 1
        elif v == "REFUTE":
            refute_count += 1
        else:
            insufficient_count += 1

    # 3. 다수결(Majority Voting) 판정 알고리즘
    votes_map = {"SUPPORT": support_count, "REFUTE": refute_count, "INSUFFICIENT_EVIDENCE": insufficient_count}
    verdict = max(votes_map, key=lambda k: votes_map[k])
    consensus_ratio = votes_map[verdict] / 3.0

    return HypothesisVerificationResult(
        verdict=verdict,
        support_count=support_count,
        refute_count=refute_count,
        insufficient_count=insufficient_count,
        consensus_ratio=consensus_ratio,
        detailed_votes=detailed_votes,
        citations=citations
    )
```

### **🔍 주요 구문 및 설계 해설:**
- **Self-Consistency 기법**: 단일 LLM 호출의 우연한 오판을 방지하고 여러 번 독립 실행한 결과의 합치율(`consensus_ratio`)을 활용하여 가설 판정의 과학적 신뢰도를 보장합니다.

---

### **2. 보안 세션 가비지 컬렉터 및 이중 소거 정책 (\\[services.py\\](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/services.py))**
기밀 유지 샌드박스의 수명 주기가 끝나면 원천 흔적을 물리 파쇄하여 유출 위협을 차단하는 비동기 가비지 컬렉터입니다.
```python
import os
import shutil
import asyncio

async def wipe_out_expired_sessions(self, expire_minutes: int = 30) -> int:
    # 1. 30분 미활동 만료 세션 목록 조회
    expired = await self.defense_arena_dao.list_expired_sessions(expire_minutes)
    if not expired:
        return 0

    count = 0
    for session in expired:
        session_id = session.session_id
        session_dir = os.path.join(UPLOAD_DIR, session_id)
        
        # OS Path Guard 적용 물리 폴더 완전 소거
        real_upload_dir = os.path.realpath(UPLOAD_DIR)
        target_dir = os.path.realpath(session_dir)
        if target_dir.startswith(real_upload_dir) and target_dir != real_upload_dir:
            try:
                await asyncio.to_thread(shutil.rmtree, target_dir, ignore_errors=True)
            except Exception as ex:
                self.logger.error(f"Failed to delete session directory: {ex}")

        # [이중 소거(Double-Wipe) 정책 분기]
        if session.is_saved:
            # 보관함 아카이빙 세션: 업로드 파일 및 pgvector 청크만 영구 삭제하고, 텍스트 결과는 보존
            await self.defense_arena_dao.delete_chunks(session_id)
            session.file_path = ""
            session.chunk_count = 0
            await self.defense_arena_dao.update_session(session)
        else:
            # 미보관 세션: DB 레코드 자체를 완전 CASCADE 소거
            await self.defense_arena_dao.delete_session(session_id)
            
        count += 1
    return count
```

### **🔍 주요 구문 및 설계 해설:**
- **이중 소거 정책**: 민감도가 매우 높은 원문 파일(PDF)과 그로부터 생성된 세부 벡터 청크(`DefenseArenaChunkEntity`)는 보관함 저장 유무와 관계없이 무조건 물리 삭제하여 원천 정보를 소거하는 강력한 보안 규격입니다.
- **`shutil.rmtree` 비동기화**: 파일 시스템의 I/O 지연이 백엔드 단일 스레드를 방해하지 않도록 `asyncio.to_thread`를 사용하여 안전하게 백그라운드 스레드에서 폴더 트리 전체를 날려버립니다.
