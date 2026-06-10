# FastAPI Annotated & Dependency Injection 가이드

본 문서는 FastAPI에서 `typing.Annotated`를 사용하는 목적과 Pydantic과의 차이점, 그리고 이를 전역/모듈 수준에서 설계하여 의존성 주입(Dependency Injection)을 효율화하는 방법에 대해 다룹니다.


---


## **1. Annotated 도입 목적**

`Annotated`는 PEP 593(Python 3.9+)에서 도입된 기능으로, **정적 타입 검사 정보**에 **임의의 메타데이터**를 추가적으로 결합할 수 있게 합니다.

FastAPI에서 `Annotated`를 사용하는 핵심 목적은 다음과 같습니다.


### **① 정적 타입 검사기(IDE, Linter) 지원성 향상**

기존 방식에서는 매개변수의 기본값으로 `Query()`, `Path()`, `Depends()` 등의 객체를 직접 할당했습니다.


```python
# 기존 방식 (타입 불일치 경고 가능성 존재)
async def read_items(q: str = Query(None, max_length=50))
```

이 방식은 타입 검사기(MyPy, Pyright 등)가 `q`를 `str`로 볼지 `Query` 객체로 볼지 헷갈려 하여 자동 완성이나 경고 필터링에 결함이 생겼습니다.


```python
# Annotated 방식 (타입 검증과 프레임워크 메타데이터의 완벽한 분리)
async def read_items(q: Annotated[str, Query(max_length=50)] = None)
```

`Annotated` 방식을 쓰면 정적 분석 도구는 `q`를 순수한 `str`로만 평가하고, 뒤의 `Query(...)`는 무시하므로 개발 도구의 지원을 완벽히 받을 수 있습니다.


### **② 런타임 메타데이터 활용**

FastAPI는 런타임에 이 메타데이터들을 추출하여, 클라이언트 요청의 바인딩(Query/Path/Header/Form/Body 분기)과 OpenAPI 문서(Swagger UI)의 사양 자동 생성에 활용합니다.


---


## **2. Pydantic과의 차이점 및 한계 비교**

Pydantic 단독 사용과 `Annotated`를 활용한 의존성 주입은 해결하려는 도메인이 다릅니다.

| 비교 항목 | Pydantic 모델 | Annotated + FastAPI 의존성 (Depends 등) |
| --- | --- | --- |
| **주요 역할** | 정적 데이터 구조(JSON/Form) 검증 및 파싱 | 정적 타입에 FastAPI 동작(의존성 주입, 헤더/쿼리 매핑 등)을 결합 |
| **동적 행위 처리** | 불가능 (정적 스키마에 국한됨) | 가능 (DB 세션 연결, 토큰 검증, 외부 API 호출 등) |
| **매핑 위치 제어** | 기본적으로 Request Body(JSON)로 인식 | Query, Path, Header, Cookie 등 데이터 추출 소스를 명시적으로 바인딩 |


---


## **3. 공통/전역 의존성 타입 설계 패턴**

동일한 검증 규칙이나 주입 로직을 여러 라우터에서 재사용하고 싶을 때, 별도의 의존성 정의 파일을 만들어 전역 타입으로 제공할 수 있습니다.


### **Step 1: 의존성 및 공통 타입 선언 (****`api/dependencies.py`**** 예시)**


```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

# 1. DB 세션 생성 제너레이터 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. 인증 처리를 수행하는 비동기 함수
async def get_current_user(db: Annotated[Session, Depends(get_db)]):
    user = ...  # 토큰 디코딩 및 유저 정보 조회
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 유효하지 않습니다."
        )
    return user

# ========================================================
# 공통으로 재사용할 Annotated 타입 Alias 선언
# ========================================================
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
UserAgentHeader = Annotated[str | None, Header(description="요청 브라우저(User-Agent) 정보")]
```


### **Step 2: 라우터에서 활용 (****`api/receivedata/controller.py`**** 예시)**


```python
from fastapi import APIRouter
from api.dependencies import DbSession, CurrentUser, UserAgentHeader

router = APIRouter(prefix="/posts")

@router.post("/create")
async def create_post(
    db: DbSession,               # 자동으로 DB 세션이 주입됨
    user: CurrentUser,           # 토큰 검증이 완료된 사용자 객체가 주입됨
    user_agent: UserAgentHeader  # HTTP Header에서 읽어온 User-Agent 주입됨):
    # 컨트롤러 내에서 자동 완성 지원 및 간결한 코드 유지
    logger.info(f"작성자: {user.username}, 브라우저: {user_agent}")
    # 비즈니스 로직 수행...
    return {"status": "success"}
```


---


## **4. 도입 시 이점 요약**

1. **DRY (Don't Repeat Yourself) 원칙 준수:** 인증 검증 로직이나 헤더 파싱 코드를 컨트롤러 함수마다 반복 선언할 필요가 없습니다.
1. **비즈니스 로직에 집중:** 라우터/컨트롤러의 매개변수 선언부가 단순 타입 어노테이션 형태로 극도로 깔끔해집니다.
1. **유지보수성 향상:** 토큰 만료 처리나 DB 생성 로직이 바뀔 때, 컨트롤러 수정 없이 `dependencies.py` 한 곳만 수정하면 전체 API에 반영됩니다.
1. **파이썬 기본값 선언 순서 제약 해결:** 파이썬에서는 기본값이 있는 매개변수 뒤에 기본값이 없는(필수) 매개변수가 선언되면 `SyntaxError`가 발생합니다.
  * **기존 방식:** `q: str = Query(...)`는 기본값 위치에 `Query` 객체가 할당되므로 무조건 기본값이 있는 매개변수로 취급되어 선언 순서가 꼬이기 쉽습니다.
  * **Annotated 방식:** `q: Annotated[str, Query(...)]`는 기본값이 생기는 것이 아니므로 필수 매개변수와 선택 매개변수의 선언 순서를 유연하게 배치할 수 있습니다.
1. **테스트 및 의존성 모킹(Dependency Override) 최적화:** 실제 컨트롤러 구현을 수정하지 않고도, 테스트 코드 상에서 `app.dependency_overrides`를 사용해 특정 `Annotated` 의존성(예: `DbSession`)을 Mock이나 테스트용 DB로 매우 편리하게 교체할 수 있습니다.
1. **파이썬 표준 생태계와의 완벽한 호환성:** `Annotated`는 FastAPI 전용 도구가 아닌 파이썬 표준 라이브러리(`typing`) 스펙입니다. 따라서 Pydantic v2, SQLModel, Typer(CLI 라이브러리) 등 타입을 활용하는 타 파이썬 라이브러리와도 자연스럽게 통합됩니다.
