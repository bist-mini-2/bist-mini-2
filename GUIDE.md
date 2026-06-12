# 🚀 신규 개발자를 위한 공동 작업 및 아키텍처 가이드 (GUIDE.md)

본 문서는 **'논문 AI 에이전트 채팅 플랫폼 (Paper Agent Chat Platform)'** 프로젝트에 참여하는 개발자분들이 빠르고 일관되게 협업하실 수 있도록 작성된 아키텍처 및 작업 가이드라인입니다. 기존 `repo_template.md`에 기재되었던 디렉토리 구조 및 기본 설계 표준을 통합하여 단일 문서로 관리합니다.

MTEB/BEIR 벤치마크 기반의 검증 및 평가 태스크는 본 프로젝트에서 진행하지 않으므로 관련 내용은 제외되었습니다.

---

## 📂 1. 레포지토리 표준 디렉토리 구조 (Directory Structure)

본 프로젝트는 백엔드(FastAPI)와 프론트엔드(Next.js)가 분리된 모노레포 구조를 기반으로 하며, 실제 구성은 다음과 같습니다. 모든 코드는 명확한 책임 분할에 따라 해당 디렉토리에 적재해야 합니다.

```text
bist-mini-2/
├── backend/                   # FastAPI 비동기 백엔드 서버
│   ├── api/
│   │   ├── common/            # JWT 인증 및 전역 예외 처리 핸들러
│   │   │   ├── auth.py        # 인증 데코레이터 및 디펜던시
│   │   │   ├── config.py      # 환경 변수 및 전역 설정 (Settings)
│   │   │   ├── exception_handler.py # 전역 에러 핸들러 및 응답 규격화
│   │   │   └── exceptions.py  # 공통 커스텀 예외 정의
│   │   ├── database/          # 데이터베이스 연결 및 기본 DTO/Entity 설정
│   │   │   └── config/
│   │   │       ├── dbsession.py  # 비동기 DB 세션 엔진 생성기
│   │   │       ├── dto_base.py   # 공통 BaseDTO 및 Response 스키마
│   │   │       └── entity_base.py # SQLAlchemy Declarative Base
│   │   └── v1/                # API v1 (도메인별 기능 폴더 분리)
│   │       ├── api_router.py  # v1의 모든 라우터를 통합하는 메인 라우터
│   │       ├── auth/          # 인증 도메인 API (endpoints, models, services)
│   │       ├── health/        # 헬스체크 API (endpoints)
│   │       └── member/        # 회원 관리 도메인 API (dao, endpoints, entity, models, services)
│   ├── static/                # 정적 에셋 폴더 (캐시 방지 적용)
│   ├── templates/             # HTML 템플릿 폴더
│   ├── tests/                 # 단위 및 통합 테스트 폴더
│   │   └── test_health.py     # 헬스체크 테스트 코드
│   ├── .env.example           # 환경 변수 설정 템플릿
│   ├── main.py                # 백엔드 실행 엔트리포인트 (테이블 자동 생성 내장)
│   └── requirements.txt       # 백엔드 의존성 패키지 정의
│
├── frontend/                  # Next.js 16 (App Router) 프론트엔드 서비스
│   ├── src/
│   │   ├── apis/              # Axios API 비동기 통신 모듈
│   │   │   ├── authApi.js     # 인증 관련 API 통신
│   │   │   ├── axiosConfig.js # Axios 클라이언트 설정 및 Interceptor
│   │   │   └── memberApi.js   # 회원 관련 API 통신
│   │   ├── app/               # Next.js 라우팅 페이지 컴포넌트
│   │   │   ├── feature1/      # 기능 1 페이지
│   │   │   ├── feature2/      # 기능 2 페이지
│   │   │   ├── feature3/      # 기능 3 페이지
│   │   │   ├── join/          # 회원가입 페이지
│   │   │   ├── login/         # 로그인 페이지
│   │   │   ├── BootstrapClient.js # Bootstrap 5 클라이언트 사이드 로더
│   │   │   ├── components.css # 컴포넌트 커스텀 스타일
│   │   │   ├── globals.css    # 전역 스타일
│   │   │   ├── layout.js      # 루트 레이아웃 (Bootstrap 5 로더 포함)
│   │   │   ├── page.js        # 메인 페이지 (검색 인터페이스 또는 대시보드)
│   │   │   ├── page.module.css
│   │   │   └── theme.css      # 테마 설정 스타일시트
│   │   ├── components/        # 재사용 가능한 UI 컴포넌트
│   │   │   ├── AppLayoutWrapper.js
│   │   │   ├── Sidebar.js
│   │   │   └── Topbar.js
│   │   └── contexts/          # React Context API 전역 상태 관리
│   │       └── AuthContext.js # 사용자 인증 정보 공유 컨텍스트
│   ├── public/                # 정적 애셋 (이미지 등)
│   ├── package.json           # 프론트엔드 패키지 의존성
│   └── jsconfig.json          # 경로 Alias 설정
│
├── docs/                      # 프로젝트 문서화
│   └── mteb_domains.md        # MTEB 데이터셋 및 도메인 분석 명세서 (참고용)
│
├── README.md                  # 전체 프로젝트 실행 가이드
├── GUIDE.md                   # [본 문서] 개발자 협업 및 아키텍처 가이드
├── frontend-checklist.md      # 프론트엔드 체크리스트
└── backend-checklist.md       # 백엔드 체크리스트
```

---

## 🤝 2. 3인 공동 개발 및 임무 분담 전략 (How to Collaborate)

여러 명이 독립된 기능을 동시에 개발할 때 Git 충돌(Merge Conflict)을 피하고 코드의 일관성을 유지하는 원칙입니다.

### ① API 버전(`v1`)은 그대로 유지
* **버전 분리(`v1`, `v2`, `v3`)**: API 버전은 릴리즈 배포 후 기존 계약을 깨트리는 큰 변경(Breaking Change)이 생겼을 때만 나누어 적용합니다.
* **폴더 단위 분리**: 3명의 팀원이 각 도메인을 맡아 개발할 때는 동일한 `v1` 스코프 내부에서 **기능(도메인) 폴더 단위로 영역을 분할**해 작업합니다.

### ② 도메인별 작업 분담 방식 (예시)
각자가 맡은 학술 도메인을 아래의 규칙에 따라 독립된 폴더 내 파일들로 구현합니다.

* **[승현: 생명공학 bio 전담]**
  - **도메인**: 생명공학 (Kaggle/arXiv에서 생명공학 카테고리 논문 데이터를 직접 추출 및 적재)
  - **폴더 경로**: `backend/api/v1/bio/` 생성
  - **엔드포인트**: `backend/api/v1/bio/endpoints.py` (HTTP 바인딩 및 라우팅)
  - **서비스**: `backend/api/v1/bio/services.py` (비즈니스 쿼리 및 RAG 연산)
  - **스키마(DTO)**: `backend/api/v1/bio/models.py` (`BaseDTO` 상속)
* **[지환: 컴퓨터 과학 cs 전담]**
  - **도메인**: 컴퓨터 과학 (Kaggle/arXiv에서 컴퓨터 과학 카테고리 논문 데이터를 직접 추출 및 적재)
  - **폴더 경로**: `backend/api/v1/cs/` 생성
  - **엔드포인트**: `backend/api/v1/cs/endpoints.py`
  - **서비스**: `backend/api/v1/cs/services.py`
  - **스키마(DTO)**: `backend/api/v1/cs/models.py`
* **[동원: 천문학 astronomy 전담]**
  - **도메인**: 천문학 (Kaggle/arXiv에서 천문학 카테고리 논문 데이터를 직접 추출 및 적재)
  - **폴더 경로**: `backend/api/v1/astronomy/` 생성
  - **엔드포인트**: `backend/api/v1/astronomy/endpoints.py`
  - **서비스**: `backend/api/v1/astronomy/services.py`
  - **스키마(DTO)**: `backend/api/v1/astronomy/models.py`

### ③ 통합 메인 라우터(`api_router.py`) 연결 규칙
도메인별 엔드포인트 작성이 완료되면, **[api_router.py](file:///c:/Repo/bist-mini-2/backend/api/v1/api_router.py)**에 각자 생성한 라우터를 포함시켜 전역 앱에 바인딩합니다.

```python
from fastapi import APIRouter
from api.v1.auth import endpoints as auth_endpoints
from api.v1.health import endpoints as health_endpoints
from api.v1.member import endpoints as member_endpoints
# 각자 개발한 도메인 엔드포인트 임포트
from api.v1.bio import endpoints as bio_endpoints
from api.v1.cs import endpoints as cs_endpoints
from api.v1.astronomy import endpoints as astronomy_endpoints

api_router = APIRouter()

# 시스템 및 공통
api_router.include_router(health_endpoints.router, tags=["System"])
api_router.include_router(auth_endpoints.router)
api_router.include_router(member_endpoints.router)

# 각자 개발한 도메인 라우터 등록
api_router.include_router(bio_endpoints.router, prefix="/similarity-search/bio", tags=["Biotechnology RAG"])
api_router.include_router(cs_endpoints.router, prefix="/similarity-search/cs", tags=["CS RAG"])
api_router.include_router(astronomy_endpoints.router, prefix="/similarity-search/astronomy", tags=["Astronomy RAG"])
```

---

## 🛠️ 3. 반드시 지켜야 할 핵심 코딩 룰셋 및 체크리스트 (Core Coding Rules)

프로젝트 상세 컨벤션 가이드와 검증 규칙은 루트의 **[백엔드 개발 체크리스트](file:///c:/Repo/bist-mini-2/backend-checklist.md)** 및 **[프론트엔드 개발 체크리스트](file:///c:/Repo/bist-mini-2/frontend-checklist.md)**에 상세히 명세되어 있습니다. 개발자는 다음 핵심 가이드라인을 반드시 준수해야 합니다.

### ⚙️ 백엔드 (Backend Rules)
* **Rule 1: 엔드포인트 내 비즈니스 로직 작성 및 예외 발생 금지**
  - 엔드포인트 함수(`endpoints.py`) 내에 데이터베이스 쿼리를 직접 작성하거나, 토큰을 직접 가공하거나, `raise HTTPException(...)`을 실행하지 마십시오.
  - 모든 비즈니스 규칙 처리, 데이터 가공 및 예외(raise) 던지기는 서비스 클래스(`services.py`) 안에서 처리되어야 합니다.
* **Rule 2: 전역 공통 성공/실패 응답 래핑 강제**
  - 모든 API 응답은 프론트엔드 파싱 일관성을 보장하기 위해 전역 규격을 따라야 합니다.
  - **성공 응답**: `{"status": "success", "data": ...}` ➡️ 응답 스키마는 `SuccessResponse`를 상속받은 래퍼 클래스를 만들어 제어합니다.
  - **실패 응답**: `{"status": "error", "message": "에러 내용"}` ➡️ 엔드포인트나 서비스에서 정상적으로 `HTTPException` 등을 발생시키면, [exception_handler.py](file:///c:/Repo/bist-mini-2/backend/api/common/exception_handler.py) 전역 처리기가 자동으로 규격화하여 응답합니다.
* **Rule 3: Pydantic DTO 분리 및 BaseDTO 상속**
  - 모든 Pydantic 모델(DTO)은 엔드포인트 내부에 작성할 수 없으며, 반드시 각 기능/도메인 폴더 내 `models.py`로 분리해야 합니다.
  - 모델 정의 시 `BaseModel`이 아닌, `from_attributes=True`가 주입된 **`BaseDTO`**를 상속하십시오.
* **Rule 4: 한국어 Google 스타일 Docstring 적용**
  - 신규 작성하는 모든 클래스, 함수, 모듈 아래에는 아키텍처 문서화와 Sphinx 연동을 위해 표준 Google Style로 작성된 한국어 Docstring을 필수 명세해야 합니다.

### 🌐 프론트엔드 (Frontend Rules)
* **Rule 1: JavaScript 사용 (TypeScript 금지)**
  - 모든 컴포넌트와 모듈은 파일 확장자 `.js` 및 `.jsx` 규격을 유지합니다.
* **Rule 2: 이모지 사용 금지 및 Bootstrap Icons 강제**
  - UI 상의 시각적 데코레이션에 텍스트 이모티콘(⚙️, 🔑 등)의 직접적인 혼용을 엄격히 금지합니다.
  - 반드시 **Bootstrap Icons** 클래스(`<i className="bi bi-gear"></i>`)를 사용하십시오.
* **Rule 3: Axios 전용 인스턴스 (`apiClient`) 활용**
  - 전역 `axios` 기본값을 직접 변조하는 것은 금지되며, `src/apis/axiosConfig.js`에 선언된 `apiClient` 인스턴스를 임포트하여 사용해야 합니다.
* **Rule 4: 인라인 CSS 배제**
  - HTML 태그 내부에 인라인 스타일(`style={{...}}`)을 선언하지 마십시오. 스타일링은 Vanilla CSS 모듈이나 Bootstrap 5 유틸리티 클래스를 우선적으로 사용해야 합니다.

---

기타 추가적인 질문이나 협업 프로세스는 팀의 리드 개발자 혹은 소통 채널을 이용해 주십시오!
수고하셨습니다. 즐거운 개발 되세요! 🚀
