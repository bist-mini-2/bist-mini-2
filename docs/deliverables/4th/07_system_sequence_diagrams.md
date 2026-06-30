# [4차 산출물] 07. 시스템 종합 시퀀스 다이어그램 설계서 (System Sequence Diagrams)

본 문서는 `bist-mini-2` 플랫폼의 최종 완성 상태를 반영하여, 각 티어 및 컴포넌트 간의 시간 흐름에 따른 메시지 교환 및 기능 동작 흐름을 도식화한 **시스템 종합 시퀀스 다이어그램 설계서**입니다. 보안 관련 시퀀스는 향후 개발 목표로 별도 분류되어 있습니다.

---

## 1. 📂 오프라인 로컬 파일 기반 배치 임베딩 및 DB 적재 파이프라인
*ArXiv 전체 스냅샷 및 개별 raw JSON 파일에서 도메인별 미적재 데이터를 추출하여 `langchain_postgres` PGVector 벌크 인덱싱을 진행하는 흐름입니다.*

```mermaid
sequenceDiagram
    autonumber
    actor Dev as 개발자 (Developer)
    participant script as scripts/datasets/append_full_domain_embeddings.py
    participant raw as cs_raw.json / astronomy_raw.json
    participant DB as PostgreSQL (pgvector)
    participant LLM as OpenAI (text-embedding-3-large)

    Dev->>script: 1. 추가 적재 배치 스크립트 실행 (python append_full_domain_embeddings.py)
    activate script
    script->>DB: 2. langchain_pg_collection 및 langchain_pg_embedding 내 이미 적재된 arxiv_id 스캔
    DB-->>script: 3. 기존 arxiv_id 해시 셋 반환
    script->>raw: 4. 로컬 raw JSON 파일 읽기 및 중복 제외 필터링
    raw-->>script: 5. 미적재 신규 논문 리스트
    
    loop BATCH_SIZE (100개 단위)
        script->>LLM: 6. 100개 논문 제목 + 초록 통합 임베딩 요청 (text-embedding-3-large)
        activate LLM
        LLM-->>script: 7. 3072차원 벡터 리스트 반환
        deactivate LLM
        
        script->>DB: 8. langchain_pg_embedding 테이블에 벌크 삽입 (collection_id 매핑)
        activate DB
        DB-->>script: 9. 트랜잭션 Commit 및 삽입 완료
        deactivate DB
    end
    
    script-->>Dev: 10. 도메인별 추가 적재 보고 및 종료
    deactivate script
```

---

## 2. ⚡ 실시간 병렬 융합 RAG 에이전트 스트리밍 (SSE 스트리밍)
*사용자의 학술 질문에 대해 최적화 쿼리를 생성하고, pgvector HNSW RAG와 Tavily 실시간 검색 노드를 무조건 병렬로 동시 수행하여, 최종 합성 노드에서 교차 융합된 답변을 SSE로 스트리밍하는 흐름입니다.*

```mermaid
sequenceDiagram
    autonumber
    actor User as 사용자 (Web Browser)
    participant UI as Next.js FE (Client Component)
    participant BE as FastAPI BE (chat/controller.py)
    participant SPV as ChatMultiAgentSupervisor
    participant PGV as pgvector Vector Store (cs/bio/astronomy)
    participant WEB as Web Search API (Tavily)
    participant SYN as Synthesis Node (gpt-4o)
    participant DB as PostgreSQL (chat_source / suggestions)

    User->>UI: 1. 질문 입력 및 대화 전송 ("Explain GAN weight evolution with recent news")
    activate UI
    UI->>BE: 2. POST /chat/sessions/{session_id}/messages/stream
    activate BE
    
    BE->>SPV: 3. run_stream(message, session_id)
    activate SPV
    SPV->>SPV: 4. AnalysisNode에서 쿼리 최적화 (paper_query & web_query 추출)
    
    Note over SPV, WEB: 두 노드를 무조건 병렬(Parallel) 비동기 호출
    par 학술 RAG 검색 실행
        SPV->>PGV: 5-1. Cosine Similarity 유사도 검색 (cs_embeddings 컬렉션)
        PGV-->>SPV: 6-1. 유사도 Top-K 논문 초록 컨텍스트 반환
    and 실시간 구글링 웹 검색 실행
        SPV->>WEB: 5-2. Tavily Web Search API 호출
        WEB-->>SPV: 6-2. 실시간 웹 정보 컨텍스트 반환
    end
    
    SPV->>SYN: 7. 합성 엔진 호출 및 RAG/Web 데이터 융합 프롬프트 인풋
    activate SYN
    
    loop 토큰 단위 순차 수신 (Chunk-by-Chunk)
        SYN-->>SPV: 8. 생성 토큰 데이터 (Token Chunks)
        SPV-->>BE: 9. 토큰 전달
        BE-->>UI: 10. SSE JSON Line 스트림 푸시 (StreamingResponse)
        UI->>UI: 11. 실시간 마크다운 파싱 및 UI 타이핑 효과 업데이트
    end
    SYN-->>SPV: 12. 스트리밍 종료 신호
    deactivate SYN
    deactivate SPV

    par 사후 메타데이터 백엔드 비동기 저장
        BE->>DB: 13-1. 참조된 논문 메타데이터를 chat_source 테이블에 영구 적재
        BE->>BE: 13-2. Q&A 꼬리 질문 추천 3선 자동 빌드
        BE->>DB: 13-3. 꼬리 질문을 chat_suggestion 테이블에 영구 적재
        BE->>DB: 13-4. DB Commit 실행
    end
    
    BE-->>UI: 14. 최종 스트림 채널 종료
    deactivate BE
    
    UI->>BE: 15. 스트리밍 완료 후 출처 및 추천 질문 재조회 (GET /chat/sessions/{session_id}/messages)
    activate BE
    BE-->>UI: 16. 출처/추천 정보가 index 결합된 대화 내역 전체 반환
    deactivate BE
    UI-->>User: 17. 전체 인용 카드 및 AI 요약 답변 최종 렌더링 완료
    deactivate UI
```

---

## 3. 🔒 보안 연구 샌드박스 가상 세션 수명 주기 및 파쇄 - [향후 구현 설계 (미구현)]
*사용자의 보안 민감 사설 논문 분석을 위한 임시 격리 샌드박스를 개설하고, 30분 초과 만료 시 DB의 외래키 ON DELETE CASCADE와 연계하여 완전 파쇄하는 보안 흐름입니다.*

```mermaid
sequenceDiagram
    autonumber
    actor User as 연구자 (Researcher)
    participant UI as Next.js FE
    participant API as FastAPI BE
    participant Storage as Secure Local Disk (PDF 저장소)
    participant DB as PostgreSQL (pgvector)
    participant Scheduler as 정기 Purge Scheduler (Cron)

    %% [Sandbox Creation & Embedding]
    Note over User, DB: [1단계: 임시 샌드박스 개설 및 로컬 데이터 적재]
    User->>UI: 1. 보안 분석용 개인 논문 PDF 업로드
    activate UI
    UI->>API: 2. POST /defense-arena/upload-isolated (Multipart Form)
    activate API
    
    API->>DB: 3. 임시 defense_arena_session 생성
    activate DB
    DB-->>API: 4. session_id (UUID) 반환
    deactivate DB
    
    API->>Storage: 5. PDF 파일 지정 격리 경로에 저장 (물리 저장소)
    API->>API: 6. PDF 텍스트 추출 및 500자/중첩 50자 청크 분할
    
    loop 청크 단위 순회
        API->>DB: 7. 임시 defense_arena_chunk 테이블에 청크/벡터 적재
    end
    
    API-->>UI: 8. 업로드 및 샌드박스 가상 세션 활성화 완료 응답
    deactivate API
    UI-->>User: 9. 샌드박스 전용 대화창 UI 렌더링 및 질문 입력창 활성화
    deactivate UI

    %% [Session Expired & Complete Purge]
    Note over Scheduler, DB: [2단계: 30분 도래 시 로컬 메모리/DB 완전 파쇄]
    loop 1분 주기로 정기 트리거 체크
        Scheduler->>API: 10. 만료 스케줄러 작동 트리거 실행
        activate API
        API->>DB: 11. 만료 쿼리 실행 (DELETE FROM defense_arena_session WHERE created_at <= NOW() - INTERVAL '30 minutes')
        activate DB
        DB->>DB: 12. 만료된 defense_arena_session 삭제 연산 수행
        
        Note over DB: ON DELETE CASCADE 트리거 작동
        DB->>DB: 13. 연결된 defense_arena_chunk 및 defense_history 자동 연쇄 삭제 (파쇄)
        
        DB-->>API: 14. 삭제된 파일 목록 (UUID, file_path) 반환
        deactivate DB
        
        loop 삭제된 파일 목록 순회
            API->>Storage: 15. 파일 파쇄 호출 (shred/os.remove 물리 저장소 삭제)
        end
        API-->>Scheduler: 16. 샌드박스 완전 파쇄 완료 보고
        deactivate API
    end
```

---

## 📬 4. 대규모 비동기 문헌 분석 (Research Gap Analyzer)
*대규모 선행 연구에 대한 배치 분석 요청을 예약하면 백엔드 BackgroundTasks가 비동기로 가동되어 한계점을 일괄 취합하고 알림 인박스에 저장하는 흐름입니다.*

```mermaid
sequenceDiagram
    autonumber
    actor User as 연구자 (Researcher)
    participant UI as Next.js FE
    participant API as FastAPI BE (research_gap/endpoints.py)
    participant Queue as BackgroundTasks (Async Worker)
    participant PGV as pgvector Vector Store (langchain_pg_embedding)
    participant LLM as External LLM API (Structured Output)
    participant DB as PostgreSQL (research_gap_task)

    User->>UI: 1. 분석하고 싶은 연구 영역 및 질의 전송
    activate UI
    UI->>API: 2. POST /research-gap/analyze
    activate API
    
    API->>DB: 3. research_gap_task 테이블에 작업 생성 (status: PENDING)
    DB-->>API: 4. task_id 반환
    
    API->>Queue: 5. BackgroundTasks에 비동기 분석 작업 큐 예약 등록
    API-->>UI: 6. 작업 예약 등록 응답 (task_id 즉시 반환)
    deactivate API
    
    UI->>UI: 7. 클라이언트 화면은 블로킹 없이 다른 대화 기능 사용 가능 (진행률 폴링 시작)
    deactivate UI

    %% [Async Processing]
    activate Queue
    Queue->>DB: 8. 작업 상태 RUNNING으로 변경 (progress: 10)
    
    Queue->>PGV: 9. 해당 주제 관련 선행 문헌 검색 (top_k=25)
    PGV-->>Queue: 10. 선행 연구 리스트 반환
    Note over Queue: arXiv ID 중복 필터링 및 유사도 상위 4개 고유 본문 선출
    
    Queue->>DB: 11. 진행 상태 업데이트 (progress: 40)
    
    loop 각 4개 논문
        Queue->>LLM: 12. 논문 초록에서 solved_problems, limitations 추출 의뢰 (Structured Output)
        LLM-->>Queue: 13. 구조화 정보 및 verbatim 영문 인용구(source_quote) 반환
    end
    
    Queue->>DB: 14. 진행률 및 중간 매트릭스 데이터 갱신 (progress: 80)
    
    Queue->>LLM: 15. 매트릭스 전체 데이터 기반 Research Gap 추론 및 추천 연구 주제 합성 제안
    LLM-->>Queue: 16. 최종 합성 리포트(gap_analysis, recommended_topics) 반환
    
    Queue->>DB: 17. 최종 분석 결과 저장 및 상태 변경 (status: COMPLETED, progress: 100)
    
    Note over Queue, DB: 알림 연동 기능 자동 트리거
    Queue->>DB: 18. notification 테이블에 'Research Gap 작업 완료' 카드 적재 및 실시간 SSE 스트림 브로드캐스트
    deactivate Queue
```
