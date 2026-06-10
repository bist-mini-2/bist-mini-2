# SQLAlchemy 비동기 PostgreSQL 드라이버 비교 가이드 (asyncpg vs psycopg)

SQLAlchemy `create_async_engine`을 활용하여 비동기로 PostgreSQL에 연결할 때 주로 사용하는 두 가지 드라이버인 `asyncpg`와 `psycopg` (버전 3)를 비교하고, 적절한 선택 및 설정 방법을 설명합니다.


---


## **1. 드라이버 핵심 개념 비교**

SQLAlchemy에서 비동기 엔진을 생성할 때, 연결 URI에 사용할 드라이버명(`postgresql+asyncpg` 또는 `postgresql+psycopg`)을 명시하여 원하는 드라이버를 선택할 수 있습니다.

| 비교 항목 | `asyncpg` (`postgresql+asyncpg`) | `psycopg` 버전 3 (`postgresql+psycopg`) |
| --- | --- | --- |
| **개발 주체** | MagicStack (오픈소스 커뮤니티) | PostgreSQL 공식 Python 드라이버 개발 팀 |
| **구현 방식** | Cython 및 순수 비동기(Async-first) 프로토콜 구현 | C 확장 및 Python 동기/비동기 듀얼 프로토콜 지원 |
| **성능 (생 쿼리)** | **매우 빠름** (Python 비동기 드라이버 중 벤치마크 최상위) | 우수한 성능 (버전 3에서 내부 최적화 다수 진행) |
| **다중 호스트 지원** | 제한적 지원 (추가 파라미터나 DSN 파싱 필요) | **기본 지원** (libpq 표준 규격 다중 호스트 URI 파싱 지원) |
| **의존성 설치** | `pip install asyncpg` | `pip install psycopg[binary]` 또는 `psycopg` |
| **기존 psycopg2 호환** | 호환되지 않음 (새로운 API 구조) | 호환성 높음 (기존 psycopg2의 사용 패턴 대부분 유지) |


---


## **2. 드라이버별 상세 분석**


### **① ****`asyncpg`**** (****`postgresql+asyncpg`****)**

* **장점**:
  * 속도가 극단적으로 빠릅니다. PostgreSQL의 프론트엔드/백엔드 프로토콜을 파이썬 비동기 환경에 맞춰 직접 구현하여 오버헤드가 적습니다.
  * 데이터 타입 변환(Data Type OID Mapping) 속도가 매우 뛰어납니다.
* **단점**:
  * PostgreSQL 공식 라이브러리(`libpq`)를 기반으로 하지 않고 독자적으로 구현했기 때문에, 표준 `libpq`에 정의된 연결 문자열 옵션(예: 복잡한 다중 호스트 Failover 설정)을 처리하는 데 제한이 있을 수 있습니다.
  * 동기(Sync) 인터페이스가 전혀 존재하지 않으므로, 동일 애플리케이션 내에서 동기 엔진(`create_engine`)을 함께 사용하려면 다른 드라이버를 혼용해야 합니다.

### **② ****`psycopg`**** 버전 3 (****`postgresql+psycopg`****)**

* **장점**:
  * **공식 드라이버의 안정성**: PostgreSQL 글로벌 개발 그룹에서 관리하는 공식 표준 드라이버입니다.
  * **다중 호스트(Failover/Load Balancing) 기본 지원**: `postgresql+psycopg://user:password@/dbname?host=HostA:5432&host=HostB:5432&host=HostC:5432`와 같이 `libpq`의 다중 호스트 DSN 규격을 그대로 해석해 줍니다.
  * **듀얼 API**: 동기(`psycopg.connect`)와 비동기(`psycopg.AsyncConnection`)를 모두 자체적으로 지원하므로 드라이버 일관성이 높습니다.
* **단점**:
  * 성능 면에서 `asyncpg`에 비해 아주 미세하게 느릴 수 있습니다(일반적인 웹 API 수준에서는 체감하기 어렵습니다).
  * 패키지 설치 시 바이너리 버전(`psycopg[binary]`) 또는 컴파일 버전(`psycopg`) 중 환경에 맞게 잘 선택해야 합니다.

---


## **3. 코드 적용 방법**


### **① ****`asyncpg`**** 드라이버 사용 설정**


```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# asyncpg를 사용하는 비동기 엔진 생성
engine = create_async_engine(
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False
)

SessionMaker = async_sessionmaker(
    bind=engine,
    autoflush=True,
    autocommit=False
)
```


### **② ****`psycopg`**** (버전 3) 드라이버 사용 설정 (다중 호스트 Failover 예시)**


```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# psycopg 3를 사용하는 비동기 엔진 생성 (Multi-host Failover 적용)
engine = create_async_engine(
    "postgresql+psycopg://postgres:postgres@/postgres?host=HostA:5432&host=HostB:5432&host=HostC:5432&target_session_attrs=read-write",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False
)

SessionMaker = async_sessionmaker(
    bind=engine,
    autoflush=True,
    autocommit=False
)
```


---


## **4. 언제 어떤 드라이버를 사용해야 하나요?**


### **`asyncpg`**** 사용이 유리한 경우**

* **성능이 극도로 중요**한 대규모 트래픽 처리 API 서비스
* 단일 DB 노드를 사용하고 복잡한 Failover/Load Balancing 설정을 필요로 하지 않을 때

### **`psycopg`**** (버전 3) 사용이 유리한 경우**

* Aurora PostgreSQL Serverless 등 복잡한 **다중 노드 이중화 구조(Failover / Read-Write 분기)**를 연결 문자열 레벨에서 쉽게 구성하고 싶을 때 (`target_session_attrs` 옵션 등 활용)
* 동기와 비동기 DB 커넥션을 하나의 프로젝트 내에서 모두 관리해야 할 때
