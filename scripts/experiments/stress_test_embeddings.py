import os
import sys
import json
import time
import requests
import argparse
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# 콘솔 출력 인코딩 강제 설정 (윈도우 환경 및 한글 깨짐 대응)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 기본 경로 설정
DEFAULT_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/archive/arxiv-metadata-oai-snapshot.json"))

class StressTestResult:
    def __init__(self):
        self.lock = Lock()
        self.success_count = 0
        self.failure_count = 0
        self.latencies = []
        self.errors = {}

    def record_success(self, latency):
        with self.lock:
            self.success_count += 1
            self.latencies.append(latency)

    def record_failure(self, error_msg):
        with self.lock:
            self.failure_count += 1
            self.errors[error_msg] = self.errors.get(error_msg, 0) + 1

def load_samples(data_path, num_samples):
    """
    ArXiv JSON Lines 파일에서 지정된 수만큼의 초록(Abstract) 데이터를 스트리밍으로 로드합니다.
    """
    print(f"📂 데이터셋에서 {num_samples:,}개의 샘플을 로드하는 중...")
    samples = []
    if not os.path.exists(data_path):
        print(f"❌ 오류: 데이터를 찾을 수 없습니다. 경로: {data_path}")
        return samples

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                if len(samples) >= num_samples:
                    break
                try:
                    data = json.loads(line)
                    abstract = data.get("abstract", "").strip()
                    # 뉴라인 문자 정리
                    abstract = abstract.replace("\n", " ")
                    if abstract:
                        samples.append({
                            "id": data.get("id"),
                            "text": abstract
                        })
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"❌ 데이터 로드 중 에러 발생: {e}")
    
    print(f"✅ 샘플 {len(samples):,}개 로드 완료.")
    return samples

def send_embedding_request(url, model, text, timeout):
    """
    단일 텍스트에 대해 임베딩 API 서버에 요청을 전송하고 응답 시간을 반환합니다.
    """
    payload = {
        "model": model,
        "input": text
    }
    
    start_time = time.perf_counter()
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        latency = time.perf_counter() - start_time
        
        if response.status_code == 200:
            res_data = response.json()
            # 응답 구조 검증 (data가 존재하고 embedding 배열이 있는지 확인)
            if "data" in res_data and len(res_data["data"]) > 0 and "embedding" in res_data["data"][0]:
                return True, latency, None
            else:
                return False, latency, "InvalidResponseStructure"
        else:
            return False, latency, f"HTTP_{response.status_code}"
    except requests.exceptions.Timeout:
        latency = time.perf_counter() - start_time
        return False, latency, "RequestTimeout"
    except requests.exceptions.ConnectionError:
        latency = time.perf_counter() - start_time
        return False, latency, "ConnectionError"
    except Exception as e:
        latency = time.perf_counter() - start_time
        return False, latency, f"UnknownError: {str(e)}"

def run_stress_test(args):
    target_url = f"http://{args.ip}:{args.port}/v1/embeddings"
    print("\n" + "="*60)
    print("🚀 맥미니 M4 임베딩 프록시 서버 병렬 과부하 테스트를 준비합니다.")
    print(f"📡 대상 API URL  : {target_url}")
    print(f"🤖 대상 모델     : {args.model}")
    print(f"👥 동시 요청 수   : {args.concurrency} (workers)")
    print(f"📊 총 요청 건수   : {args.limit} 건")
    print(f"⏱️ 타임아웃 제한  : {args.timeout} 초")
    print("="*60 + "\n")

    # 1. 샘플 로드
    samples = load_samples(args.data_path, args.limit)
    if not samples:
        print("❌ 테스트를 진행할 샘플 데이터가 없습니다.")
        return

    # 실제 요청할 수 (로드된 샘플이 타겟보다 적을 경우 조정)
    total_requests = min(len(samples), args.limit)
    samples = samples[:total_requests]

    results = StressTestResult()
    start_time = time.time()
    
    print(f"\n⚡ 병렬 과부하 테스트를 시작합니다... (Concurrency={args.concurrency})")
    
    last_report_time = time.time()
    completed = 0

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        # 스레드풀에 작업 제출
        futures = {
            executor.submit(
                send_embedding_request, 
                target_url, 
                args.model, 
                sample["text"], 
                args.timeout
            ): sample for sample in samples
        }
        
        for future in as_completed(futures):
            success, latency, err_msg = future.result()
            if success:
                results.record_success(latency)
            else:
                results.record_failure(err_msg)
            
            completed += 1
            
            # 50건 완료 혹은 5초마다 진행 상태 출력
            if completed % 100 == 0 or (time.time() - last_report_time) > 5.0:
                elapsed = time.time() - start_time
                current_rate = completed / elapsed if elapsed > 0 else 0
                print(f"  > 진행률: {completed}/{total_requests} ({completed/total_requests*100:.1f}%) | "
                      f"성공: {results.success_count} | 실패: {results.failure_count} | "
                      f"처리 속도: {current_rate:.1f} req/sec")
                last_report_time = time.time()

    total_elapsed = time.time() - start_time
    
    # 통계 처리
    print("\n" + "="*60)
    print("📊 과부하 테스트 최종 결과 분석 리포트")
    print("="*60)
    print(f"⏱️ 총 소요 시간      : {total_elapsed:.2f} 초")
    print(f"📈 총 요청 시도 건수  : {total_requests:,} 건")
    print(f"✅ 성공적인 응답 건수: {results.success_count:,} 건")
    print(f"❌ 실패한 응답 건수  : {results.failure_count:,} 건")
    
    success_rate = (results.success_count / total_requests) * 100 if total_requests > 0 else 0
    print(f"🎯 전체 성공률       : {success_rate:.2f} %")
    
    throughput = total_requests / total_elapsed if total_elapsed > 0 else 0
    print(f"⚡ 초당 평균 처리량  : {throughput:.2f} req/sec")

    if results.latencies:
        latencies_np = np.array(results.latencies) * 1000 # ms 단위로 변환
        print("\n⏱️ 응답 지연 시간(Latency) 통계 (성공한 요청 기준):")
        print(f"  - 최소 지연 시간 (Min)  : {np.min(latencies_np):.1f} ms")
        print(f"  - 평균 지연 시간 (Mean) : {np.mean(latencies_np):.1f} ms")
        print(f"  - 중간 지연 시간 (Median): {np.median(latencies_np):.1f} ms")
        print(f"  - 최대 지연 시간 (Max)  : {np.max(latencies_np):.1f} ms")
        print(f"  - 90% 지연 시간 (p90)   : {np.percentile(latencies_np, 90):.1f} ms")
        print(f"  - 95% 지연 시간 (p95)   : {np.percentile(latencies_np, 95):.1f} ms")
        print(f"  - 99% 지연 시간 (p99)   : {np.percentile(latencies_np, 99):.1f} ms")
    else:
        print("\n⚠️ 성공한 요청이 없어 레이턴시 통계를 낼 수 없습니다.")

    if results.errors:
        print("\n❌ 발생 에러 통계:")
        for err, count in results.errors.items():
            err_percentage = (count / total_requests) * 100
            print(f"  - {err:<25} : {count:>5,} 건 ({err_percentage:.1f}%)")
    else:
        print("\n✨ 테스트 중 에러가 발생하지 않았습니다.")
        
    print("="*60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="맥미니 M4 임베딩 API 서버 병렬 과부하 테스트 도구")
    parser.add_argument("--ip", type=str, default="192.168.5.13", help="임베딩 서버 IP 주소 (기본: 192.168.5.13)")
    parser.add_argument("--port", type=str, default="8001", help="임베딩 서버 포트 번호 (기본: 8001)")
    parser.add_argument("--model", type=str, default="qwen3-embedding", help="사용할 임베딩 모델 (기본: qwen3-embedding)")
    parser.add_argument("--data-path", type=str, default=DEFAULT_DATA_PATH, help="테스트에 사용할 ArXiv JSON 파일 경로")
    parser.add_argument("--limit", type=int, default=1000, help="테스트에 사용할 총 샘플(요청) 수 (기본: 1000)")
    parser.add_argument("--concurrency", type=int, default=20, help="동시 요청을 수행할 스레드(워커) 수 (기본: 20)")
    parser.add_argument("--timeout", type=float, default=30.0, help="각 요청의 타임아웃 제한 시간(초) (기본: 30.0)")

    args = parser.parse_args()
    
    # 간단한 가상환경 내 의존성(numpy) 체크 및 예외처리
    try:
        import numpy
    except ImportError:
        print("⚠️ numpy 라이브러리가 필요합니다. 설치 중... (pip install numpy)")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        import numpy as np

    run_stress_test(args)
