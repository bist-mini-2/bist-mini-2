## **📝 이번 주 실제 개발 내용 요약 (월요일)**
- **백엔드 비동기(Async) 리팩토링 및 동기식 블로킹 연산 제거**:
	- CPU 집약적인 `bcrypt` 해싱 작업(`bcrypt.hashpw`, `bcrypt.checkpw`)을 `asyncio.to_thread`를 사용하여 별도의 작업 스레드로 오프로딩하여 이벤트 루프 블로킹을 해소했습니다.
	- Git 로그 조회 등 외부 서브프로세스 실행 시 동기식 `subprocess` 대신 `asyncio.create_subprocess_exec`을 적용하여 비동기 논블로킹 방식으로 백엔드 가동성을 극대화했습니다.
- **튜토리얼 노트북 단일화 및 아키텍처 재구성**:
	- 난잡하게 흩어져 있던 10여 개의 Jupyter 노트북(기초/심화)들을 각 핵심 모듈(`chat_service`, `embedding_ingestion`, `rag_pipeline`, `gem_service`, `defense_arena`, `research_gap`)별로 매칭되는 5개 코어 튜토리얼로 깔끔하게 정리했습니다.
	- 각 노트북의 의존성 오류(NameError, 타입 불일치 등)와 모듈 임포트 버그들을 전면 수정하여 신규 개발자가 즉시 동작 가능한 수준으로 복원하고 백엔드 패키지 의존성(`requirements.txt`)을 업데이트했습니다.

---

## **💻 핵심 코드 예제 및 상세 해설**

### **1. Bcrypt 암호화 및 검증 비동기 오프로딩 구현 (\\[services.py\\](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/member/services.py))**
CPU 소모가 큰 Bcrypt 해싱 함수를 비동기 이벤트 루프에서 실행할 때 전체 서버가 블로킹되는 현상을 방지하기 위해 `asyncio.to_thread`를 적용한 구현 코드입니다.
```python
import asyncio
import bcrypt

# [비동기 회원 가입 내 Bcrypt 해싱 최적화]
async def join(self, member_entity: MemberEntity) -> MemberEntity:
    self.logger.info("join 실행")
    
    # 중복 아이디 존재 여부 비동기 조회
    existing = await self.member_dao.select_by_mid(member_entity.mid)
    if existing:
        raise BusinessException("이미 존재하는 회원 아이디입니다.", error_code="MEMBER_DUPLICATE")

    # bcrypt.hashpw는 동기식 blocking 연산이므로 asyncio.to_thread로 감싸 스레드 풀에서 실행합니다.
    hashed = await asyncio.to_thread(
        bcrypt.hashpw,
        member_entity.mpassword.encode('utf-8'),
        bcrypt.gensalt()
    )
    member_entity.mpassword = hashed.decode('utf-8')
    member_entity = await self.member_dao.insert(member_entity)
    return member_entity

# [비동기 로그인 내 Bcrypt 패스워드 검증 최적화]
async def authenticate(self, mid: str, password: str) -> MemberEntity:
    self.logger.info("authenticate 실행")
    db_member_entity = await self.member_dao.select_by_mid(mid)
    if not db_member_entity:
        raise MemberNotFoundError("존재하지 않는 회원 아이디")
        
    # bcrypt.checkpw 역시 동기 블로킹 함수이므로 스레드 풀 오프로딩을 적용합니다.
    is_valid = await asyncio.to_thread(
        bcrypt.checkpw,
        password.encode('utf-8'),
        db_member_entity.mpassword.encode('utf-8')
    )
    if not is_valid:
        raise InvalidPasswordError("회원 비밀번호가 틀림")
    return db_member_entity
```

### **🔍 주요 구문 및 설계 해설:**
- **`asyncio.to_thread`**: 파이썬의 GIL(Global Interpreter Lock) 하에서도 I/O 바운드나 CPU 바운드 작업을 별도 OS 스레드 풀에서 실행하여 FastAPI의 주 이벤트 루프가 멈추지 않고 다른 가벼운 HTTP 요청을 계속 처리할 수 있도록 돕습니다.

---

### **2. 비동기 서브프로세스를 활용한 Git 로그 수집 (\\[endpoints.py\\](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/health/endpoints.py))**
동기식 `subprocess.run`은 OS 명령어가 종료될 때까지 전체 싱글 스레드 이벤트 루프를 멈추게 만듭니다. 이를 논블로킹으로 개선하기 위해 `asyncio.create_subprocess_exec`을 적용했습니다.
```python
import asyncio

# [개발자 대시보드 내 실시간 Git Changelog 수집]
async def get_dashboard_context(request: Request) -> dict:
    workspace_root = "/Users/pileuszu/Repos/bist-mini-2"
    git_changelog = []
    try:
        # 동기 subprocess.run 대신 비동기 서브프로세스를 실행합니다.
        proc = await asyncio.create_subprocess_exec(
            "git", "log", "-n", "20", "--pretty=format:%h|%an|%ar|%s",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace_root
        )
        # communicate()를 await하여 서브프로세스가 백그라운드에서 실행되는 동안 제어권을 양보합니다.
        stdout, _ = await proc.communicate()
        git_log = stdout.decode("utf-8")
        for line in git_log.split("\n"):
            if "|" in line:
                h, an, ar, s = line.split("|", 3)
                git_changelog.append({
                    "hash": h,
                    "author": an,
                    "time": ar,
                    "subject": s
                })
    except Exception as e:
        git_changelog = [{"hash": "N/A", "author": "System", "time": "N/A", "subject": f"Git 로그 조회 실패: {str(e)}"}]
    
    return {"git_changelog": git_changelog}
```

### **🔍 주요 구문 및 설계 해설:**
- **`asyncio.create_subprocess_exec`**: OS 레벨의 자식 프로세스를 논블로킹으로 생성하고, 표준 입출력 스트림(`asyncio.subprocess.PIPE`)을 비동기식으로 대기(`await proc.communicate()`)하여 높은 동시성을 확보합니다.
