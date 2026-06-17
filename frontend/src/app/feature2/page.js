"use client"

import { useState, useEffect, useRef } from "react";
import styles from "./page.module.css";
import { startAnalysis, getTaskStatus, getTaskResult } from "@/apis/researchGap";

/**
 * 대규모 문헌 비교 분석기 (Research Gap Analyzer) 페이지 컴포넌트입니다.
 * 
 * - 비동기 분석 작업을 요청(POST /research-gap/analyze)하고,
 * - 진행 상태를 실시간 폴링하여 프로그레스 바를 갱신하며,
 * - 완료 시 최종 공백 매트릭스 테이블과 AI 제안 방향을 화려한 UI로 렌더링합니다.
 * - 또한, SSE(Server-Sent Events) 스트림을 연결하여 실시간 작업 완료 알림을 수신합니다.
 */
export default function ResearchGapPage() {
  // 입력 폼 상태
  const [domain, setDomain] = useState("cs");
  const [query, setQuery] = useState("");

  // 비동기 작업 상태
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [statusText, setStatusText] = useState("");

  // 최종 결과물 상태
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // SSE 실시간 트렌드 인박스 알림 상태
  const [notifications, setNotifications] = useState([]);

  // useRef를 활용해 비동기 콜백에서 최신 taskId 및 폴링 제어를 참조합니다.
  const currentTaskIdRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  // 컴포넌트 마운트 시 실시간 SSE 알림 스트림 연결
  useEffect(() => {
    const sseUrl = "http://localhost:8000/api/v1/research-gap/stream-notifications";
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("SSE push received:", data);

        // 새로운 완료/실패 알림 추가
        setNotifications((prev) => [data, ...prev].slice(0, 15)); // 최대 15개 유지

        // 만약 수신된 이벤트의 task_id가 현재 실행 중인 작업의 task_id와 같다면 
        // 폴링을 종료하고 즉각 최종 결과를 조회합니다.
        if (data.task_id === currentTaskIdRef.current) {
          clearInterval(pollingIntervalRef.current);
          if (data.status === "COMPLETED") {
            fetchFinalResult(data.task_id);
          } else if (data.status === "FAILED") {
            setError(data.error_message || "분석 작업 중 에러가 발생했습니다.");
            setStatus("FAILED");
            setProgress(100);
            setLoading(false);
          }
        }
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE connection error, retrying...", err);
    };

    return () => {
      eventSource.close();
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // 최종 분석 결과 조회
  const fetchFinalResult = async (id) => {
    try {
      setStatusText("결과 리포트 분석 완료 및 렌더링 중...");
      const res = await getTaskResult(id);
      if (res.status === "success" && res.data) {
        setResult(res.data.result);
        setStatus("COMPLETED");
        setProgress(100);
      } else {
        setError("분석 결과를 불러오지 못했습니다.");
        setStatus("FAILED");
      }
    } catch (err) {
      console.error(err);
      setError("결과 조회 중 서버 오류가 발생했습니다.");
      setStatus("FAILED");
    } finally {
      setLoading(false);
    }
  };

  // 배치 작업 진행도 폴링 처리 (SSE 누락 대비 및 정확한 게이지용)
  const startPolling = (id) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const res = await getTaskStatus(id);
        if (res.status === "success" && res.data) {
          const taskData = res.data;
          setProgress(taskData.progress);
          setStatus(taskData.status);

          // 상태 단계별 메세지 매핑
          if (taskData.status === "PENDING") {
            setStatusText("서버 작업 대기 중...");
          } else if (taskData.status === "RUNNING") {
            if (taskData.progress < 30) {
              setStatusText("임베딩 생성 및 벡터 연산 중...");
            } else if (taskData.progress < 60) {
              setStatusText("선택 도메인 RAG 유사도 문헌 추출 중...");
            } else if (taskData.progress < 80) {
              setStatusText("논문별 핵심 해결 과제 및 한계점 추출 중...");
            } else {
              setStatusText("통합 한계점 매트릭스 도출 및 AI Synthesis 진행 중...");
            }
          } else if (taskData.status === "COMPLETED") {
            clearInterval(pollingIntervalRef.current);
            fetchFinalResult(id);
          } else if (taskData.status === "FAILED") {
            clearInterval(pollingIntervalRef.current);
            setError("배치 태스크 처리 중 실패했습니다.");
            setLoading(false);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1500);
  };

  // 분석 시작 요청 실행
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);
    setError(null);
    setProgress(5);
    setStatus("PENDING");
    setStatusText("태스크 초기화 및 작업 시작 요청 중...");

    try {
      const res = await startAnalysis(domain, query);
      if (res.status === "success" && res.data?.task_id) {
        const newTaskId = res.data.task_id;
        setTaskId(newTaskId);
        currentTaskIdRef.current = newTaskId;
        startPolling(newTaskId);
      } else {
        setError("비동기 분석 작업을 등록하지 못했습니다.");
        setLoading(false);
      }
    } catch (err) {
      console.error(err);
      setError("서버 연결에 실패했거나 권한이 없습니다.");
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* 대시보드 헤더 */}
      <div className={`d-flex align-items-center ${styles.dashboardHeader}`}>
        <div className={styles.titleIcon}>
          <i className="bi bi-cpu-fill"></i>
        </div>
        <div>
          <h1 className={`mb-1 ${styles.headerTitle}`}>대규모 문헌 비교 분석기</h1>
          <p className="text-muted mb-0">RAG 파이프라인과 LLM을 연동하여 분야별 논문의 해결 문제 및 한계점(Gap)을 시각화하고 최신 연구 주제를 도출합니다.</p>
        </div>
      </div>

      {/* 분석기 및 실시간 인박스 영역 */}
      <div className={styles.gridContainer}>
        {/* 분석 생성 카드 */}
        <div className={`card shadow-sm p-4 ${styles.glassCard}`}>
          <h4 className="fw-bold mb-4">
            <i className="bi bi-search-heart-fill text-primary"></i> 분석 생성 폼
          </h4>
          <form onSubmit={handleAnalyze}>
            <div className="mb-3">
              <label className={`form-label ${styles.formLabel}`}>학술 도메인</label>
              <select
                className={`form-select ${styles.customSelect}`}
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                disabled={loading}
              >
                <option value="cs">Computer Science (cs.NE)</option>
              </select>
            </div>
            <div className="mb-4">
              <label className={`form-label ${styles.formLabel}`}>주제 키워드</label>
              <input
                type="text"
                className={`form-control ${styles.customInput}`}
                placeholder="예: neural network, genome sequence 등"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              className={`w-100 btn ${styles.btnGradient}`}
              disabled={loading || !query.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  분석 진행 중...
                </>
              ) : (
                <>
                  <i className="bi bi-play-circle-fill me-2"></i> 분석 시작
                </>
              )}
            </button>
          </form>

          {/* 진행 상자 및 로딩 메시지 */}
          {loading && (
            <div className="mt-4 p-3 bg-light rounded border border-light-subtle">
              <div className="d-flex justify-content-between mb-2">
                <span className="text-primary fw-semibold small">{statusText}</span>
                <span className="text-secondary fw-semibold small">{progress}%</span>
              </div>
              <div className={styles.progressBarWrapper}>
                <div className={styles.progressBarFill} style={{ width: `${progress}%` }}></div>
              </div>
            </div>
          )}

          {error && (
            <div className="alert alert-danger mt-4 d-flex align-items-center" role="alert">
              <i className="bi bi-exclamation-triangle-fill me-2"></i>
              <div>{error}</div>
            </div>
          )}
        </div>

        {/* 실시간 알림 인박스 (Trend Inbox) */}
        <div className={`card shadow-sm p-4 ${styles.glassCard}`}>
          <h4 className="fw-bold mb-3 d-flex justify-content-between align-items-center">
            <span>
              <i className="bi bi-bell-fill text-warning"></i> 실시간 알림 센터
            </span>
            <span className="badge bg-danger rounded-pill fs-7">LIVE</span>
          </h4>
          <p className="text-muted small mb-3">서버의 백그라운드 태스크에서 발행된 완료 내역이 실시간 SSE 푸시 이벤트로 갱신됩니다.</p>
          <div className={styles.inboxContainer}>
            {notifications.length === 0 ? (
              <div className="text-center text-muted py-5">
                <i className="bi bi-cloud-slash-fill fs-2 mb-2 d-block"></i>
                수신된 실시간 완료 알림이 없습니다.
              </div>
            ) : (
              notifications.map((notif, idx) => (
                <div key={idx} className={styles.inboxItem}>
                  <div className="d-flex justify-content-between mb-1">
                    <span className={`badge ${notif.domain === "cs" ? styles.badgeCs : styles.badgeBio} rounded-pill`}>
                      {notif.domain.toUpperCase()}
                    </span>
                    <span className="text-muted small">
                      <i className="bi bi-clock me-1"></i> {notif.status === "COMPLETED" ? "완료" : "실패"}
                    </span>
                  </div>
                  <div className="fw-bold mb-1 text-dark small">{notif.query}</div>
                  <div className="text-secondary small">
                    {notif.status === "COMPLETED" ? (
                      <span className="text-success"><i className="bi bi-check-circle-fill me-1"></i> 분석이 최종 종료되었습니다.</span>
                    ) : (
                      <span className="text-danger"><i className="bi bi-x-circle-fill me-1"></i> {notif.error_message || "오류 발생"}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 완료된 분석 결과 대시보드 */}
      {result && (
        <div className="fade-in">
          {/* 1. Research Gap Matrix Table */}
          <div className={`card shadow-sm p-4 mb-4 ${styles.glassCard}`}>
            <h4 className="fw-bold mb-4 text-gradient">
              <i className="bi bi-grid-3x3-gap-fill text-primary"></i> 문헌 비교 분석 매트릭스
            </h4>
            <div className={styles.matrixTableWrapper}>
              <table className={styles.matrixTable}>
                <thead>
                  <tr>
                    <th className={styles.matrixTh} style={{ width: "30%" }}>논문 서지 정보</th>
                    <th className={styles.matrixTh} style={{ width: "35%" }}>해결된 문제 & 제안 방법론</th>
                    <th className={styles.matrixTh} style={{ width: "35%" }}>식별된 한계점 & 공백</th>
                  </tr>
                </thead>
                <tbody>
                  {result.papers.map((paper, idx) => (
                    <tr key={idx}>
                      <td className={styles.matrixTd}>
                        <div className="fw-bold text-dark mb-1">{paper.title}</div>
                        <a
                          href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-outline-primary btn-sm mt-2"
                        >
                          <i className="bi bi-link-45deg"></i> ArXiv 이동
                        </a>
                      </td>
                      <td className={styles.matrixTd}>
                        <ul className={styles.listUnstyled}>
                          {paper.problems_solved.map((item, i) => (
                            <li key={i} className={styles.listItem}>{item}</li>
                          ))}
                        </ul>
                      </td>
                      <td className={styles.matrixTd}>
                        <ul className={styles.listUnstyled}>
                          {paper.limitations.map((item, i) => (
                            <li key={i} className={styles.listItem}>{item}</li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 2. Synthesis & Suggested Roadmap */}
          <div className="row g-4">
            {/* 공통 한계점 카드 */}
            <div className="col-md-5">
              <div className={`card shadow-sm p-4 h-100 ${styles.glassCard}`}>
                <h4 className="fw-bold mb-4 text-gradient">
                  <i className="bi bi-lightbulb-fill text-warning"></i> 학계 핵심 공통 한계점
                </h4>
                <p className="text-muted small">분석된 문헌 집합 전반에 걸쳐 지속적으로 발견되는 미해결 연구 장벽입니다.</p>
                <div className="mt-3">
                  {result.common_limitations.map((limit, idx) => (
                    <div key={idx} className="p-3 bg-light rounded border border-light-subtle mb-3">
                      <div className="fw-bold text-danger mb-1">
                        <i className="bi bi-slash-circle-fill me-2"></i> 이슈 #{idx + 1}
                      </div>
                      <div className="text-secondary small">{limit}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* AI 추천 미래 연구 방향 로드맵 */}
            <div className="col-md-7">
              <div className={`card shadow-sm p-4 h-100 ${styles.glassCard}`}>
                <h4 className="fw-bold mb-4 text-gradient">
                  <i className="bi bi-signpost-split-fill text-success"></i> AI 추천 연구 로드맵 제안
                </h4>
                <p className="text-muted small">식별된 학계 공백을 돌파하기 위해 AI가 추천하는 최우선 학술 기여 테마 리스트입니다.</p>
                <div className="mt-3">
                  {result.suggested_directions.map((dir, idx) => (
                    <div key={idx} className={`card shadow-sm p-3 mb-3 border-0 border-start ${styles.directionCard}`}>
                      <div className="d-flex align-items-center mb-2">
                        <div className={`me-3 ${styles.cardIcon}`}>
                          <i className="bi bi-rocket-takeoff-fill"></i>
                        </div>
                        <h5 className="fw-bold mb-0 text-dark fs-6">추천 제안 #{idx + 1}</h5>
                      </div>
                      <p className="text-secondary mb-0 small">{dir}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
