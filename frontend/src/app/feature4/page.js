"use client"

import { useState, useEffect, useRef, useCallback } from "react";
import { 
  uploadIsolatedPdf, 
  runAcademicPeerReview, 
  verifyHypothesis, 
  defenseChatArena 
} from "@/apis/defenseArena";
import styles from "./page.module.css";

export default function Feature4Page() {
  // Session states
  const [sessionId, setSessionId] = useState(null);
  const [fileName, setFileName] = useState("");
  const [chunkCount, setChunkCount] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState("");
  
  // Timer state
  const [countdown, setCountdown] = useState(1800); // 30 minutes in seconds
  const [isSessionExpired, setIsSessionExpired] = useState(false);

  // General navigation
  const [activeTab, setActiveTab] = useState("peer_review"); // "peer_review" | "hypothesis" | "defense"

  // Tab 1: Peer Review states
  const [targetJournal, setTargetJournal] = useState("IEEE Transactions on Pattern Analysis and Machine Intelligence");
  const [peerReviewResult, setPeerReviewResult] = useState(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [reviewError, setReviewError] = useState("");

  // Tab 2: Hypothesis states
  const [hypothesis, setHypothesis] = useState("");
  const [hypothesisResult, setHypothesisResult] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState("");

  // Tab 3: Defense Arena states
  const [chatHistory, setChatHistory] = useState([]); // Array of { turn, question, answer, score, feedback }
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [currentTurn, setCurrentTurn] = useState(1);
  const [userAnswer, setUserAnswer] = useState("");
  const [isDefenseFinished, setIsDefenseFinished] = useState(false);
  const [finalReport, setFinalReport] = useState(null);
  const [isChatting, setIsChatting] = useState(false);
  const [chatError, setChatError] = useState("");

  const chatBottomRef = useRef(null);

  // 1. Session Countdown Timer Logic
  useEffect(() => {
    let timerInterval = null;
    if (sessionId && countdown > 0) {
      setIsSessionExpired(false);
      timerInterval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timerInterval);
            handleSessionExpiry();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (timerInterval) clearInterval(timerInterval);
    };
  }, [sessionId, countdown]);

  const resetTimer = useCallback(() => {
    setCountdown(1800);
  }, []);

  const handleSessionExpiry = () => {
    setSessionId(null);
    setFileName("");
    setChunkCount(0);
    setIsSessionExpired(true);
    // Reset all tab states
    setPeerReviewResult(null);
    setHypothesisResult(null);
    setChatHistory([]);
    setCurrentQuestion("");
    setCurrentTurn(1);
    setIsDefenseFinished(false);
    setFinalReport(null);
  };

  // Scroll chat window to bottom on new messages
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory, currentQuestion, isChatting]);

  // Helper to format countdown timer as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // 2. Drag & Drop File Handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setUploadError("");

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type !== "application/pdf") {
        setUploadError("PDF 문서 파일만 업로드할 수 있습니다.");
        return;
      }
      await processUpload(file);
    }
  };

  const handleFileChange = async (e) => {
    setUploadError("");
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type !== "application/pdf") {
        setUploadError("PDF 문서 파일만 업로드할 수 있습니다.");
        return;
      }
      await processUpload(file);
    }
  };

  const processUpload = async (file) => {
    setIsUploading(true);
    try {
      const response = await uploadIsolatedPdf(file);
      if (response.status === "success" && response.data) {
        setSessionId(response.data.session_id);
        setFileName(response.data.file_name);
        setChunkCount(response.data.chunk_count);
        resetTimer();
      } else {
        setUploadError(response.message || "파일 업로드에 실패했습니다.");
      }
    } catch (err) {
      console.error(err);
      setUploadError(err.response?.data?.message || "파일 서버 연동 도중 오류가 발생했습니다.");
    } finally {
      setIsUploading(false);
    }
  };

  // 3. Peer Review Action Handlers
  const handleRunPeerReview = async (e) => {
    e.preventDefault();
    if (!sessionId) return;
    setIsReviewing(true);
    setReviewError("");
    try {
      const response = await runAcademicPeerReview(sessionId, targetJournal);
      if (response.status === "success" && response.data) {
        setPeerReviewResult(response.data);
        resetTimer();
      } else {
        setReviewError(response.message || "리뷰 리포트 생성에 실패했습니다.");
      }
    } catch (err) {
      console.error(err);
      setReviewError(err.response?.data?.message || "리뷰 에이전트 연동 도중 오류가 발생했습니다.");
    } finally {
      setIsReviewing(false);
    }
  };

  // 4. Hypothesis Verification Action Handlers
  const handleVerifyHypothesis = async (e) => {
    e.preventDefault();
    if (!sessionId || !hypothesis.trim()) return;
    setIsVerifying(true);
    setVerifyError("");
    try {
      const response = await verifyHypothesis(sessionId, hypothesis);
      if (response.status === "success" && response.data) {
        setHypothesisResult(response.data);
        resetTimer();
      } else {
        setVerifyError(response.message || "가설 검증에 실패했습니다.");
      }
    } catch (err) {
      console.error(err);
      setVerifyError(err.response?.data?.message || "자기일관성 검증 모듈 연동 도중 오류가 발생했습니다.");
    } finally {
      setIsVerifying(false);
    }
  };

  // 5. Defense Arena Action Handlers
  // Auto-initiate first question when switching to defense tab for the first time
  useEffect(() => {
    if (activeTab === "defense" && sessionId && chatHistory.length === 0 && !currentQuestion && !isChatting) {
      initiateDefense();
    }
  }, [activeTab, sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  const initiateDefense = async () => {
    setIsChatting(true);
    setChatError("");
    try {
      const response = await defenseChatArena(sessionId, null);
      if (response.status === "success" && response.data) {
        setCurrentQuestion(response.data.question);
        setCurrentTurn(response.data.turn);
        setIsDefenseFinished(response.data.is_finished);
        resetTimer();
      } else {
        setChatError(response.message || "모의 디펜스 세션 초기화에 실패했습니다.");
      }
    } catch (err) {
      console.error(err);
      setChatError(err.response?.data?.message || "디펜스 아레나 연결에 실패했습니다.");
    } finally {
      setIsChatting(false);
    }
  };

  const handleSendDefenseAnswer = async (e) => {
    e.preventDefault();
    if (!sessionId || !userAnswer.trim() || isChatting) return;
    
    const ansToSend = userAnswer;
    setUserAnswer("");
    setIsChatting(true);
    setChatError("");

    // Optimistically push the user's answer into the chat log showing loading on judge response
    const tempHistories = [...chatHistory, {
      turn: currentTurn,
      question: currentQuestion,
      answer: ansToSend,
      score: null,
      feedback: null
    }];
    setChatHistory(tempHistories);

    try {
      const response = await defenseChatArena(sessionId, ansToSend);
      if (response.status === "success" && response.data) {
        const data = response.data;
        // Update the previous history item with the actual grade and critique feedback
        setChatHistory((prev) => {
          return prev.map((h) => {
            if (h.turn === data.turn) {
              return {
                ...h,
                score: data.score,
                feedback: data.feedback
              };
            }
            return h;
          });
        });

        setCurrentQuestion(data.question);
        setCurrentTurn(data.turn + 1);
        setIsDefenseFinished(data.is_finished);
        if (data.is_finished && data.final_report) {
          setFinalReport(data.final_report);
        }
        resetTimer();
      } else {
        setChatError(response.message || "반론 전송 및 평가에 실패했습니다.");
      }
    } catch (err) {
      console.error(err);
      setChatError(err.response?.data?.message || "심사위원 평가서 수신 도중 오류가 발생했습니다.");
    } finally {
      setIsChatting(false);
    }
  };

  const resetSession = () => {
    setSessionId(null);
    setFileName("");
    setChunkCount(0);
    setPeerReviewResult(null);
    setHypothesisResult(null);
    setChatHistory([]);
    setCurrentQuestion("");
    setCurrentTurn(1);
    setIsDefenseFinished(false);
    setFinalReport(null);
    setIsSessionExpired(false);
  };

  const getScoreColorClass = (score) => {
    if (score >= 80) return styles.scoreGreen;
    if (score >= 50) return styles.scoreYellow;
    return styles.scoreRed;
  };

  return (
    <div className={styles.container}>
      {/* Upper Title Panel */}
      <div className={styles.headerSection}>
        <div>
          <h1 className={styles.title}>
            <i className="bi bi-shield-lock-fill text-primary"></i> Peer Review & Defense Arena
          </h1>
          <p className={styles.subtitle}>
            보안이 강화된 격리 샌드박스에서 학술 논문의 취약점을 분석하고 가상 심사위원 에이전트와 모의 디펜스를 진행합니다.
          </p>
        </div>
        {sessionId && (
          <span className={`${styles.monoBadge} ${styles.badgeSecure}`}>
            <i className="bi bi-shield-fill-check"></i> Isolated Sandbox
          </span>
        )}
      </div>

      {/* Expiry / Error Alerts */}
      {isSessionExpired && (
        <div className="alert alert-warning border-0 shadow-sm d-flex align-items-center gap-3 py-3" role="alert">
          <i className="bi bi-exclamation-triangle-fill text-warning fs-4"></i>
          <div>
            <strong>보안 세션 만료:</strong> 30분 동안 미활동 상태가 지속되어 기밀 유지를 위해 로컬 임시 파일 및 임베딩 벡터가 서버에서 영구 완전 소거(Wipe Out)되었습니다. 분석을 지속하려면 문서를 재업로드해 주십시오.
          </div>
        </div>
      )}

      {/* Active Session Timer Banner */}
      {sessionId && (
        <div className={styles.timerBanner}>
          <div className={styles.timerLeft}>
            <i className={`bi bi-clock-history ${styles.timerIcon}`}></i>
            <span>보안 세션 만료 대기 시간:</span>
            <span className={styles.timerValue}>{formatTime(countdown)}</span>
          </div>
          <div className={styles.timerRight}>
            <i className="bi bi-info-circle me-1"></i> 화면 내 동작 수행 시 자동으로 30분이 연장됩니다.
          </div>
        </div>
      )}

      {/* 1. PDF Sandbox Upload Zone (if no active session) */}
      {!sessionId ? (
        <div 
          className={`${styles.uploadSandbox} ${dragActive ? styles.uploadSandboxHovered : ""}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById("sandbox-file-input").click()}
          role="button"
          tabIndex={0}
        >
          <input 
            type="file" 
            id="sandbox-file-input" 
            className="d-none" 
            accept="application/pdf"
            onChange={handleFileChange}
          />
          {isUploading ? (
            <>
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className={styles.loadingText}>논문 텍스트 보안 분석 및 고차원 임베딩 변환 중...</p>
            </>
          ) : (
            <>
              <i className={`bi bi-cloud-arrow-up-fill ${styles.uploadIcon}`}></i>
              <div className="d-flex flex-column gap-2">
                <div className={styles.uploadTitle}>분석할 PDF 드래그 또는 클릭 업로드</div>
                <div className={styles.uploadDesc}>
                  업로드된 논문은 <strong>3072차원 임시 벡터 데이터</strong>로 청킹 분할되어 휘발성 격리 디렉토리에 저장됩니다. 30분간 활동이 없으면 완벽히 소거됩니다.
                </div>
              </div>
              {uploadError && <div className="text-danger fs-7 mt-2">{uploadError}</div>}
            </>
          )}
        </div>
      ) : (
        /* 2. Main Active Feature Dashboard */
        <div className="d-flex flex-column gap-4">
          {/* Active File Session Header */}
          <div className={styles.sessionHeader}>
            <div className={styles.fileInfo}>
              <i className={`bi bi-file-earmark-pdf-fill ${styles.pdfFileIcon}`}></i>
              <div>
                <span className={styles.fileName}>{fileName}</span>
                <div className={styles.chunkCount}>
                  <i className="bi bi-grid-fill me-1"></i> {chunkCount} 텍스트 청크 임베딩 완료
                </div>
              </div>
            </div>
            <button className={styles.resetBtn} onClick={resetSession}>
              <i className="bi bi-trash3-fill me-2"></i> 세션 완전 소거 및 파일 파쇄
            </button>
          </div>

          {/* Tab Selection Navigation */}
          <div className={styles.tabsContainer}>
            <button 
              className={`${styles.tabButton} ${activeTab === "peer_review" ? styles.tabButtonActive : ""}`}
              onClick={() => setActiveTab("peer_review")}
            >
              <i className="bi bi-people-fill"></i> Peer Review
            </button>
            <button 
              className={`${styles.tabButton} ${activeTab === "hypothesis" ? styles.tabButtonActive : ""}`}
              onClick={() => setActiveTab("hypothesis")}
            >
              <i className="bi bi-journal-check"></i> Hypothesis Verification
            </button>
            <button 
              className={`${styles.tabButton} ${activeTab === "defense" ? styles.tabButtonActive : ""}`}
              onClick={() => setActiveTab("defense")}
            >
              <i className="bi bi-easel3-fill"></i> Defense Arena
            </button>
          </div>

          {/* Tab Contents */}
          <div className={styles.tabContent}>
            
            {/* Tab 1: Peer Review */}
            {activeTab === "peer_review" && (
              <div className={styles.panelCard}>
                <form onSubmit={handleRunPeerReview} className={styles.inputGroup}>
                  <div className={styles.inputFieldWrapper}>
                    <label className={styles.label}>투고 대상 저널 (Target Journal)</label>
                    <input 
                      type="text" 
                      className={styles.textInput} 
                      value={targetJournal}
                      onChange={(e) => setTargetJournal(e.target.value)}
                      placeholder="학회 또는 저널명을 입력하세요."
                      required
                    />
                  </div>
                  <button type="submit" className={styles.primaryBtn} disabled={isReviewing}>
                    {isReviewing ? (
                      <>
                        <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        심사 의견 논의 중...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-play-fill"></i> 피어리뷰 시뮬레이션 기동
                      </>
                    )}
                  </button>
                </form>

                {reviewError && <div className="alert alert-danger mb-0">{reviewError}</div>}

                {isReviewing && (
                  <div className="d-flex flex-column gap-3 my-3">
                    <div className={styles.skeletonCard}>
                      <div className={styles.skeletonHeader}></div>
                      <div className={styles.skeletonBody}>
                        <div className={styles.skeletonLine}></div>
                        <div className={styles.skeletonLine}></div>
                        <div className={styles.skeletonLineShort}></div>
                      </div>
                    </div>
                  </div>
                )}

                {peerReviewResult && !isReviewing && (
                  <div className="d-flex flex-column gap-4">
                    {/* Overall Summary Card */}
                    <div className={styles.reportSummaryCard}>
                      <div className={styles.summaryHeader}>
                        <h3 className={styles.summaryTitle}>
                          <i className="bi bi-file-earmark-bar-graph me-2"></i> Review Summary
                        </h3>
                        <span className={styles.scoreBadgeLarge}>
                          Score: {peerReviewResult.overall_score}/100
                        </span>
                      </div>
                      <p className={styles.summaryText}>{peerReviewResult.summary}</p>
                    </div>

                    {/* 3 Agents Critique Grids */}
                    <div className={styles.opinionGrid}>
                      {peerReviewResult.opinions.map((op, index) => (
                        <div key={index} className={styles.opinionCard}>
                          <div className={styles.opinionHeader}>
                            <span className={styles.agentLabel}>
                              <i className={`bi ${
                                op.agent_type === "methodology" ? "bi-calculator-fill text-info" :
                                op.agent_type === "novelty" ? "bi-lightbulb-fill text-warning" : "bi-fonts text-success"
                              }`}></i>
                              {op.agent_type === "methodology" && "Methodology Critique"}
                              {op.agent_type === "novelty" && "Novelty Critique"}
                              {op.agent_type === "style" && "Academic Style Critique"}
                            </span>
                            <span className={`${styles.opinionScore} ${getScoreColorClass(op.score)}`}>
                              {op.score} pts
                            </span>
                          </div>
                          <p className={styles.opinionBody}>{op.feedback}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Hypothesis Verification */}
            {activeTab === "hypothesis" && (
              <div className={styles.panelCard}>
                <form onSubmit={handleVerifyHypothesis} className={styles.inputGroup}>
                  <div className={styles.inputFieldWrapper}>
                    <label className={styles.label}>검증하고자 하는 핵심 가설 (Research Hypothesis)</label>
                    <input 
                      type="text" 
                      className={styles.textInput} 
                      value={hypothesis}
                      onChange={(e) => setHypothesis(e.target.value)}
                      placeholder="예: 제안한 알고리즘은 기존 CNN 기반 모델에 비해 훈련 속도가 20% 이상 빠르다."
                      minLength={5}
                      required
                    />
                  </div>
                  <button type="submit" className={styles.primaryBtn} disabled={isVerifying || !hypothesis.trim()}>
                    {isVerifying ? (
                      <>
                        <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        다수결 합의 도출 중...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-patch-check"></i> 가설 검증
                      </>
                    )}
                  </button>
                </form>

                {verifyError && <div className="alert alert-danger mb-0">{verifyError}</div>}

                {isVerifying && (
                  <div className="d-flex flex-column gap-3 my-3">
                    <div className={styles.skeletonCard}>
                      <div className={styles.skeletonHeader}></div>
                      <div className={styles.skeletonBody}>
                        <div className={styles.skeletonLine}></div>
                        <div className={styles.skeletonLineShort}></div>
                      </div>
                    </div>
                  </div>
                )}

                {hypothesisResult && !isVerifying && (
                  <div className="d-flex flex-column gap-4">
                    {/* Verification Verdict Gauge */}
                    <div className={styles.gaugeContainer}>
                      <span className={styles.gaugeLabel}>
                        합의 검증 결과: 
                        <span className={`ms-2 ${
                          hypothesisResult.verdict === "SUPPORT" ? "text-success" :
                          hypothesisResult.verdict === "REFUTE" ? "text-danger" : "text-warning"
                        }`}>
                          {hypothesisResult.verdict}
                        </span>
                      </span>
                      <div className={styles.gaugeTrack}>
                        <div 
                          className={`${styles.gaugeFill} ${
                            hypothesisResult.verdict === "SUPPORT" ? styles.gaugeFillSupport :
                            hypothesisResult.verdict === "REFUTE" ? styles.gaugeFillRefute : styles.gaugeFillInsufficient
                          }`}
                          style={{ width: `${hypothesisResult.consensus_ratio * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-secondary fs-8">
                        의견 합의율: {(hypothesisResult.consensus_ratio * 100).toFixed(1)}% ({hypothesisResult.support_count} Support, {hypothesisResult.refute_count} Refute, {hypothesisResult.insufficient_count} Insufficient)
                      </span>
                    </div>

                    {/* Detailed Votes (Self-Consistency Rounds) */}
                    <div>
                      <h4 className="fs-6 fw-bold mb-3">
                        <i className="bi bi-fingerprint text-primary me-2"></i> Self-Consistency 투표 세부 내역 (3회 독립 시행)
                      </h4>
                      <div className={styles.voteList}>
                        {hypothesisResult.detailed_votes.map((vt, index) => (
                          <div key={index} className={styles.voteCard}>
                            <div className={styles.voteHeader}>
                              <span className={styles.voteTitle}>Round {index + 1}</span>
                              <span className={`${styles.opinionScore} ${
                                vt.vote === "SUPPORT" ? styles.scoreGreen :
                                vt.vote === "REFUTE" ? styles.scoreRed : styles.scoreYellow
                              }`}>
                                {vt.vote}
                              </span>
                            </div>
                            <p className={styles.opinionBody}>{vt.reason}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Document Citations RAG Context */}
                    {hypothesisResult.citations && hypothesisResult.citations.length > 0 && (
                      <div className={styles.citationSection}>
                        <div className={styles.citationTitle}>
                          <i className="bi bi-journal-text text-primary"></i> 검증 근거 인용구 (RAG Citations)
                        </div>
                        {hypothesisResult.citations.map((cite, idx) => (
                          <div key={idx} className={styles.citationCard}>
                            {cite}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Defense Arena */}
            {activeTab === "defense" && (
              <div className="d-flex flex-column gap-3">
                
                {/* 1. If not finished, show chat console */}
                {!isDefenseFinished ? (
                  <div className={styles.chatConsole}>
                    <div className={styles.chatMessages}>
                      {chatHistory.map((ch, index) => (
                        <div key={index} className="d-flex flex-column gap-3">
                          {/* Judge Question bubble */}
                          <div className={`${styles.messageRow} ${styles.messageRowJudge}`}>
                            <div className={`${styles.bubble} ${styles.bubbleJudge}`}>
                              <strong className="d-block text-primary mb-1">
                                <i className="bi bi-person-fill-exclamation me-1"></i> Committee (Turn {ch.turn})
                              </strong>
                              {ch.question}
                            </div>
                          </div>
                          
                          {/* User Answer bubble */}
                          {ch.answer && (
                            <div className={`${styles.messageRow} ${styles.messageRowUser}`}>
                              <div className={`${styles.bubble} ${styles.bubbleUser}`}>
                                <strong className="d-block mb-1 text-white-50">
                                  <i className="bi bi-person-fill-check me-1"></i> Author
                                </strong>
                                {ch.answer}
                              </div>
                            </div>
                          )}

                          {/* Live grading result card from Committee */}
                          {ch.score !== null && ch.score !== undefined && (
                            <div className={`${styles.messageRow} ${styles.messageRowJudge} mt-1`}>
                              <div className={styles.gradingCard}>
                                <div className={styles.gradingHeader}>
                                  <span className={styles.scoreLabel}>
                                    <i className="bi bi-award-fill me-1"></i> Defense Score: {ch.score}/100
                                  </span>
                                </div>
                                <p className={styles.critiqueText}>{ch.feedback}</p>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}

                      {/* Current active question from Judge */}
                      {currentQuestion && (chatHistory.length === 0 || chatHistory[chatHistory.length - 1].answer) && (
                        <div className={`${styles.messageRow} ${styles.messageRowJudge}`}>
                          <div className={`${styles.bubble} ${styles.bubbleJudge}`}>
                            <strong className="d-block text-primary mb-1">
                              <i className="bi bi-person-fill-exclamation me-1"></i> Committee (Turn {currentTurn})
                            </strong>
                            {currentQuestion}
                          </div>
                        </div>
                      )}

                      {/* Judge typing skeleton */}
                      {isChatting && (
                        <div className={`${styles.messageRow} ${styles.messageRowJudge}`}>
                          <div className={`${styles.bubble} ${styles.bubbleJudge}`}>
                            <div className="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                            <span className="text-secondary fs-8">심사위원이 답변을 채점하고 반론을 검토 중입니다...</span>
                          </div>
                        </div>
                      )}

                      <div ref={chatBottomRef} />
                    </div>

                    {/* Chat Input Bar */}
                    <form onSubmit={handleSendDefenseAnswer} className={styles.chatInputBar}>
                      <textarea
                        className={styles.chatTextArea}
                        placeholder={isChatting ? "대기 중..." : "압박 질문에 대한 학술적이고 논리적인 답변을 입력하세요."}
                        value={userAnswer}
                        onChange={(e) => setUserAnswer(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSendDefenseAnswer(e);
                          }
                        }}
                        disabled={isChatting || isDefenseFinished}
                        required
                      />
                      <button 
                        type="submit" 
                        className={styles.primaryBtn} 
                        disabled={isChatting || isDefenseFinished || !userAnswer.trim()}
                      >
                        <i className="bi bi-send-fill"></i>
                      </button>
                    </form>
                  </div>
                ) : (
                  /* 2. If finished, show Final Scorecard */
                  <div className={styles.scorecard}>
                    <i className={`bi bi-trophy-fill ${styles.trophyIcon}`}></i>
                    <div>
                      <h3 className={styles.scorecardTitle}>Oral Defense Completed!</h3>
                      <p className={styles.scorecardDesc}>
                        3턴 간의 강도 높은 심사위원 모의 압박 질문 및 논박이 완료되었습니다. 종합 방어 평가 등급을 확인해 주십시오.
                      </p>
                    </div>

                    {/* Aggregate Average Score */}
                    {chatHistory.length > 0 && (
                      <div className={styles.totalAverage}>
                        <span className={styles.avgLabel}>Average Defense Score</span>
                        <span className={styles.avgVal}>
                          {(chatHistory.reduce((acc, cur) => acc + (cur.score || 0), 0) / chatHistory.length).toFixed(1)} / 100
                        </span>
                      </div>
                    )}

                    {/* Final Board Recommendation Document */}
                    {finalReport && (
                      <div className={styles.reportTextWrapper}>
                        <h4 className="fs-6 fw-bold mb-3 text-secondary text-start">
                          <i className="bi bi-file-earmark-text me-2"></i> Board of Committee Decision
                        </h4>
                        <div className={styles.reportText}>
                          {finalReport}
                        </div>
                      </div>
                    )}

                    <button className={styles.primaryBtn} onClick={() => {
                      setChatHistory([]);
                      setCurrentQuestion("");
                      setCurrentTurn(1);
                      setIsDefenseFinished(false);
                      setFinalReport(null);
                      initiateDefense();
                    }}>
                      <i className="bi bi-arrow-clockwise"></i> 새 디펜스 게임 시작
                    </button>
                  </div>
                )}

                {chatError && <div className="alert alert-danger mb-0">{chatError}</div>}

              </div>
            )}

          </div>
        </div>
      )}
    </div>
  );
}
