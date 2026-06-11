# FastAPI StreamingResponse 구현 및 서버리스(Vercel) 고려사항

이 문서는 FastAPI와 LangChain을 결합하여 스트리밍 응답을 구현할 때 발생한 타입 에러, 프론트엔드 연동 트러블슈팅 과정 및 Vercel과 같은 서버리스 배포 환경에서의 비용 및 타임아웃 문제를 정리한 가이드입니다.


---


## **1. StreamingResponse의 타입 불일치(Type Mismatch) 이슈**


### **현상 및 에러 메시지**


```plain text
Argument AsyncGenerator[list[dict[Unknown, Unknown] | str] | str, Unknown] is not assignable to parameter content with type AsyncIterable[Content] | Iterable[Content] in function starlette.responses.StreamingResponse.__init__
```


### **원인**

* LangChain의 메시지 청크 객체 `BaseMessageChunk.content`는 타입 시스템상 문자열(`str`) 외에도 이미지나 툴 호출 등을 포함하는 복합 리스트(`list[dict | str]`) 형태를 가질 수 있습니다.
* 이로 인해 비동기 제너레이터 함수 `generate()`의 반환 타입이 `AsyncGenerator[Union[list, str], None]`으로 추론됩니다.
* 그러나 FastAPI/Starlette의 `StreamingResponse`는 `AsyncIterable[str | bytes]`만을 수용하므로 정적 타입 분석기(Pyright/Mypy)에서 타입 불일치 오류를 발생시킵니다.

### **해결 방안**

`isinstance(content, str)` 검사를 수행하여 명시적으로 문자열인 청크만 `yield`하도록 보장합니다. 이렇게 하면 타입 검사기가 제너레이터의 반환 타입을 `AsyncGenerator[str, None]`로 추론하여 오류가 해결됩니다.


```python
async def generate():
    async for aiMessageChunk in chat.astream(messages):
        content = aiMessageChunk.content
        # content가 문자열(str)인 경우에만 yield하도록 타입 검증 수행
        if isinstance(content, str) and content:
            yield content
```


---


## **2. 프론트엔드 연동 트러블슈팅: NDJSON vs 순수 텍스트 스트리밍**


### **현상**

서버에서 `application/x-ndjson` 규격에 맞춰 `yield json.dumps({"content": content}) + "\n"`을 수행할 경우, 브라우저 화면에 `{"content": "안녕"} {"content": "하세요"}`와 같이 날것의 JSON 형식이 그대로 출력되는 현상이 발생했습니다.


### **원인**

* 클라이언트 공통 코드(`ai-utils.js`) 내부의 `ai_utils.printAnswerStreamText` 함수는 들어오는 스트림 데이터를 단순히 디코딩하여 문자열로 이어붙이기만 할 뿐(`content += chunk`), JSON 객체에 대한 파싱 처리를 수행하고 있지 않았습니다.
* 즉, HTTP 헤더로는 `application/x-ndjson`을 사용하지만 클라이언트는 이를 사실상 **단순 텍스트 스트리밍**으로 처리하고 있었습니다.

### **해결 방안**

클라이언트 코드의 구현 흐름에 맞춰, 서버 단에서 데이터 패킹(`json.dumps`)을 제거하고 순수 문자열(`str`) 그 자체만 `yield`하도록 수정했습니다.


---


## **3. 서버리스(Vercel) 환경에서의 HTTP 스트리밍 및 비용 고려사항**


### **Q. 스트리밍(StreamingResponse) 시 HTTP 요청 횟수가 늘어나 비용 문제가 생기나요?**

* **아닙니다.** HTTP 스트리밍은 TCP 연결을 1회 수립한 상태에서 데이터 스트림을 쪼개서(`chunked`) 전송하는 방식입니다.
* 즉, **단 1회의 HTTP 요청(Request Count)**만 발생하므로 Vercel의 요청 수 기반 비용 요금제에는 영향을 주지 않습니다.

### **서버리스 환경 배포 시 반드시 주의해야 할 기술적 한계들**


### **① 함수 실행 시간 제한 (Timeout Limit)**

* Vercel 무료(Hobby) 티어의 Serverless Function은 실행 시간이 최대 **10초**로 매우 짧습니다.
* 만약 LLM의 전체 답변 생성이 길어져 10초를 넘어가게 되면, 데이터 스트리밍 도중에 Vercel 인프라가 작동을 멈추고 `504 Gateway Timeout` 에러를 클라이언트에게 전송합니다.

### **② 가상 실행 시간 요금 (Duration Cost)**

* 서버리스 요금제는 실행 횟수뿐 아니라 **실행 시간(Duration, GB-seconds)**을 과금 기준으로 삼습니다.
* 스트리밍은 커넥션을 길게(예: 5초~10초) 유지하므로, 서버리스 컨테이너 인스턴스가 오랜 시간 동안 메모리/CPU를 점유하게 되어 누적 비용이 증가할 수 있습니다.

### **③ 권장 솔루션: Vercel Edge Functions**

* Vercel에 스트리밍 API를 호스팅하려는 경우, Node.js/Python의 일반 Serverless Function 대신 **Vercel Edge Functions**로 배포할 것을 강력히 권장합니다.
* Edge Functions는 응답의 첫 바이트가 전송되기 시작하면 타임아웃 카운트가 멈추므로 타임아웃의 제약을 받지 않고 실시간 LLM 스트리밍을 효율적으로 구현할 수 있습니다.
