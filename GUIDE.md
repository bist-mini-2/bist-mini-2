# 🚀 공동 작업 및 아키텍처 가이드 (GUIDE.md)

본 문서는 **'논문 AI 에이전트 채팅 플랫폼 (Paper Agent Chat Platform)'** 프로젝트 백엔드 팀에 합류하신 신규 개발자분들이 빠르고 일관되게 협업하실 수 있도록 작성된 아키텍처 및 작업 가이드라인입니다.

---

## 📂 1. 백엔드 폴더 구조 (Directory Structure)

본 프로젝트는 클린 아키텍처와 관심사 분리(SoC)를 준수하며, 개발자 간의 간섭을 최소화하고 코드 응집도를 극대화하기 위해 **기능 중심(Feature-based / Vertical Slice) 폴더 구조**를 채택하고 있습니다.

```directory
api/
├── common/                # [전역 공통 인프라] 버전에 무관한 백엔드 공통 설정
│   ├── auth.py            # JWT 토큰 생성, 인증 데코레이터 및 FastAPI 디펜던시
│   ├── config.py          # Pydantic-Settings 기반 환경 변수 및 전역 설정 (Settings)
│   └── exception_handler.py # 전역 에러 핸들러 및 응답 규격화
│
├── database/              # [데이터베이스 공통] DB 접속 정보 및 엔진 설정
│   └── config/
│       ├── dto_base.py    # 공통 BaseDTO 및 Success/ErrorResponse 스키마 정의
│       ├── dbsession.py   # 비동기 DB 엔진, 세션 메이커 및 의존성 주입 (OrmSessionDep)
│       └── entity_base.py # SQLAlchemy DeclarativeBase 상속 베이스 클래스 (Base)
│
└── v1/                    # API v1 (하위 호환성 유지 구간)
    ├── api_router.py      # v1 하위의 모든 기능별 router들을 통합 취합하는 메인 라우터
    │
    ├── auth/              # 🔐 [기능 패키지: 인증 및 회원]
    │   ├── endpoints.py   # HTTP 라우팅 및 요청/응답 검증만 처리 (Business Logic 작성 금지)
    │   ├── service.py     # 회원가입, 인증 비즈니스 로직 및 해싱 처리 담당
    │   ├── schemas.py     # 회원가입 및 로그인에 쓰이는 Pydantic DTO 정의
    │   ├── entities.py    # member 테이블과 매핑되는 SQLAlchemy ORM 엔티티
    │   └── dao.py         # member 테이블에 직접 접근하는 CRUD 메소드 캡슐화 (DAO)
    │
    ├── medical/           # 🧬 [기능 패키지: 의학/바이오 NFCorpus RAG] (개발자 A 전담)
    │   ├── endpoints.py
    │   ├── service.py
    │   └── schemas.py
    │
    ├── cs/                # 💻 [기능 패키지: 컴퓨터 과학 SCIDOCS RAG] (개발자 B 전담)
    │   ├── endpoints.py
    │   ├── service.py
    │   └── schemas.py
    │
    └── science/           # 🧪 [기능 패키지: 자연 과학 SciFact RAG] (개발자 C 전담)
        ├── endpoints.py
        ├── service.py
        └── schemas.py
```

---

## 🤝 2. 3인 공동 개발 및 임무 분담 전략 (How to Collaborate)

여러 명이 독립된 기능을 동시에 개발할 때 Git 충돌(Merge Conflict)을 피하고 코드의 일관성을 유지하는 원칙입니다.

### ① API 버전(`v1`)은 그대로 유지

* **버전 분리(`v1`, `v2`, `v3`)**: API 버전은 릴리즈 배포 후 기존 계약을 깨트리는 큰 변경(Breaking Change)이 생겼을 때만 나누어 적용합니다.
* **기능별 폴더(Feature Domain) 분리**: 3명의 팀원이 각 도메인을 개발할 때는 동일한 `v1` 스코프 내부에서 **기능별 폴더 단위로 분할**해 독립적으로 작업합니다.

### ② 도메인별 작업 분담 방식

각자가 맡은 학술 도메인을 아래의 규칙에 따라 전용 폴더 및 파일 쌍으로 구현합니다.

* **[개발자 A: 의학/바이오 NFCorpus 전담]**
  * 폴더 생성: `api/v1/medical/`
  * 구현 파일: `endpoints.py`, `service.py`, `schemas.py`
* **[개발자 B: 컴퓨터 과학 SCIDOCS 전담]**
  * 폴더 생성: `api/v1/cs/`
  * 구현 파일: `endpoints.py`, `service.py`, `schemas.py`
* **[개발자 C: 자연 과학 SciFact 전담]**
  * 폴더 생성: `api/v1/science/`
  * 구현 파일: `endpoints.py`, `service.py`, `schemas.py`

### ③ 통합 메인 라우터(`api_router.py`) 연결 규칙

도메인별 기능 작성이 완료되면, **[api_router.py](file:///d:/Repo/bist-mini-2-backend/api/v1/api_router.py)**에 각자 생성한 기능 라우터를 포함시켜 전역 앱에 바인딩합니다.

```python
from fastapi import APIRouter
from api.v1.endpoints import health
from api.v1.auth.endpoints import router as auth_router
from api.v1.medical.endpoints import router as medical_router
from api.v1.cs.endpoints import router as cs_router
from api.v1.science.endpoints import router as science_router

api_router = APIRouter()

# 시스템 및 공통
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth_router)

# 각자 개발한 도메인 라우터 등록
api_router.include_router(medical_router, prefix="/similarity-search/medical", tags=["Medical RAG"])
api_router.include_router(cs_router, prefix="/similarity-search/cs", tags=["CS RAG"])
api_router.include_router(science_router, prefix="/similarity-search/science", tags=["Science RAG"])
```

---

## 🛠️ 3. 반드시 지켜야 할 4대 핵심 코딩 룰셋 (Core Coding Rules)

프로젝트 루트의 [CONVENTIONS.md](file:///d:/Repo/bist-mini-2-backend/CONVENTIONS.md)에 상세 명세가 기술되어 있습니다. 신규 개발자는 다음 4가지를 반드시 준수해야 합니다.

### Rule 1: 엔드포인트 내 비즈니스 로직 작성 및 예외 발생 금지

- 엔드포인트 파일(`endpoints.py`) 내에 데이터베이스 쿼리를 직접 작성하거나, 토큰을 직접 가공하거나, `raise HTTPException(...)`을 실행하지 마십시오.
* 모든 비즈니스 규칙 처리, 데이터 가공 및 예외(raise) 던지기는 서비스 클래스(`service.py`) 안에서 처리되어야 합니다.

### Rule 2: 전역 공통 성공/실패 응답 래핑 강제

- 모든 API 응답은 프론트엔드 파싱 일관성을 보장하기 위해 전역 규격을 따라야 합니다.
* **성공 응답**: `{"status": "success", "data": ...}` ➡️ 응답 스키마는 `SuccessResponse`를 상속받은 래퍼 클래스를 만들어 제어합니다.
* **실패 응답**: `{"status": "error", "message": "에러 내용"}` ➡️ 엔드포인트나 서비스에서 정상적으로 `HTTPException` 등을 발생시키면, [exception_handler.py](file:///d:/Repo/bist-mini-2-backend/api/common/exception_handler.py) 전역 처리기가 자동으로 규격화하여 응답합니다.

### Rule 3: Pydantic DTO 분리 및 BaseDTO 상속

- 모든 Pydantic 모델(DTO)은 엔드포인트 내부에 작성할 수 없으며, 반드시 `schemas.py` 단독 파일 내에 분리하여 작성합니다.
* DTO 모델 정의 시 `BaseModel`이 아닌, `from_attributes=True`가 주입된 **`BaseDTO`**를 상속하십시오.

### Rule 4: 한국어 Google 스타일 Docstring 적용

- 신규 작성하는 모든 클래스, 함수, 모듈 아래에는 아키텍처 문서화와 Sphinx 연동을 위해 표준 Google Style로 작성된 한국어 Docstring을 필수 명세해야 합니다.

---

기타 추가적인 질문이나 협업 프로세스는 팀의 리드 개발자 혹은 소통 채널을 이용해 주십시오!
수고하셨습니다. 즐거운 개발 되세요! 🚀
