📅** 이번 주 학습 현황 (완료했을경우 ‘○’ 표시)**
<table>
<tr>
<td>**월요일**</td>
<td>**화요일**</td>
<td>**수요일**</td>
<td>**목요일**</td>
<td>**금요일**</td>
</tr>
<tr>
<td>\[ **○ **\] 완료</td>
<td>\[ **○ **\] 완료</td>
<td>\[ **○ **\] 완료</td>
<td>\[ **○ **\] 완료</td>
<td>\[ **○ **\] 완료</td>
</tr>
</table>
<details>
<summary>**월요일 : \\[백엔드 비동기(Async) 리팩토링 및 5대 코어 Jupyter Notebook 튜토리얼 아키텍처 재구성\\]**</summary>
	<callout icon="💡" color="gray_bg">
		- **학습 내용:**
			- CPU 바운드 `bcrypt` 해싱 작업(`hashpw`, `checkpw`) 및 디스크 I/O 작업을 `asyncio.to_thread`를 사용하여 별도 스레드 풀로 오프로딩하는 이벤트 루프 블로킹 개선
			- 동기식 `subprocess`를 비동기식 `asyncio.create_subprocess_exec`으로 전면 교체하여 Git changelog 수집 시 가동성 확보
			- 기존 10여 개의 어지러운 튜토리얼 노트북들을 5대 코어 논리 노트북 구조(`chat_service`, `embedding_ingestion`, `rag_pipeline`, `gem_service`, `defense_arena`, `research_gap`)로 통합 단일화 및 요구사항 버그 해결
			<page url="https://app.notion.com/p/38bedca29a158047a21eed772b29efa1">**RAG의 기초 및 LangGraph 멀티 에이전트 설계**</page>
	</callout>
	<callout icon="💡" color="gray_bg">
		- **해결한 에러(Troubleshooting):**
			- 동기 bcrypt 해싱 중 다중 동시 요청 시 이벤트 루프 전체가 대기 상태에 빠지는 현상 감지 -> `asyncio.to_thread` 래핑 적용으로 대기 시간 90% 단축 및 병목 해소
	</callout>
	<callout icon="💡" color="gray_bg">
		- **나의 한 줄 평:**
			동기 블로킹 코드를 싹 다 찾아 비동기로 전환하고 튜토리얼 뼈대를 단단하게 고쳤더니 백엔드 가동성이 날아오를 듯하다.
	</callout>
	<empty-block/>
</details>
<details>
<summary>**화요일 : \\[기밀 유지 보안 격리 구역 설계: PDF 업로드 파싱, OS Path Guard 및 대표 청크 스마트 샘플링\\]**</summary>
	<callout icon="💡" color="gray_bg">
		- **학습 내용:**
			- Defense Arena 샌드박스의 파일 업로드 비동기화 및 물리 절대 경로 비교(`os.path.realpath`) 검증을 통한 OS Path Guard 구현 (디렉토리 트래버스 취약점 원천 방지)
			- 논문의 전체 텍스트 구조를 고르게 대변하도록 도입(20%), 방법론/본문(60%), 결론(20%)의 영역 비중을 맞추어 15개 청크만 스마트 추출하는 대표 청크 균등 샘플링 알고리즘 적용
			<page url="https://app.notion.com/p/38bedca29a158054a646df525f1bf5c0">**LangGraph를 활용한 고객 지원 멀티에이전트 시스템**</page>
	</callout>
	<callout icon="💡" color="gray_bg">
		- **해결한 에러(Troubleshooting):**
			- 경로 조작 문자열(`..`)을 활용한 디렉토리 이탈 시도 탐색 -> OS Path Guard 비교 함수 추가로 취약점 차단
	</callout>
	<callout icon="💡" color="gray_bg">
		- **나의 한 줄 평:**
			경로 우회 보안 위협을 철저히 막고, 논문을 고르게 훑는 스마트 샘플링 필터를 걸어 LLM에 질 좋은 컨텍스트를 먹여주니 보안과 성능을 모두 챙긴 기분이다.
	</callout>
	<empty-block/>
</details>
<details>
<summary>**수요일 : \\[대용량 데이터 백업 및 버전 관리: Hugging Face Dataset 자동 업로드 및 Paging 처리\\]**</summary>
	<callout icon="💡" color="gray_bg">
		- **학습 내용:**
			- pgvector의 수만 건 임베딩 데이터를 Paging(LIMIT/OFFSET 5000) 인출하여 대용량 DB 조회 시 네트워크 데드락 및 타임아웃 방지
			- Parquet 파일 포맷을 활용한 Hugging Face Dataset 변환 및 업로드 자동화 구축
			- `HfApi`를 사용하여 Dataset Card 메타데이터가 기입된 README.md 자동 생성 및 푸시
			<page url="https://app.notion.com/p/38bedca29a1580449f46f6200d2928a4">**비동기 배치 작업 구조 및 API 엔드포인트 설계**</page>
	</callout>
	<callout icon="💡" color="gray_bg">
		- **해결한 에러(Troubleshooting):**
			- 3만 건 이상의 임베딩을 한 번에 select할 때 서버 커넥션이 중단되는 현상 -> 5,000건 페이징 단위 스캔 및 tqdm 진척도 결합으로 연결 안정화
	</callout>
	<callout icon="💡" color="gray_bg">
		- **나의 한 줄 평:**
			대용량 데이터베이스를 페이징 스캔으로 한 땀 한 땀 우아하게 인출해 허브로 실시간 백업 연동하고 나니, 데이터 버전 관리가 한결 수월해졌다.
	</callout>
</details>
<details>
<summary>**목요일 : \\[Stage-2 Full-Text RAG 파이프라인 및 온디맨드 벡터화(On-Demand Vectorization)\\]**</summary>
	<callout icon="💡" color="gray_bg">
		- **학습 내용:**
			- 3개 학술 도메인의 파편화된 RAG 로직의 `rag_pipeline.py` 공통 모듈 단일화
			- 초록 RAG의 정보 한계를 넘어 논문 본문 전체를 긁어오고 RAG 유사도 검색을 수행하는 **Stage-2 Full-Text RAG** 메커니즘 설계
			- 본문이 벡터 DB에 존재하지 않을 경우 실시간 수집 및 청킹 적재를 위임하는 실시간 온디맨드 지연 인덱싱(Lazy-Indexing) 및 메타데이터 `paper_id` 타겟팅 필터링 구현
			<page url="https://app.notion.com/p/38bedca29a15801e9544dd929721c1e4">**RAG 연동 및 LLM Structured Output을 이용한 다단계 학술 문헌 분석**</page>
	</callout>
	<callout icon="💡" color="gray_bg">
		- **해결한 에러(Troubleshooting):**
			- 전체 논문 청크 풀에서 키워드가 겹쳐 엉뚱한 논문의 본문 내용이 RAG 컨텍스트로 튀어나오는 현상 -> pgvector의 `filter={"paper_id": clean_id}` 파라미터 매핑으로 검색 바운더리 격리
	</callout>
	<callout icon="💡" color="gray_bg">
		- **나의 한 줄 평:**
			추상적인 abstract 수준의 RAG를 넘어, 필요에 따라 실시간으로 전체 논문 본문을 임베딩하고 칼같이 필터링하는 2단계 RAG를 손수 엮어내어 RAG의 정수를 맛보았다.
	</callout>
</details>
<details>
<summary>**금요일 : \\[피어리뷰 시뮬레이션 및 턴제 모의 디펜스 아레나 아키텍처\\]**</summary>
	<callout icon="💡" color="gray_bg">
		- **학습 내용:**
			- Methodology, Novelty, Academic Style 3대 전문 LLM 에이전트 피어리뷰 grading 시뮬레이션
			- RAG 팩트 인출 및 다소 높은 온도의 3회 독립 추론 다수결 판정(Majority Voting) 기반 자기 일관성(Self-Consistency) 가설 검증 구현
			- 4대 엄격한 루브릭 채점 지표 기반의 턴제 구두 디펜스 실시간 채점 및 최종 리포트 합성
			- 30분 만료 세션 가비지 컬렉터(이중 소거) 스케줄러를 통한 업로드 파일 및 DB vector 청크 완전 소거
			<page url="https://app.notion.com/p/38bedca29a158045893dc41c7152dfe0">**SSE 실시간 완료 알림 및 다국어 학술 번역 캐싱 메커니즘**</page>
	</callout>
	<callout icon="💡" color="gray_bg">
		- **해결한 에러(Troubleshooting):**
			- 디펜스 세션 만료 후 기밀 논문 데이터가 DB에 계속 남아있는 문제 -> 30분 미활동 스케줄러 내 is_saved 속성에 따른 이중 파쇄 정책 설계로 영구 삭제 보장
	</callout>
	<callout icon="💡" color="gray_bg">
		- **나의 한 줄 평:**
			3명의 깐깐한 심사위원이 압박 질문을 던지고 가설을 다수결로 판정하는 oral defense 게임 보드를 구현하고 보안 파일 파쇄기까지 달아놓으니 프로덕션급 서비스가 따로 없다.
	</callout>
</details>
<empty-block/>
### 🧠 주간 회고 (Weekly Reflection)
**한 주를 마무리하며 스스로의 성장을 돌아봅니다😊** {color="pink"}
- **Liked (좋았던 점)**
	- 실제 학술 논문 에이전트 협업 레포지토리인 `bist-mini-2`에서 그동안 개발해온 RAG 파이프라인, 디펜스 아레나(Feature 4) 모듈, 데이터 백업 파이프라인을 체계적으로 구조화하고 실무에 즉시 적용 가능한 완성도로 리팩토링 및 고도화할 수 있어 보람찼습니다.
	- 비동기 처리의 병목이었던 Bcrypt 해싱이나 디스크 I/O 등을 완벽히 비동기 논블로킹 패턴으로 전환하면서 백엔드 아키텍처의 내실을 튼튼히 다졌습니다.
- **Learned (배운 점)**
	- **보안 및 실효성 있는 샘플링 기법:** OS Path Guard(`os.path.realpath`)를 통한 파일 디렉토리 트래버스 방지 기술과, 긴 텍스트의 도입-본문-결론을 대표하는 가중치 균등 샘플링 알고리즘 설계법을 깊이 있게 배웠습니다.
	- **대용량 데이터 Paging & 버전 관리:** 원격 DB 커넥션 타임아웃을 피하기 위해 5,000건 단위의 LIMIT/OFFSET 페이징 방식을 적용해 안전하게 Hugging Face Dataset API로 적재하고, Parquet 및 Dataset Card 메타데이터 카드를 파이썬 코드로 제어하는 노하우를 습득했습니다.
	- **Self-Consistency & Turn-based Logic:** 다소 높은 LLM 온도로 여러 번 독립 판정한 후 다수결(Majority Voting)을 합성하는 자기 일관성 기법과, 턴 기반 대화 세션의 실시간 채점 평가 루브릭 설계 기법을 깨달았습니다.
- **Lacked (아쉬운 점)**
	- 디펜스 아레나의 턴제 대화 상태 전이 시, 예기치 않은 사용자 응답이 들어오거나 DB 트랜잭션 수명 주기가 꼬일 때 발생하는 극단적인 예외 상황들을 처리하기 위한 아키텍처 예외 처리 라인이 복잡해져 구현 시간이 더 소요된 점이 아쉽습니다.
	- pgvector HNSW 인덱스의 construction 매개변수와 실시간 적재 시의 삽입 오버헤드 간 최적의 밸런스를 엄격한 벤치마크 테스트로 검증해보지 못한 점이 미완으로 남았습니다.
- **Longed for (다음 주 목표)**
	- 이번 주에 구현한 Stage-2 Full-Text RAG와 실시간 온디맨드 임베딩 로직을 실제 프론트엔드 UI의 Chat Playground와 매끄럽게 연결하고, 실시간 스트리밍 답변 도중 사용자가 입력한 가설을 즉각 검증하여 위젯에 상태를 뿌려주는 양방향 인터렉션을 고도화하겠습니다.
	- 백엔드에 남아있는 다른 blocking 연산들을 추가 발굴하여 마이너 리팩토링을 완수하고, 전체 도메인 통합 가상 테스트 스위트를 작성해 Git CI 파이프라인에서 자동으로 검증되도록 완성하겠습니다.
### 📎 참고 자료 보관함
- (이번 주 공부하며 참고했던 공식 문서나 블로그 링크를 모아두세요.)
