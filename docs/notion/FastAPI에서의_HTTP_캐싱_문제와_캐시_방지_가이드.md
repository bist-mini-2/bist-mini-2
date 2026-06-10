# FastAPI에서의 HTTP 캐싱 문제와 캐시 방지 가이드

웹 애플리케이션 개발 중 이미지, 파일 등의 자원을 API를 통해 가져올 때, 두 번째 요청부터 서버 로그가 전혀 남지 않는 현상이 발생할 수 있습니다. 본 문서는 이 현상의 원인인 **휴리스틱 캐싱(Heuristic Caching)**과 FastAPI에서 이를 해결(캐시 방지)하는 방법에 대해 설명합니다.


---


## **1. 문제 현상 및 원인**


### **① 현상**

* 특정 파일 다운로드 API 또는 정적 파일(`/static/...`)을 브라우저에서 최초 호출 시에는 서버 로그가 정상 기록됨.
* 그러나 페이지를 새로고침하거나 재호출하면 서버 로그가 전혀 기록되지 않고 화면에 자원이 바로 나타남.

### **② 원인: 휴리스틱 캐싱 (Heuristic Caching)**

* FastAPI의 `FileResponse`는 파일을 전송할 때 파일의 수정 시간(`Last-Modified`)과 고유 식별자(`ETag`) 헤더를 자동으로 생성해 응답에 포함합니다.
* 하지만 명시적인 캐시 제어 헤더인 **`Cache-Control`****은 기본 응답 헤더에 포함하지 않습니다.**
* 브라우저는 `Last-Modified`는 존재하지만 `Cache-Control`이 없는 경우, **휴리스틱 캐싱 알고리즘**에 의해 자체적으로 캐시 만료 시간을 계산하여 저장합니다.
* 이에 따라 이후 동일한 자원에 대한 요청은 서버로 가지 않고 **브라우저 로컬 캐시(Memory Cache 또는 Disk Cache)**에서 즉시 반환되므로, 서버에는 어떠한 HTTP 요청도 도달하지 않고 로그도 남지 않게 됩니다.

---


## **2. FastAPI 기본 동작 및 설정 위치**

Starlette(FastAPI의 기반 라이브러리)의 `FileResponse` 소스코드를 보면 캐싱 관련 헤더가 강제로 자동 설정되는 것을 볼 수 있습니다.

* **소스 파일:** `starlette.responses.FileResponse`
* **동작 방식:**여기서 `Cache-Control` 헤더를 설정하는 기본 파라미터는 부재하며, 캐싱 제어는 전적으로 개발자가 수동으로 헤더를 주입해 조절해야 합니다.

```python
# Starlette 내부 소스코드 구조 요약
stat_result = os.stat(self.path)
self.headers.setdefault("last-modified", formatdate(stat_result.st_mtime, usegmt=True))
self.headers.setdefault("etag", f'W/"{stat_result.st_mtime}-{stat_result.st_size}"')
```


---


## **3. 해결 방법 (캐시 방지 대책)**

브라우저가 매번 서버로 직접 요청을 보내도록 강제하려면 `Cache-Control` 헤더를 설정하여 캐시 사용을 완전히 금지해야 합니다.


### **① FileResponse 호출 시 설정**

`FileResponse` 객체를 반환할 때 `headers` 매개변수에 캐시 무효화 헤더들을 명시적으로 추가합니다.


```python
import mimetypes
from urllib.parse import quote
from fastapi.responses import FileResponse

@router.get("/file", response_class=FileResponse)
async def return_file():
    file_name = "photo.png"
    file_path = f"C:/Temp/{file_name}"
    media_type, _ = mimetypes.guess_type(file_path)
    file_encoded_filename = quote(file_name)

    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{file_encoded_filename}",
            # 강력한 캐시 방지 헤더 설정
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
```


### **② 정적 파일 서빙(StaticFiles) 설정**

웹 서버가 마운트하고 있는 `/static` 디렉토리 하위의 파일에 대해 캐싱을 비활성화하려면, `StaticFiles` 클래스를 상속받아 커스텀 클래스를 만든 뒤 마운트합니다.


```python
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 캐시 제어 헤더를 주입하는 커스텀 StaticFiles 클래스 정의
class NoCacheStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# main.py에서 커스텀 클래스를 마운트
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")
```


---


## **4. 캐시 제어 핵심 헤더 설명**

* **`no-store`****:** 브라우저 및 중간 캐시 서버가 응답 데이터를 로컬에 어떠한 형태로도 저장하지 않도록 강제합니다.
* **`no-cache`****:** 데이터를 캐시할 수는 있으나, 사용하기 전에 반드시 원본 서버에 `ETag` 등을 이용해 유효성 검증(Validation) 요청을 보내도록 합니다.
* **`must-revalidate`****:** 캐시가 만료된 이후에는 무조건 원본 서버에 재검증 요청을 보내어 최신 데이터를 확인하도록 강제합니다.
