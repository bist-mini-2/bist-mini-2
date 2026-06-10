# HTTP 상태 코드 (HTTP Status Codes) 정리 가이드

본 문서는 웹 애플리케이션 및 REST API 개발에서 가장 자주 사용되는 HTTP 상태 코드(HTTP Status Codes)를 그룹별로 정리하고, FastAPI 프레임워크에서의 활용 방식을 설명합니다.


---


## **1. HTTP 상태 코드 대분류**

| 대역 (Range) | 분류 (Category) | 설명 (Description) |
| --- | --- | --- |
| **1xx** | 정보 제공 (Informational) | 요청을 받았으며 작업을 계속 진행 중임을 나타냄 |
| **2xx** | 성공 (Success) | 요청을 성공적으로 받았고, 이해했으며, 수락했음을 나타냄 |
| **3xx** | 리다이렉션 (Redirection) | 요청을 완료하기 위해 클라이언트가 추가적인 동작을 취해야 함 |
| **4xx** | 클라이언트 오류 (Client Error) | 클라이언트의 요청에 문법 오류가 있거나 요청을 완료할 수 없음 |
| **5xx** | 서버 오류 (Server Error) | 서버가 유효한 요청을 명백히 수행하지 못하거나 실패함 |


---


## **2. 주요 HTTP 상태 코드 상세 표**


### **① 2xx 성공 (Success)**

가장 빈번하게 반환되며, 클라이언트의 요청이 정상적으로 처리되었음을 뜻합니다.

| 코드 (Code) | 명칭 (Name) | 설명 (Description) & 주요 사용 예시 |
| --- | --- | --- |
| **200** | OK | 요청 성공. GET(조회), PUT(수정) 성공 시 주로 반환됩니다. |
| **201** | Created | 요청 성공 및 자원 생성. POST(데이터 등록) 성공 시 주로 반환됩니다. |
| **204** | No Content | 요청 성공하였으나 응답 바디에 보낼 데이터가 없음. DELETE(삭제) 성공 시 사용됩니다. |


### **② 3xx 리다이렉션 (Redirection)**

요청한 리소스의 위치가 변경되어 새로운 URL로 유도할 때 사용합니다.

| 코드 (Code) | 명칭 (Name) | 설명 (Description) & 주요 사용 예시 |
| --- | --- | --- |
| **301** | Moved Permanently | 지정한 리소스가 영구적으로 새로운 URL로 이동했음. |
| **302** | Found | 임시 리다이렉션. 주소가 일시적으로 변경되었을 때 사용됩니다. |
| **304** | Not Modified | 클라이언트가 캐시한 자원이 변경되지 않았음. (네트워크 트래픽 절약) |
| **307** | Temporary Redirect | 임시 리다이렉션. 302와 유사하나, 클라이언트가 요청 메서드(GET/POST 등)를 변경하지 않고 요청해야 함. |
| **308** | Permanent Redirect | 영구 리다이렉션. 301과 유사하나, 클라이언트가 요청 메서드를 변경하지 않고 요청해야 함. |


### **③ 4xx 클라이언트 오류 (Client Error)**

클라이언트 측의 잘못된 요청이나 유효하지 않은 인증 정보 등으로 인해 서버가 처리를 거부할 때 반환됩니다.

| 코드 (Code) | 명칭 (Name) | 설명 (Description) & 주요 사용 예시 |
| --- | --- | --- |
| **400** | Bad Request | 잘못된 요청. 클라이언트의 요청 파라미터나 요청 구조가 잘못되었을 때 사용됩니다. |
| **401** | Unauthorized | 권한 없음(인증 실패). 로그인 토큰(JWT 등)이 누락되었거나 만료되었을 때 반환합니다. |
| **403** | Forbidden | 금지됨(인가 실패). 인증은 되었으나 해당 리소스에 접근할 권한이 없을 때 반환합니다. |
| **404** | Not Found | 리소스를 찾을 수 없음. 데이터베이스에 조회 대상이 존재하지 않거나 잘못된 엔드포인트 요청 시 반환합니다. |
| **405** | Method Not Allowed | 허용되지 않은 HTTP 메서드. (예: POST만 지원하는 엔드포인트에 GET으로 요청했을 때) |
| **409** | Conflict | 요청이 충돌함. 아이디 중복 가입 등 데이터베이스 정합성이 깨질 위험이 있을 때 사용합니다. |
| **422** | Unprocessable Entity | **(FastAPI/Pydantic 핵심)** 요청 값은 전달되었으나 데이터의 포맷이나 제약조건 유효성 검사(Validation)에 실패했을 때 반환됩니다. |
| 429 | Too Many Requests | 클라이언트가 지정된 시간 동안 서버에 너무 많은 요청을 보냈을 때(속도 제한 초과) 발생하는 응답 |


### **④ 5xx 서버 오류 (Server Error)**

서버 자체의 버그, 데이터베이스 다운, 로직 실행 중 예외(Exception) 발생 등 서버 환경의 문제로 처리를 완료할 수 없을 때 발생합니다.

| 코드 (Code) | 명칭 (Name) | 설명 (Description) & 주요 사용 예시 |
| --- | --- | --- |
| **500** | Internal Server Error | 내부 서버 오류. 서버 내 코드에서 처리되지 않은 예외(Exception) 발생 시 반환되는 기본 오류 코드입니다. |
| **502** | Bad Gateway | 게이트웨이 오류. 프록시 서버(Nginx 등)가 백엔드 서버(FastAPI 등)로부터 올바른 응답을 받지 못했을 때 발생합니다. |
| **503** | Service Unavailable | 서비스 이용 불가. 서버가 오버로드되었거나 유지보수로 인해 일시적으로 서비스를 제공할 수 없을 때 사용됩니다. |
| **504** | Gateway Timeout | 게이트웨이 시간 초과. 프록시 서버가 요청을 전달하고 응답을 대기하는 도중 타임아웃이 발생했을 때 나타납니다. |


---


## **3. FastAPI에서 상태 코드 사용하기**

FastAPI에서는 하드코딩된 숫자 대신 `fastapi.status` 모듈에 상수로 정의된 값을 사용하여 코드의 가독성을 높입니다.


### **① status 모듈을 활용한 컨트롤러 선언 예시**


```python
from fastapi import APIRouter, Response, status

router = APIRouter()

@router.delete("/items/{item_id}")
async def delete_item(item_id: int, response: Response):
    # 삭제 작업 완료 후 HTTP 204 No Content 반환
    response.status_code = status.HTTP_204_NO_CONTENT
    return {"message": "Deleted"}
```


### **② HTTPException 발생 예시**


```python
from fastapi import HTTPException, status

if not user_exists:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="사용자를 찾을 수 없습니다."
    )
```



