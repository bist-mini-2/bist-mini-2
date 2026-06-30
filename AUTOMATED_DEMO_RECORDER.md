# 🎥 Automated Demo GIF Generation Guide

본 플랫폼에는 로컬 터미널 환경에서 마우스 클릭 및 타이핑 인터랙션을 자동으로 시뮬레이션하고, 1920x1080 고해상도로 화면을 녹화한 뒤 고화질 홍보용 데모 GIF를 즉시 추출해 주는 자동화 스크립트가 내장되어 있습니다.

---

## ⚙️ 사전 요구 사항 (Prerequisites)

1. **Playwright** 설치: 브라우저 동작 자동화 시뮬레이션 및 영상 녹화를 위해 필요합니다.
   ```bash
   npm install -g playwright
   npx playwright install chromium
   ```
2. **FFmpeg** 설치: 녹화된 WebM 비디오 파일을 고화질 GIF로 최적화 변환하기 위해 필요합니다. (프로젝트 내부 `@ffmpeg-installer/ffmpeg`가 내장되어 있어 별도 설치 없이도 즉시 구동 가능합니다)
3. **로컬 백엔드 서버 구동**: 본 자동화 도구는 실제 백엔드 API와의 실시간 데이터 통신을 시뮬레이션하므로, 로컬 백엔드가 실행 중이어야 합니다 (`http://localhost:8000` 활성화 상태).

---

## 🚀 자동 녹화 및 GIF 생성 절차

1. **프론트엔드 최적화 빌드 추출**
   정적 빌드를 통해 Next.js 개발자 오류 오버레이(Dev Overlay Indicator)가 화면 녹화본에 간섭하는 현상을 완벽히 차단합니다.
   ```bash
   cd frontend
   npm run build
   ```

2. **로컬 정적 파일 서버 구동 (포트 3001)**
   Next.js 정적 빌드 산출물(`out/`)을 BasePath 경로 구조에 맞춰 포트 `3001`로 호스팅합니다.
   ```bash
   # 프로젝트 루트 폴더 기준 실행
   mkdir -p frontend/dist && ln -sf ../out frontend/dist/bist-mini-2
   cd frontend/dist
   python3 -m http.server 3001
   ```

3. **자동화 스크립트 실행**
   터미널 세션을 하나 더 열어 프로젝트 루트 폴더에서 아래 자동화 스크립트를 실행합니다:
   ```bash
   node scripts/generate_demo_gif.js
   ```

---

## 🎬 자동화 시나리오 내부 동작 흐름

스크립트 실행 시 로봇이 아래 단계를 스스로 100% 자율 주행하며 녹화합니다:

1. **신규 계정 회원가입 & 로그인**
   - `/join.html`로 진입해 임의의 고유 타임스탬프 계정을 발급받아 가입 처리를 마친 뒤, `/login.html`에서 실제 백엔드 JWT 인증 토큰을 발급받아 세션을 수립합니다.
2. **Feature 1 - Chat Hub (실시간 RAG 일반 챗)**
   - 대화방 진입 후 pgvector HNSW 최적화 성능과 관련된 학술 검색 질의를 타이핑하고 전송한 뒤, 실시간 마크다운 SSE 토큰 스트리밍 출력을 녹화합니다.
3. **Feature 2 - Research Gap Analyzer (비동기 비교 분석)**
   - 분석 중점 키워드를 기입하고 비동기 분석을 제출합니다. 백엔드에서 Celery/비동기 태스크 연산이 완료되어 결과 매트릭스(Matrix Table)와 미래 로드맵 카드가 화면에 자동으로 펼쳐질 때까지 동적 대기(Polled Wait)합니다.
4. **Feature 3 - Gems Factory (커스텀 젬 생성 및 특화 채팅)**
   - NASA 우주론 특화 젬을 새로 생성(이름, 요청사항, 천문학 데이터 소스 체크)하여 젬 팩토리에 적재한 뒤, 해당 젬의 전용 대화 공간에 들어가 문답을 교환합니다.
5. **GIF 컴파일링**
   - 시나리오 종료 즉시 FFmpeg 팔레트 빌드 및 란초스(Lanczos) 필터 보간법을 적용해 1920x1080 뷰포트 비율을 유지한 고화질 GIF 파일들로 컴파일하여 `docs/deliverables/final/demo_feature[1/2/3].gif` 경로로 덮어씁니다.

---

## 🔗 바로가기 링크 (Shortcuts)

* [⬅️ 플랫폼 메인 소개서로 돌아가기 (README.md)](README.md)
* [📄 프로젝트 최종 보고서 열기 (docs/deliverables/final/wrap_up_report.pdf)](docs/deliverables/final/wrap_up_report.pdf)
* [🚀 공동 작업 및 아키텍처 가이드 (GUIDE.md)](GUIDE.md)
* [⚙️ 백엔드 개발 체크리스트 (backend-checklist.md)](backend-checklist.md)
* [🌐 프론트엔드 개발 체크리스트 (frontend-checklist.md)](frontend-checklist.md)
* [📊 MTEB 정보 검색 및 데이터셋 분석 명세서 (docs/mteb_domains.md)](docs/mteb_domains.md)
