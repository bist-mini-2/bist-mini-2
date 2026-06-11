# FastAPI FileResponse vs StreamingResponse 가이드

FastAPI(Starlette)에서 대용량 데이터를 처리하거나 파일 다운로드를 구현할 때 사용하는 두 대표적인 응답 클래스인 `FileResponse`와 `StreamingResponse`를 비교하고 사용법을 설명합니다.


---


## **1. 핵심 개념 비교**

| 비교 항목 | FileResponse | StreamingResponse |
| --- | --- | --- |
| **주요 대상** | **디스크 상에 실제 존재하는 물리 파일** | **메모리 상의 데이터 또는 실시간 스트림** |
| **입력 인자** | 파일의 절대/상대 경로 (`Path` 또는 `str`) | 제너레이터 함수/반복기 (`Generator`, `Iterator`) |
| **HTTP 헤더 처리** | `Content-Length`, `Content-Disposition`, `Last-Modified`, `ETag` 등 자동 생성 | 수동으로 헤더를 생성하여 지정 필요 |
| **HTTP Range 지원** | **지원함** (대용량 파일 이어받기, 동영상 특정 구간 이동 등) | **지원하지 않음** (청크 단위 순차 전송만 가능) |
| **메모리 사용 방식** | 비동기로 파일 조각을 읽어 스트리밍 전송 | Generator가 반환하는 청크 단위로 즉시 전송 |


---


## **2. 언제 어떤 응답을 사용해야 하나요?**


### **① FileResponse 사용이 유리한 경우**

* 서버의 파일 시스템(`static/images/photo.jpg` 등)에 저장되어 있는 이미지, PDF, ZIP 등의 파일을 클라이언트에게 보낼 때.
* 대용량 파일 다운로드 기능을 제공하며 **이어받기(Range Request)** 기능이 필요할 때.
* 브라우저 동영상 플레이어에서 파일의 특정 시간대로 이동(Seek)을 지원해야 할 때.

### **② StreamingResponse 사용이 유리한 경우**

* *데이터베이스나 클라우드 스토리지(S3 등)**에서 실시간으로 스트림 데이터를 받아 파일로 중계할 때 (로컬 디스크에 임시 저장하지 않고 전송하려 할 때).
* 엑셀 파일이나 PDF를 메모리(`io.BytesIO`) 상에서 동적으로 생성하여 바로 전송할 때.
* GPT API처럼 실시간으로 생성되는 **텍스트/데이터를 실시간 스트리밍(SSE: Server-Sent Events)**으로 뿌려줄 때.

---


## **3. 코드 예시**


### **① FileResponse 예시 (로컬 파일 전송)**


```python
import mimetypes
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/download-file")
async def download_file():
    file_path = Path("static/files/report.pdf")
    encoded_filename = quote(file_path.name)

    return FileResponse(
        path=file_path,
        media_type=mimetypes.guess_type(str(file_path))[0],
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
```


### **② StreamingResponse 예시 (메모리 내 동적 데이터 전송)**


```python
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

# 1초에 한 번씩 데이터를 청크 단위로 생성하는 비동기 제너레이터
async def fake_data_streamer():
    for i in range(1, 6):
        yield f"로그 데이터 조각 #{i}\n"
        await asyncio.sleep(1)

@router.get("/log-stream")
async def log_stream():
    return StreamingResponse(
        fake_data_streamer(),
        media_type="text/event-stream"
    )
```

