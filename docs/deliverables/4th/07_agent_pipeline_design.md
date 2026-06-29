# 7. 핵심 기능별 에이전트 파이프라인 설계 (Agent Pipeline Design)

본 문서는 `bist-mini-2` 플랫폼의 AI 지식 합성 오케스트레이션을 제어하는 **LangGraph 멀티 에이전트 파이프라인**의 물리 설계 스펙과 실시간 동적 툴 바인딩 및 데이터 격리 메커니즘을 상세히 정의합니다.

---

## 7-1. 섹션 도입 및 전략적 중요성

단일 LLM 호출에만 의존하는 기존의 아키텍처는 여러 지식 소스를 조합하는 과정에서 프롬프트가 과대화되어 인스트럭션이 누수되거나 환각(Hallucination) 현상이 발생하는 기술적 난제를 안고 있습니다. 

본 플랫폼은 이를 극복하기 위해 **LangGraph 기반의 상태 전이(State Transition) 오케스트레이션**을 도입했습니다. 각 노드에 독립된 역할군과 제약 조건을 부여하고, 병렬 I/O 처리와 클로저 기반 툴 주입 기법을 적용함으로써 응답 레이턴시의 단축과 답변의 논리적 신뢰성을 동시에 확보하는 전략을 실현했습니다.

---

## 7-2. 일반 챗 허브 (Unconditional Parallel Execution)

일반 챗 허브는 속도 향상을 위해 데이터 라우팅을 판단하는 조건부 분기 단계를 거치지 않고, **학술 RAG와 실시간 웹 검색을 무조건적으로 병렬 가동(Unconditional Parallel Execution)**하여 지식 풀의 즉각적인 풍부함을 수립합니다.

![Agent Pipeline Workflow](ai_agent_workflow.png)

### 1) 노드별 동작 및 융합 합성 메커니즘
1.  **AnalysisNode**: 자연어 질문으로부터 RAG에 타겟팅할 영어 키워드와 최신 동향 탐색용 웹 검색 쿼리를 동시에 인출하여 컨텍스트 분해를 완료합니다 (`gpt-4o-mini` 기용).
2.  **PaperNode & WebNode (병렬 가동)**: `asyncio.gather` 비동기 큐를 타격하여 pgvector 코사인 유사도 검색과 Tavily Search API 웹 크롤링을 동시 가동합니다. 두 I/O 바운드 작업의 최대 시간 소요는 결국 $\max(T_{\text{paper}}, T_{\text{web}})$로 수렴하므로 레이턴시가 크게 단축됩니다.
3.  **SynthesisNode**: 두 지식 소스의 교차 조인(Cross-Join) 팩트 분석을 수행하고 인라인 인용 부호가 포함된 완성도 높은 마크다운 보고서로 답변을 최종 합성합니다 (`gpt-4o` 기용).

---

## 7-3. Gem 팩토리 동적 바인딩 및 격리 메커니즘

맞춤형 비서인 Gem 팩토리는 사용자가 업로드한 개별 연구 문서와 맞춤 지침을 런타임에 동적으로 해석하여 동작하는 RAG 파이프라인 격리 아키텍처를 지원합니다.

![LangGraph Engine Architecture](system_architecture_tier2.png)

### 1) 클로저(Closure) 기반 동적 도구 주입 기술
*   **런타임 바인딩**: 개별 젬(Gem)은 런타임 가동 전까지 어떠한 파일 소스도 고정되어 있지 않습니다. 세션이 시작되면 백엔드는 **클로저(Closure)** 함수 기법을 사용하여 해당 `gem_id`를 내부 메모리 스코프에 캡처한 커스텀 RAG 툴을 즉석에서 동적 개설 및 바인딩합니다.
*   **동적 툴 생성 코드 예시**:
    ```python
    def create_gem_search_tool(gem_id: str):
        async def gem_search_tool(query: str) -> str:
            # 런타임에 바인딩된 gem_{gem_id}_files 컬렉션에서만 강제 탐색
            return await common_rag.similarity_search_isolated(
                collection_name=f"gem_{gem_id}_files", 
                query=query
            )
        return gem_search_tool
    ```

### 2) 물리적 데이터 격리 및 소멸 (Wipe-out)
*   **보안 격리**: 각 파일 데이터는 pgvector 내의 격리된 `gem_{gem_id}_files` 테이블 컬렉션 공간에만 독립 적재되어, 타 젬 대화방이나 외부 사용자에 의한 컨텍스트 누출이 완벽히 차단됩니다.
*   **데이터 파쇄**: 사용자가 젬을 스토어에서 영구 소멸시키면, 관계형 메타 소거와 동시에 `DROP COLLECTION` 쿼리가 작동하여 데이터베이스 상의 벡터 임베딩 조각들을 흔적 없이 영구 완전 삭제(Wipe-out)합니다.
