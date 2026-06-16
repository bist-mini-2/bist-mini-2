# 🚀 Paper Agent 온보딩 및 개발 가이드 (README.md)

이 저장소는 **Paper Agent (학술 에이전트 서비스 플랫폼)**의 개발을 위한 풀스택 템플릿 프로젝트입니다. 
FastAPI 비동기 백엔드와 Next.js 16(App Router) 기반의 프론트엔드로 구성되어 있습니다.

신규 팀원분들은 이 문서를 참고하여 개발 환경을 세팅하고, 개발 컨벤션을 숙지하여 프로젝트를 원활하게 시작해 주시기 바랍니다.

---

## 📂 1. 전체 디렉토리 구조 (Repository Structure)

이 저장소는 모듈성 극대화와 클린 아키텍처를 지향하기 위해 프론트엔드와 백엔드가 명확히 분리되어 있습니다.

```directory
bist-mini-2/
├── backend/                   # FastAPI 비동기 백엔드 서버
│   ├── api/
│   │   ├── common/            # JWT 인증 및 전역 예외 처리 핸들러
│   │   ├── database/          # 데이터베이스 연결(dbsession) 및 기본 엔티티
│   │   └── v1/                # API v1 (auth, member 등 도메인 폴더 분리)
│   ├── static/                # 정적 에셋 폴더 (캐시 방지 적용)
│   ├── templates/             # Jinja2 템플릿 폴더
│   ├── .env.example           # 환경 변수 설정 템플릿
│   ├── main.py                # 백엔드 실행 엔트리포인트 (테이블 자동 생성 훅 내장)
│   └── requirements.txt       # 백엔드 의존성 패키지 정의
│
├── frontend/                  # Next.js 16 (App Router) 프론트엔드 서비스
│   ├── src/
│   │   ├── apis/              # Axios API 호출 모듈 (apiClient 내장)
│   │   ├── app/               # Next.js 페이지 라우터 (join, login, feature1~3)
│   │   ├── components/        # 공통 컴포넌트 (Sidebar, AppLayoutWrapper 등)
│   │   └── contexts/          # Context API를 통한 전역 상태 관리 (AuthContext)
│   ├── package.json           # 프론트엔드 종속성 정의
│   └── jsconfig.json          # 경로 Alias 설정
│
├── frontend-checklist.md      # 프론트엔드 작업 완료 전 자가 검증 체크리스트
└── backend-checklist.md       # 백엔드 작업 완료 전 자가 검증 체크리스트
```

---

## 🛠️ 기술 스택 및 버전 사양 (Technology Stack & Versions)

플랫폼 구동 및 빌드 안정성을 위해 검증된 기술 스택과 라이브러리 명세입니다.

### 💻 백엔드 (Backend API)
- **Runtime Engine**: Python `3.12` (uv 가상환경 격리 지원)
- **Framework**: FastAPI `0.116.1`
- **ASGI Server**: Uvicorn `0.35.0`
- **ORM**: SQLAlchemy `2.0.43`
- **Database Driver**: psycopg `3.3.3` (asyncpg `0.30.0` 병행)
- **Semantic Search**: pgvector `0.3.6` (HNSW 인덱싱 지원)
- **AI / Agentic Workflow**:
  - LangChain `1.2.10`
  - LangGraph `1.0.10`
  - OpenAI SDK `2.24.0`

### 🌐 프론트엔드 (Frontend Web)
- **Framework**: Next.js `16.2.9` (App Router 규격 채택)
- **Library**: React `19.2.4` / React-DOM `19.2.4`
- **HTTP Client**: Axios `1.17.0`
- **UI Styling**: Bootstrap `5.3.8` (Bootstrap Icons `@1.11.3` 표준 활용)

### 🗄️ 데이터베이스 및 인프라 (Database & Infrastructure)
- **Database**: PostgreSQL `17.x` (pgvector Extension 활성화 필수)
- **Cache / Context Store**: Redis (RAG 캐싱 레이어)

---

## 🛠️ 2. 로컬 개발 환경 세팅 (Getting Started)

### ① 데이터베이스 준비
- 이 프로젝트는 **PostgreSQL** 비동기 연결(`asyncpg`)을 기본적으로 사용합니다.
- 로컬 또는 컨테이너 환경에 PostgreSQL 데이터베이스를 구동해 줍니다.
  - 기본 접속 주소: `postgresql+asyncpg://postgres:postgres@localhost:5432/postgres`

### ② 백엔드 (FastAPI) 설정 및 실행
1. 백엔드 폴더로 이동합니다.
   ```bash
   cd backend
   ```
2. 가상환경 생성 및 활성화:
   - **Windows (PowerShell/CMD)**:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```
4. 환경 변수 파일 생성:
   - `.env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요에 따라 데이터베이스 URL 등을 수정합니다.
   ```bash
   copy .env.example .env     # Windows
   cp .env.example .env       # macOS / Linux
   ```
5. 서버 구동:
   ```bash
   python main.py
   ```
   - *참고: 서버 구동 시 SQLAlchemy가 작동하여 필요한 테이블(`member` 등)을 데이터베이스에 자동으로 신설해 줍니다.*

### ③ 프론트엔드 (Next.js) 설정 및 실행
1. 프론트엔드 폴더로 이동합니다.
   ```bash
   cd ../frontend
   ```
2. 의존성 패키지 설치:
   ```bash
   npm install
   ```
3. 개발 서버 실행:
   ```bash
   npm run dev
   ```
4. 웹 브라우저에서 `http://localhost:3000`으로 접속하여 로그인 화면을 확인합니다.

---

## 🤝 3. 핵심 개발 컨벤션 및 아키텍처 패턴

팀의 모든 구성원은 아래의 규칙을 엄격히 준수하여 코드를 작성해야 합니다.

### 🌐 프론트엔드 (Frontend Rules)
1. **JavaScript 사용 (TypeScript 금지)**:
   - 모든 컴포넌트와 모듈은 파일 확장자 `.js` 및 `.jsx` 규격을 유지합니다.
2. **이모지 사용 금지 및 Bootstrap Icons 강제**:
   - UI 상의 시각적 데코레이션에 텍스트 이모티콘(⚙️, 🔑 등)의 직접적인 혼용을 엄격히 금지합니다.
   - 반드시 **Bootstrap Icons** 클래스(`<i className="bi bi-gear"></i>`)를 사용하십시오.
3. **Axios 전용 인스턴스 (`apiClient`) 활용**:
   - 전역 `axios` 기본값을 직접 변조하는 것은 금지됩니다.
   - [axiosConfig.js](file:///c:/Repo/bist-mini-2/frontend/src/apis/axiosConfig.js)에 선언된 `apiClient` 인스턴스를 임포트하여 API 요청을 보내야 합니다.
   - `apiClient`에 탑재된 Request Interceptor가 로컬스토리지에서 `accessToken`을 동적으로 파싱해 헤더에 자동 기입해 줍니다.
4. **전역 401 Unauthorized 감지 및 로그아웃**:
   - `AuthContext.js` 내에 장착된 Response Interceptor가 401 오류 감지 시 자동으로 세션을 파기하고 `/login`으로 튕기도록 제어하므로, 각 기능 페이지 내부에서 개별 401 에러 리다이렉션을 따로 작성할 필요가 없습니다.

### ⚙️ 백엔드 (Backend Rules)
1. **관심사 분리 (Auth vs Member 이원화)**:
   - **`/auth` 계열 API**: 로그인 및 세션 검증 전담 (OAuth2 표준 규격에 맞추어 평평한 JSON 형태로 토큰 반환).
   - **`/member` 계열 API**: 가입, 상세 정보 조회, 비밀번호 변경 등 데이터베이스 리소스 CRUD 전담 (공통 API 응답 래퍼 적용).
2. **FastAPI 의존성 주입**:
   - 반드시 `typing.Annotated` 방식을 사용하여 의존성을 정의합니다 (예: `db: Annotated[AsyncSession, Depends(get_db)]`).
3. **Pydantic BaseDTO 상속**:
   - 스키마 설계 시 엔드포인트 내 선언을 금지하고, 기능별 `models.py`에 물리적으로 구분해 선언하며 `BaseDTO`를 상속합니다.

---

## 🚦 4. 커밋 및 가이드라인 문서 참고

- 커밋 메시지는 **Conventional Commits** 형식을 명확히 준수합니다 (`feat`, `fix`, `style`, `docs`, `refactor` 등).
- 변경 사항을 커밋하거나 PR(Pull Request)을 제출하기 전에 반드시 다음 체크리스트를 정독하고 자가 체크를 완료해야 합니다.
  - [frontend-checklist.md](file:///c:/Repo/bist-mini-2/frontend-checklist.md)
  - [backend-checklist.md](file:///c:/Repo/bist-mini-2/backend-checklist.md)
  - 상세 개발 컨벤션 및 규칙: [.agents/rules/antigravity_rules.md](file:///c:/Repo/bist-mini-2/.agents/rules/antigravity_rules.md)
