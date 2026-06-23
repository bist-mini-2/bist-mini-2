# Bist Mini 2 - Backend Presentation Script (발표 대본)

본 문서는 `Bist Mini 2` 백엔드 프로젝트의 전체 소스 코드 구조와 핵심 클래스/메소드의 역할을 학회나 프로젝트 심사 등에서 구두 발표할 수 있도록 구성한 **발표 대본(Presentation Script)**입니다. 각 파일 내 메소드 단위의 구현 세부사항과 동작 원리를 구어체로 설명합니다.

---

## 🖥️ Slide 1: 오프닝 및 아키텍처 개요
**[발표자]**
> 안녕하세요. `Bist Mini 2` 백엔드 파트 발표를 맡은 [발표자 이름]입니다.
> 저희 백엔드 시스템은 **FastAPI** 프레임워크를 기반으로 하며, 결합도를 낮추고 유지보수성을 극대화하기 위해 **Controller - Service - DAO - Entity**로 관심사를 명확히 격리한 **Layered Architecture**를 채택했습니다.
> 
> 프로젝트 루트의 `main.py`를 중심으로, 공통 기능을 다루는 `api/common`, 데이터베이스 설정을 위한 `api/database/config`, 그리고 실질적인 도메인 비즈니스 로직들이 격리되어 있는 `api/v1`으로 구성되어 있습니다.
> 이제부터 백엔드의 코어 클래스 및 메소드들을 중심 파일 단위로 하나씩 소개해 드리겠습니다.

---

## 🖥️ Slide 2: 애플리케이션 진입점 및 생명주기 관리
#### 📄 대상 코드: [main.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/main.py)

**[발표자]**
> 애플리케이션의 시작점인 [main.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/main.py)부터 말씀드리겠습니다. 
> 
> 먼저, 정적 자원을 서빙할 때 브라우저가 임의로 이전 자원을 캐싱하는 문제를 원천 차단하기 위해 **`NoCacheStaticFiles`** 클래스를 정의했습니다. 이 클래스의 **`file_response`** 메소드는 정적 파일 반환 시 HTTP 헤더에 `Cache-Control: no-cache`를 강제 주입해 매번 최신 웹 자원이 클라이언트에 로드되도록 제어합니다.
> 
> 웹앱의 생명주기를 관장하는 비동기 컨텍스트 매니저 **`lifespan`** 함수는 중요한 역할을 수행합니다.
> 첫째, 내부 함수인 **`custom_signal_handler`**를 통해 Uvicorn 핫리로드 시 실시간 SSE 알림이 물려있어 서버가 꺼지지 않고 멈추는(hang) 교착 상태를 완벽히 해결합니다. 
> 둘째, PostgreSQL 연동 시 RAG 처리에 필수적인 pgvector 익스텐션을 활성화하고 DB 스키마 테이블들을 자동으로 동기화합니다.
> 셋째, 내부 비동기 코루틴인 **`cleanup_daemon`**을 기동합니다. 이 데몬은 1분 주기 백그라운드 루프를 돌며, 데이터베이스 세션을 활성화해 30분 동안 마우스 움직임이나 질의 등 활성 기록이 끊긴 격리 구역 보안 세션을 영구 완전 소거(`wipe_out_expired_sessions`)하도록 지시합니다.
> 
> 마지막으로 **`add_cache_control_header`** HTTP 미들웨어는 v1 엔드포인트를 타겟으로 모든 동적 API 응답 헤더에 캐시 방지 필드를 주입하여 브라우저의 오염된 캐시 반환을 사전에 예방하고 있습니다.

---

## 🖥️ Slide 3: 자격 증명 및 인증 공통 모듈
#### 📄 대상 코드: [api/common/auth.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/auth.py)

**[발표자]**
> 다음은 사용자의 안전한 세션 수립을 보장하는 인증 공통 모듈, [auth.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/auth.py)입니다.
> 
> 첫째, **`create_token`** 함수는 로그인에 성공한 사용자 ID인 `mid`와 권한 역할인 `mrole`을 페이로드로 담아, 단방향 서명 비밀키로 암호화한 JWT 스트링을 발급합니다.
> 
> 둘째, **`get_payload`** 함수는 전달된 JWT의 무결성과 서명을 검증하고 디코딩을 수행합니다. 토큰이 오염되었거나 만료되었을 경우, `ExpiredSignatureError` 등 구체적인 상태를 구별해 `401 Unauthorized` 예외를 즉각 유발합니다.
> 
> 셋째, FastAPI의 핵심 메커니즘인 Depends 종속성을 활용하기 위해 **`verify_access_token`** 비동기 함수를 선언했습니다. 이 함수는 들어온 HTTP Request 객체의 헤더 또는 쿼리 스트링 파라미터에서 토큰을 자동 인출하고 `get_payload` 검증을 연계 처리하여 인증이 확인된 사용자의 `UserPayload` 딕셔너리를 반환합니다.
> 
> 마지막으로, 어드민 전용 등 권한 격리가 필요한 경우를 위해 **`require_roles`** 의존성 빌더 함수를 둡니다. 이 함수는 허용된 역할 리스트를 인자로 받아, 현재 요청을 보낸 사용자의 `mrole`이 리스트에 포함되어 있지 않을 시 `403 Forbidden` 예외를 가로채 던지는 중첩 검사기 함수(`check_roles`)를 리턴합니다.
> 개발자는 `LoginCheckDep` 및 `AdminCheckDep` 타입 에일리어스 어노테이션을 컨트롤러 매개변수에 달아둠으로써 가독성 높게 보안 가드를 적용할 수 있습니다.

---

## 🖥️ Slide 4: 공통 RAG 파이프라인 및 LangGraph 연동 툴
#### 📄 대상 코드: [api/common/rag_pipeline.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/rag_pipeline.py)

**[발표자]**
> 저희 서비스의 심장부인 공통 RAG 파이프라인과 LangGraph 에이전트 연동용 툴 모듈, [rag_pipeline.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/common/rag_pipeline.py)입니다.
> 
> RAG 처리를 전담하는 **`CommonRagPipeline`** 클래스는 pgvector 기반의 코사인 유사도 연산을 단일화된 구조로 대행합니다.
> *   **`get_embeddings`** 메소드는 지연 로딩 방식을 적용해 실제 임베딩 계산이 요구되는 최초 시점에 `text-embedding-3-large` (3072차원) 모델 인스턴스를 초기화하여 자원을 효율적으로 공유합니다.
> *   **`similarity_search`** 비동기 메소드는 타겟 도메인 컬렉션(`bio`, `cs`, `astronomy`)에 맞춰 pgvector 비동기 쿼리를 수행하고, 계산된 거리(distance) 점수를 사람이 인지하기 쉬운 코사인 유사도 스코어(`1.0 - distance`)로 포매팅하여 상위 k개의 매칭 문서 청크 정보를 수집해 반환합니다.
> 
> 이 파이프라인 인스턴스는 싱글톤으로 메모리에 상주하며, LangGraph가 실시간 질의응답 시 호출할 `@tool` 기반 함수 세트인 **`search_bio_papers`**, **`search_cs_papers`**, **`search_astronomy_papers`**에 의해 직접 공유 호출됩니다. 
> 이 툴 함수들은 에이전트의 생각을 돕는 Context를 수집하며, 최종적으로 LangGraph 상태 그래프에 검색 출처(`sources`)를 주입하고 흐름을 제어하기 위해 `Command` 제어 객체를 리턴합니다.

---

## 🖥️ Slide 5: 비동기 데이터베이스 커넥션 풀 관리
#### 📄 대상 코드: [api/database/config/dbsession.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/database/config/dbsession.py)

**[발표자]**
> 다음으로 안정적인 비동기 트랜잭션 처리를 보장하는 데이터베이스 세션 관리 모듈, [dbsession.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/database/config/dbsession.py)입니다.
> 
> 저희 백엔드는 매 HTTP API 요청 단위마다 트랜잭션의 시작과 소멸이 깔끔하게 정리되도록 비동기 제너레이터 함수인 **`get_orm_session`**을 선언했습니다.
> 이 함수는 세션 메이커를 통해 `AsyncSession` 인스턴스를 하나 개방한 뒤 컨트롤러 비즈니스 단으로 양도(yield)합니다. 
> 요청 처리가 성공적으로 종결되어 제너레이터 루프가 회수되면 `orm_session.commit()`이 실행되어 DB 반영이 완료됩니다. 
> 만약 비즈니스 수행 도중 예상치 못한 오류가 터지면 즉각 `except` 절로 제어가 넘어가 `orm_session.rollback()`이 자동 실행되며, `finally` 구문을 통해 DB 커넥션 풀 자원 누수 방지를 위해 무조건 `orm_session.close()`를 닫아줍니다. 
> 이를 통해 개발자의 트랜잭션 롤백 누락 실수를 원천적으로 차단합니다.

---

## 🖥️ Slide 6: 사용자 가입 및 인증 비즈니스 도메인
#### 📄 대상 코드: [member](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/member/) / [auth](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/auth/)

**[발표자]**
> 이제 비즈니스 도메인 영역으로 넘어가 회원 정보와 인증 처리를 담당하는 `member` 및 `auth` 모듈을 살펴보겠습니다.
> 
> 회원 데이터베이스 처리를 담당하는 **`MemberDao`** 클래스에는 회원 추가를 집행하는 **`insert`**, 수정값을 선별 갱신하는 **`update`**, ID 기준 단건 매칭 조회를 대행하는 **`select_by_mid`** 메소드가 정의되어 있습니다.
> 
> 이 DAO를 조율하는 상위 서비스 레이어인 **`MemberService`** 클래스는 암호 보안 및 중복 검증 비즈니스를 수행합니다.
> *   **`join`** 비동기 메소드는 먼저 회원 아이디 중복을 검사하고, 입력된 평문 비밀번호를 bcrypt 단방향 해싱 솔트 알고리즘으로 안전하게 암호화 값으로 변환하여 DAO에 인서트를 위임합니다.
> *   **`authenticate`** 메소드는 로그인 시 아이디 유무 확인 후 bcrypt 대조 기능인 `checkpw`를 가동해 비밀번호 자격 증명을 가립니다. 일치하지 않을 시 `InvalidPasswordError`를 던집니다.
> *   **`modify`** 메소드는 개인 정보 수정을 대행하되, 패스워드 재설정 시 단방향 해시를 다시 씌우는 암호보안 파이프라인을 만족합니다.
> 
> 최종 관문인 **`endpoints.py`** 컨트롤러에서는 회원 가입 수용 라우터인 **`join`**, 내 정보 가져오기용 **`info`**, 프로필 수정용 **`update`**가 매핑되어 있으며, 이들은 DTO 변환 및 유효성 필터링을 거쳐 성공 응답 래퍼(`SuccessResponse`)에 바인딩되어 사용자에게 최종 반환됩니다.

---

## 🖥️ Slide 7: LangGraph 챗봇 대화 세션 도메인
#### 📄 대상 코드: [api/v1/chat/chat_agent.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/chat_agent.py) / [services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/chat/services.py)

**[발표자]**
> 다음으로 LangGraph 기반 RAG 챗봇 연동 도메인인 `chat` 모듈입니다. RAG 대화는 이전 메시지 이력을 기억하며 답변해야 하므로 복잡한 세션 관리가 요구됩니다.
> 
> 먼저, 핵심 AI 클래스인 **`ChatAgent`**를 조명해 보겠습니다.
> *   **`_initialize`** 비동기 메소드는 멀티스레드 진입 시 교착을 막는 비동기 락(`self._init_lock`)을 기반으로 동작하며, 최초 RAG 가동 시점에 `AsyncPostgresSaver`를 PostgreSQL 커넥션 풀에 물려 **대화 히스토리 영구 체크포인팅 데이터 테이블을 멱등하게 자동 생성**합니다. 그 후 RAG 검색 툴 3종을 LLM 에이전트에 동적 연동하여 인스턴스를 구축합니다.
> *   **`run`** 메소드는 대화 히스토리 테이블에서 이전 대화 흐름을 session_id 기반으로 복원한 뒤 RAG 답변 explanation과 참고 논문 목록인 papers를 추출해 전달합니다.
> *   **`run_stream`** 메소드는 화면상의 타이핑 특수 효과 서빙을 위해 구조화 JSON 포맷을 잠시 해제하고, 토큰 단위의 낱개 문자열 조각을 실시간 흘려주는 비동기 제너레이터입니다.
> *   **`get_latest_sources`** 메소드는 스트리밍 챗이 종료된 시점에 체크포인터 내에 누적 탑재된 RAG 출처들을 중복 제거하여 호출자에게 인계합니다.
> *   **`generate_title`** 메소드는 사용자의 최초 질문을 경량 LLM 모델에 던져 6~20자의 간결한 대화방 요약 제목으로 가공해 주는 헬퍼 함수입니다.
> 
> 이 에이전트 뒤편에서 비즈니스를 수행하는 **`ChatService`** 클래스는 매우 체계적입니다.
> *   **`send_message`** 및 **`send_message_stream`** 메소드는 RAG 대화가 진행되는 즉시 그 답변의 근거가 된 실시간 논문 출처 리스트를 DB 테이블인 `chat_source` 에 메시지 인덱스 번호와 정교하게 엮어 영구 기록합니다.
> *   사용자가 이 방에 다시 진입하면, **`get_messages`** 메소드가 작동하여 영구 보존된 `chat_source` 기록들을 LangGraph 히스토리 메시지 턴에 1:1 매핑 후 병합 가공하여, 이전 대화 내용과 당시 참고한 논문 카드를 한 번에 로드하는 완전한 세션 복원 기능을 수행합니다.

---

## 🖥️ Slide 8: 기밀 보장 보안 격리 모의 디펜스 아레나
#### 📄 대상 코드: [api/v1/defense_arena/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/services.py)

**[발표자]**
> 이번 프로젝트의 핵심 특화 기능 중 하나인 기밀 보장 격리 구역 내 피어리뷰 및 구두 모의 디펜스 아레나 서비스인 [services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/services.py)입니다.
> 기밀 연구 문서 유출을 막는 동시에 고도화된 검증 연산을 수행하기 위해 설계되었습니다.
> 
> *   **`process_pdf_upload`** 메소드는 격리 업로드 처리를 관장합니다.
>     사용자가 PDF 파일을 올리면 즉시 세션 UUID 폴더를 uploads 하위에 신설하고 파일 복사를 단행합니다. 
>     이때 디렉토리 탈출 공격을 원천 봉쇄하는 **OS Path Guard** 검증을 무조건 수행합니다. 
>     이후 `pypdf`를 통한 텍스트 비어있음 검사, `RecursiveCharacterTextSplitter`를 통한 1000자 단위 청킹 분할을 거쳐 `text-embedding-3-large`로 추출한 3072차원 임베딩 벡터 목록을 `DefenseArenaChunkEntity`로 매핑해 DB pgvector 임시 테이블에 일괄 적재합니다.
> 
> *   **`run_peer_review`** 메소드는 격리된 텍스트 중 대표 요약 청크 10개를 합성하여 `ChatOpenAI(temp=0.2)`와 `with_structured_output` 기술로 연결됩니다.
>     학술 비평 전문가인 방법론 에이전트, 신규성 에이전트, 학술문체 에이전트 3인의 가상 협동 토론 과정을 구조화하여 종합 점수 및 심사 요약 보고서(`PeerReviewReport`)로 즉각 출력합니다.
> 
> *   **`verify_hypothesis`** 메소드는 연구 가설 다수결 자아-일관성(Self-Consistency) 검증을 담당합니다.
>     사용자가 입력한 가설 문장을 임베딩 변환해 격리 문서 내 RAG 유사 구절 5개를 도출합니다. 
>     그 후, 온도가 다른 3개의 ChatOpenAI 채널에 독립 시행을 수행하여 찬성(SUPPORT), 반대(REFUTE), 증거부족(INSUFFICIENT_EVIDENCE) 투표를 획득하고 다수결 결론과 합의 신뢰 지수를 통계적으로 산출해 줍니다.
> 
> *   **`process_defense_chat`** 메소드는 턴제(Turn-based) 모의 구두 디펜스 질의응답을 구현합니다.
>     *   **1턴 시작**: 업로드된 문서 내용을 파악하여 학술적 취약점이나 한계점을 매섭게 찌르는 저널 심사위원의 1차 압박 질문을 생산하고 DB에 기록합니다.
>     *   **후속 턴 진행**: 사용자가 이에 대응하는 변명/반론 답변을 보내오면, 논리력과 증거력을 채점하는 LLM 체인(`ScoreDTO` 구조화 형식)을 구동해 100점 만점 평점과 크리틱 피드백을 실시간 기록합니다.
>     *   **최종 3턴 도달**: 누적 문답 역사를 요약해 최종 학술 투고 심사 통과 의견서(`final_report`)를 합성해 주며, 3턴 미만인 경우 이전 소명의 허점을 파고드는 추가 꼬리물기 압박 질문을 도출하여 다음 턴을 준비합니다.
> 
> *   **`wipe_out_expired_sessions`** 메소드는 보안 생명 주기를 수호합니다.
>     30분 이상 활동이 멈춰 만료된 임시 세션이 감지되면 OS Path Guard 대조 필터를 한 번 더 통과시킨 후 로컬 디렉토리를 완전히 날려버립니다(`shutil.rmtree`). 
>     또한 DB 상의 메타 세션을 제거함과 동시에 외래키 **ON DELETE CASCADE** 제약 조건에 의해 pgvector 임베딩 청크 테이블 및 모의 대화 테이블을 데이터베이스상에서 영구 소거(Wipe Out)하는 완벽한 정보 파쇄를 완료합니다.

---

## 🖥️ Slide 9: 사용자 정의 커스텀 RAG 비서 공간
#### 📄 대상 코드: [api/v1/gems/gem_agent.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/gem_agent.py) / [services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/gems/gem_agent.py)

**[발표자]**
> 다음은 사용자가 직접 도메인과 비서 페르소나 지침을 조합하여 개인 맞춤형 AI 연구 조력자를 개설하는 `gems` 도메인입니다.
> 
> 핵심인 **`GemAgent`** 클래스의 동작 원리는 다이내믹 룰 빌더 방식입니다.
> *   **`_build_system_prompt`** 메소드는 사용자가 직접 한글로 타이핑한 비서의 성격 프롬프트 문자열을 기반으로 작동합니다. 하단에 사용자가 체크박스로 선택한 도메인 데이터소스(bio/cs/astronomy)에 대응하는 툴 가이드를 주입합니다. 특히 **"한글 질문이 들어와도 내부 RAG 툴 검색에 넘길 검색 질의 인자 query는 반드시 영어 학술 핵심 용어로 자동 번역 및 치환해서 던질 것"**에 대한 엄격한 프롬프트 지침을 LLM에 추가 합성해 줍니다.
> *   **`_build_agent`** 메소드는 합성된 시스템 프롬프트와 동적으로 선별 추출된 RAG 툴 목록을 엮어 `create_agent`로 **유일무이한 Gem 챗봇 런타임 인스턴스를 즉석에서 다이내믹 빌딩**해 냅니다.
> *   이후 **`run`** 및 **`get_history`** 메소드는 사용자가 부여한 thread_id를 기억하여 DB pgvector Saver 테이블과 엮어 해당 Gem 비서만의 독립적인 이전 대화 이력 유지 및 답변 추출을 위임 처리합니다.
> 
> 상위 **`GemService`** 클래스는 이 dynamic agent 생성을 뒤에서 보조하며, 유저의 입력 사양(이름, RAG 소스, 지침) 중 일부 항목만 전달되어도 Partial Update를 완수하는 **`update_gem`** 비동기 메소드 및 기밀 보장을 위해 비서 파괴 시 이력까지 전부 지워주는 **`delete_gem`** 등을 완벽하게 제공합니다.

---

## 🖥️ Slide 10: SSE 실시간 알림 연동 및 대규모 공백 분석
#### 📄 대상 코드: [api/v1/notification/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/notification/services.py) / [api/v1/research_gap/services.py](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/research_gap/services.py)

**[발표자]**
> 마지막으로, 백그라운드 비동기 작업을 수신 처리하는 SSE 알림 및 대규모 연구 공백 분석 모듈에 대한 연동 설명입니다.
> 
> 먼저 실시간 알림을 담당하는 **`NotificationService`**의 **`stream_notifications`** 비동기 제너레이터를 조명해 보겠습니다.
> 이 함수는 브라우저가 SSE 채널로 연결을 요청하면 인메모리 퍼블리셔(`NotificationBroadcaster`)를 구독하고 큐를 할당받습니다. 
> 1초 타임아웃 주기로 큐의 이벤트를 감시하며, 이벤트가 비어있을 때는 **`TimeoutError`를 이용해 `: keep-alive\n\n` 데이터 조각을 실시간 브라우저로 쏴 줌으로써 Nginx 등 프록시 게이트웨이가 커넥션을 임의 차단하는 현상을 극적으로 극복**합니다. 
> 신규 이벤트 인출 시에는 본인의 소유 ID(`mid`)를 검출 대조해 타인에게 알림이 오염 배달되는 현상을 차단하고 yield 송출을 완수합니다.
> 
> 이 SSE 채널은 대용량 문헌 비교 분석 서비스인 **`ResearchGapService`**와 직접 시너지 효과를 냅니다.
> *   **`start_analysis`** 메소드는 cs 등의 도메인 유효성 체크 후 task_id를 UUID로 신설해 DB에 PENDING 상태로 올립니다. 그 후 FastAPI BackgroundTasks 대기열에 배치 연산 루틴을 밀어 넣은 뒤 ID를 우선 즉시 리턴해 클라이언트의 요청-응답 지연 블로킹을 해제합니다.
> *   백그라운드에서 깨어나는 **`run_batch_analysis`** 비동기 메소드는 아래의 배치 연산을 순차 진행하며 DB 세션을 지속 커밋하고 진척도(10%, 40%, 80%, 100%)를 밀어 올립니다.
>     1. RAG 유사도 검색을 k=25개 대량 질의합니다.
>     2. **고유 문헌 필터링 및 병합**: 분할 파싱된 텍스트 중 `arxiv_id`를 기준으로 중복을 걸러내어, 가장 신뢰도가 우수한 **상위 4개 고유 문헌**만을 최종 분석 대상군으로 안전 축약합니다.
>     3. 각 논문에 대해 `gpt-4o-mini` Structured Output을 엮어 해결 기법(최대 2개), 한계 한계(최대 2개)를 추출하고 **이를 입증하는 원문의 Verbatim 영문 구절(`source_quote`)을 훼손 없이 정확히 긁어옵니다**.
>     4. 종합 매트릭스를 LLM에 재차 피딩하여 전체 문헌군의 공동 한계점(`common_limitations`)과 이를 극복할 **3개의 혁신적 추천 연구 로드맵 방향성(`suggested_directions`)을 도출**한 뒤 완료 업데이트를 실행합니다.
>     5. 완료 즉시 알림 엔티티를 적재하고, 전역 `notification_broadcaster.broadcast`를 트리거하여 대기 중이던 브라우저 SSE 리스너에게 완료 이벤트 푸시를 즉각 송달합니다.
> *   **`translate_matrix`** 메소드는 영문 매트릭스 리포트를 한국어로 합성 번역 캐싱합니다.
>     번역 시 **"Transformer, RAG 등 표준 약어명은 영문으로 보존하거나 한글 병기를 결합"**하고, **"논문 검증 팩트인 verbatim 'source_quote' 인용 필드는 번역을 배제하고 영어 원문 그대로를 무조건 보존"**하는 가이드라인 프롬프트를 주어 `ResearchGapMatrix` DTO로 구조화 합성해 DB 캐시 컬럼(`translated_result`)에 적재 및 서비스합니다.

---

## 🖥️ Slide 11: 마무리 및 질의응답 (Q&A)
**[발표자]**
> 이상으로 `Bist Mini 2` 백엔드 프로젝트의 전체 핵심 코드에 대한 메소드 및 클래스 단위 아키텍처 발표를 마치겠습니다.
> 
> 저희 시스템은 단순한 RAG 챗봇을 넘어, 
> 1. 기밀 유출 방지를 위한 **OS Path Guard 보안 격리 아레나**,
> 2. 3대 비평가 가상 토론을 활용한 **Multi-Agent 피어리뷰**,
> 3. 온도를 가변 설정한 독립 추론과 **Self-Consistency 다수결 가설 판정**,
> 4. 꼬리물기 압박 질문 및 실시간 채점 기반의 **턴제 구두 디펜스**,
> 5. 가시적인 Next.js / FastAPI / DB 스키마 맵핑 및 **실시간 Mermaid ERD 자동 렌더링 DevPortal**까지 
> 실질적인 학술 연구 조력을 위한 견고하고 신뢰도 높은 백엔드 비즈니스 인프라를 완성했습니다.
> 
> 경청해 주셔서 감사합니다. 질문 있으시면 답변해 드리겠습니다.
