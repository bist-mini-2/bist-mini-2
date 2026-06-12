# 🌐 프론트엔드 개발 체크리스트 (Frontend Development Checklist)

본 체크리스트는 Next.js 16 (App Router), React 19, Bootstrap 5, Axios 기반 프론트엔드 서비스 개발 시 준수해야 하는 코딩 가이드라인 및 검증 규칙입니다. 모든 프론트엔드 수정 PR은 아래 항목을 통과해야 합니다.

---

## 1. 기술 스택 제약 사항 (Technical Stack Constraints)
- [ ] **JavaScript 사용 (TypeScript 금지)**: 전체 코드베이스는 반드시 **JavaScript**(`.js`, `.jsx`, `.mjs`)로 작성되어야 하며, 경로 설정 및 alias 매핑을 위해 `jsconfig.json`을 사용합니까?
- [ ] **Vanilla CSS 및 Bootstrap 5 사용 (Tailwind CSS 금지)**: UI 스타일링을 위해 **Vanilla CSS**와 **Bootstrap 5**만을 사용해야 합니다. 명시적 요청이 없는 한 Tailwind CSS 클래스 및 설정 파일 사용은 금지됩니다.
- [ ] **Axios를 통한 API 요청**: 백엔드와의 모든 비동기 API 통신은 Axios를 사용하며, 관련 통신 모듈은 `src/apis/` 디렉토리에 잘 분리되어 있습니까?

## 2. Next.js App Router 구조 (Next.js App Router Structure)
- [ ] **라우팅 구조**: 모든 페이지 구성이 Next.js App Router 규격에 따라 `src/app/` 하위 폴더 구조로 설계되어 있습니까?
  - 동적 세그먼트 파라미터는 `[param]` 폴더 명을 올바르게 사용하고 있는지 확인하십시오.
- [ ] **서버 및 클라이언트 컴포넌트 분리**:
  - 기본적으로 모든 컴포넌트는 Server Component로 유지됩니다.
  - React 훅(`useState`, `useEffect`, `useContext` 등)이 필요한 파일에만 상단에 `"use client"` 지시어를 사용했습니까?

## 3. 스타일링 및 Bootstrap 통합 (Styling & Bootstrap Integration)
- [ ] **Bootstrap 클라이언트 컴포넌트 로드**: 루트 `layout.js`에 `BootstrapClient.js` 래퍼 컴포넌트가 적절하게 마운트되어 있습니까?
  - 이를 통해 Bootstrap CSS 스타일 및 JS 번들 스크립트가 클라이언트 단에서 정상 작동되도록 제어해야 합니다.
- [ ] **Bootstrap 유틸리티 클래스 활용**: 페이지 레이아웃 구조화 및 컴포넌트 디자인 시 Bootstrap의 표준 스타일 클래스(`container`, `row`, `col-*`, `d-flex`, `justify-content-*`, `align-items-*`, `shadow`, `border-0`, `rounded-*` 등)를 적극적으로 활용하고 있습니까?
- [ ] **커스텀 스타일 가이드**: 추가 커스텀 스타일이 필요할 경우, `src/app/globals.css` 또는 모듈형 CSS 스타일시트(`*.module.css`)에만 추가해 구현했습니까?

## 4. 상태 관리 및 Context API (State Management & Context API)
- [ ] **Context API를 통한 전역 상태 관리**: 사용자 인증 정보나 시스템 설정과 같이 여러 컴포넌트에서 공유되어야 하는 상태 정보들은 React **Context API**를 구현해 관리합니까?
  - 생성된 컨텍스트 관련 파일은 `src/contexts/` 폴더 내에 정의되어야 합니다.
  - 컨텍스트 프로바이더(예: `AuthContextProvider`, `ColorContextProvider`)는 필요한 하위 컴포넌트 트리(주로 `layout.js` 단)를 감싸도록 설정되었습니까?

## 5. 협업 및 커밋 컨벤션 (Collaboration & Commit Conventions)
- [ ] **브랜치 전략**: `main` 브랜치가 아닌, 개별 기능 작업을 위한 브랜치(`feature/`, `fix/`, `refactor/`, `design/`, `docs/` 등)를 생성해 작업하고 있습니까?
- [ ] **커밋 메시지 규칙**: 모든 커밋 메시지가 Conventional Commits 형식을 준수하고 있습니까?
  - `feat`: 새로운 기능 추가
  - `fix`: 버그 수정
  - `design`: UI 및 스타일 변경 작업
  - `docs`: 문서 변경 및 생성
  - `refactor`: 구조적인 개선 (기능 변화가 없는 경우)
- [ ] **PR 전 셀프 리뷰**: PR 생성 전 변경 사항 중 임시로 작성한 디버깅 로그(`console.log` 등)나 불필요한 주석이 남아있지 않은지 검토했습니까?
