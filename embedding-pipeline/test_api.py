import requests
import json

LOCAL_API_URL = "http://localhost:8001"

def test_health():
    print("==================================================")
    print("1. API 서버 헬스체크 및 백본 진단 요청")
    print("--------------------------------------------------")
    try:
        r = requests.get(f"{LOCAL_API_URL}/health", timeout=5)
        print(f"상태 코드: {r.status_code}")
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ API 서버 연결 실패: {e}")
        print("💡 uvicorn main:app --port 8001 명령으로 서버를 구동했는지 확인하세요.")

def test_ollama_endpoint():
    print("\n==================================================")
    print("2. Ollama 호환 규격 (/api/embeddings) 호출 테스트")
    print("--------------------------------------------------")
    
    # 단일 문장 임베딩
    payload_single = {
        "prompt": "동일 네트워크 내부 기가비트 이더넷 통신 속도 측정용 테스트 문항입니다."
    }
    
    # 복수 문장 배치 임베딩
    payload_batch = {
        "prompt": [
            "첫 번째 문장입니다.",
            "두 번째 문장입니다.",
            "세 번째 문장입니다."
        ]
    }
    
    try:
        # 1. 단일 요청
        print("  - 단일 문장 요청 송신...")
        r_single = requests.post(f"{LOCAL_API_URL}/api/embeddings", json=payload_single, timeout=10)
        if r_single.status_code == 200:
            vector = r_single.json().get("embedding")
            print(f"  ✅ 단일 임베딩 수신 완료! (차원: {len(vector)})")
        else:
            print(f"  ❌ 단일 요청 실패 (상태: {r_single.status_code}): {r_single.text}")
            
        # 2. 배치 요청
        print("  - 3개 문장 배치 요청 송신 (스레드풀 병렬 처리)...")
        r_batch = requests.post(f"{LOCAL_API_URL}/api/embeddings", json=payload_batch, timeout=10)
        if r_batch.status_code == 200:
            vectors = r_batch.json().get("embedding")
            print(f"  ✅ 배치 임베딩 수신 완료! (개수: {len(vectors)}, 개별 차원: {len(vectors[0])})")
        else:
            print(f"  ❌ 배치 요청 실패 (상태: {r_batch.status_code}): {r_batch.text}")
            
    except Exception as e:
        print(f"❌ 호출 실패: {e}")

def test_openai_endpoint():
    print("\n==================================================")
    print("3. OpenAI 호환 규격 (/v1/embeddings) 호출 테스트")
    print("--------------------------------------------------")
    
    payload = {
        "input": [
            "OpenAI API 규격을 호환하여 랭체인을 연동하는 시뮬레이션입니다.",
            "이 엔드포인트를 바라보는 OpenAIEmbeddings 인스턴스를 즉시 꽂아쓸 수 있습니다."
        ]
    }
    
    try:
        r = requests.post(f"{LOCAL_API_URL}/v1/embeddings", json=payload, timeout=10)
        if r.status_code == 200:
            res_json = r.json()
            data = res_json.get("data", [])
            print(f"  ✅ OpenAI 호환 임베딩 수신 완료!")
            print(f"  - 모델: {res_json.get('model')}")
            print(f"  - 반환 벡터 개수: {len(data)}")
            print(f"  - 토큰 예측 사용량: {res_json.get('usage', {}).get('total_tokens')} tokens")
            if data:
                print(f"  - 첫 번째 벡터 크기: {len(data[0].get('embedding'))}")
        else:
            print(f"  ❌ OpenAI 규격 실패 (상태: {r.status_code}): {r.text}")
    except Exception as e:
        print(f"❌ 호출 실패: {e}")

if __name__ == "__main__":
    test_health()
    test_ollama_endpoint()
    test_openai_endpoint()
