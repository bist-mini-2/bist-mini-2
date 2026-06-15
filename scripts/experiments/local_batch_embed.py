import os
import json
import time
import torch
from sentence_transformers import SentenceTransformer

# 1. 경로 및 설정 정보
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/archive/arxiv-metadata-oai-snapshot.json"))
OUTPUT_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/archive/local_embeddings_output.jsonl"))

# Ollama의 qwen3-embedding에 대응하는 Hugging Face 원본 가중치 모델명
MODEL_NAME = "Qwen/Qwen3-Embedding-4B"
BATCH_SIZE = 64  # M4 GPU 메모리 최적 배치 사이즈


def main():
    # 2. MPS 가속 디바이스 확인 및 모델 로드
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"📡 임베딩 디바이스 설정: {device}")
    
    start_model = time.time()
    # Qwen 임베딩 모델은 trust_remote_code=True가 필요합니다.
    model = SentenceTransformer(MODEL_NAME, device=device, trust_remote_code=True)
    print(f"✅ 모델 로드 완료 (소요시간: {time.time() - start_model:.2f}초)")

    # 출력 디렉토리 확인 및 생성
    os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)

    if not os.path.exists(DATA_PATH):
        print(f"❌ 원본 데이터를 찾을 수 없습니다: {DATA_PATH}")
        return

    total_processed = 0
    batch_records = []
    start_time = time.time()

    print("🚀 로컬 배치 임베딩 연산을 시작합니다...")
    
    # 이미 임베딩된 기록이 있다면 이어서 수행할 수 있도록 재개(Resume) 처리
    existing_ids = set()
    if os.path.exists(OUTPUT_FILE_PATH):
        print("🔍 기존 임베딩 출력 파일 감지. 중복 제외 처리를 진행합니다...")
        with open(OUTPUT_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    existing_ids.add(record["arxiv_id"])
                except json.JSONDecodeError:
                    continue
        print(f"   -> 이미 처리 완료된 논문 수: {len(existing_ids):,} 건")

    # 출력 파일을 append('a') 모드로 오픈하여 중간에 끊겨도 이어서 작업 가능하게 설계
    with open(DATA_PATH, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE_PATH, "a", encoding="utf-8") as outfile:
        
        for line in infile:
            try:
                data = json.loads(line)
                arxiv_id = data.get("id")
                
                # 이미 처리한 ID는 건너뜀
                if arxiv_id in existing_ids:
                    continue
                
                # 3대 타겟 도메인(cs.*) 필터링 예시
                categories = data.get("categories", "")
                if not any(cat.startswith("cs.") for cat in categories.strip().split()):
                    continue
                
                abstract = data.get("abstract", "").strip().replace("\n", " ")
                if not abstract:
                    continue
                
                batch_records.append((arxiv_id, abstract))
                
                # 배치 사이즈만큼 쌓이면 GPU 연산 수행 및 파일 출력
                if len(batch_records) >= BATCH_SIZE:
                    texts = [rec[1] for rec in batch_records]
                    
                    # GPU MPS 가속 Dynamic Batching 연산
                    embeddings = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=False)
                    
                    # 파일에 순차 기록 (JSON Lines)
                    for i in range(len(batch_records)):
                        out_data = {
                            "arxiv_id": batch_records[i][0],
                            # 3072 차원으로 맞추기 위해 슬라이싱 처리
                            "embedding": embeddings[i].tolist()[:3072]
                        }
                        outfile.write(json.dumps(out_data) + "\n")
                    
                    total_processed += len(batch_records)
                    batch_records = []
                    
                    # 1만 건마다 진행 상황 로깅
                    if total_processed % 10000 == 0:
                        elapsed = time.time() - start_time
                        rate = total_processed / elapsed
                        print(f"  > 누적 연산: {total_processed:,} 건 | 소요 시간: {elapsed:.1f}초 | 속도: {rate:.1f} items/sec")
                        
            except Exception as e:
                print(f"⚠️ 라인 처리 중 오류 발생 (건너뜀): {e}")

        # 잔여 데이터 처리
        if batch_records:
            texts = [rec[1] for rec in batch_records]
            embeddings = model.encode(texts, batch_size=len(texts), show_progress_bar=False)
            for i in range(len(batch_records)):
                out_data = {
                    "arxiv_id": batch_records[i][0],
                    "embedding": embeddings[i].tolist()[:3072]
                }
                outfile.write(json.dumps(out_data) + "\n")
            total_processed += len(batch_records)

    total_elapsed = time.time() - start_time
    print(f"\n🎉 전체 로컬 임베딩 파일 저장 완료! 총 {total_processed:,} 건 | 소요시간: {total_elapsed:.2f}초")

if __name__ == "__main__":
    main()
