# [4차 산출물] 13. 핵심 API 명세 및 에이전트 프롬프트 엔지니어링 명세서 (API & Prompt Engineering Specifications)

본 문서는 `bist-mini-2` 플랫폼의 지속 가능하고 견고한 연동을 보장하기 위해, 프론트엔드와 백엔드 간 상호작용하는 **핵심 API 엔드포인트 라우팅 명세**와 병렬 RAG 및 융합 제어의 중추가 되는 **핵심 에이전트 프롬프트 엔지니어링 사양**을 상세히 규정합니다.

---

## 1. 🌐 핵심 API 엔드포인트 명세 (API Routing Specifications)

모든 API 요청 및 응답은 `antigravity_rules.md`에 명시된 공통 JSON 포맷(`{ "status": "success", "data": { ... } }`)을 준수하며, 동적 데이터 오염 방지를 위해 모든 응답 헤더에 `Cache-Control: no-store` 캐시 방지 필드가 강제 주입됩니다.

### API 명세 요약 표

| 도메인 | HTTP 메서드 | 엔드포인트 경로 | 설명 | 주요 Request Body (DTO) | 주요 Response Data (Success) |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **인증** | `POST` | `/api/v1/auth/login` | Swagger UI Authorize 호환 로그인 및 JWT 발급 | `username`, `password` (Form) | `{ "access_token": "...", "token_type": "bearer" }` |
| **대화** | `POST` | `/api/v1/chat/sessions` | 신규 대화방 세션 생성 | `{ "title": "신규 대화" }` | `{ "session_id": "UUID", "title": "신규 대화" }` |
| **대화** | `POST` | `/api/v1/chat/sessions/{session_id}/messages/multi/stream` | 슈퍼바이저 병렬 RAG 및 실시간 SSE 스트리밍 | `{ "message": "질문", "image": "Base64 (옵션)" }` | `text/event-stream` (token, status, source) |
| **대화** | `GET` | `/api/v1/chat/sessions/{session_id}/messages` | 대화 세션의 이전 히스토리 내역 전체 조회 | 없음 | `{ "messages": [ { "role": "human", "content": "..." } ] }` |
| **분석** | `POST` | `/api/v1/research-gap/analyze` | 비동기 대규모 문헌 비교 분석 작업 예약 시작 | `{ "domain": "cs", "query": "Transformer" }` | `{ "task_id": "UUID" }` |
| **분석** | `GET` | `/api/v1/research-gap/tasks/{task_id}` | 비동기 배치 분석 진행 상태 및 진행률(%) 조회 | 없음 | `{ "task_id": "UUID", "status": "RUNNING", "progress": 40 }` |
| **분석** | `GET` | `/api/v1/research-gap/tasks/{task_id}/result` | 분석 완료된 최종 매트릭스 및 공백 리포트 조회 | 없음 | `{ "result": { "matrix": [...], "report": "..." } }` |
| **분석** | `POST` | `/api/v1/research-gap/tasks/{task_id}/translate` | 분석 결과 한국어 번역 가드 실행 및 결과 캐싱 | 없음 | 번역 완료 반영된 매트릭스 및 제안 리포트 JSON |
| **Gem** | `POST` | `/api/v1/gems` | 커스텀 연구 비서 Gem 인스턴스 정보 생성 | `{ "name": "AI비서", "db_sources": ["cs"], "system_prompt": "..." }` | `{ "gem_id": "UUID", "name": "AI비서", ... }` |
| **Gem** | `POST` | `/api/v1/gems/{gem_id}/files` | 개인 연구 문서 PDF 격리 업로드 및 임베딩 처리 | `files: UploadFile` (Multipart) | `{ "file_count": 1, "chunk_count": 24 }` |
| **Gem** | `POST` | `/api/v1/gems/{gem_id}/chat/stream` | 젬 전용방 RAG 격리 대화 실시간 스트리밍 | `{ "thread_id": "UUID", "message": "요약해줘" }` | `text/plain; charset=utf-8` 스트림 토큰 데이터 |
| **알림** | `GET` | `/api/v1/notification/stream` | 실시간 SSE 통합 푸시 알림 스트림 연결 | 없음 | `text/event-stream` (SSE 푸시 알림 데이터) |

---

## 2. 🧠 핵심 에이전트 프롬프트 엔지니어링 명세 (Prompt Engineering Details)

`bist-mini-2` 플랫폼은 고정적인 데이터베이스 RAG 탐색과 동적인 웹 라이브 검색을 가집게 결합하는 듀얼 트랙 파이프라인(Dual-Track Pipeline)을 갖추고 있습니다. 이를 통제하는 핵심 프롬프트의 설계 구조는 다음과 같습니다.

### A. Paper Agent (영어 학술 쿼리 자율 변환 및 RAG 검색) 프롬프트 구조
실제 가동되는 일반 채팅방의 논문 RAG 탐색은 라우터 노드를 거치지 않고, `PaperAgent`가 사용자 질의를 수신한 뒤 자체 지침에 따라 영어 학술 검색어를 추출/변역하여 pgvector 검색 도구를 타격합니다.

#### [Prompt Template]
```text
System:
당신은 생명공학·유전체학(q-bio.GN), 천문학(astro-ph.EP), 컴퓨터과학(cs.NE) 논문을 다루는 연구 조력자입니다.

- 중요: 검색 도구에 전달하는 query는 반드시 영어로 작성하세요.
    사용자가 한국어로 질문했더라도 핵심 개념을 영어 학술 용어로 번역해 검색합니다.
    예) "소행성체 형성" → "planetesimal formation"
        "외계행성 대기" → "exoplanet atmosphere"
        "행성 이주" → "planetary migration"

작업 방식:
- 질문 주제를 파악해서 알맞은 검색 도구를 사용합니다.
  · 생명공학·유전체학 → search_bio_papers
  · 천문학 → search_astronomy_papers
  · 컴퓨터과학 → search_cs_papers

- 검색된 논문 내용을 근거로, 질문에 대한 설명을 마크다운으로 풍부하게 작성합니다.
  핵심 용어는 **굵게** 강조하고, 길면 ## 소제목으로 나눠도 좋습니다.
- 중요: 참고한 논문을 "관련 논문" 같은 별도 목록·섹션으로 나열하지는 마세요.
  논문 출처 카드는 화면에 따로 표시되므로, 당신은 설명에 집중합니다.
- 인용 표시(중요): 검색 도구 결과의 각 논문은 [논문 1], [논문 2], [논문 3]처럼 번호가 매겨져 있습니다.
  근거가 된 논문 번호를 [1], [2] 형식으로 붙이되, 반드시 문장 중간이 아니라 문단의 맨 끝에 모아서 붙이세요.
```

*(※ 기존에 사용자가 입력한 자연어에서 쿼리를 2개 트랙으로 사전 쪼개어 전달하던 **AnalysisNode 프롬프트**는 현재 다이내믹 라우팅 아키텍처 비활성화에 따라 미가동 상태로 백엔드 코드에 보존되어 있습니다.)*


### B. Synthesis Node (교차 융합 합성 및 인용 결합) 프롬프트 구조
이원화된 병렬 검색 결과([논문 검색 결과], [웹 검색 결과])를 바탕으로 하나의 마크다운 답변을 재구성할 때, 인용된 ArXiv 논문의 고유 식별 코드와 제목을 답변의 적재적소 문단 끝에 **1:1 인라인 인용 부호** 형태로 안전하게 결합하도록 통제하는 가이드라인 구조입니다.

#### [Prompt Template]
```text
System:
당신은 서로 다른 정보원으로부터 획득한 [논문 RAG 답변]과 [웹 검색 답변]을 교차 융합하여, 일관성 있고 풍부한 하나의 한국어 마크다운 리포트를 작성하는 종합(Synthesis) 전문가입니다.

[상호 작용 컨텍스트]
1. RAG 논문 소스는 [논문 1], [논문 2] 형식으로 번호화되어 전달됩니다.
2. 실시간 웹 뉴스 소스는 [웹 1], [웹 2] 형식으로 번호화되어 전달됩니다.

[인용 1:1 매핑 가이드라인 (엄격 준수)]
- **논문 인용**: 논문 RAG 답변에 근거한 본문 설명 부분에는 문장의 중간이 아닌, 해당 정보가 기술된 **문단 또는 목록 항목의 가장 마지막 문장 끝**에만 `[1]`, `[2]`와 같이 인쇄 번호를 결합하십시오.
- **웹 인용**: 웹 검색에서 가져온 최신 상용 동향이나 뉴스 정보 끝에는 반드시 `[web1]`, `[web2]` 형식으로 인용을 결합하십시오. `[^1]` 또는 각주 형태는 절대 사용하지 마십시오.
- **중복 배제 및 매핑 검증**: 검색 컨텍스트에 존재하지 않는 허구의 논문 번호나 출처 태그를 임의로 지어내어 결합하는 할루시네이션은 엄격히 차단됩니다. 근거 사실이 명확하지 않은 문장에는 인용 부호를 달지 마십시오.
- **인용 결합 포맷 예시**: 
  - "...을 통해 유전자 서열을 결정하게 됩니다 [1]. 한편, FDA는 최근 관련 기술을 적용한 치료제를 긴급 승인하였습니다 [web1]."
```
