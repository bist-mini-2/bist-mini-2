# 📋 프로젝트 산출물 리스트 및 개발 로드맵 계획서 (Project Deliverables & Roadmap)

본 문서는 **'논문 AI 에이전트 채팅 플랫폼 (Paper Agent Chat Platform)'** 개발 프로젝트의 **현재 기완료된 산출물 리스트**와 향후 구현 단계에서 생성될 **미래 산출물에 대한 개발 계획 로드맵**을 일목요연하게 정리한 명세서입니다.

---

## 📂 1. 현재 완료된 산출물 현황 (Current Deliverables)

기초 기획, 사용자 시나리오 정의, 화면 프로토타이핑(와이어프레임) 및 개발 스펙 정의 단계가 완벽히 마감되어 아래의 산출물들이 물리적으로 적재 완료되었습니다.

### 📝 1.1 기획 및 전략 문서 (Planning & Strategy)
*   **프로젝트 정의서**: [project-summary.md](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/project-summary.md)
    *   *내용*: RAG 결과물 LLM 활용 방안 및 MTEB 데이터셋 매핑 등 프로젝트 요약서
*   **비즈니스 린 캔버스**: [lean-canvas.md](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/lean-canvas.md)
    *   *내용*: 핵심 고객 세그먼트, 고유 가치 제안(UVP), 비용 구조 및 핵심 지표 분석서
*   **사용자 페르소나 정의서**: [persona.md](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/persona.md)
    *   *내용*: 석·박사과정 및 기업 연구원 등 가상의 핵심 사용자 니즈와 페인 포인트 정의
*   **의사결정 체크리스트**: [project-decision-checklist.md](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/project-decision-checklist.md)
    *   *내용*: 개발 착수 전 합의해야 할 DB 설정, API 비용, 개인정보 가이드라인 등 회의 안건

### 📐 1.2 설계 및 개발 스펙 문서 (Design & Specifications)
*   **유즈케이스 명세서**: [use-cases.md](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/use-cases.md)
    *   *내용*: 사용자 행동 여정 시퀀스 다이어그램(Mermaid) 및 구체적 basic flow 정의
*   **화면 연동 관계 정의서**: [wireframe-connections.md](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/wireframe-connections.md)
    *   *내용*: 7대 화면의 연동 흐름도 및 화면 간 전달 데이터 바인딩 규격 명세
*   **상세 기능 명세서**: [functional-specification-1st.md](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/functional-specification-1st.md)
    *   *내용*: 유즈케이스와 매핑된 초정밀 세분화 API 핸들러, Pydantic DTO, 보안 로직 명세
*   **공통 코드 컨벤션**: [code-conventions.md](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/code-conventions.md)
    *   *내용*: FastAPI DI 패턴, 예외 처리, 비동기 트랜잭션, Sphinx 주석 규격 정의

### 🖥️ 1.3 UI/UX 와이어프레임 프로토타입 (HTML & PNG)

| 화면 ID | 화면 설명 | HTML 원본 파일 경로 | 고해상도 스크린샷 뷰 |
| :---: | :--- | :--- | :---: |
| **W-01** | 유저 메인 채팅 화면 | [user-main-chat.html](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/user-main-chat.html) | [Screenshot](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/images/user-main-chat.png) |
| **W-02** | 문헌 요약 리포트 화면 | [user-report-view.html](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/user-report-view.html) | [Screenshot](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/images/user-report-view.png) |
| **W-03** | 관리자/검증용 테스트 화면 | [admin-test.html](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/admin-test.html) | [Screenshot](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/images/admin-test.png) |
| **W-04** | 문헌 보관함 및 리포트 아카이브 화면 | [user-library-archive.html](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/user-library-archive.html) | [Screenshot](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/images/user-library-archive.png) |
| **W-05** | 인용 관계 그래프 및 상세 화면 | [user-citation-graph.html](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/user-citation-graph.html) | [Screenshot](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/images/user-citation-graph.png) |
| **W-06** | 개인용 보안 샌드박스 설정 화면 | [user-sandbox-control.html](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/user-sandbox-control.html) | [Screenshot](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/images/user-sandbox-control.png) |
| **W-07** | 유저 피어 리뷰 워크숍 화면 | [user-peer-review.html](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/user-peer-review.html) | [Screenshot](file:///c:/Repo/bist-mini-2/docs/deliverables/1st/wireframes/images/user-peer-review.png) |

---

## 🗺️ 2. 향후 생성될 산출물 계획 로드맵 (Future Roadmap)

실제 백엔드, 데이터베이스 및 프론트엔드 연동을 진행하는 과정에서 추가로 생성해야 할 주요 코드 및 검증 산출물의 상세 계획입니다.

### 🗺️ 2.1 단계 0: 기획 설계 및 개발 준비 단계 산출물 계획 (Planning & Design Specs)
*   **데이터셋 EDA 및 DB 스키마 설계** (`c:/Repo/bist-mini-2/docs/deliverables/2nd/project_plans/dataset-eda-db-schema.md`):
    *   *역할*: MTEB 3대 데이터셋 구조분석 및 PostgreSQL pgvector DB 테이블 명세(ERD) DDL 정의.
*   **시스템 아키텍처 및 API 명세** (`c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/system-architecture-api-spec.md`):
    *   *역할*: 플랫폼 3티어 연동 관계도 및 14대 JSON API 상세 입출력 규격 명세.
*   **종합 시스템 시퀀스 다이어그램** (`c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/sequence-diagrams.md`):
    *   *역할*: W-01~W-07, FastAPI, LangGraph 및 DB 연동 간의 데이터 흐름 다이어그램.
*   **Git 협업 및 커밋 규칙 정의서** (`c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/git-collaboration-rules.md`):
    *   *역할*: GitHub Flow 브랜치 전략, Conventional Commits 규칙 및 PR 머지 정책 정의.

### 🗄️ 2.2 단계 1: 데이터베이스 & 데이터 가공 (Database & ETL Layer)
*   **데이터베이스 DDL 스크립트** (`c:/Repo/bist-mini-2/backend/database/schema.sql`):
    *   *역할*: pgvector 인덱스 설정, 대화 기록 저장용 `PostgresSaver` 스키마 및 요약 보관함/아카이브 저장 테이블 정의.
*   **ArXiv 벌크 데이터 로더 및 필터** (`c:/Repo/bist-mini-2/scripts/data_loader.py`):
    *   *역할*: Kaggle ArXiv 메타데이터 JSON을 스트리밍 파싱하여 생명공학(q-bio), 컴퓨터과학(cs), 천문학(astro-ph) 카테고리별로 분류 및 적재하는 자동화 스크립트.
*   **텍스트 청커 및 전처리기** (`c:/Repo/bist-mini-2/scripts/chunker.py`):
    *   *역할*: 문단 분실 없이 500자 단위로 논문을 절단하고 메타데이터와 벡터 임베딩을 결합하는 가공 유틸리티.

### 🔌 2.3 단계 2: 백엔드 API & DTO 정의 (FastAPI Layer)
*   **API 핸들러 및 라우터** (`c:/Repo/bist-mini-2/backend/api/` 하위):
    *   *역할*: RAG 유사도 검색, 격리 파일 전송, 요약 보고서 등록 등의 엔드포인트 구현.
*   **Pydantic DTO 스키마** (`c:/Repo/bist-mini-2/backend/api/` 하위):
    *   *역할*: 인용 정보 DTO(`CitationSource`), 가설 검증 결과 DTO, 채점 스코어카드 및 리포트 내보내기용 DTO 정의.
*   **보안 가드 및 파일 와이퍼** (`c:/Repo/bist-mini-2/backend/api/common/` 또는 utils):
    *   *역할*: Directory Traversal 방지 경로 가드 및 30분 초과 시 비활성 세션을 파쇄(Wipe)하는 데몬 로직.

### 🧠 2.4 단계 3: AI 에이전트 & LangGraph 구축 (Agent Layer)
*   **에이전트 오케스트레이터 및 그래프** (`c:/Repo/bist-mini-2/backend/api/` 또는 `app/agents/`):
    *   *역할*: LangGraph 기반 질문 분석 ➡️ 도메인 라우팅 ➡️ 병렬 RAG 검색 ➡️ 취합(Gather) 노드로 연결되는 상태 그래프 정의. 피어 리뷰 워크숍용 Conditional Edge 및 Shared State 구조 설계.
*   **프롬프트 템플릿 매니저** (`c:/Repo/bist-mini-2/backend/api/` 또는 `app/agents/`):
    *   *역할*: Step-Back 질문 변환, CoT 추론 유도, 학술 피어 리뷰(방법론/신규성/문체) 3대 리뷰어 전용 프롬프트 리포지토리.
*   **요약 미들웨어 및 영구 메모리** (`c:/Repo/bist-mini-2/backend/api/` 또는 `app/utils/`):
    *   *역할*: `SummarizationMiddleware` 토큰 최적화 및 `PostgresSaver` 데이터베이스 세션 관리 모듈.

### 💻 2.5 단계 4: 프론트엔드 연동 (Frontend & API Integration)
*   **Next.js API 클라이언트** (`c:/Repo/bist-mini-2/frontend/src/apis/`):
    *   *역할*: 백엔드 FastAPI 엔드포인트를 호출하여 스레드, 샌드박스, 피어 리뷰 정보를 수신하는 fetch 모듈.
*   **SSE 토큰/CoT 스트리밍 리스너** (`c:/Repo/bist-mini-2/frontend/src/app/` 하위 또는 hooks):
    *   *역할*: 실시간 응답 토큰 및 생각의 흐름 로그를 실시간으로 스트리밍하여 W-01 화면에 점진적으로 렌더링하는 React Hook.
*   **D3/인터랙티브 그래프 렌더러** (`c:/Repo/bist-mini-2/frontend/src/components/`):
    *   *역할*: `GET /graph-structure` 및 `GET /papers/{id}/citations` 데이터 기반으로 관계망(LangGraph 및 Citation Graph) 노드-링크 시각화 컴포넌트 구현.

### 🧪 2.6 단계 5: 테스트 & 제품 완료 보고 (Validation & Final Deliverables)
*   **통합 및 단위 테스트 스크립트** (`c:/Repo/bist-mini-2/backend/tests/`):
    *   *역할*: RAG 유사도 성능, Pydantic Structured Output 규격, 다중 에이전ล 가설 검증 결과의 정확도를 검증하는 PyTest 코드.
*   **테스트 검증 완료 보고서** (`c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/test-report-1st.md`):
    *   *역할*: API 및 도구 연동 단위 테스트 성공 기록 및 RAG 정확도 팩트체크 테스트 스코어.
*   **제품 시연 가이드 & 완료 보고서** (`c:/Repo/bist-mini-2/docs/deliverables/1st/project_plans/walkthrough-1st.md` 업데이트):
    *   *역할*: 개발이 완수된 최종 플랫폼 구동 및 시연 가이드라인과 릴리즈 버전의 산출물 현황 보고서.
