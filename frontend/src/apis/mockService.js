// mockService.js
// 로컬스토리지(localStorage)를 활용하여 클라이언트 측 가데이터 데이터베이스를 구현하고 유지합니다.

const LOCAL_STORAGE_KEY = "bist_mini_mock_db";

// 초기화 데이터
const defaultDb = {
  sessions: [
    {
      session_id: "session-1",
      title: "CS.NE 병렬 RAG 최적화 검증",
      created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
      messages: [
        { role: "user", content: "HNSW 인덱스를 사용한 pgvector 검색 성능 평가 요약해줘" },
        {
          role: "assistant",
          content: `HNSW 인덱스를 적용한 pgvector(3072차원) 검색 성능 검증 결과는 다음과 같습니다:

1. **검색 레이턴시**: 100,000건의 고밀도 임베딩을 탑재한 상태에서 HNSW 인덱스를 통해 Top-3 검색 시 평균 **14.8 ms** 내외의 초고속 조회를 실현했습니다. (기존 Linear Scan 대비 20배 이상 단축)
2. **최적 임계값**: 코사인 유사도 임계치 **0.35** 설정 시, 학술 노이즈 필터링 성공률 **99.4%** 및 F1-Score **0.91**로 정보 누수와 과도한 필터링의 최적의 Trade-off를 입증하였습니다.
3. **병렬 RAG 동시 타격**: RAG 및 실시간 웹 검색(Tavily)의 비동기 병렬 결합을 통해 총 응답 속도를 기존 9.22초에서 **7.10초**로 단축(22.99% 개선)했습니다.

궁금한 사항이 더 있으시면 아래 추천 질문들을 확인해 보세요.`,
          sources: [
            { arxiv_id: "2403.0123", title: "Evaluating Vector Database Performance under High Write Load", summary: "HNSW index comparison." },
            { arxiv_id: "2405.4521", title: "Reciprocal Rank Fusion for Hybrid Search Systems", summary: "BM25 and Vector Search merging." }
          ],
          web_sources: [
            { url: "https://openai.com/blog", title: "OpenAI Embeddings API updates", summary: "3072 dimension embedding capabilities." }
          ],
          suggestions: [
            "HNSW vs IVF-Flat 차이점은 무엇인가요?",
            "실시간 백그라운드 배치 분석의 진행률 업데이트 로직을 알려주세요.",
            "임계값 0.35 설정 시 Recall 값 하락 폭은 어느 정도인가요?"
          ]
        }
      ]
    },
    {
      session_id: "session-2",
      title: "Bio CRISPR 전달 바이러스 한계 연구",
      created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
      messages: [
        { role: "user", content: "CRISPR-Cas9 기법의 전달 바이러스 포장 한계에 대해 설명해줘" },
        {
          role: "assistant",
          content: `CRISPR-Cas9 유전자 가위 전달체로 가장 널리 기용되는 **아데노 부속 바이러스(Adeno-Associated Virus, AAV)**의 물리적 포장 한계 및 해소 동향은 다음과 같습니다:

1. **물리적 포장 한계(Packaging Capacity)**:
   - AAV 벡터의 최대 유입 단백질 코딩 용량은 약 **4.7 kb**로 극히 제한되어 있습니다.
2. **SpCas9의 크기 병목**:
   - 가장 대표적인 *Streptococcus pyogenes* Cas9 (SpCas9) 단백질 코딩 서열은 단독으로 약 **4.2 kb**를 차지합니다.
   - 이에 따라 타겟 gRNA, 프로모터(Promoter), 폴리아데닐화 서열(PolyA) 등을 하나의 AAV 캡시드 내에 동시 탑재하는 단일 벡터 포장이 사실상 불가능합니다.
3. **학계의 극복 방안**:
   - **소형 Cas9 적용**: 크기가 작은 *Staphylococcus aureus* Cas9 (SaCas9, 약 **3.2 kb**) 혹은 Cas12a 단백질을 대체 도입하여 잔여 용량을 확보합니다.
   - **Dual-AAV 시스템**: Cas9 유전자를 두 개로 분할(Split-Cas9)하여 두 개의 AAV로 나누어 주입한 후, 표적 세포 내에서 인테인(Intein) 접합을 통해 복원하는 듀얼 벡터 기법을 구사합니다.`,
          sources: [
            { arxiv_id: "2308.8912", title: "Viral Vector Delivery Systems for CRISPR-Cas9", summary: "AAV capacities." },
            { arxiv_id: "2401.0945", title: "Dual-AAV Intein-mediated Gene Splicing in Vivo", summary: "Split Cas9 reconstitution." }
          ],
          web_sources: [],
          suggestions: [
            "SaCas9의 타겟 시퀀스 PAM 사이트 제약은 무엇인가요?",
            "AAV 외에 LNP(지질나노입자)를 활용한 비바이러스 전달체의 장점은?",
            "Split-Cas9의 생체 내 재조합 효율(%) 데이터가 궁금합니다."
          ]
        }
      ]
    }
  ],
  gems: [
    {
      gem_id: "gem-1",
      name: "NASA 제트추진연구소 우주론 비서",
      db_sources: ["astronomy"],
      system_prompt: "당신은 NASA JPL 소속의 수석 천체물리학자이며 우주 배경 복사(CMB) 및 암흑물질 분야의 최고 권위자입니다. 정중하면서도 심도 있는 학술적 어조로 답변하십시오.",
      has_files: true,
      created_at: new Date(Date.now() - 3600000 * 50).toISOString(),
      files: [
        { file_id: "file-1", filename: "astro_background_cmb.pdf", chunk_count: 34, uploaded_at: new Date(Date.now() - 3600000 * 48).toISOString() }
      ],
      sessions: []
    },
    {
      gem_id: "gem-2",
      name: "CRISPR 생명정보학 특화 젬",
      db_sources: ["bio"],
      system_prompt: "당신은 세계 최고의 유전자 가위 생물정보학 분석가입니다. 코딩 및 서열 매칭 한계를 정량적 데이터 기반으로 꼼꼼하게 검증해 줍니다.",
      has_files: false,
      created_at: new Date(Date.now() - 3600000 * 12).toISOString(),
      files: [],
      sessions: []
    }
  ],
  tasks: [
    {
      task_id: "task-1",
      domain: "cs",
      query: "Retrieval Augmented Generation tuning",
      status: "COMPLETED",
      progress: 100,
      created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
      updated_at: new Date(Date.now() - 3600000 * 4.9).toISOString(),
      result: {
        papers: [
          {
            title: "Dense-Sparse Fusion in Information Retrieval",
            arxiv_id: "2404.1235",
            similarity: 0.94,
            problems_solved: [
              {
                summary: "Reciprocal Rank Fusion (RRF) successfully merges BM25 lexical scores with semantic dense embeddings.",
                source_quote: "Integrating lexical scores prevents semantic hallucination in rare tokens."
              }
            ],
            limitations: [
              {
                summary: "Concurreny write loads drop HNSW index recall quality below 75%.",
                source_quote: "High thread lock contention during index creation severely impacts build reliability."
              }
            ]
          }
        ],
        common_limitations: [
          "Lacks hybrid BM25 cross-domain ranking, causing 14% recall decay.",
          "Physical shredding daemon latency delays file removal by up to 2.4 seconds."
        ],
        suggested_directions: [
          "Apply a dynamic sub-collection partition method (Gem Isolation) to bypass index locks.",
          "Introduce a real-time shredding listener that cleans temporary PostgresSaver checkpointer states."
        ]
      },
      translated_result: {
        papers: [
          {
            title: "정보 검색에서의 밀집-희소 융합 (Dense-Sparse Fusion)",
            arxiv_id: "2404.1235",
            similarity: 0.94,
            problems_solved: [
              {
                summary: "상호 순위 융합(RRF)을 통해 BM25 어휘 점수와 시맨틱 고밀도 임베딩을 성공적으로 병합했습니다.",
                source_quote: "Integrating lexical scores prevents semantic hallucination in rare tokens."
              }
            ],
            limitations: [
              {
                summary: "동시 쓰기 부하는 HNSW 인덱스 재현율 품질을 75% 미만으로 떨어뜨립니다.",
                source_quote: "High thread lock contention during index creation severely impacts build reliability."
              }
            ]
          }
        ],
        common_limitations: [
          "이종 도메인 하이브리드 어휘 랭킹이 결여되어 약 14%의 재현율 감쇄가 발생합니다.",
          "물리적 파쇄 데몬의 대기시간 지연으로 파일 삭제가 최대 2.4초 지연됩니다."
        ],
        suggested_directions: [
          "인덱스 락을 우회하기 위해 젬 단위의 동적 서브 컬렉션 분할 기법을 도입합니다.",
          "임시 PostgresSaver 체크포인터 상태를 주기적으로 소거하는 실시간 파쇄 리스너를 장착합니다."
        ]
      }
    }
  ],
  notifications: [
    {
      id: "notif-1",
      message: "[성능 검증] 3대 도메인 10만 건 벌크 적재 및 HNSW(m=16, ef=64) 인덱싱 완성 완료",
      read: false,
      created_at: new Date(Date.now() - 600000).toISOString()
    },
    {
      id: "notif-2",
      message: "비동기 배치 분석 'Retrieval Augmented Generation tuning' 작업이 성공적으로 완료되었습니다.",
      read: true,
      created_at: new Date(Date.now() - 3600000 * 5).toISOString()
    }
  ],
  defenseHistory: [
    {
      session_id: "history-1",
      title: "다중 에이전트 토론 기반의 가설 자가 검증 검토",
      score: 88,
      status: "PASS",
      created_at: new Date(Date.now() - 3600000 * 3).toISOString(),
      file_name: "self_consistency_debate_draft.pdf",
      target_journal: "IEEE Access",
      hypothesis: "Multi-Agent Debate loops with split validator and novelty agent improve hypothesis factual correctness.",
      peerReview: {
        methodology_score: 90,
        novelty_score: 85,
        clarity_score: 90,
        feedback: "가설 제안의 구글 RAG 결합 및 자가 디펜스 아레나 아키텍처는 흥미로우며, 실제 Latency 단축률 증명이 훌륭히 기재되어 있음. 단, 다수결 합의(Self-Consistency) 시점의 오버헤드 정량 분석이 추가되면 좋겠음."
      },
      messages: [
        { role: "assistant", content: "학회 심사위원 에이전트단입니다. 제출하신 논문의 피어 리뷰 종합 점수는 88점(PASS)입니다. 모의 디펜스 압박 질문을 시작합니다.\n\n[Q1] 가설 검증 시 3대 심사위원 에이전트 간의 토론 루프를 2회 이상 보완하도록 설계하셨는데, 이 순환형 그래프(Stateful Ring Graph)에서 발생할 수 있는 교착 상태(Deadlock)나 API 원가 과다 소모 한계는 어떻게 제어하시겠습니까?" }
      ]
    },
    {
      session_id: "history-2",
      title: "HNSW pgvector 인덱스 대규모 실시간 갱신성 검증",
      score: 62,
      status: "FAIL",
      created_at: new Date(Date.now() - 3600000 * 25).toISOString(),
      file_name: "hnsw_realtime_updates.pdf",
      target_journal: "Bioinformatics",
      hypothesis: "HNSW index maintains search recall above 90% during parallel background streaming ingest.",
      peerReview: {
        methodology_score: 60,
        novelty_score: 65,
        clarity_score: 62,
        feedback: "초당 1만 건 쓰기 동시성 하에서 HNSW의 lock contention에 따른 재현율 하락 수치가 명확히 밝혀지지 않았음. 수치 검증이 부실함."
      },
      messages: [
        { role: "assistant", content: "심사위원단입니다. 종합 피어리뷰 점수 62점(FAIL)으로 보완이 시급합니다.\n\n[Q1] HNSW 생성 시 ef_construction=64 설정을 고수하셨는데, 쓰기 속도를 위해 이를 낮출 경우 탐색 정밀도가 급락합니다. 실시간 갱신 환경에서 Recall과 Insert throughput 간의 정량적 트레이드오프 검증 결과가 왜 누락되었습니까?" }
      ]
    }
  ]
};

// DB 로드 또는 초기화
function getDb() {
  if (typeof window === "undefined") return defaultDb;
  const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
  if (!raw) {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(defaultDb));
    return defaultDb;
  }
  try {
    const db = JSON.parse(raw);
    let needsSave = false;
    if (db && Array.isArray(db.gems)) {
      db.gems.forEach(g => {
        if (typeof g.db_sources === "string") {
          g.db_sources = [g.db_sources];
          needsSave = true;
        }
      });
    }
    if (needsSave) {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(db));
    }
    return db;
  } catch {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(defaultDb));
    return defaultDb;
  }
}

function saveDb(db) {
  if (typeof window !== "undefined") {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(db));
  }
}

// ----------------- Auth & Member -----------------
export function login(mid, mpassword) {
  return {
    access_token: "mock-jwt-token-abcdef123456",
    token_type: "bearer",
    username: mid || "guest_researcher",
    role: mid === "admin" ? "ROLE_ADMIN" : "ROLE_USER"
  };
}

export function join(joinData) {
  return { status: "success", message: "회원 가입 완료 (Mock)" };
}

// ----------------- Chat Sessions (Feature 1) -----------------
export function getSessions() {
  const db = getDb();
  return { status: "success", data: db.sessions.map(s => ({ session_id: s.session_id, title: s.title, created_at: s.created_at })) };
}

export function createSession(title) {
  const db = getDb();
  const newSession = {
    session_id: "session-" + Date.now(),
    title: title || "새로운 학술 대화방",
    created_at: new Date().toISOString(),
    messages: []
  };
  db.sessions.unshift(newSession);
  saveDb(db);
  return { status: "success", data: newSession };
}

export function deleteSession(sessionId) {
  const db = getDb();
  db.sessions = db.sessions.filter(s => s.session_id !== sessionId);
  saveDb(db);
  return { status: "success", message: "세션 삭제 완료" };
}

export function renameSession(sessionId, title) {
  const db = getDb();
  const session = db.sessions.find(s => s.session_id === sessionId);
  if (session) {
    session.title = title;
    saveDb(db);
  }
  return { status: "success", data: session };
}

export function getMessages(sessionId) {
  const db = getDb();
  const session = db.sessions.find(s => s.session_id === sessionId);
  return { status: "success", data: session ? session.messages : [] };
}

export function sendMessage(sessionId, message) {
  const db = getDb();
  const session = db.sessions.find(s => s.session_id === sessionId);
  if (session) {
    session.messages.push({ role: "user", content: message });
    const responseData = mockChatResponses[0];
    const assistantMsg = {
      role: "assistant",
      content: responseData.answer,
      sources: responseData.sources,
      web_sources: responseData.web_sources,
      suggestions: responseData.suggestions
    };
    session.messages.push(assistantMsg);
    saveDb(db);
    return { status: "success", data: assistantMsg };
  }
  throw new Error("세션을 찾을 수 없습니다.");
}

// 듀얼 RAG 시뮬레이션 스트리밍 답변 목록
const mockChatResponses = [
  {
    answer: `질문하신 내용에 대한 병렬 RAG(학술 논문 및 실시간 웹 검색) 교차 융합 답변입니다:

1. **이론적 근거 및 선행 연구**:
   - arXiv의 최신 연구에 따르면, HNSW pgvector 3072차원 고정 인덱스 설정은 Cosine Similarity 기준 **0.35**에서 가장 안정적인 노이즈 차단을 제공합니다. [1]
   - 다중 에이전트 결합 모델(Split-Validator & Novelty Agent)은 생성 가설의 Fact를 교차 확인하여 환각률을 18.2% 가량 억제합니다.

2. **실시간 트렌드 및 최신 동향**:
   - 최근 OpenAI 및 빅테크 벤더들이 발표한 임베딩 API 명세에 따르면, 고밀도 벡터 청킹 시 500자 이하의 조밀한 크기를 유지하고, overlapping 구조를 10% 이상 부여하는 하이브리드(BM25+HNSW) RRF 결합이 대세로 자리잡고 있습니다. [2]

3. **향후 해결 과제**:
   - 30분 초과 세션 만료 시 임시 업로드 파일에 대한 포렌식 방지용 물리 소거(Shredding 데몬) 완성도가 프로덕션 레벨의 최종 핵심 마일스톤이 될 것입니다.`,
    sources: [
      { arxiv_id: "2405.1203", title: "Stateful Graph Debate Networks for Factual Verification", summary: "LangGraph consensus node logic." },
      { arxiv_id: "2406.8912", title: "Concurreny and Reciprocal Rank Fusion in Vector Databases", summary: "HNSW multi-threading analysis." }
    ],
    web_sources: [
      { url: "https://tavily.com", title: "Tavily Search API Academic Integration Guides", summary: "Real-time query routing parameters." }
    ],
    suggestions: [
      "HNSW 인덱싱 재구축 DDL 명령의 WBS 일정을 보여주세요.",
      "번역 시 원본 영문 인용구 Safe Overwrite 로직의 에러 핸들링 코드는?",
      "30분 무활동 세션 감지용 Redis expired event 설정 방법을 알려줘."
    ]
  }
];

export async function sendMessageStream(sessionId, message, onToken, onStatus, image) {
  const db = getDb();
  const session = db.sessions.find(s => s.session_id === sessionId);
  if (!session) throw new Error("세션을 찾을 수 없습니다.");

  // 1. 유저 메시지 저장
  session.messages.push({ role: "user", content: message });
  saveDb(db);

  // 2. 진행 상태 피드백 시뮬레이션
  onStatus({ status: "RAG_SEARCHING", text: "학술 pgvector DB (HNSW 인덱스) 병렬 스캔 중..." });
  await new Promise(r => setTimeout(r, 600));
  onStatus({ status: "WEB_SEARCHING", text: "Tavily 실시간 검색 병렬 브로드캐스팅 중..." });
  await new Promise(r => setTimeout(r, 600));
  onStatus({ status: "SYNTHESIZING", text: "학술 및 실시간 정보 교차 융합(Synthesis Node) 구동 중..." });
  await new Promise(r => setTimeout(r, 700));

  // 3. 토큰 전송 시뮬레이션
  const responseData = mockChatResponses[0];
  const text = responseData.answer;
  let currentText = "";
  const chunks = text.split(" ");
  
  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i] + (i === chunks.length - 1 ? "" : " ");
    currentText += chunk;
    onToken(chunk);
    await new Promise(r => setTimeout(r, 40));
  }

  // 4. 어시스턴트 메시지 저장 (출처, 추천 질문 포함)
  session.messages.push({
    role: "assistant",
    content: text,
    sources: responseData.sources,
    web_sources: responseData.web_sources,
    suggestions: responseData.suggestions
  });
  saveDb(db);
}

// ----------------- Gems (Feature 3) -----------------
export function getGems() {
  const db = getDb();
  return db.gems;
}

export function createGem(gemData) {
  const db = getDb();
  const newGem = {
    gem_id: "gem-" + Date.now(),
    name: gemData.name,
    db_sources: gemData.db_sources,
    system_prompt: gemData.system_prompt,
    has_files: false,
    created_at: new Date().toISOString(),
    files: [],
    sessions: []
  };
  db.gems.unshift(newGem);
  saveDb(db);
  return newGem;
}

export function deleteGem(gemId) {
  const db = getDb();
  db.gems = db.gems.filter(g => g.gem_id !== gemId);
  saveDb(db);
  return { status: "success", message: "Gem 삭제 완료" };
}

export function getGemFiles(gemId) {
  const db = getDb();
  const gem = db.gems.find(g => g.gem_id === gemId);
  return gem ? gem.files : [];
}

export function uploadGemFile(gemId, filename) {
  const db = getDb();
  const gem = db.gems.find(g => g.gem_id === gemId);
  if (gem) {
    const newFile = {
      file_id: "file-" + Date.now(),
      filename: filename || "uploaded_research_note.pdf",
      chunk_count: Math.floor(Math.random() * 40) + 10,
      uploaded_at: new Date().toISOString()
    };
    gem.files.push(newFile);
    gem.has_files = true;
    saveDb(db);
    return newFile;
  }
  throw new Error("Gem을 찾을 수 없습니다.");
}

export function deleteGemFile(gemId, fileId) {
  const db = getDb();
  const gem = db.gems.find(g => g.gem_id === gemId);
  if (gem) {
    gem.files = gem.files.filter(f => f.file_id !== fileId);
    gem.has_files = gem.files.length > 0;
    saveDb(db);
    return { status: "success" };
  }
  throw new Error("Gem을 찾을 수 없습니다.");
}

// ----------------- Research Gap Analyzer (Feature 2) -----------------
export function listUserTasks() {
  const db = getDb();
  return { status: "success", data: db.tasks };
}

export function startAnalysis(domain, query) {
  const db = getDb();
  const taskId = "task-" + Date.now();
  const newTask = {
    task_id: taskId,
    domain,
    query,
    status: "PENDING",
    progress: 10,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    result: null,
    translated_result: null
  };
  db.tasks.unshift(newTask);
  saveDb(db);

  // 진행률 시뮬레이션 트리거
  simulateTaskProgress(taskId);

  return { status: "success", data: { task_id: taskId } };
}

function simulateTaskProgress(taskId) {
  let progress = 10;
  const interval = setInterval(() => {
    const db = getDb();
    const task = db.tasks.find(t => t.task_id === taskId);
    if (!task) {
      clearInterval(interval);
      return;
    }

    if (progress === 10) {
      progress = 40;
      task.status = "RUNNING";
      task.progress = 40;
    } else if (progress === 40) {
      progress = 80;
      task.status = "RUNNING";
      task.progress = 80;
    } else if (progress === 80) {
      progress = 100;
      task.status = "COMPLETED";
      task.progress = 100;
      task.updated_at = new Date().toISOString();
      // 완성 결과 탑재
      task.result = {
        papers: [
          {
            title: `Dense-Sparse Fusion in Information Retrieval (${task.query})`,
            arxiv_id: "2402.0456",
            similarity: 0.92,
            problems_solved: [
              {
                summary: `HNSW indices accelerate similarity search in '${task.query}' by 92.1%.`,
                source_quote: "Static ef_construction configurations yield suboptimal precision profiles under load."
              }
            ],
            limitations: [
              {
                summary: "Lacks hybrid BM25 cross-domain ranking, causing 14% recall decay.",
                source_quote: "Verbatim quotes must be isolated in secondary memory states to bypass translation distortion."
              }
            ]
          }
        ],
        common_limitations: [
          "Lacks hybrid BM25 cross-domain ranking, causing 14% recall decay.",
          "Physical shredding daemon latency delays file removal by up to 2.4 seconds."
        ],
        suggested_directions: [
          `Integrate Reciprocal Rank Fusion (RRF) on top of ${task.domain} pgvector collection.`,
          `Construct dynamic thread pools to optimize HNSW constructionef_construction variables.`
        ]
      };
      
      // 번역 데이터도 탑재
      task.translated_result = {
        papers: [
          {
            title: `정보 검색에서의 밀집-희소 융합 (${task.query})`,
            arxiv_id: "2402.0456",
            similarity: 0.92,
            problems_solved: [
              {
                summary: `HNSW 인덱스를 사용하여 '${task.query}' 영역의 유사도 검색 속도를 92.1% 향상시켰습니다.`,
                source_quote: "Static ef_construction configurations yield suboptimal precision profiles under load."
              }
            ],
            limitations: [
              {
                summary: "하이브리드 BM25 교차 도메인 랭킹 부재로 인해 약 14%의 재현율(Recall) 저하가 발생합니다.",
                source_quote: "Verbatim quotes must be isolated in secondary memory states to bypass translation distortion."
              }
            ]
          }
        ],
        common_limitations: [
          "이종 도메인 하이브리드 어휘 랭킹이 결여되어 약 14%의 재현율 감쇄가 발생합니다.",
          "물리적 파쇄 데몬의 대기시간 지연으로 파일 삭제가 최대 2.4초 지연됩니다."
        ],
        suggested_directions: [
          "인덱스 락을 우회하기 위해 젬 단위의 동적 서브 컬렉션 분할 기법을 도입합니다.",
          "임시 PostgresSaver 체크포인터 상태를 주기적으로 소거하는 실시간 파쇄 리스너를 장착합니다."
        ]
      };

      // 완료 알림 푸시
      db.notifications.unshift({
        id: "notif-" + Date.now(),
        message: `비동기 배치 분석 '${task.query}' 작업이 완료되어 한국어 보고서가 자동 캐싱되었습니다.`,
        read: false,
        created_at: new Date().toISOString()
      });

      clearInterval(interval);
    }
    saveDb(db);
  }, 1500);
}

export function getTaskStatus(taskId) {
  const db = getDb();
  const task = db.tasks.find(t => t.task_id === taskId);
  if (!task) throw new Error("분석 작업을 찾을 수 없습니다.");
  return { status: "success", data: { task_id: taskId, status: task.status, progress: task.progress } };
}

export function getTaskResult(taskId) {
  const db = getDb();
  const task = db.tasks.find(t => t.task_id === taskId);
  if (!task) throw new Error("분석 작업을 찾을 수 없습니다.");
  return { status: "success", data: task };
}

export function translateMatrix(taskId) {
  const db = getDb();
  const task = db.tasks.find(t => t.task_id === taskId);
  if (!task) throw new Error("분석 작업을 찾을 수 없습니다.");
  return { status: "success", data: task.translated_result };
}

export function deleteTask(taskId) {
  const db = getDb();
  db.tasks = db.tasks.filter(t => t.task_id !== taskId);
  saveDb(db);
  return { status: "success", message: "작업 기록 삭제 완료" };
}

export function bulkDeleteTasks(taskIds) {
  const db = getDb();
  const initialCount = db.tasks.length;
  db.tasks = db.tasks.filter(t => !taskIds.includes(t.task_id));
  saveDb(db);
  return { status: "success", data: { deleted_count: initialCount - db.tasks.length } };
}

// ----------------- Notifications (Realtime Inbox) -----------------
export function listNotifications() {
  const db = getDb();
  return { status: "success", data: db.notifications };
}

export function markNotificationAsRead(id) {
  const db = getDb();
  const notif = db.notifications.find(n => n.id === id);
  if (notif) {
    notif.read = true;
    saveDb(db);
  }
  return { status: "success", message: "알림 읽음 처리 완료" };
}

export function markAllNotificationsAsRead() {
  const db = getDb();
  db.notifications.forEach(n => n.read = true);
  saveDb(db);
  return { status: "success", message: "모든 알림 읽음 처리 완료" };
}

export function deleteNotification(id) {
  const db = getDb();
  db.notifications = db.notifications.filter(n => n.id !== id);
  saveDb(db);
  return { status: "success", message: "알림 삭제 완료" };
}

export function deleteAllNotifications() {
  const db = getDb();
  db.notifications = [];
  saveDb(db);
  return { status: "success", message: "모든 알림 삭제 완료" };
}

// ----------------- Defense Arena (Feature 4) -----------------
export function getDefenseHistoryList() {
  const db = getDb();
  return { status: "success", data: db.defenseHistory };
}

export function getDefenseSessionDetail(sessionId) {
  const db = getDb();
  const session = db.defenseHistory.find(s => s.session_id === sessionId);
  if (!session) throw new Error("디펜스 기록을 찾을 수 없습니다.");
  return { status: "success", data: session };
}

export function deleteDefenseSession(sessionId) {
  const db = getDb();
  db.defenseHistory = db.defenseHistory.filter(s => s.session_id !== sessionId);
  saveDb(db);
  return { status: "success", message: "디펜스 기록 삭제 완료" };
}

export function uploadIsolatedPdf(filename) {
  const sessionId = "history-" + Date.now();
  const newSession = {
    session_id: sessionId,
    title: filename.replace(".pdf", "") + " 모의 디펜스 세션",
    score: 0,
    status: "UNDER_REVIEW",
    created_at: new Date().toISOString(),
    file_name: filename || "isolated_proposal.pdf",
    target_journal: "",
    hypothesis: "",
    peerReview: null,
    messages: []
  };
  const db = getDb();
  db.defenseHistory.unshift(newSession);
  saveDb(db);
  return {
    status: "success",
    data: {
      session_id: sessionId,
      file_name: newSession.file_name,
      chunk_count: Math.floor(Math.random() * 45) + 15
    }
  };
}

export function runAcademicPeerReview(sessionId, targetJournal) {
  const db = getDb();
  const session = db.defenseHistory.find(s => s.session_id === sessionId);
  if (!session) throw new Error("세션을 찾을 수 없습니다.");

  session.target_journal = targetJournal || "Nature Scientific Reports";
  session.peerReview = {
    methodology_score: Math.floor(Math.random() * 20) + 70,
    novelty_score: Math.floor(Math.random() * 20) + 70,
    clarity_score: Math.floor(Math.random() * 20) + 70,
    feedback: `제안된 가설과 방법론에 대한 [${session.target_journal}] 심사위원단의 종합 비평입니다:\n\n1. **방법론의 타당성**: 제시한 병렬 asyncio.gather 가동 시의 Lock contention 제어 파라미터가 명확하지 않음. \n2. **신규성 및 독창성**: HNSW pgvector 3072차원 환경에서의 코사인 임계치 0.35 설정은 일반적이나, 도메인 융합 RRF 결합부의 기여가 우수함.\n\n가설 검증 단계 및 디펜스 아레나에서 추가 소명이 요구됩니다.`
  };
  saveDb(db);
  return { status: "success", data: session.peerReview };
}

export function verifyHypothesis(sessionId, hypothesis) {
  const db = getDb();
  const session = db.defenseHistory.find(s => s.session_id === sessionId);
  if (!session) throw new Error("세션을 찾을 수 없습니다.");

  session.hypothesis = hypothesis;
  const passed = Math.random() > 0.35;
  const verification = {
    verdict: passed ? "SUPPORT" : "REFUTE",
    consensus_score: Math.floor(Math.random() * 20) + 75,
    rationales: passed
      ? [
          "HNSW pgvector 검색 결과 내에 제시된 논증과 사용자가 수립한 명제가 의미론적으로 부합합니다.",
          "Tavily 실시간 검색에 등재된 업계 최신 관측 트렌드와 방향성이 일치합니다."
        ]
      : [
          "SpCas9 단백질의 4.2kb 용량과 단일 AAV 벡터의 4.7kb 포장 한계를 연동했을 때, gRNA가 한 번에 포장된다는 사용자의 수식 가설은 논리적 모순을 내포합니다."
        ]
  };
  saveDb(db);
  return { status: "success", data: verification };
}

const mockDefenseQuestions = [
  "연구자님, 제출하신 논문에서 RAG 레이턴시를 22.99% 단축시켰다고 하셨는데, 쓰기 부하가 집중되는 동적 HNSW 생성 연산 중에도 이 속도가 보장됩니까? 구체적인 동시성 제어 모델은 무엇인가요?",
  "제안한 Dual-AAV vector intein 접합 방식에서 생체 내 조율 비율이 15% 수준에 그친다면, 기밀 사설 R&D 관점에서 임상적 가치를 지닌다고 증명할 수 있겠습니까?",
  "임계치 0.35 설정이 Noise를 걸러내 준다고 하나, 만약 핵심 특허에서 rare term(희귀 단어)이 검출될 시 재현율(Recall)의 격심한 붕괴가 발생할 텐데 이에 대한 예방 조치는 왜 명세되지 않았습니까?"
];

export function defenseChatArena(sessionId, userResponse) {
  const db = getDb();
  const session = db.defenseHistory.find(s => s.session_id === sessionId);
  if (!session) throw new Error("세션을 찾을 수 없습니다.");

  if (!userResponse) {
    // 첫 질문 기동
    const question = mockDefenseQuestions[0];
    session.messages = [{ role: "assistant", content: question }];
    saveDb(db);
    return {
      status: "success",
      data: {
        score: 0,
        verdict: "UNDER_REVIEW",
        feedback: "심사위원이 압박 질문을 던집니다. 논리적으로 소명하십시오.",
        next_question: question
      }
    };
  }

  // 사용자의 반론 추가
  session.messages.push({ role: "user", content: userResponse });

  // 다음 진행 상태 연산
  const turnCount = session.messages.filter(m => m.role === "user").length;
  const isFinished = turnCount >= 2;

  let currentScore = Math.floor(Math.random() * 15) + (userResponse.length > 30 ? 80 : 65);
  let nextQuestion = null;
  let verdict = "UNDER_REVIEW";
  let feedback = "";

  if (isFinished) {
    verdict = currentScore >= 70 ? "PASS" : "FAIL";
    session.score = currentScore;
    session.status = verdict;
    feedback = `모의 디펜스가 최종 마감되었습니다. 종합 평가 점수는 **${currentScore}점**으로 최종 **${verdict}** 판정을 내립니다. ${
      verdict === "PASS"
        ? "제시한 수치 제어 및 RRF 보완 방안이 타당하여 본 저널에 게재 수락할 의향이 있습니다."
        : "동시성 이슈 및 Recall 붕괴 방지에 대한 해명이 명확하지 않아 게재 거절 조치합니다."
    }`;
  } else {
    nextQuestion = mockDefenseQuestions[turnCount];
    feedback = `사용자 답변 접수 완료 (현재 중간 평가 점수: ${currentScore}점). 심사위원이 다음 추궁 질문을 진행합니다.`;
    session.messages.push({ role: "assistant", content: nextQuestion });
  }

  saveDb(db);
  return {
    status: "success",
    data: {
      score: currentScore,
      verdict,
      feedback,
      next_question: nextQuestion
    }
  };
}

export function translateText(text) {
  return {
    status: "success",
    data: {
      translated_text: text.includes("methodology") 
        ? "제안된 방법론과 3-Tier 아키텍처는 흥미롭고 우수합니다."
        : "한글 번역이 완료된 학술 자료입니다 (Safe Overwrite 가드 동작 중)."
    }
  };
}
