# [4차 산출물] 10. 기술적 문제 해결 및 트러블슈팅 일지 (Troubleshooting & Lessons Learned)

본 문서는 `bist-mini-2` 미니 프로젝트 개발 과정에서 직면했던 대표적인 기술적 병목 현상과 에러 해결 사례를 분석하여, 프로젝트의 기술적 신뢰성과 배운 점(Lessons Learned)을 상세히 기록한 산출물입니다.

---

## 🛠️ 트러블슈팅 사례 1: Pytest 수집 단계에서의 OpenAI API 키 미등록 에러

### 🚨 1. 문제 현황 및 에러 로그
로컬 및 CI/CD 환경에서 자동화 단위 테스트를 가동하기 위해 `pytest`를 실행했을 때, 아래와 같이 에러가 발생하며 테스트 수집(Test Collection) 조차 되지 못하고 전체 테스트 빌드가 즉시 깨지는 현상이 있었습니다.

```text
E   openai.OpenAIError: The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable
E   ValidationError: 1 validation error for ChatOpenAI
E     api_key: Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
```

### 🔍 2. 발생 원인
*   백엔드 서비스 모듈(`services.py` 및 `supervisor.py`) 로드 시점에 `ChatOpenAI(model="gpt-4o-mini")` 및 `OpenAIEmbeddings()` 인스턴스가 모듈 전역 레벨(Module-Level)에서 즉시 생성되도록 설계되어 있었습니다.
*   이로 인해 테스트 코드가 API 키 요구와 무관한 회원가입이나 헬스체크만 임포트하더라도, 파이썬 파일 임포트 과정에서 모듈 최상단의 OpenAI 유효성 검증 로직이 트리거되어 환경변수 누출 경고와 함께 빌드가 종료되었습니다.

### 💡 3. 해결 방안 (Refactoring)
*   **지연 초기화(Lazy Loading) 및 의존성 주입 패턴**을 도입했습니다.
*   모듈 전역에서의 에이전트 인스턴스 생성을 금지하고, 실제 LLM 동작이 수행되는 함수 호출 시점에 인스턴스가 빌드되도록 변경하였으며, FastAPI `Depends`를 활용해 LLM 클라이언트를 의존성으로 전달받는 구조로 리팩토링했습니다.
*   이를 통해 로컬 테스트 환경에 별도의 OpenAI API 키가 없어도 핵심 비즈니스 로직(JWT 인증, DB CRUD) 및 테스트 모킹이 정상 구동되도록 정합성을 확보했습니다.

---

## 🛠️ 트러블슈팅 사례 2: pgvector 10만 건 대용량 벌크 적재 네트워크 타임아웃 및 Hang 현상

### 🚨 1. 문제 현황 및 에러 로그
ArXiv 데이터셋 106,974건에 대해 OpenAI Embeddings API를 조회하고 pgvector DB 테이블에 대량으로 벌크 인서트(`langchain_pg_embedding`)를 시도할 때, 삽입 루프가 실행된 지 약 5~10분 후에 프로세스가 아무런 에러 없이 멈추거나(Hang) 데이터베이스 접속 커넥션 유실 에러가 발생했습니다.

```text
psycopg2.OperationalError: connection to server at "127.0.0.1", port 5432 failed: Connection timed out
Is the server running on that host and accepting TCP/IP connections?
```

### 🔍 2. 발생 원인
*   초기 적재 배치 스크립트가 10만 건이 넘는 대용량 임베딩 데이터를 단일 트랜잭션 범위 내에서 삽입하도록 설계되어 있었습니다.
*   이로 인해 DB 트랜잭션 로그 메모리가 한계치에 도달하고, 대용량 바이너리 벡터 데이터를 상호 쓰기하는 도중 데이터베이스 락(Lock) 및 커넥션 시간 초과가 누적되는 병목이 생겼습니다.

### 💡 3. 해결 방안 (Paging & Commit 분할)
*   **페이징 오프셋(Paging Offset) 적재 기법**을 적용했습니다.
*   단일 파일 로드 대신 `LIMIT 5,000`과 `OFFSET`을 적용하여 5,000건 단위로 청크 데이터를 분할 인출하도록 멱등 적재 스크립트([append_full_domain_embeddings.py](file:///Users/pileuszu/Repos/bist-mini-2/scripts/datasets/append_full_domain_embeddings.py))를 리팩토링했습니다.
*   각 5,000건 페이지 적재가 완료될 때마다 세션 `db.commit()`을 수행해 트랜잭션 버퍼를 비워내고, 실패 시 해당 페이지 오프셋부터 재가동할 수 있게 구현하여 106,974건 적재를 다운 타임 없이 안정적으로 완수했습니다.

---

## 🛠️ 트러블슈팅 사례 3: 아카데믹 한국어 번역 시 원어 인용구(`source_quote`) 번역 유실

### 🚨 1. 문제 현황 및 에러 로그
연구 공백 분석기에서 생성된 영어 리포트를 사용자가 한국어로 번역 요청했을 때, LLM이 문장 전체를 번역하는 도중 `source_quote` 내에 담긴 영문 논문 실제 문구까지 한글로 오역하거나, 인라인 팩트 검증용 영문 텍스트의 앞뒤 구두점을 누락시켜 팩트 검증용 원어 카드와 논문 원본의 텍스트가 일치하지 않는 현상이 발생했습니다.

### 🔍 2. 발생 원인
*   LLM 번역 프롬프트에 `"source_quote 필드는 영어 그대로 유지하시오"`라는 시스템 지침을 주었으나, 텍스트가 길고 복잡해질수록 LLM의 Instruction Following 능력 저하로 인해 해당 규칙이 간헐적으로 무시되는 한계(환각 현상)가 존재했습니다.

### 💡 3. 해결 방안 (Hard-Coded Safe Overwrite)
*   LLM 프롬프트에만 의존하지 않고, **파이썬 서비스 레이어 상에서 팩트를 물리 복원하는 안전 장치**를 추가했습니다.
*   `research_gap/services.py` 모듈 내 `translate_matrix` 함수 동작 방식:
    1.  번역 작업을 수행하기 전, 기존 영어 매트릭스에 있던 모든 `source_quote` 텍스트를 메모리 딕셔너리에 백업합니다.
    2.  `gpt-4o-mini`를 통해 전체 구조화 출력 데이터셋 번역을 수행합니다.
    3.  번역이 완료된 직후, 파이썬 루프를 통해 번역된 DTO 내의 `source_quote` 필드를 1단계에서 백업해 둔 **원본 영어 텍스트 데이터로 강제 덮어쓰기(Overwrite)하여 재할당**합니다.
*   이로써 프롬프트 미지시로 인한 다국어 왜곡 우려를 $100\%$ 차단하고 실제 논문 문구가 영어 그대로 유지되도록 구현했습니다.
