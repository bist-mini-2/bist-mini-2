import sys
import os
import json
import requests

# Windows 인코딩 대응
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def test_embedding_api(target_ip="192.168.5.13", target_port="8001"):
    """
    맥미니 M4에서 구동 중인 임베딩 중계 프록시 API(FastAPI) 서버를 대상으로
    Ollama 호환 규격 및 OpenAI 호환 규격 엔드포인트 통신을 테스트하는 스크립트입니다.
    """
    print("==========================================================")
    print("🧪 맥미니 M4 임베딩 API 호출 테스트를 실행합니다.")
    print(f"📡 타겟 서버: http://{target_ip}:{target_port}")
    print("==========================================================\n")

    # 테스트용 샘플 데이터
    sample_prompts = [
        "컴퓨터 과학 분야 인공지능 연구 논문 초록 데이터셋",
        "생명공학 mRNA 백신 면역 작용 원리 RAG 임베딩"
    ]
    model_name = "qwen3-embedding"

    # 1. Ollama 호환 API (/api/embeddings) 테스트
    ollama_url = f"http://{target_ip}:{target_port}/api/embeddings"
    print(f"--- [1] Ollama 호환 API 테스트 (/api/embeddings) ---")
    print(f"요청 URL: {ollama_url}")
    
    ollama_payload = {
        "model": model_name,
        "prompt": sample_prompts
    }

    try:
        response = requests.post(ollama_url, json=ollama_payload, timeout=5)
        print(f"응답 상태 코드: {response.status_code}")
        if response.status_code == 200:
            res_json = response.json()
            embeddings = res_json.get("embedding")
            if embeddings:
                print("✅ 통신 성공!")
                print(f"  - 추출된 임베딩 개수: {len(embeddings)}개")
                print(f"  - 첫 번째 임베딩 차원: {len(embeddings[0])}차원 (3072차원 규격 확인)")
                print(f"  - 샘플 벡터 값 (앞 5개): {embeddings[0][:5]}")
            else:
                print("❌ 오류: 응답에 'embedding' 키가 존재하지 않습니다.")
                print(res_json)
        else:
            print(f"❌ 요청 실패: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 연결 실패 (서버가 켜져 있지 않거나 네트워크 차단): {e}")

    print("\n" + "-"*58 + "\n")

    # 2. OpenAI 호환 API (/v1/embeddings) 테스트
    openai_url = f"http://{target_ip}:{target_port}/v1/embeddings"
    print(f"--- [2] OpenAI 호환 API 테스트 (/v1/embeddings) ---")
    print(f"요청 URL: {openai_url}")
    
    openai_payload = {
        "model": model_name,
        "input": sample_prompts
    }

    try:
        response = requests.post(openai_url, json=openai_payload, timeout=5)
        print(f"응답 상태 코드: {response.status_code}")
        if response.status_code == 200:
            res_json = response.json()
            data_list = res_json.get("data", [])
            if data_list:
                print("✅ 통신 성공!")
                print(f"  - 추출된 데이터 개수: {len(data_list)}개")
                first_vector = data_list[0].get("embedding", [])
                print(f"  - 첫 번째 임베딩 차원: {len(first_vector)}차원 (OpenAI 규격 확인)")
                print(f"  - 샘플 벡터 값 (앞 5개): {first_vector[:5]}")
            else:
                print("❌ 오류: 응답에 'data' 목록이 비어 있거나 존재하지 않습니다.")
                print(res_json)
        else:
            print(f"❌ 요청 실패: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 연결 실패 (서버가 켜져 있지 않거나 네트워크 차단): {e}")

    print("\n==========================================================")

if __name__ == "__main__":
    # 사용자가 명령행 인자로 IP와 포트를 넘길 수 있도록 지원
    # 예: python test_embedding_call.py 192.168.5.13 8001
    ip = "192.168.5.13"
    port = "8001"
    
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    if len(sys.argv) > 2:
        port = sys.argv[2]
        
    test_embedding_api(ip, port)
