import os
import time
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union, List, Optional
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 설정 변수 로드
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-embedding")
EMBEDDING_DIM = os.getenv("EMBEDDING_DIM")
EMBEDDING_DIM = int(EMBEDDING_DIM) if EMBEDDING_DIM else 3072 # 기본 3072차원 슬라이싱

# Hugging Face 로컬 모델 디렉토리 경로
HF_MODEL_NAME = os.path.abspath(os.path.join(os.path.dirname(__file__), "models/Qwen3-Embedding-4B"))

# 전역 모델 변수
embedding_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedding_model
    # Apple Silicon GPU(MPS) 우선 가속 설정
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"📡 [Lifespan] 로컬 GPU 가속 장치 설정: {device}")
    print(f"🤖 [Lifespan] 모델 로드 시작: {HF_MODEL_NAME}...")
    start_time = time.time()
    try:
        embedding_model = SentenceTransformer(HF_MODEL_NAME, device=device, trust_remote_code=True)
        print(f"✅ [Lifespan] 모델 메모리 적재 성공! (소요시간: {time.time() - start_time:.2f}초)")
    except Exception as e:
        print(f"❌ [Lifespan] 모델 로드 중 심각한 에러 발생: {e}")
        raise e
    yield
    # 종료 시 메모리 반환
    del embedding_model
    if device == "mps":
        torch.mps.empty_cache()
    print("💤 [Lifespan] 모델 언로드 및 리소스 해제 완료.")


app = FastAPI(
    title="Local High-Performance Embedding API Server",
    description="Mac Mini M4 GPU(MPS) 가속을 이용해 직접 추론 및 슬라이싱을 수행하는 고성능 임베딩 API 서버",
    version="2.0.0",
    lifespan=lifespan
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


# --- 임베딩 추론 헬퍼 함수 ---

def compute_embeddings(prompts: List[str]) -> List[List[float]]:
    """로드된 SentenceTransformer 모델을 통해 다이렉트 GPU 추론을 수행하고 차원을 슬라이싱합니다."""
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="임베딩 모델이 아직 준비되지 않았거나 로드에 실패했습니다.")
    
    try:
        # GPU MPS 가속 일괄 추론 진행 (sentence-transformers 자체 배치 병렬화 활용)
        embeddings = embedding_model.encode(prompts, batch_size=32, show_progress_bar=False)
        
        results = []
        for vec in embeddings:
            vector_list = vec.tolist()
            # Matryoshka 슬라이싱 및 부족할 시 제로 패딩(Zero Padding) 처리
            if EMBEDDING_DIM:
                if len(vector_list) > EMBEDDING_DIM:
                    vector_list = vector_list[:EMBEDDING_DIM]
                elif len(vector_list) < EMBEDDING_DIM:
                    # 차원이 부족한 경우 뒤를 0.0으로 채워 target dimension(3072)을 맞춤
                    # 코사인 유사도 점수는 수학적으로 완전히 동일하게 유지됨
                    vector_list += [0.0] * (EMBEDDING_DIM - len(vector_list))
            results.append(vector_list)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPU 임베딩 연산 중 에러 발생: {e}")


# --- API 엔드포인트 정의 ---

@app.get("/health", summary="서버 헬스 체크 및 GPU 상태 진단")
def health_check():
    """서버 작동 상태와 GPU(MPS) 장치 사용 여부를 모니터링합니다."""
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_loaded = embedding_model is not None
    return {
        "status": "UP",
        "device": device,
        "model_loaded": model_loaded,
        "model_name": HF_MODEL_NAME,
        "embedding_dim": EMBEDDING_DIM
    }


@app.post("/api/embeddings", response_model=OllamaEmbedResponse, summary="Ollama 호환 규격 직접 임베딩 반환 API")
def get_ollama_embeddings(request: OllamaEmbedRequest):
    """Ollama API와 규격이 일치하며, 내부적으로는 직접 GPU 추론 후 3072차원으로 슬라이싱하여 고속 반환합니다."""
    if isinstance(request.prompt, str):
        prompts = [request.prompt]
        is_single = True
    elif isinstance(request.prompt, list):
        prompts = request.prompt
        is_single = False
    else:
        raise HTTPException(status_code=400, detail="prompt 타입이 올바르지 않습니다 (str 또는 List[str] 필요).")

    vectors = compute_embeddings(prompts)
    
    if is_single:
        return OllamaEmbedResponse(embedding=vectors[0])
    else:
        return OllamaEmbedResponse(embedding=vectors)


@app.post("/v1/embeddings", response_model=OpenAIEmbedResponse, summary="OpenAI 호환 규격 직접 임베딩 반환 API")
def get_openai_embeddings(request: OpenAIEmbedRequest):
    """OpenAI API 규격과 일치하며, 직접 GPU(MPS) 추론을 수행하여 OpenAIEmbeddings 플러그인과 호환 작동합니다."""
    if isinstance(request.input, str):
        prompts = [request.input]
    elif isinstance(request.input, list):
        prompts = request.input
    else:
        raise HTTPException(status_code=400, detail="input 타입이 올바르지 않습니다 (str 또는 List[str] 필요).")

    vectors = compute_embeddings(prompts)
    
    data_list = []
    total_chars = 0
    for idx, vec in enumerate(vectors):
        data_list.append(OpenAIEmbedDatum(
            object="embedding",
            embedding=vec,
            index=idx
        ))
        total_chars += len(prompts[idx])
        
    # 간략한 토큰 추정
    estimated_tokens = int(total_chars / 4) + 1
    
    return OpenAIEmbedResponse(
        object="list",
        data=data_list,
        model=request.model or DEFAULT_MODEL,
        usage=OpenAIEmbedUsage(
            prompt_tokens=estimated_tokens,
            total_tokens=estimated_tokens
        )
    )
