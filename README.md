# 🚀 Paper Agent: 지능형 학술 검색 및 융합 R&D 지원 플랫폼

[![Live Demo on GitHub Pages](https://img.shields.io/badge/Demo-GitHub_Pages-blue?style=for-the-badge&logo=github)](https://bist-mini-2.github.io/bist-mini-2/)

**Paper Agent**는 대규모 학술 메타데이터 아카이브와 실시간 외부 웹 지식을 병렬 비동기로 교차 분석하여, 연구자의 학술적 공백(Research Gap) 추론과 맞춤형 R&D 지식 탐색을 지원하는 지능형 연구 비서 플랫폼입니다.

---

## 🎥 플랫폼 데모 프리뷰 (Demo Preview)

### 1. 실시간 RAG 일반 채팅 허브 (Parallel RAG & SSE Streaming)
사용자 질문에 대해 학술 pgvector DB(HNSW) 세만틱 스캔과 외부 웹 검색을 비동기 병렬로 동시 수행하여, 실시간 교차 융합된 지식 컨텍스트를 마크다운 토큰 스트리밍 형태로 전달합니다.

![Chat Hub Demo](docs/deliverables/final/demo_feature1.gif)

### 2. 비동기 배치 대규모 문헌 비교 및 공백(Research Gap) 분석기
대량의 학술 문헌을 일괄 정제하여 논문별 핵심 해결과제 및 한계점(Limitations)을 추출한 뒤, 학계의 대표적인 연구 공백과 추천 미래 연구 로드맵을 자동으로 합성하여 제공합니다.

![Research Gap Demo](docs/deliverables/final/demo_feature2.gif)

### 3. 맞춤형 R&D 비서 Gem 팩토리 & 격리 스토어
연구 목적에 맞는 특정 학술 도메인 RAG와 고유 페르소나 지침(System Prompt)을 바인딩한 독립형 가상 연구 비서(Gem)를 개설하고 특화 대화를 수행할 수 있습니다.

![Gems Factory Demo](docs/deliverables/final/demo_feature3.gif?v=2)

---

## 👥 팀원 소개 및 역할 분담 (Team & Roles)

| 이름 (Name) | 담당 주요 역할 및 기능 개발 (Key Contributions) | GitHub |
| :--- | :--- | :--- |
| **김지환** | 컴퓨터 과학 분야 RAG 파이프라인 구현 및 대규모 문헌 분석 기능 개발 | [@pileuszu](https://github.com/pileuszu) |
| **신동원** | 천문학 분야 RAG 파이프라인 구현 및 젬 팩토리 기능 개발 | [@shindw2001](https://github.com/shindw2001) |
| **천승현** | 생명공학 분야 RAG 파이프라인 구현 및 채팅 허브 기능 개발 | [@kennedy0919](https://github.com/kennedy0919) |

---

## 📂 디렉토리 구조 (Directory Structure)

```directory
bist-mini-2/
├── backend/                   # FastAPI 비동기 백엔드 서버
│   ├── api/
│   │   ├── common/            # 병렬 RAG 검색 파이프라인 (rag_pipeline.py) 및 DTO
│   │   ├── database/          # PostgreSQL 비동기 세션 구성 및 체크포인터
│   │   └── v1/                # 도메인별 API 및 서비스/핸들러/툴 격리
│   ├── static/                # 정적 에셋 (No-cache Static Files)
│   └── main.py                # 백엔드 실행 엔트리포인트
│
├── frontend/                  # Next.js 16 (App Router) 프론트엔드 서비스
│   ├── src/
│   │   ├── apis/              # 백엔드 연동 API 및 로컬 Mocking 서비스 (mockService.js)
│   │   ├── app/               # Next.js 페이지 라우터 (join, login, feature1~4)
│   │   └── contexts/          # 전역 상태 관리 Context (Auth, Notification)
│   └── next.config.mjs        # Next.js 빌드 및 GitHub Pages 배포 설정
│
├── docs/                      # 설계 사양서 및 프로젝트 산출물
│   └── deliverables/
│       ├── final/             # 최종 완성 통합 산출물 (wrap_up_report.pdf, 데모 GIF들)
│       └── 4th/               # 4차 기획/설계 상세 마크다운 문서들
│           └── images/        # 문서들에 삽입된 PNG 다이어그램 에셋 격리 폴더
│
└── scripts/                   # 추가 적재 멱등 배치 스크립트 및 데모 GIF 생성기
```

---

## 💻 설치 및 실행 방법 (Getting Started)

### ① 데이터베이스 및 환경 설정
* PostgreSQL 17에 pgvector 확장을 설치하고 활성화합니다.
* `backend/.env.example` 파일을 복사하여 `backend/.env`를 생성하고 OpenAI API Key 및 데이터베이스 URL을 수정합니다.

### ② 백엔드 (FastAPI) 구동
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### ③ 프론트엔드 (Next.js) 구동
```bash
cd frontend
npm install
npm run dev
```
브라우저에서 `http://localhost:3000`에 접속하여 기능을 확인합니다. 만약 백엔드 없이 목업 데이터로만 테스트하고 싶으시다면 `http://localhost:3000/bist-mini-2/?mock=true`로 접속해 주십시오.

---

## 🛠️ 개발자 자동화 도구 및 상세 문서 바로가기

* 🎥 [데모 GIF 자동 생성 가이드 (AUTOMATED_DEMO_RECORDER.md)](AUTOMATED_DEMO_RECORDER.md) - 로컬 환경에서 1080p 고화질 데모 영상을 자동으로 녹화하고 GIF 프레임을 빌드하는 절차가 정리되어 있습니다.
* 📄 [프로젝트 최종 완료 보고서 (docs/deliverables/final/wrap_up_report.pdf)](docs/deliverables/final/wrap_up_report.pdf) - 아키텍처 다이어그램, pgvector 성능 벤치마크 및 종합 개발 성과 보고서의 완전본입니다.
* 🚀 [공동 작업 및 아키텍처 가이드 (GUIDE.md)](GUIDE.md) - 모노레포 구조 규칙 및 백엔드/프론트엔드 전반의 아키텍처 가이드라인이 정리되어 있습니다.
* ⚙️ [백엔드 개발 체크리스트 (backend-checklist.md)](backend-checklist.md) - API 예외 처리, 의존성 주입 패턴 및 SQLAlchemy asyncpg 규격에 관한 개발 규칙 체크리스트입니다.
* 🌐 [프론트엔드 개발 체크리스트 (frontend-checklist.md)](frontend-checklist.md) - Next.js App Router, Axios 통신 규격 및 Bootstrap 5 레이아웃 컨벤션 체크리스트입니다.
* 📊 [MTEB 정보 검색 및 데이터셋 분석 명세서 (docs/mteb_domains.md)](docs/mteb_domains.md) - Bio-Medical(Bio), Computer Science(CS), Astronomy(천문학) 학술 도메인별 벤치마크 명세서입니다.
