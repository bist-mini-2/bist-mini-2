## **📝 이번 주 실제 개발 내용 요약 (화요일)**
- **기밀 유지 보안 격리 구역 설계 및 파일 저장 비동기 최적화**:
	- 디펜스 아레나(Defense Arena)에서 사용자가 분석용 미공개 논문 PDF나 텍스트를 업로드할 때, 격리된 `uploads` 하위 디렉토리를 세션별 UUID로 자동 구성하여 저장하고 비동기적 스레드로 파일을 쓰도록 최적화했습니다.
- **OS Path Guard를 통한 디렉토리 트래버스(Directory Traversal) 방어**:
	- 파일 업로드 및 소거 연산 시, 사용자 입력이나 조작된 세션 ID로 인해 상위 디렉토리(예: `../../etc`)로 탈출하여 서버 기밀 파일이 유출되거나 파괴되는 취약점을 물리적인 절대 경로 비교(`os.path.realpath`)로 완전 방어했습니다.
- **도입-본문-결론 영역 비율을 반영한 스마트 대표 청크 샘플링**:
	- 전체 논문 텍스트를 단순히 잘라 앞부분만 참조하는 비효율을 방어하고자, 전체 청크 리스트를 도입(20%), 방법론/본문(60%), 결론(20%)의 3대 영역으로 분할한 뒤, 균등 간격으로 총 15개의 대표 청크만을 스마트 추출하여 단일 프롬프트 컨텍스트를 구성하는 알고리즘을 도입했습니다.

---

## **💻 핵심 코드 예제 및 상세 해설**

### **1. OS Path Guard 및 PDF 업로드 처리 (\\[services.py\\](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/services.py))**
물리적 디렉토리 트래버스 위협을 방지하기 위한 OS Path Guard 검증 로직과 스레드 풀 기반 파일 쓰기 코드입니다.
```python
import os
import shutil
import uuid
import asyncio
from fastapi import UploadFile

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads")

async def process_pdf_upload(self, file: UploadFile, mid: str) -> dict:
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    
    filename = file.filename
    if not filename:
        raise BusinessException(message="파일명이 누락되었습니다.", error_code="INVALID_FILE_NAME")

    # [OS Path Guard]: 상위 디렉토리 접근 시도 등 경로 조작 여부를 엄격히 확인합니다.
    real_upload_dir = os.path.realpath(UPLOAD_DIR)
    target_path = os.path.realpath(os.path.join(session_dir, filename))
    
    # 생성될 절대 경로가 허용된 UPLOAD_DIR 하위로 시작하지 않으면 즉시 중단합니다.
    if not target_path.startswith(real_upload_dir):
        raise BusinessException(message="허용되지 않는 파일 업로드 경로 접근 시도입니다.", error_code="PATH_GUARD_VIOLATION")

    os.makedirs(session_dir, exist_ok=True)
    file_path = os.path.join(session_dir, filename)
    
    # 동기식 파일 디스크 쓰기 연산을 asyncio.to_thread로 래핑하여 논블로킹화합니다.
    def save_file_sync():
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    await asyncio.to_thread(save_file_sync)
    return {"session_id": session_id, "file_path": file_path}
```

### **🔍 주요 구문 및 설계 해설:**
- **`os.path.realpath`**: 경로 내부의 상대 참조(`.`, `..`) 및 심볼릭 링크를 모두 풀어서 물리적인 실제 절대 경로로 반환합니다. 이를 통해 `.startswith(real_upload_dir)` 검사를 적용함으로써 경로 우회 취약점을 근본적으로 무력화합니다.

---

### **2. 영역별 가중치 기반 대표 청크 스마트 샘플링 (\\[services.py\\](file:///Users/pileuszu/Repos/bist-mini-2/backend/api/v1/defense_arena/services.py))**
논문의 특정 구역에 편향되지 않고, 도입부(Abstract/Intro), 본문(Methodology), 결론(Conclusion)의 균형 잡힌 컨텍스트를 추출하는 스마트 샘플링 알고리즘입니다.
```python
def _sample_representative_chunks(self, chunks: List[DefenseArenaChunkEntity], max_chunks: int = 15) -> str:
    total = len(chunks)
    if total <= max_chunks:
        return "\n\n".join([c.text_chunk for c in chunks])
        
    sorted_chunks = sorted(chunks, key=lambda c: c.chunk_index)
    
    # 1. 도입부(20%), 본문(60%), 결론(20%) 경계 구분
    intro_boundary = int(total * 0.2)
    conclusion_boundary = int(total * 0.8)
    
    intro_chunks = sorted_chunks[:intro_boundary]
    body_chunks = sorted_chunks[intro_boundary:conclusion_boundary]
    conclusion_chunks = sorted_chunks[conclusion_boundary:]
    
    # 2. 비중 할당 (20%:60%:20% -> 3 : 9 : 3 구조화)
    intro_target = max(1, int(max_chunks * 0.2))
    conclusion_target = max(1, int(max_chunks * 0.2))
    body_target = max_chunks - intro_target - conclusion_target
    
    sampled = []
    
    def sample_subset(subset, target_count):
        if not subset:
            return []
        sub_len = len(subset)
        if sub_len <= target_count:
            return subset
        if target_count == 1:
            return [subset[sub_len // 2]]
        # 균등한 거리 배분으로 인덱스 추출
        indices = [int(i * (sub_len - 1) / (target_count - 1)) for i in range(target_count)]
        return [subset[idx] for idx in sorted(list(set(indices)))]
        
    sampled.extend(sample_subset(intro_chunks, intro_target))
    sampled.extend(sample_subset(body_chunks, body_target))
    sampled.extend(sample_subset(conclusion_chunks, conclusion_target))
    
    # 최종 청크 인덱스 순서대로 재정렬하여 문맥의 시간 순 복원
    sampled = sorted(list(set(sampled)), key=lambda c: c.chunk_index)
    return "\n\n".join([f"[Section Chunk {c.chunk_index + 1}]: {c.text_chunk}" for c in sampled])
```

### **🔍 주요 구문 및 설계 해설:**
- **구역 가중치 샘플링**: 단순 랜덤 샘플링은 논문의 핵심인 결론이나 도입부 요약이 누락될 수 있으나, 본 방식은 도입/본문/결론을 3:9:3 비율로 강제하여 전체 논문의 아키텍처 흐름을 LLM에게 고르게 전달해 줍니다.
