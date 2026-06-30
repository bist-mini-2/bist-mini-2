# [4차 산출물] 12. 프로젝트 종합 기술 스택 명세서 (Technology Stack Summary)

본 문서는 `bist-mini-2` 플랫폼 개발 프로젝트에 최종 적용된 **프론트엔드, 백엔드, 데이터베이스, AI 에이전트 및 인프라스트럭처 전반의 기술 스택 명세서**입니다. 미니 프로젝트의 스펙에 맞추어 현행화된 실제 코드베이스 내의 패키지 및 런타임 사양을 기준으로 작성되었습니다.

---

## 💻 1. 기술 스택 요약 분류표

| 레이어 | 기술 스택 (Technology) | 역할 및 용도 | 주요 선정 이유 및 특징 |
| :--- | :--- | :--- | :--- |
| **Frontend** | • **Next.js (React)**<br>• **JavaScript (ES6+)**<br>• **Bootstrap 5**<br>• **Axios** | • 사용자 웹 대시보드 인터페이스 구축<br>• 비동기 클라이언트 통신 모듈<br>• 반응형 그리드 및 UI 컴포넌트 | • App Router 기반의 고효율 서버/클라이언트 컴포넌트 분리<br>• Bootstrap CSS를 활용한 인라인 스타일 배제 및 UI 일관성 확보<br>• Axios 인터셉터를 통한 JWT 토큰 관리 |
| **Backend** | • **FastAPI**<br>• **Python 3.12**<br>• **Uvicorn**<br>• **Pydantic v2** | • 고성능 비동기 API 서버 엔진<br>• 데이터 검증 및 DTO(Data Transfer Object) 통제 | • Asynchronous ASGI 기반의 고속 Q&A 스트리밍 및 SSE 알림 브로드캐스팅 지원<br>• Pydantic BaseDTO 상속을 통한 REST API 스키마 정합성 보장 |
| **Database<br>& Storage** | • **PostgreSQL 17**<br>• **pgvector 0.7+**<br>• **SQLAlchemy 2.0+**<br>• **Asyncpg**<br>• **Redis** | • 관계형 데이터 영구 적재<br>• 3대 학술 도메인 10만 건 임베딩 관리<br>• 비동기 DB 커넥션 ORM 매핑<br>• 인메모리 캐싱 및 실시간 Pub/Sub | • HNSW(Hierarchical Navigable Small World) 인덱스 탑재로 코사인 유사도 검색 속도 최적화 ($68\text{ms}$)<br>• LangGraph의 AsyncPostgresSaver 연동을 통해 스레드 체킹 히스토리 백업 |
| **AI Agent** | • **LangGraph**<br>• **LangChain**<br>• **OpenAI API**<br>• **Tavily Search API** | • 멀티 에이전트 상태 전이 및 워크플로우<br>• 듀얼 트랙 병렬 LLM 오케스트레이션<br>• 실시간 외부 시사/오픈소스 정보 수집 | • `asyncio.gather`를 통한 `paper_node`와 `web_node` 무조건 병렬 가동 구조 제어<br>• gpt-4o-mini/gpt-4o 결합을 통한 비용 최적화 답변 합성 및 번역 수행 |
| **Testing &<br>Infrastructure** | • **Docker & Compose**<br>• **Pytest**<br>• **Pytest-asyncio**<br>• **NPM / Pip** | • 로컬 통합 컨테이너 환경 가동<br>• 비동기 API 단위 테스트 수행<br>• 패키지 의존성 관리 | • `docker-compose` 단일 명령을 통한 FE/BE/DB 전체 로컬 구동 표준화<br>• 테스트 시 외부 API 종속 제거를 위한 Mocking 수트 완성 |

---

## 🛠️ 2. 컴포넌트별 상세 의존성 라이브러리 명세

### A. 백엔드 (Python / FastAPI) 핵심 의존성 (`requirements.txt`)
*   **fastapi**: `0.111.0` (비동기 웹 프레임워크)
*   **uvicorn**: `0.30.1` (ASGI 서버)
*   **langgraph**: `0.0.60` (멀티 에이전트 워크플로우 제어 엔진)
*   **langchain-openai**: `0.1.8` (OpenAI 연동 래퍼 모듈)
*   **langchain-postgres**: `0.0.6` (PostgreSQL vector store 연동)
*   **sqlalchemy**: `2.0.30` (비동기 ORM 드라이버 지원 및 세션 관리)
*   **asyncpg**: `0.29.0` (PostgreSQL 비동기 접속 클라이언트)
*   **pydantic**: `2.7.2` (BaseDTO 데이터 밸리데이터)
*   **colorlog**: `6.8.2` (표준 Google 스타일 로그 포맷 컬러 라이브러리)

### B. 프론트엔드 (Node.js / React / Next.js) 핵심 의존성 (`package.json`)
*   **next**: `14.2.3` (App Router React 프레임워크)
*   **react**: `18.3.1`
*   **bootstrap**: `5.3.3` (CSS 프레임워크)
*   **bootstrap-icons**: `1.11.3` (일관된 표준 아이콘 세트)
*   **axios**: `1.7.2` (비동기 통신 클라이언트)

---

## 📊 3. 기술 스택 선정 전략 및 한계 극복 (SaaS Optimization)

1. **Type-Safe DTO 통제**:
   - 백엔드는 Pydantic v2와 SQLAlchemy 2.0 매핑 방식을 결합하여 API 입출력 단에서의 유효성 검증을 자동화하고, 프론트엔드는 Axios 통신 객체의 타입 가드를 적용하여 데이터 흐름의 안정성을 높였습니다.
2. **비동기 성능 고도화**:
   - AI 연산의 지연(Latency)을 최소화하기 위해 백엔드 통신에 `async/await` 및 `AsyncSession` 비동기 드라이버를 기본으로 채택하여, SSE(Server-Sent Events) 스트리밍 토큰 방출 시 동시 다발적인 클라이언트 요청을 효율적으로 소화하도록 설계했습니다.
3. **가벼운 프론트엔드와 풍부한 CSS**:
   - 무거운 프레임워크와 Tailwind CSS의 ad-hoc 유틸리티 오버헤드를 배제하기 위해, Next.js에 **Bootstrap 5**만을 통합 배치하여 인라인 코드 없는 완결성 있는 깔끔한 UI를 제공합니다.
