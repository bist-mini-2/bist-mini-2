import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Union, List, Optional
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 설정 변수 로드
MAC_MINI_IP = os.getenv("MAC_MINI_IP", "127.0.0.1")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-embedding")
OLLAMA_EMBED_URL = f"http://{MAC_MINI_IP}:11434/api/embeddings"
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "30"))
EMBEDDING_DIM = os.getenv("EMBEDDING_DIM")
EMBEDDING_DIM = int(EMBEDDING_DIM) if EMBEDDING_DIM else None


app = FastAPI(
    title="Local Distributed Embedding API Server",
    description="Mac Mini M4 Ollama 중계를 위한 임베딩 전용 프록시 API 서버",
    version="1.0.0"
)

# --- Pydantic 스키마 정의 ---

# 1. Ollama 규격
class OllamaEmbedRequest(BaseModel):
    model: Optional[str] = None
    prompt: Union[str, List[str]]
    options: Optional[dict] = None

class OllamaEmbedResponse(BaseModel):
    embedding: Union[List[float], List[List[float]]]

# 2. OpenAI 규격
class OpenAIEmbedRequest(BaseModel):
    model: Optional[str] = None
    input: Union[str, List[str]]
    user: Optional[str] = None

class OpenAIEmbedDatum(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int

class OpenAIEmbedUsage(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0

class OpenAIEmbedResponse(BaseModel):
    object: str = "list"
    data: List[OpenAIEmbedDatum]
    model: str
    usage: OpenAIEmbedUsage


# --- 내부 유틸리티 함수 ---

def fetch_single_embedding(text_prompt: str, model_name: str) -> List[float]:
    """맥미니 Ollama 서버로 단일 텍스트의 임베딩 요청을 전송하고 벡터를 가져옵니다."""
    payload = {
        "model": model_name,
        "prompt": text_prompt
    }
    try:
        response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=15)
        if response.status_code == 200:
            embedding = response.json().get("embedding")
            if embedding:
                # 지정된 차원이 있다면 슬라이싱하여 반환 (Matryoshka 임베딩 지원)
                if EMBEDDING_DIM and len(embedding) > EMBEDDING_DIM:
                    embedding = embedding[:EMBEDDING_DIM]
                return embedding
        raise HTTPException(
            status_code=response.status_code, 
            detail=f"Ollama 서버 에러: {response.text}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"맥미니 Ollama 서버 연결 실패: {e}"
        )


def get_embeddings_concurrently(prompts: List[str], model_name: str) -> List[List[float]]:
    """멀티스레드를 사용하여 리스트 형태의 프롬프트 임베딩을 병렬로 신속하게 추출합니다."""
    # 단일 쓰레드로만 연산이 막히지 않도록 ThreadPoolExecutor 활용
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(prompts))) as executor:
        # 원래 순서를 보장하기 위해 인덱스를 포함해 처리
        futures = {
            executor.submit(fetch_single_embedding, prompt, model_name): i 
            for i, prompt in enumerate(prompts)
        }
        
        results = [None] * len(prompts)
        for future in futures:
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"임베딩 병렬 처리 에러 (Index {idx}): {e}")
                
        return results


# --- API 엔드포인트 정의 ---

@app.get("/health", summary="서버 헬스 체크 및 맥미니 통신 진단")
def health_check():
    """임베딩 API 서버가 구동 중인지 및 맥미니 Ollama 서버와 정상 통신 중인지 확인합니다."""
    base_url = f"http://{MAC_MINI_IP}:11434"
    ollama_status = "UNKNOWN"
    try:
        r = requests.get(base_url, timeout=3)
        if r.status_code == 200:
            ollama_status = "UP"
        else:
            ollama_status = f"DOWN (HTTP {r.status_code})"
    except Exception as e:
        ollama_status = f"UNREACHABLE ({str(e)})"
        
    return {
        "status": "UP",
        "mac_mini_ip": MAC_MINI_IP,
        "ollama_status": ollama_status,
        "target_model": DEFAULT_MODEL
    }


@app.post("/api/embeddings", response_model=OllamaEmbedResponse, summary="Ollama 호환 규격 임베딩 반환 API")
def get_ollama_embeddings(request: OllamaEmbedRequest):
    """Ollama와 동일한 형태의 요청/응답 규격을 따르는 엔드포인트입니다.
    
    LangChain의 `OllamaEmbeddings` 클래스에서 이 주소를 바라보도록 연동 가능합니다.
    """
    model_name = request.model or DEFAULT_MODEL
    
    if isinstance(request.prompt, str):
        # 단일 텍스트 처리
        vector = fetch_single_embedding(request.prompt, model_name)
        return OllamaEmbedResponse(embedding=vector)
    elif isinstance(request.prompt, list):
        # 다중 텍스트 병렬 처리
        vectors = get_embeddings_concurrently(request.prompt, model_name)
        return OllamaEmbedResponse(embedding=vectors)
    else:
        raise HTTPException(status_code=400, detail="prompt 타입이 올바르지 않습니다 (str 또는 List[str] 필요).")


@app.post("/v1/embeddings", response_model=OpenAIEmbedResponse, summary="OpenAI 호환 규격 임베딩 반환 API")
def get_openai_embeddings(request: OpenAIEmbedRequest):
    """OpenAI 임베딩 API와 동일한 형태의 규격을 따르는 엔드포인트입니다.
    
    LangChain의 `OpenAIEmbeddings` 클래스에서 `openai_api_base`를 이 서버로 설정하여 연동 가능합니다.
    """
    model_name = request.model or DEFAULT_MODEL
    
    # 입력 파싱
    if isinstance(request.input, str):
        prompts = [request.input]
    elif isinstance(request.input, list):
        prompts = request.input
    else:
        raise HTTPException(status_code=400, detail="input 타입이 올바르지 않습니다 (str 또는 List[str] 필요).")

    # 병렬 임베딩 계산
    vectors = get_embeddings_concurrently(prompts, model_name)
    
    # OpenAI 응답 양식 빌드
    data_list = []
    total_chars = 0
    for idx, vec in enumerate(vectors):
        data_list.append(OpenAIEmbedDatum(
            object="embedding",
            embedding=vec,
            index=idx
        ))
        total_chars += len(prompts[idx])
        
    # 간략한 토큰 추정 (문자 수 기반 대략치 설정)
    estimated_tokens = int(total_chars / 4) + 1
    
    return OpenAIEmbedResponse(
        object="list",
        data=data_list,
        model=model_name,
        usage=OpenAIEmbedUsage(
            prompt_tokens=estimated_tokens,
            total_tokens=estimated_tokens
        )
    )
