# MTEB Retrieval(정보 검색) 도메인 및 데이터셋 분석 명세서

본 문서는 **MTEB (Massive Text Embedding Benchmark)**의 정보 검색(Retrieval) 영역 및 **BEIR (Benchmarking Information Retrieval)** 프레임워크에서 제공하는 도메인별 데이터셋의 리스트와 구조를 정리한 명세서입니다. 

서비스 내 도메인별 논문 데이터 및 특화 데이터 검색 성능 평가와 RAG(Retrieval-Augmented Generation) 시스템 구축에 활용할 수 있도록 분류하였습니다.

---

## 📂 1. 학술 및 논문 (Scientific & Bio-Medical) 도메인 데이터셋

학술 논문의 초록(Abstract), 본문(Full-text) 또는 인용 관계 등을 다루는 핵심 데이터셋 리스트입니다.

### 🧬 TREC-COVID
*   **도메인**: Bio-Medical / Clinical Medicine (COVID-19 및 의생명 과학)
*   **데이터 출처**: CORD-19 (COVID-19 Open Research Dataset)
*   **코퍼스 형태**: COVID-19 관련 학술 논문의 제목, 초록, 저자, 학회 메타데이터 및 전문(Full-text)
*   **태스크**: 코로나19 바이러스 전파, 치료, 유전적 특성 등에 관한 임상/학술 질문에 대해 가장 관련성이 높은 논문을 검색하는 Ad-hoc Retrieval 태스크
*   **Hugging Face**: [mteb/trec-covid](https://huggingface.co/datasets/mteb/trec-covid)
*   **데이터 구조 및 매핑 명세**:
    *   `queries` (질문): 코로나19 관련 임상/의학 검색어 (예: "what is the origin of COVID-19", "effective treatments for covid-19")
    *   `corpus` (문서): 논문의 `doc_id`, `title`, `text` (초록 및 본문 일부)
    *   `qrels` (매핑): 3단계 적합도 평가 점수 (0: 무관, 1: 부분 연관, 2: 완전 연관)

### 🔬 SciFact
*   **도메인**: Scientific / Bio-Medical (과학 사실 검증)
*   **데이터 출처**: PubMed 과학 논문 초록
*   **코퍼스 형태**: 과학 논문의 제목 및 초록
*   **태스크**: 주어진 과학적 주장(Claim)이 참(Supported)인지 거짓(Refuted)인지 판별하기 위해, 이를 뒷받침하거나 반증하는 근거 학술 논문 초록 및 문장을 검색하는 Fact Verification 태스크
*   **Hugging Face**: [mteb/scifact](https://huggingface.co/datasets/mteb/scifact)
*   **데이터 구조 및 매핑 명세**:
    *   `queries` (주장): 검증 대상이 되는 단일 문장의 과학적 주장 (예: "Acupuncture is effective for treating depression.")
    *   `corpus` (문서): PubMed 학술 논문 초록 (`doc_id`, `title`, `text`)
    *   `qrels` (매핑): 참/거짓 판별의 근거가 되는 논문 ID와 구체적인 문장(Sentence) 매핑 정보

### 🥗 NFCorpus
*   **도메인**: Bio-Medical / Nutrition (영양학 및 일반 의학)
*   **데이터 출처**: NutritionFacts.org & PubMed 의학 도서관
*   **코퍼스 형태**: 의학 논문의 제목 및 초록
*   **태스크**: 일반인이 이해하기 쉬운 비전문적 일상 영양/건강 질의에 대해 신뢰할 수 있는 PubMed 의학 학술 논문을 검색하여 연관도를 매칭하는 태스크 (비전문가 용어와 전문가 연구 용어 간의 차이 극복 성능 측정)
*   **Hugging Face**: [mteb/nfcorpus](https://huggingface.co/datasets/mteb/nfcorpus)
*   **데이터 구조 및 매핑 명세**:
    *   `queries` (질문): 일반 사용자가 작성한 영양 및 건강 질문 (예: "how to lower cholesterol naturally")
    *   `corpus` (문서): 관련 PubMed 의학 논문의 제목과 초록 (`doc_id`, `title`, `text`)
    *   `qrels` (매핑): 다단계 relevance 점수 (3: 매우 연관, 2: 연관, 1: 부분 연관 등)

### 📄 SCIDOCS
*   **도메인**: Scientific / Computer Science (과학 논문 인용 및 의미 분석)
*   **데이터 출처**: 컴퓨터 과학(Computer Science) 분야 학술 논문
*   **코퍼스 형태**: 논문의 제목, 초록, 저자, 발표 연도, 피인용 수 등의 메타데이터
*   **태스크**: 논문 간의 인용 예측(Citation Prediction), 공동 저자 예측(Co-authorship), 논문 추천 등 다각도의 학술 문서 매칭 및 분류 성능을 평가하는 벤치마크
*   **Hugging Face**: [mteb/scidocs](https://huggingface.co/datasets/mteb/scidocs)
*   **데이터 구조 및 매핑 명세**:
    *   `queries` (대상 논문): 기준이 되는 학술 논문 정보
    *   `corpus` (문서 후보): 검색 후보군 논문 제목 및 초록 (`doc_id`, `title`, `text`)
    *   `qrels` (매핑): 기준 논문과 인용(cited), 동시 인용(co-cited), 추천 등의 의미론적 연결 강도로 정량화된 1/0 매핑 정보

### 🧪 BioASQ
*   **도메인**: Bio-Medical / Genomics (의생명 과학)
*   **데이터 출처**: BioASQ Challenge (의생명의학 분야 대규모 챌린지)
*   **코퍼스 형태**: PubMed 논문 초록
*   **태스크**: 생물/의학 전문가들이 작성한 고난도 질의에 대해 관련 PubMed 문헌을 고도로 정확하게 추출해내는 전문가 도메인 검색 태스크
*   **Hugging Face**: [mteb/bioasq](https://huggingface.co/datasets/mteb/bioasq)

---

## 📊 2. MTEB Retrieval 전체 도메인 및 데이터셋 리스트

MTEB Retrieval 태스크는 다양한 형태의 텍스트(논문, 위키피디아, 뉴스, 웹페이지, SNS 등)와 도메인을 포괄하여 임베딩 모델의 제로샷(Zero-shot) 일반화 능력을 평가합니다.

| 도메인 대분류 | 데이터셋 이름 | 데이터 형태 (Corpus) | 검색 태스크 성격 | Hugging Face 링크 |
| :--- | :--- | :--- | :--- | :--- |
| **의학 / 바이오** | **TREC-COVID** | 코로나19 의학 논문 초록/전문 | 학술 질문 -> 관련 논문 검색 | [Link](https://huggingface.co/datasets/mteb/trec-covid) |
| **의학 / 바이오** | **BioASQ** | 의생명 과학 학술 논문 초록 | 전문가 질의 -> 의생명 문헌 검색 | [Link](https://huggingface.co/datasets/mteb/bioasq) |
| **의학 / 영양학** | **NFCorpus** | 영양학/의학 학술 논문 초록 | 일반인 질의 -> 전문 논문 매칭 | [Link](https://huggingface.co/datasets/mteb/nfcorpus) |
| **과학기술 일반** | **SciFact** | 과학 논문 초록 | 과학 주장 -> 검증 근거 논문 검색 | [Link](https://huggingface.co/datasets/mteb/scifact) |
| **컴퓨터 과학** | **SCIDOCS** | 컴퓨터 과학 논문 메타데이터 | 논문 -> 인용/추천 관련 논문 검색 | [Link](https://huggingface.co/datasets/mteb/scidocs) |
| **일반 웹 검색** | **MS MARCO** | Bing 웹 페이지 추출 단락 (Passage) | 실제 검색창 쿼리 -> 해결책 단락 검색 | [Link](https://huggingface.co/datasets/mteb/msmarco) |
| **일반 지식** | **NQ (Natural Questions)** | Wikipedia 문서 전체 | 구글 검색 질의 -> 위키피디아 단락 검색 | [Link](https://huggingface.co/datasets/mteb/natural-questions) |
| **일반 지식** | **HotpotQA** | Wikipedia 문서 전체 | 다단계 추론 질의 -> 여러 위키 문서 통합 검색 | [Link](https://huggingface.co/datasets/mteb/hotpotqa) |
| **일반 지식** | **DBPedia-Entity** | DBPedia 엔티티 (지식 그래프) | 엔티티 명칭/속성 질의 -> 매칭 엔티티 검색 | [Link](https://huggingface.co/datasets/mteb/dbpedia-entity) |
| **일반 지식** | **FEVER** | Wikipedia 문서 전체 | 일반 주장 -> 사실 검증 근거 위키 검색 | [Link](https://huggingface.co/datasets/mteb/fever) |
| **기후 변화** | **Climate-FEVER** | Wikipedia 및 기후 변화 문서 | 기후 주장 -> 사실 검증 근거 문서 검색 | [Link](https://huggingface.co/datasets/mteb/climate-fever) |
| **금융 / 비즈니스**| **FiQA-2018** | 금융 포럼, 뉴스, 블로그 텍스트 | 금융 질문 -> 금융 뉴스/포럼 답변 검색 | [Link](https://huggingface.co/datasets/mteb/fiqa) |
| **온라인 커뮤니티**| **Quora** | Quora 중복 질문 쌍 데이터 | 사용자 질문 -> 의미가 동일한 질문 검색 | [Link](https://huggingface.co/datasets/mteb/quora) |
| **온라인 커뮤니티**| **CQADupStack** | StackExchange 12개 전문 서브포럼 | IT/수학/기술 질문 -> 중복 질문 검색 | [Link](https://huggingface.co/datasets/mteb/cqadupstack) |
| **뉴스** | **TREC-NEWS** | Washington Post 뉴스 기사 아카이브 | 특정 뉴스 주제 -> 심층 분석 기사 검색 | [Link](https://huggingface.co/datasets/mteb/trec-news) |
| **뉴스** | **Robust04** | 80~90년대 전통 뉴스 기사 코퍼스 | 복잡하고 모호한 질의 -> 뉴스 기사 검색 | [Link](https://huggingface.co/datasets/mteb/robust04) |
| **소셜 / 찬반토론**| **ArguAna** | 온라인 토론 플랫폼(Debatabase 등) | 특정 주장 -> 논리적으로 대응하는 반론 검색 | [Link](https://huggingface.co/datasets/mteb/arguana) |
| **소셜 / 찬반토론**| **Touché-2020** | 웹상의 논쟁거리/주장 문서 | 논쟁 질문 -> 찬반 논증 및 설득 문서 검색 | [Link](https://huggingface.co/datasets/mteb/touche2020) |
| **소셜 미디어** | **Signal-1M** | 실시간 트위터 트윗 및 뉴스 기사 | 이벤트 질의 -> 실시간 소셜 미디어 검색 | [Link](https://huggingface.co/datasets/mteb/signal1m) |

---

## 📝 3. 일반/커뮤니티 및 기타 도메인 데이터셋 상세

학술 논문 이외에 임베딩 모델의 범용적인 검색 능력을 검증하기 위해 MTEB에서 사용하는 데이터셋의 상세 내역입니다.

### 💻 CQADupStack (StackExchange Subsets)
*   **특징**: StackExchange 산하의 12개 독립된 전문 기술 분야 웹 포럼(Android, Gaming, Mathematica, Physics, Stats, Unix, WordPress 등)에서 수집되었습니다.
*   **활용**: 프로그래밍, 수학, 물리 등 고도의 IT 및 전문 지식 영역에서 중복 질의를 해결하기 위한 용도로 적합합니다.

### 💬 Quora Retrieval
*   **특징**: 일반적인 삶의 지혜부터 가벼운 일상 질문까지 포괄하는 Quora 플랫폼의 데이터셋입니다.
*   **활용**: 질문의 자구적인 매칭을 넘어 '문장의 숨은 의도'가 동일한지 파악하는 시맨틱 매칭 성능 평가에 최적화되어 있습니다.

### 💰 FiQA-2018
*   **특징**: 주식 정보, 투자 조언, 금융 용어 등 비즈니스 및 파이낸셜 전문 도메인에 특화되어 있습니다.
*   **활용**: 핀테크 서비스나 금융 특화 챗봇, RAG 기반 금융 정보 솔루션을 검증할 때 중요한 지표로 사용됩니다.

### 📰 MS MARCO
*   **특징**: 실제 Microsoft Bing 검색엔진에 입력된 사용자 쿼리와 그에 매칭된 웹 문서 단락들로 구성된 사실상의 글로벌 웹 검색 표준 데이터셋입니다.
*   **활용**: 가장 방대하고 실제 사용 사례에 가까운 일반 웹 검색 벤치마크 평가 데이터로 적합합니다.

---

## 🇰🇷 4. 한국어 특화 검색 (Korean Retrieval) 도메인 데이터셋 (참고)

한국어 서비스 혹은 다국어 RAG를 구축하는 경우 활용할 수 있는 MTEB 및 주요 한국어 검색 벤치마크 데이터셋 목록입니다.

1.  **Ko-StrategyQA**
    *   **도메인**: 일반 상식 및 논리적 추론 (Wikipedia 기반)
    *   **설명**: 예/아니오로 답할 수 있으나, 단번에 답하기 어렵고 여러 단계를 거쳐 지식을 조합(Multi-hop)해야 답할 수 있는 질문에 대해 관련 위키 문서를 검색하는 데이터셋입니다.
2.  **AutoRAG Retrieval**
    *   **도메인**: 금융, 공공, 의료, 법률, 커머스 등 5대 실무 비즈니스 영역
    *   **설명**: 한국어 공공 및 비즈니스 실제 PDF 문서를 파싱하여 정제한 고품질 실무 문서 검색 벤치마크입니다. RAG 성능 검증에 매우 강력합니다.
3.  **PublicHealthQA**
    *   **도메인**: 의료, 공중보건 및 웰니스
    *   **설명**: 한국어로 구성된 공중보건/의료 지식 질문에 대하여 정확한 의학 정보를 담은 관련 문서를 찾아 매칭하는 특화 데이터셋입니다.
4.  **MIRACL Retrieval (ko)**
    *   **도메인**: Wikipedia 일반 상식
    *   **설명**: 다국어 검색 평가 프로젝트(MIRACL)의 한국어 서브셋으로, 위키피디아 문서를 기반으로 질문과 답변 문맥을 매핑합니다.
