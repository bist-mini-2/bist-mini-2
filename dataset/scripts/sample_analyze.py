import os
import json
import time
import sys
from collections import Counter

# 콘솔 출력 인코딩 강제 설정 (윈도우 환경 대응)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 파일 경로 정의
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/archive/arxiv-metadata-oai-snapshot.json"))

def analyze_arxiv_dataset():
    """
    ArXiv 대용량 JSON 파일(JSON Lines format)을 스트리밍 방식으로 읽어 
    데이터 샘플을 확인하고, 카테고리별 논문 수 및 3대 타겟 도메인의 
    논문 개수를 통계적으로 분석(EDA)하는 스크립트입니다.
    """
    if not os.path.exists(DATA_PATH):
        print(f"오류: 데이터를 찾을 수 없습니다. 아래 경로에 파일이 존재해야 합니다:\n{DATA_PATH}")
        return

    print("======================================================================")
    print("  ArXiv 데이터셋 EDA 및 샘플 스트리밍 분석을 시작합니다.")
    print(f"  대상 파일: {DATA_PATH}")
    print(f"  파일 크기: {os.path.getsize(DATA_PATH) / (1024 * 1024 * 1024):.2f} GB")
    print("======================================================================\n")

    # 1. 처음 3개 데이터 샘플 스트리밍 출력
    print("--- [1] 처음 3개 논문 데이터 샘플 구조 확인 ---")
    samples_shown = 0
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if samples_shown >= 3:
                break
            try:
                data = json.loads(line)
                print(f"\n[샘플 #{samples_shown + 1}] ID: {data.get('id')}")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                samples_shown += 1
            except Exception as e:
                print(f"샘플 파싱 중 오류: {e}")
    print("\n-----------------------------------------------\n")

    # 2. 전체 데이터 분석 (Line-by-line Streaming)
    print("  전체 데이터 통계 분석 중... (대용량 파일이므로 시간이 약간 소요됩니다.)")
    print("  진행 상황을 20만 라인마다 출력합니다.")
    
    start_time = time.time()
    total_papers = 0
    
    # 카테고리 통계용 카운터
    # 1) 주요 카테고리 (첫 번째 카테고리) 기준
    primary_category_counter = Counter()
    # 2) 3대 타겟 도메인 분류 기준
    target_domains = {
        "Biotechnology (q-bio.*)": 0,
        "Computer Science (cs.*)": 0,
        "Astronomy (astro-ph.*)": 0,
        "Others": 0
    }

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            for line in f:
                total_papers += 1
                
                # 20만 개마다 진행 상황 출력
                if total_papers % 200000 == 0:
                    elapsed = time.time() - start_time
                    rate = total_papers / elapsed
                    print(f"  > 분석 완료: {total_papers:,} 개 논문... (소요 시간: {elapsed:.1f}초, 속도: {rate:.0f} lines/sec)")

                try:
                    data = json.loads(line)
                    categories_str = data.get("categories", "")
                    if not categories_str:
                        continue
                    
                    # 카테고리는 여러 개가 공백으로 구분되어 있을 수 있음
                    cats = categories_str.strip().split()
                    if not cats:
                        continue
                        
                    # 주요 카테고리 기록
                    primary_cat = cats[0]
                    primary_category_counter[primary_cat] += 1
                    
                    # 3대 타겟 도메인 매핑 검사
                    is_mapped = False
                    for cat in cats:
                        if cat.startswith("q-bio"):
                            target_domains["Biotechnology (q-bio.*)"] += 1
                            is_mapped = True
                            break
                        elif cat.startswith("cs."):
                            target_domains["Computer Science (cs.*)"] += 1
                            is_mapped = True
                            break
                        elif cat.startswith("astro-ph"):
                            target_domains["Astronomy (astro-ph.*)"] += 1
                            is_mapped = True
                            break
                    
                    if not is_mapped:
                        target_domains["Others"] += 1
                        
                except json.JSONDecodeError:
                    continue
                    
    except KeyboardInterrupt:
        print("\n  사용자에 의해 분석이 중단되었습니다. 현재까지 집계된 통계를 출력합니다.")
    
    end_time = time.time()
    total_elapsed = end_time - start_time
    
    print("\n======================================================================")
    print("  ArXiv 데이터셋 EDA 분석 결과 보고서")
    print("======================================================================")
    print(f"  총 소요 시간: {total_elapsed:.2f} 초")
    print(f"  총 분석 논문 수: {total_papers:,} 개")
    print("----------------------------------------------------------------------")
    print("  [1] 3대 타겟 도메인 분류 통계 (모든 매핑 카테고리 검사 기준)")
    for domain, count in target_domains.items():
        percentage = (count / total_papers) * 100 if total_papers > 0 else 0
        print(f"  * {domain:<25} : {count:>8,} 개 ({percentage:.2f}%)")
    
    print("----------------------------------------------------------------------")
    print("  [2] 가장 논문이 많은 상위 15대 카테고리 (주요 카테고리 기준)")
    for rank, (cat, count) in enumerate(primary_category_counter.most_common(15), 1):
        percentage = (count / total_papers) * 100 if total_papers > 0 else 0
        print(f"  {rank:>2}. {cat:<15} : {count:>8,} 개 ({percentage:.2f}%)")
        
    print("======================================================================\n")

if __name__ == "__main__":
    analyze_arxiv_dataset()
