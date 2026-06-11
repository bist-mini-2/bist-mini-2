# SQLAlchemy 로깅 통합 가이드 (표준 logging 모듈 연동)

SQLAlchemy 비동기 엔진 설정 시 `echo` 및 `echo_pool` 옵션을 사용하는 대신, 파이썬 표준 `logging` 라이브러리를 연동하여 통일된 로그 형식(예: `colorlog`, 로그 파일 저장 등)을 구성하는 방법을 설명합니다.


---


## **1. 개요 및 필요성**

SQLAlchemy의 `create_async_engine()` 함수 등에서 `echo=True` 또는 `echo_pool="debug"`를 지정하면, SQLAlchemy는 기본적으로 `sys.stdout`으로 출력되는 전용 핸들러를 내부적으로 자동 생성합니다.

이 방식으로 사용하면 다음과 같은 문제가 발생할 수 있습니다.

1. **로그 포맷의 불일치**: 애플리케이션의 공통 로그 포맷(예: 컬러 로그, 날짜/시간 포맷 등)이 데이터베이스 로그에는 적용되지 않고 기본 텍스트 형태로만 출력됩니다.
1. **로그 중복 출력**: 이미 루트 로거(Root Logger)에 설정해 둔 콘솔 핸들러와 SQLAlchemy 자체 핸들러가 겹쳐서 로그가 2번씩 출력될 수 있습니다.
1. **제어 편의성 저하**: 개발(Dev) 및 운영(Prod) 환경에 맞춰 로그 레벨을 코드 변경 없이 유연하게 제어하기 어렵습니다.
따라서 실제 제품 개발 시에는 엔진 레벨의 직접 로깅을 비활성화하고, **표준 ****`logging`**** 모듈**에 로거별 레벨을 지정해 주는 것이 권장됩니다.


---


## **2. 연동 및 설정 방법**


### **① 데이터베이스 엔진 설정 ([dbsession.py](file:///d:/Repo/kosa-fastapi/api/database/config/dbsession.py))**

`create_async_engine()`에서 `echo=False`, `echo_pool=None`(기본값)으로 설정하여 자체 `sys.stdout` 스트림 핸들러 등록을 제한합니다.


```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+psycopg://postgres:postgres@localhost:5432/postgres",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,       # sys.stdout 자동 출력을 막기 위해 False 설정
    echo_pool=None    # sys.stdout 자동 출력을 막기 위해 None 설정
)
```


### **② 애플리케이션 진입점 설정 ([main.py](file:///d:/Repo/kosa-fastapi/main.py))**

애플리케이션 진입점에서 `sqlalchemy` 부모 로거에 파일 핸들러(`FileHandler`)를 붙여 모든 DB 로그를 `db.log` 파일로 출력하고, 메인 콘솔이 너무 복잡해지는 것을 막기 위해 상위(Root) 로거로의 **전파(propagate)를 비활성화**합니다.


```python
import logging

# 1. SQLAlchemy용 파일 핸들러 생성 (db.log 파일로 분리)
db_file_handler = logging.FileHandler("db.log", encoding="utf-8")
db_file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s]: %(message)s'
))

# 2. sqlalchemy 로거 획득 및 설정
sqlalchemy_logger = logging.getLogger("sqlalchemy")
sqlalchemy_logger.addHandler(db_file_handler)
sqlalchemy_logger.propagate = False  # Root 로거로 로그가 넘어가 메인 콘솔창에 찍히는 것을 방지

# 3. 각 하위 로거의 로그 레벨 설정
# - sqlalchemy.engine: SQL 실행 쿼리 및 파라미터 로깅 담당 (echo 옵션 대응)
# - sqlalchemy.pool: 커넥션 풀 상태 및 pre-ping 로깅 담당 (echo_pool 옵션 대응)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)  # SQL 실행 내용
logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)   # 커넥션 풀 상세 내용
```


---


## **3. 작동 원리**

1. `echo=False`로 설정되어 SQLAlchemy는 자체 로거에 개별적인 콘솔 출력 핸들러를 바인딩하지 않습니다.
1. `main.py`에서 `sqlalchemy_logger.propagate = False` 설정을 함으로써, `sqlalchemy`와 그 하위 패키지(`sqlalchemy.engine`, `sqlalchemy.pool`)에서 일어나는 로그가 루트 로거(Root Logger)로 흘러 들어가지 않습니다. 이 덕분에 FastAPI 메인 콘솔은 클린하게 유지됩니다.
1. 대신 `sqlalchemy_logger.addHandler(db_file_handler)`를 설정하였으므로 모든 DB 관련 로그는 지정한 `db.log` 파일로만 기록됩니다.

---


## **4. 실시간으로 DB 로그 전용 콘솔 창 띄우기**

분리된 `db.log` 파일을 새로운 콘솔(터미널) 창에서 실시간으로 확인하려면 모니터링(Tailing) 명령어를 실행하면 됩니다.


### **① Windows PowerShell에서 실행할 때**

새로운 PowerShell 창을 열고 프로젝트 루트 디렉토리에서 다음 명령어를 실행합니다:


```powershell
Get-Content db.log -Wait -Tail 50
```


### **② macOS / Linux 또는 Git Bash에서 실행할 때**

새로운 터미널 창을 열고 다음 명령어를 실행합니다:


```bash
tail -f db.log
```

이 방식을 사용하면 **메인 콘솔창은 FastAPI 요청/응답 및 일반 에러 로그만 보여 가독성이 유지**되고, **두 번째 콘솔창에서 DB 쿼리와 풀의 상태 변화를 실시간으로 모니터링**할 수 있어 개발 생산성이 향상됩니다.

