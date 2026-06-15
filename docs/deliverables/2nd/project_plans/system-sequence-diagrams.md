# 📊 시스템 종합 시퀀스 다이어그램 설계서 (System Sequence Diagrams)

본 문서는 **'논문 AI 에이전트 채팅 플랫폼 (Paper Agent Chat Platform)'**의 핵심 서비스 아키텍처와 비즈니스 시나리오를 구현 레벨에서 가시화하기 위한 종합 시퀀스 다이어그램 명세서입니다. 

플랫폼의 4대 주요 비즈니스 흐름에 맞춰 시스템 구성 요소(클라이언트, 백엔드 API, GPU 임베딩 가속 서버, 데이터베이스, 외부 AI 모델) 간의 상호 작용 및 데이터 통신 규격을 정의합니다.

---

## 🏛️ 1. 오프라인 로컬 파일 기반 배치 임베딩 및 DB 적재 파이프라인
*ArXiv 대용량 데이터셋에서 도메인별 5,000건의 경량화 후보군을 추출해 로컬 GPU(MPS/CUDA)로 임베딩을 변환한 후 로컬 PostgreSQL pgvector에 고속 벌크 적재하는 흐름입니다.*

```mermaid
sequenceDiagram
    autonumber
    actor Dev as 개발자 (Developer)
    participant script as scripts/local_batch_embed.py
    participant data as arxiv-metadata-oai-snapshot.json
    participant PyTorch as sentence-transformers (GPU/MPS/CUDA)
    participant backup as local_embeddings_output.jsonl
    participant db_script as scripts/bulk_load_to_db.py
    participant db as PostgreSQL (pgvector)

    %% [Step 1: Embedding Generation & File Backup]
    Note over Dev, backup: [1단계: GPU 배치 연산 및 임시 파일 백업]
    Dev->>script: 1. 배치 스크립트 실행 (python local_batch_embed.py)
    activate script
    script->>backup: 2. 기존 결과 파일 존재 여부 확인
    alt 기존 결과 파일 존재 시 (Resume 처리)
        backup-->>script: 이미 처리 완료된 arxiv_id 목록 반환
    end
    script->>data: 3. 데이터셋 스트리밍 오픈
    loop Line-by-Line (Memory Efficient)
        data-->>script: ArXiv 단일 논문 JSON 데이터
        script->>script: 4. 중복 ID 체크 및 타겟 카테고리 필터링 (예: cs.NE)
        alt 필터 통과 및 미처리 논문인 경우
            script->>script: 5. 64개 단위로 abstract 텍스트 배치 패킹
        end
        critical 배치 용량 도달 시 (Batch Size = 64)
            script->>PyTorch: 6. 일괄 임베딩 인코딩 요청 (batch_size=64)
            activate PyTorch
            PyTorch->>PyTorch: 7. GPU (MPS/CUDA) 병렬 텐서 포워드 패스 연산
            PyTorch-->>script: 3072차원 (2560차원 + 512 제로 패딩) 벡터 리스트 반환
            deactivate PyTorch
            loop 레코드 순차 순회
                script->>backup: 8. {"arxiv_id", "embedding"} Append 기록
            end
        end
    end
    script-->>Dev: 9. 로컬 임베딩 파일 저장 완료 및 종료 보고
    deactivate script

    %% [Step 2: Database Bulk Loading]
    Note over Dev, db: [2단계: 임베딩 결과 파일의 DB 벌크 적재]
    Dev->>db_script: 10. 벌크 적재 스크립트 실행 (python bulk_load_to_db.py)
    activate db_script
    db_script->>backup: 11. 임베딩 결과 파일 스트리밍 오픈
    db_script->>db: 12. pgvector 확장 활성화 및 cs_embeddings 테이블 생성 (vector(3072))
    loop Line-by-Line
        backup-->>db_script: 단일 임베딩 레코드 (arxiv_id, embedding)
        db_script->>db_script: 13. 5,000개 단위로 레코드 일괄 튜플 패킹
        critical 벌크 임계점 도달 시 (Bulk Size = 5000)
            db_script->>db: 14. Bulk Copy / execute_values() 호출
            activate db
            db->>db: 15. cs_embeddings 테이블에 5,000건 일괄 벌크 삽입
            db-->>db_script: 16. 삽입 성공 응답
            deactivate db
            db_script->>db: 17. 트랜잭션 Commit 완료
        end
    end
    db_script-->>Dev: 18. 전체 데이터베이스 적재 성공 및 완료 보고
    deactivate db_script
```

---

## ⚡ 2. 실시간 하이브리드 RAG 에이전트 검색 및 답변 생성 (SSE 스트리밍)
*사용자의 학술 질문에 대해 Redis 캐시 진단 후, M4 GPU 임베딩 및 pgvector HNSW 고속 유사도 검색을 거쳐 LLM의 스트리밍 답변과 인용 서지를 실시간 반환하는 흐름입니다.*

```mermaid
sequenceDiagram
    autonumber
    actor User as 사용자 (Web Browser)
    participant UI as Next.js FE (Client Component)
    participant API as FastAPI BE (Server API)
    participant Cache as Redis (Cache Store)
    participant M4 as M4 임베딩 서버 (:8001)
    participant DB as PostgreSQL (pgvector)
    participant LLM as External LLM API

    User->>UI: 1. 질문 입력 및 대화 전송 ("Explain multi-agent networks...")
    activate UI
    UI->>API: 2. POST /chat/threads/{id}/messages (SSE Connection 수립)
    activate API
    
    %% [Cache Check]
    API->>Cache: 3. 동일 질문에 대한 캐시 히트 체크
    activate Cache
    alt 캐시 히트 (Cache Hit)
        Cache-->>API: 기존 RAG 컨텍스트 및 생성 답변 반환
        deactivate Cache
        API-->>UI: (즉시 점프) 14. 캐싱된 요약 및 인용 서지 데이터 반환
    else 캐시 미스 (Cache Miss)
        %% [Embedding Extraction]
        API->>M4: 4. 쿼리 임베딩 요청 POST /v1/embeddings (qwen3-embedding)
        activate M4
        M4->>M4: 5. 로컬 GPU(MPS) 직접 추론 및 3072차원 슬라이싱/패딩
        M4-->>API: 6. 3072차원 쿼리 벡터 반환
        deactivate M4

        %% [pgvector HNSW Vector Search]
        API->>DB: 7. Cosine Similarity 유사도 검색 DML 실행
        activate DB
        DB->>DB: 8. HNSW Index 스캔 및 코사인 거리 연산 (vector_cosine_ops)
        DB-->>API: 9. 유사도 점수 기준 최상위 Top-K 논문 초록 데이터 반환
        deactivate DB

        %% [LLM Inference & SSE Streaming]
        API->>API: 10. 획득된 초록 컨텍스트와 질문을 결합하여 RAG 프롬프트 구성
        API->>LLM: 11. OpenAI/Anthropic SDK Streaming 호출 (stream=True)
        activate LLM
        loop 토큰 단위 순차 수신 (Chunk-by-Chunk)
            LLM-->>API: 12. 생성 토큰 데이터 덩어리 (Token Chunks)
            API-->>UI: 13. Server-Sent Events (data: {token, sources}) 푸시
            UI->>UI: 14. 실시간 마크다운 파싱 및 UI 타이핑 효과 업데이트
        end
        LLM-->>API: 15. 스트리밍 종료 신호 (Stop Signal)
        deactivate LLM
        
        API->>Cache: 16. 질문-답변-인용 매핑 정보 Redis 캐시 적재
        API-->>UI: 17. 최종 SSE 스트림 종료 (event: close)
    end
    deactivate API
    UI-->>User: 18. 전체 인용 링크 및 AI 요약 답변 렌더링 완료
    deactivate UI
```

---

## 🔒 3. 보안 연구 샌드박스 가상 세션 수명 주기 및 파쇄
*사용자의 보안 민감 사설 논문 분석을 위한 임시 격리 샌드박스를 개설하고, 30분 초과 만료 시 DB의 외래키 ON DELETE CASCADE와 연계하여 완전 파쇄하는 보안 흐름입니다.*

```mermaid
sequenceDiagram
    autonumber
    actor User as 연구자 (Researcher)
    participant UI as Next.js FE
    participant API as FastAPI BE
    participant Storage as Secure Local Disk (PDF 저장소)
    participant M4 as M4 임베딩 서버 (:8001)
    participant DB as PostgreSQL (pgvector)
    participant Scheduler as 정기 Purge Scheduler (Cron)

    %% [Sandbox Creation & Embedding]
    Note over User, DB: [1단계: 임시 샌드박스 개설 및 로컬 데이터 적재]
    User->>UI: 1. 보안 분석용 개인 논문 PDF 드래그 업로드
    activate UI
    UI->>API: 2. POST /sandbox/sessions/upload (Multipart Form)
    activate API
    
    API->>DB: 3. 임시 sandbox_session 생성 (created_at, expires_at = +30분)
    activate DB
    DB-->>API: 4. session_id (UUID) 반환
    deactivate DB
    
    API->>Storage: 5. PDF 파일 지정 격리 경로에 저장 (물리 저장소)
    API->>API: 6. PDF 텍스트 추출 및 500자/중첩 50자 청크 분할
    
    loop 청크 단위 순회
        API->>M4: 7. 청크 텍스트 임베딩 요청 POST /v1/embeddings
        M4-->>API: 8. 3072차원 조밀 벡터 데이터 반환
    end
    
    API->>DB: 9. sandbox_file 및 sandbox_embeddings 임시 테이블에 청크/벡터 저장
    activate DB
    DB-->>API: 10. DB 적재 성공 응답
    deactivate DB
    
    API-->>UI: 11. 업로드 및 샌드박스 가상 세션 활성화 완료 응답
    deactivate API
    UI-->>User: 12. 샌드박스 전용 대화창 UI 렌더링 및 질문 입력 차창 활성화
    deactivate UI

    %% [Secure RAG Chatting]
    Note over User, DB: [2단계: 임시 샌드박스 RAG 채팅 질의응답 (외부 유출 방지)]
    User->>UI: 13. 파일에 대한 보안 질문 전송
    activate UI
    UI->>API: 14. POST /sandbox/sessions/{id}/chat (RAG 검색 및 LLM 연동)
    activate API
    API->>DB: 15. sandbox_embeddings 테이블 내에서 session_id 한정 유사도 검색
    DB-->>API: 16. 임시 청크 반환 ➔ LLM 호출 ➔ 응답 반환
    API-->>UI: 17. 답변 출력
    deactivate API
    deactivate UI

    %% [Session Expired & Complete Purge]
    Note over Scheduler, DB: [3단계: 30분 도래 시 로컬 메모리/DB 완전 파쇄]
    loop 1분 주기로 정기 트리거 체크
        Scheduler->>API: 18. 만료 스케줄러 작동 트리거 실행
        activate API
        API->>DB: 19. 만료 쿼리 실행 (DELETE FROM sandbox_session WHERE expires_at <= NOW())
        activate DB
        DB->>DB: 20. 만료된 sandbox_session 삭제 연산 수행
        
        Note over DB: ON DELETE CASCADE 트리거 작동
        DB->>DB: 21. 연결된 sandbox_file 및 sandbox_embeddings 자동 연쇄 삭제 (파쇄)
        
        DB-->>API: 22. 삭제된 파일 목록 (UUID, file_path) 반환
        deactivate DB
        
        loop 삭제된 파일 목록 순회
            API->>Storage: 23. 파일 파쇄 호출 (shred/os.remove 물리 저장소 삭제)
        end
        API-->>Scheduler: 24. 샌드박스 완전 파쇄 완료 보고
        deactivate API
    end
```

---

## 📬 4. 가설 검증 및 자동 논문 수집 정기 구독 알림 시스템
*연구 가설을 구독하면 백그라운드 스케줄러가 매일 주기적으로 신규 논문을 탐색하고, LLM을 통해 지지(PRO) 및 반박(CONTRA) 포지션을 판별한 뒤 이메일 알림을 푸시하는 흐름입니다.*

```mermaid
sequenceDiagram
    autonumber
    actor User as 연구자 (Researcher)
    participant UI as Next.js FE
    participant API as FastAPI BE
    participant DB as PostgreSQL (Schema)
    participant Scheduler as 정기 스케줄러 (Cron)
    participant LLM as External LLM API (GPT/Claude)
    participant SMTP as 이메일 발송 모듈 (SMTP Server)

    %% [Subscription Registration]
    Note over User, DB: [1단계: 가설 구독 신청 및 등록]
    User->>UI: 1. 검증 가설 입력 및 알림 메일 설정 ("mRNA vaccines cause myocarditis")
    activate UI
    UI->>API: 2. POST /subscriptions (가설 내용, 이메일 주소)
    activate API
    API->>DB: 3. hypothesis_subscription 테이블에 구독 레코드 삽입
    DB-->>API: 4. 등록 성공
    API-->>UI: 5. 구독 신청 성공 메시지 및 가설 감시 상태 렌더링
    deactivate API
    deactivate UI

    %% [Batch Cron Task Execution]
    Note over Scheduler, DB: [2단계: 백그라운드 크론을 통한 신규 논문 분석]
    Scheduler->>API: 6. 가설 정기 감시 정밀 분석 태스크 가동 (매일 자정)
    activate API
    API->>DB: 7. 활성화된 가설 구독 목록 조회 (SELECT * FROM hypothesis_subscription)
    DB-->>API: 8. 전체 가설 구독 리스트 반환
    
    loop 개별 가설 순회
        API->>DB: 9. pgvector 기반 최신 적재 논문 중 의미론적 관련 연구 검색 (Cosine Distance)
        DB-->>API: 10. 관련성이 높은 신규 논문 리스트 (doc_id, title, abstract) 반환
        
        loop 신규 검색 논문 순회
            API->>LLM: 11. 논문 분석 프롬프트 전송 (가설 검증용 PRO/CONTRA 판별 의뢰)
            activate LLM
            LLM->>LLM: 12. 가설과 논문 초록 내용의 논리적 의미론 매칭 판별
            LLM-->>API: 13. 판별 결과 반환 (type: PRO_EVIDENCE / CONTRA_EVIDENCE, 요약문: summary)
            deactivate LLM
            
            API->>DB: 14. inbox_notification 테이블에 알림 레코드 삽입 (is_read=False)
            
            %% [Realtime Email Notification]
            API->>SMTP: 15. 이메일 템플릿 빌드 및 전송 요청 (SMTP TLS)
            activate SMTP
            SMTP->>User: 16. "구독하신 가설에 대한 신규 지지/반박 논문 분석 보고서 도착" 메일 발송
            SMTP-->>API: 17. 이메일 발송 완료
            deactivate SMTP
        end
    end
    API-->>Scheduler: 18. 가설 정기 구독 분석 및 알림 배포 태스크 종료
    deactivate API
```
