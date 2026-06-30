# [4차 산출물] 11. 로컬 가동 가이드 및 API cURL 테스트 핸드북 (Quick Start & API cURL Handbook)

본 문서는 평가자나 동료 개발자가 로컬 PC 환경에서 `bist-mini-2` 플랫폼을 내려받아 백엔드(FastAPI) 및 프론트엔드(Next.js)를 즉각 기동할 수 있도록 안내하고, 핵심 기능을 HTTP cURL 요청을 통해 수동 테스트할 수 있도록 작성한 개발 안내 매뉴얼입니다.

---

## 🚀 1. 로컬 개발 환경 실행 가이드 (Quick Start)

### 📂 A. 백엔드 (FastAPI) 기동 및 DB 적재

#### 1) 파이썬 가상환경 구성 및 패키지 설치
백엔드 폴더(`backend/`)로 이동하여 가상환경을 구축하고 요구 의존성을 설치합니다.
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 패키지 설치
pip install -r backend/requirements.txt
```

#### 2) 환경 변수 설정 (.env)
백엔드 루트 디렉토리에 `.env` 파일을 생성하고 데이터베이스 연결 주소와 OpenAI API 키를 입력합니다.
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bist_db
OPENAI_API_KEY=your-openai-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here
JWT_SECRET=your-jwt-secret-key-for-auth
```

#### 3) ArXiv 논문 데이터셋 배치 적재 스크립트 실행
로컬 pgvector 인스턴스에 도메인별 106,974건의 논문을 멱등성 있게 백업 적재하는 스크립트를 구동합니다.
```bash
# CS 및 천문학 추가 적재 실행
python scripts/datasets/append_full_domain_embeddings.py

# 생명공학 추가 서브 카테고리 적재 실행
python scripts/datasets/append_bio_categories.py
```

#### 4) FastAPI 서버 가동
```bash
# Uvicorn 개발 서버 실행 (기본 8000포트)
uvicorn backend.api.main:app --reload
```

---

### 🌐 B. 프론트엔드 (Next.js & Bootstrap 5) 기동

Next.js 웹 애플리케이션 개발 서버를 띄워 백엔드와 연동합니다.
```bash
# 프론트엔드 의존성 패키지 설치
npm install

# Next.js 개발 서버 실행 (기본 3000포트)
npm run dev
```
가동 후 웹 브라우저에서 `http://localhost:3000` 주소로 접속하면 대시보드 UI에 정상 진입할 수 있습니다.

---

## 🔌 2. 핵심 API cURL 테스트 시나리오 핸드북

로컬 터미널에서 FastAPI 백엔드로 직접 API를 호출해 볼 수 있는 cURL 요청 모음집입니다.

### 🔑 1) 회원 가입 및 로그인 (Authentication)

*   **회원 가입 (POST `/auth/signup`)**:
    ```bash
    curl -X POST "http://localhost:8000/auth/signup" \
         -H "Content-Type: application/json" \
         -d '{
           "mid": "testuser1",
           "mname": "홍길동",
           "mpassword": "password123",
           "memail": "testuser1@bist.ac.kr"
         }'
    ```

*   **로그인 및 JWT 토큰 발급 (POST `/auth/login`)**:
    *   *안내*: Swagger UI 인증 및 표준 준수를 위해 플랫 JSON 형태로 토큰을 반환합니다.
    ```bash
    curl -X POST "http://localhost:8000/auth/login" \
         -H "Content-Type: application/json" \
         -d '{
           "username": "testuser1",
           "password": "password123"
         }'
    ```
    *   *반환 성공 시 얻은 `access_token` 값을 복사하여 아래의 모든 요청 헤더에 `-H "Authorization: Bearer <token>"` 형태로 첨부하여 테스트를 진행합니다.*

---

### ⚡ 2) 일반 챗 허브 (General Chat Hub) 대화 스트리밍

*   **대화방 세션 개설 (POST `/chat/sessions`)**:
    ```bash
    curl -X POST "http://localhost:8000/chat/sessions" \
         -H "Authorization: Bearer <your_jwt_token>" \
         -H "Content-Type: application/json" \
         -d '{
           "title": "신경망 최적화 세션"
         }'
    ```
    *   *출력 반환 예시*: `session_id: "8c7b827e-8c88-4228-94ef-650a256a2bbd"`

*   **병렬 RAG 및 웹 검색 융합 스트리밍 질문 송신 (POST `/chat/sessions/{id}/messages/stream`)**:
    ```bash
    curl -N -X POST "http://localhost:8000/chat/sessions/8c7b827e-8c88-4228-94ef-650a256a2bbd/messages/stream" \
         -H "Authorization: Bearer <your_jwt_token>" \
         -H "Content-Type: application/json" \
         -d '{
           "message": "인공신경망 가중치 진화와 관련 깃허브 최신 웹 동향 알려줘."
         }'
    ```
    *   `-N` 옵션은 버퍼링을 해제하여 서버가 방출하는 SSE 스트림 토큰을 한 자씩 즉시 출력해 줍니다.

---

### 📬 3) 대규모 문헌 비교 분석 (Research Gap Analyzer)

*   **비동기 배치 분석 의뢰 (POST `/research-gap/analyze`)**:
    ```bash
    curl -X POST "http://localhost:8000/research-gap/analyze" \
         -H "Authorization: Bearer <your_jwt_token>" \
         -H "Content-Type: application/json" \
         -d '{
           "domain": "cs",
           "query": "Retrieval Augmented Generation tables parsing"
         }'
    ```
    *   *출력 반환 예시*: `task_id: "gap-task-uuid-4567"`

*   **배치 처리 및 온디맨드 한글 번역 요청 (POST `/research-gap/tasks/{task_id}/translate`)**:
    ```bash
    curl -X POST "http://localhost:8000/research-gap/tasks/gap-task-uuid-4567/translate" \
         -H "Authorization: Bearer <your_jwt_token>"
    ```

---

### 🛠️ 4) 맞춤형 연구 비서 (Research Gem) 팩토리

*   **커스텀 비서 젬 개설 (POST `/gems`)**:
    ```bash
    curl -X POST "http://localhost:8000/gems" \
         -H "Authorization: Bearer <your_jwt_token>" \
         -H "Content-Type: application/json" \
         -d '{
           "name": "외계행성 기후 비서",
           "db_sources": ["astronomy"],
           "system_prompt": "당신은 행성 대기압 전문가로..."
         }'
    ```
    *   *출력 반환 예시*: `gem_id: "gem-uuid-9999"`

*   **젬 전용 개인 연구 PDF 적재 (POST `/gems/{gem_id}/upload-files`)**:
    ```bash
    curl -X POST "http://localhost:8000/gems/gem-uuid-9999/upload-files" \
         -H "Authorization: Bearer <your_jwt_token>" \
         -F "files=@/path/to/your/research_note.pdf"
    ```
