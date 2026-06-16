# 📅 3인 기준 2주 단기 집중 개발 일정 및 R&R 계획 (Development Roadmap & WBS)

본 문서는 **6월 30일 프로젝트 완료 및 최종 배포**를 목표로, 평일 작업(총 11영업일) 기준으로 3명의 팀원(A, B, C)에게 태스크를 유기적으로 분담한 단기 집중 로드맵입니다.

---

## 👥 1. 팀원 구성 및 R&R (Role & Responsibility)

*   **Developer A (AI & Agent)**: RAG 데이터 가공(청킹, 임베딩), LangGraph 상태 그래프 및 라우팅 오케스트레이션, 프롬프트 엔지니어링, RAG 정확도/성능 평가 총괄.
*   **Developer B (Backend & DB)**: PostgreSQL DB 물리 스케마 반영, 벌크 데이터 로더/가공 스크립트 작성, FastAPI API 엔드포인트(Auth, Member, Chat, Sandbox, Subscription) 구현, 보안 파쇄 스케줄러 구현.
*   **Developer C (Frontend)**: Next.js App Router UI 컴포넌트화, Axios API 연동, SSE 실시간 토큰/CoT 스트리밍 리스너 구현, D3.js 기반 인터랙티브 인용 관계망 렌더러 개발.

---

## 🗓️ 2. 상세 WBS (일자별 마일스톤)

### 📅 [1주차] 데이터셋 구축, DB 적재 및 기본 API/UI 마운트 (6/16 ~ 6/19, 4영업일)

*   **6/16 (화)**
    *   **Developer A**: ArXiv 1.5만 건 경량 도메인 필터링 조건 설정 및 `chunker.py` 텍스트 분할 초안 완성.
    *   **Developer B**: PostgreSQL pgvector 확장 반영 및 `schema.sql` 데이터베이스 테이블 신설 완료.
    *   **Developer C**: 2차 고도화 와이어프레임(HTML/CSS) 마크업을 Next.js(React) 구조로 이관 및 Sage/Warm 테마 시스템 마운트.
*   **6/17 (수)**
    *   **Developer A**: `local_batch_embed.py` 구동을 통한 Apple Silicon M4 GPU 기반 1.5만 건 논문 임베딩 생성 (JSONL 저장).
    *   **Developer B**: `bulk_load_to_db.py` 완성 및 5,000건 단위의 pgvector 고속 DB 벌크 적재(Copy) 실행 완료.
    *   **Developer C**: `AuthContext.js` 연동을 통한 로그인/회원가입 API 연동 및 클라이언트 세션 관리 구현.
*   **6/18 (목)**
    *   **Developer A**: LangGraph 상태 그래프(StateGraph) 정의 및 도메인 분기 조건부 에지(Conditional Edge) 설계.
    *   **Developer B**: FastAPI `BaseDTO` 정의 및 `/auth` (인증), `/member` (회원 CRUD) 백엔드 API 핸들러 완수.
    *   **Developer C**: 일반 챗 허브 (W2-01) UI 컴포넌트 구현 및 백엔드 SSE 응답 마운트 준비.
*   **6/19 (금)**
    *   **Developer A**: RAG 유사도 검색 연동 노드 구현 및 LangGraph 오케스트레이터 기본 파이프라인 작동 테스트.
    *   **Developer B**: `/chat` 계열 스레드/메시지 데이터 저장 API 및 FastAPI SSE(Server-Sent Events) 스트리밍 채널 구현.
    *   **Developer C**: Next.js 내 실시간 SSE 토큰 수신 리스너 Hook 개발 및 Chat UI에 생각의 흐름(CoT) 실시간 타이핑 렌더링 연동.

### 📅 [2주차] 샌드박스 보안 데몬, 다중 에이전트 및 UI 인터랙션 고도화 (6/22 ~ 6/26, 5영업일)

*   **6/22 (월)**
    *   **Developer A**: 문헌 비교 및 Gap 분석용 Multi-Query / Step-Back 프롬프트 설계 및 분석 요약 노드 구축.
    *   **Developer B**: `/sandbox` 임시 세션 개설 및 격리 PDF 업로드 처리 API 구현.
    *   **Developer C**: 대규모 문헌 비교 및 Gap 분석기 (W2-02) UI 렌더링 및 비동기 상태 진행바 연동.
*   **6/23 (화)**
    *   **Developer A**: 보안 리뷰 및 가설 디펜스용 3대 가상 에이전트(리뷰어) 페르소나 설계 및 의견 취합 노드 개발.
    *   **Developer B**: 30분 소거 타이머를 검증하는 스케줄러 (`purge_expired_sandboxes`) 구현 및 CASCADE 테이블 삭제 기능 연동.
    *   **Developer C**: 보안 리뷰 및 가설 디펜스 아레나 (W2-03) UI 연동 및 30분 소거 타이머 배너 기능 구현.
*   **6/24 (수)**
    *   **Developer A**: 가설 구독 정기 백그라운드 크론 태스크 및 논문 의미론적 지지/반박(PRO/CONTRA) 판별 LLM 가이드라인 적용.
    *   **Developer B**: 가설 알림 수신 인박스 API 구현 및 SMTP 모듈 연동을 통한 이메일 발송 데몬 완성.
    *   **Developer C**: 맞춤형 연구 비서 Gem 팩토리 (W2-04) UI 연동 (RAG 소스 및 시스템 프롬프트 데이터 전송 및 생성 테스트).
*   **6/25 (목)**
    *   **Developer A**: 다중 에이전트 및 RAG 전체 질의에 대한 테스트 데이터셋 빌드 및 품질 정확도 측정 (PyTest).
    *   **Developer B**: `/subscriptions`, `/gem_agent` API 마이너 버그 튜닝 및 pgvector 검색 속도 인덱스 최적화.
    *   **Developer C**: D3.js 연동을 통한 논문 인용망 시각화(W2-01 내 팝업 관계망) 컴포넌트 개발 및 그래프 데이터 연계.
*   **6/26 (금)**
    *   **공통**: 프론트엔드와 백엔드 간의 E2E 통합 테스트 수행, API 런타임 예외 처리(4xx/5xx) 디버깅 및 UI 마이크로 애니메이션 폴리싱.

### 📅 [3주차] 최종 통합 성능 검증, 릴리즈 마감 및 배포 (6/29 ~ 6/30, 2영업일)

*   **6/29 (월)**
    *   **Developer A**: RAG 데이터셋 누수 및 가설 오분류율 검증 후 `test-report-2nd.md` 통합 성능 분석 보고서 마감.
    *   **Developer B/C**: Next.js 프로덕션 빌드 최적화 및 FastAPI ASGI 다중 커넥션 부하 테스트 수행.
*   **6/30 (화)**
    *   **공통**: 플랫폼 구동 및 시연용 화면 녹화/가이드북을 정리한 `walkthrough-2nd.md` 갱신. 로컬 `dev` 브랜치를 `main` 브랜치로 최종 풀리퀘스트(PR) 병합 후 릴리즈 배포 완료.
