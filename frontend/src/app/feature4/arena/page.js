"use client"

import { useState, useEffect, useRef, useCallback, Suspense, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import {
  uploadIsolatedPdf,
  runAcademicPeerReview,
  verifyHypothesis,
  defenseChatArena,
  keepAliveDefenseSession,
  translateText,
  getDefenseSessionDetail
} from "@/apis/defenseArena";
import styles from "../page.module.css";
import LoadingSpinner from "@/components/loading-spinner/LoadingSpinner";

// Slugify text to create clean HTML ids for scrolling
const slugify = (text) => {
  return String(text)
    .toLowerCase()
    .trim()
    .replace(/[^\w\sㄱ-힣-]/g, "") // Keep alphanumeric, Korean characters, spaces, and hyphens
    .replace(/[\s_]+/g, "-");     // Replace spaces/underscores with hyphens
};

// Extract plain text from React elements children
const getHeaderText = (children) => {
  if (!children) return "";
  if (typeof children === "string") return children;
  if (Array.isArray(children)) {
    return children.map(child => getHeaderText(child)).join("");
  }
  if (children.props && children.props.children !== undefined) {
    return getHeaderText(children.props.children);
  }
  return "";
};

// Parse headers from raw markdown text to generate table of contents items
const getTocItems = (mdText) => {
  if (!mdText) return [];
  const lines = mdText.split("\n");
  const items = [];
  const seen = {};

  for (const line of lines) {
    const match = line.match(/^(#{1,6})\s+(.+)$/);
    if (match) {
      const level = match[1].length;
      let text = match[2].trim();
      text = text.replace(/[\*\`\_]/g, ""); // strip bold, code, etc.
      let baseSlug = slugify(text) || "heading";
      let slug = baseSlug;
      let count = 1;
      while (seen[slug]) {
        slug = `${baseSlug}-${count}`;
        count++;
      }
      seen[slug] = true;
      items.push({ level, text, id: slug });
    }
  }
  return items;
};

// Heading components config for ReactMarkdown
const headingRenderer = (level) => {
  const HeadingTag = `h${level}`;
  const CustomHeading = ({ children }) => {
    const text = getHeaderText(children);
    const slug = slugify(text);
    return <HeadingTag id={slug}>{children}</HeadingTag>;
  };
  CustomHeading.displayName = `CustomH${level}`;
  return CustomHeading;
};

const mdComponents = {
  h1: headingRenderer(1),
  h2: headingRenderer(2),
  h3: headingRenderer(3),
  h4: headingRenderer(4),
  h5: headingRenderer(5),
  h6: headingRenderer(6),
};

// Language translation dictionary
const t = {
  ko: {
    title: "피어리뷰 및 디펜스 아레나",
    subtitle: "보안이 강화된 격리 샌드박스에서 학술 논문의 취약점을 분석하고 가상 심사위원 에이전트와 모의 디펜스를 진행합니다.",
    isolatedSandbox: "보안 격리 샌드박스",
    sessionExpiredTitle: "보안 세션 만료:",
    sessionExpiredDesc: "30분 동안 미활동 상태가 지속되어 기밀 유지를 위해 로컬 임시 파일 및 임베딩 벡터가 서버에서 영구 완전 소거(Wipe Out)되었습니다. 분석을 지속하려면 문서를 재업로드해 주십시오.",
    sessionTimeoutLabel: "보안 세션 만료 대기 시간:",
    sessionPaused: "일시 정지됨",
    autoDeleteLabel: "30분 자동 삭제",
    extendInfo: "화면 내 동작 수행 시 자동으로 30분이 연장됩니다.",
    dragTitle: "분석할 PDF 또는 마크다운 파일 드래그 또는 클릭 업로드",
    dragDesc: "업로드된 논문은 3072차원 임시 벡터 데이터로 청킹 분할되어 휘발성 격리 디렉토리에 저장됩니다. 30분간 활동이 없으면 완벽히 소거됩니다.",
    allowedFilesError: "PDF 또는 마크다운/텍스트 (.md, .txt) 파일만 업로드할 수 있습니다.",
    uploadingText: "문서 보안 분석 및 3072차원 고차원 임베딩 변환 중...",
    embeddingCompleted: "텍스트 청크 임베딩 완료",
    sessionWipeBtn: "세션 완전 소거 및 파일 파쇄",
    peerReviewTab: "피어 리뷰",
    hypothesisTab: "가설 검증",
    defenseTab: "디펜스 아레나",
    targetJournalLabel: "투고 대상 저널 (Target Journal)",
    targetJournalPlaceholder: "학회 또는 저널명을 입력하세요.",
    runPeerReviewBtn: "피어리뷰 시뮬레이션 기동",
    reviewingText: "심사 의견 논의 중...",
    peerReviewSummaryTitle: "리뷰 요약 리포트 (Review Summary)",
    methodologyCritique: "방법론 심사",
    noveltyCritique: "신규성 심사",
    styleCritique: "학술 문체 교정",
    researchHypothesisLabel: "검증하고자 하는 핵심 가설 (Research Hypothesis)",
    researchHypothesisPlaceholder: "예: 제안한 알고리즘은 기존 CNN 기반 모델에 비해 훈련 속도가 20% 이상 빠르다.",
    verifyHypothesisBtn: "가설 검증",
    verifyingText: "다수결 합의 도출 중...",
    consensusVerdictLabel: "합의 검증 결과:",
    consensusRatioLabel: "의견 합의율:",
    selfConsistencyTitle: "Self-Consistency 투표 세부 내역 (3회 독립 시행)",
    citationsTitle: "검증 근거 인용구 (RAG Citations)",
    oralDefenseTitle: "Oral Defense Completed!",
    oralDefenseDesc: "3턴 간의 강도 높은 심사위원 모의 압박 질문 및 논박이 완료되었습니다. 종합 방어 평가 등급을 확인해 주십시오.",
    averageDefenseScore: "Average Defense Score",
    committeeDecision: "Board of Committee Decision",
    newGameBtn: "새 디펜스 게임 시작",
    judgeActiveTitle: "심사위원회",
    authorActiveTitle: "Author",
    typingText: "심사위원이 답변을 채점하고 반론을 검토 중입니다...",
    placeholderAnswer: "압박 질문에 대한 학술적이고 논리적인 답변을 입력하세요.",
    loadingText: "대기 중...",
  },
  en: {
    title: "Peer Review & Defense Arena",
    subtitle: "Analyze academic drafts inside a secure sandbox and debate with a simulated peer review committee.",
    isolatedSandbox: "Isolated Sandbox",
    sessionExpiredTitle: "Security Session Expired:",
    sessionExpiredDesc: "Due to 30 minutes of inactivity, all temporary files and embedding vectors have been permanently shredded from the server to protect confidentiality. Please re-upload your document.",
    sessionTimeoutLabel: "Session Expiry Countdown:",
    sessionPaused: "Paused",
    autoDeleteLabel: "30-Min Auto Delete",
    extendInfo: "Performing any action on this page will automatically reset the 30-minute timer.",
    dragTitle: "Drag & drop PDF or Markdown file here, or click to browse",
    dragDesc: "Uploaded drafts are recursively chunked, converted to 3072-dimensional vectors, and stored in an isolated sandbox. Session data is completely wiped out after 30 minutes.",
    allowedFilesError: "Only PDF, Markdown, or Text (.md, .txt) files are allowed.",
    uploadingText: "Analyzing document and computing 3072-dimensional embeddings...",
    embeddingCompleted: "Text Chunk Embeddings Completed",
    sessionWipeBtn: "Wipe Session & Shred File",
    peerReviewTab: "Peer Review",
    hypothesisTab: "Hypothesis Verification",
    defenseTab: "Defense Arena",
    targetJournalLabel: "Target Journal",
    targetJournalPlaceholder: "Enter academic conference or journal name.",
    runPeerReviewBtn: "Run Peer Review Simulation",
    reviewingText: "Simulating referee debate...",
    peerReviewSummaryTitle: "Review Summary",
    methodologyCritique: "Methodology Critique",
    noveltyCritique: "Novelty Critique",
    styleCritique: "Academic Style Critique",
    researchHypothesisLabel: "Research Hypothesis to Validate",
    researchHypothesisPlaceholder: "e.g., The proposed algorithm achieves 20% faster training compared to CNN baselines.",
    verifyHypothesisBtn: "Verify Hypothesis",
    verifyingText: "Tallying consensus votes...",
    consensusVerdictLabel: "Consensus Verdict:",
    consensusRatioLabel: "Consensus Ratio:",
    selfConsistencyTitle: "Self-Consistency Voting Log (3 Independent Runs)",
    citationsTitle: "RAG Citations (Supporting Evidence)",
    oralDefenseTitle: "Oral Defense Completed!",
    oralDefenseDesc: "The 3-turn intensive referee interrogation has finished. Please check your final defense grade card.",
    averageDefenseScore: "Average Defense Score",
    committeeDecision: "Board of Committee Decision",
    newGameBtn: "Start New Defense Session",
    judgeActiveTitle: "Committee",
    authorActiveTitle: "Author",
    typingText: "The referee is evaluating your argument and preparing a rebuttal...",
    placeholderAnswer: "Provide a rigorous and logical academic rebuttal to the referee's critique.",
    loadingText: "Waiting...",
  }
};

function DefenseArenaPlayground() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const restoredSessionId = searchParams.get("sessionId");

  // UI Language Switch
  const [lang, setLang] = useState("ko");

  // Session states
  const [sessionId, setSessionId] = useState(null);
  const [fileName, setFileName] = useState("");
  const [chunkCount, setChunkCount] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [isExpiredSession, setIsExpiredSession] = useState(false);

  // Timer state
  const [countdown, setCountdown] = useState(1800); // 30 minutes in seconds
  const [autoDeleteEnabled, setAutoDeleteEnabled] = useState(true);
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
  const [chatHistory, setChatHistory] = useState([]); // Array of { turn, question, answer, score, feedback, question_ko, feedback_ko, translated }
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [currentQuestionKo, setCurrentQuestionKo] = useState("");
  const [currentTurn, setCurrentTurn] = useState(1);
  const [userAnswer, setUserAnswer] = useState("");
  const [isDefenseFinished, setIsDefenseFinished] = useState(false);
  const [finalReport, setFinalReport] = useState(null);
  const [finalReportKo, setFinalReportKo] = useState(null);
  const [isChatting, setIsChatting] = useState(false);
  const [chatError, setChatError] = useState("");

  // Translation Loading state
  const [isTranslating, setIsTranslating] = useState(false);

  const chatBottomRef = useRef(null);

  // Compute TOC items based on the active report text
  const activeReportText = lang === "ko" ? (finalReportKo || finalReport) : finalReport;
  const tocItems = useMemo(() => getTocItems(activeReportText), [activeReportText]);

  const textareaRef = useRef(null);

  // Auto-resize chat textarea based on input text height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "44px"; // Reset to default line height
      const scrollHeight = textareaRef.current.scrollHeight;
      if (scrollHeight > 44) {
        textareaRef.current.style.height = `${Math.min(scrollHeight, 150)}px`;
      }
    }
  }, [userAnswer]);

  // Restore session from URL query parameter
  useEffect(() => {
    if (restoredSessionId) {
      restoreSession(restoredSessionId);
    }
  }, [restoredSessionId]);

  const restoreSession = async (restoredId) => {
    try {
      const response = await getDefenseSessionDetail(restoredId);
      if (response.status === "success" && response.data) {
        const data = response.data;
        setSessionId(data.session_id);
        setFileName(data.file_name);
        setChunkCount(data.is_expired ? 0 : 1);
        setIsExpiredSession(data.is_expired);
        setPeerReviewResult(data.peer_review_result);
        setHypothesisResult(data.hypothesis_result);
        setFinalReport(data.final_report);
        setFinalReportKo(null);
        setCurrentQuestionKo("");
        
        if (data.chat_history && data.chat_history.length > 0) {
          const formattedHist = data.chat_history.map(ch => ({
            turn: ch.turn,
            question: ch.question,
            answer: ch.answer,
            score: ch.score,
            feedback: ch.feedback,
            question_ko: null,
            feedback_ko: null,
            translated: false
          }));
          
          const lastTurn = data.chat_history[data.chat_history.length - 1];
          if (lastTurn.score !== null && lastTurn.score !== undefined) {
            setIsDefenseFinished(true);
            setCurrentQuestion("");
            setCurrentTurn(lastTurn.turn + 1);
            setChatHistory(formattedHist);
          } else {
            setIsDefenseFinished(false);
            setCurrentQuestion(lastTurn.question);
            setCurrentTurn(lastTurn.turn);
            const completedHist = formattedHist.filter(h => h.answer !== null);
            setChatHistory(completedHist);
          }
        } else {
          setChatHistory([]);
          setCurrentQuestion("");
          setCurrentTurn(1);
          setIsDefenseFinished(false);
        }
        
        setIsSessionExpired(false);
        setCountdown(1800);
      }
    } catch (err) {
      console.error("Failed to restore session:", err);
    }
  };

  // Translation helpers for AI-generated reports
  const translatePeerReview = async (rawResult) => {
    if (!rawResult || rawResult.translated) return;
    setIsTranslating(true);
    try {
      const summaryRes = await translateText(rawResult.summary);
      const translatedSummary = summaryRes.data?.translated_text || rawResult.summary;

      const translatedOpinions = await Promise.all(
        rawResult.opinions.map(async (op) => {
          const opRes = await translateText(op.feedback);
          return {
            ...op,
            feedback_ko: opRes.data?.translated_text || op.feedback
          };
        })
      );

      setPeerReviewResult({
        ...rawResult,
        summary_ko: translatedSummary,
        opinions: translatedOpinions,
        translated: true
      });
    } catch (err) {
      console.error("Failed to translate peer review:", err);
    } finally {
      setIsTranslating(false);
    }
  };

  const translateHypothesis = async (rawResult) => {
    if (!rawResult || rawResult.translated) return;
    setIsTranslating(true);
    try {
      const translatedVotes = await Promise.all(
        rawResult.detailed_votes.map(async (vt) => {
          const vtRes = await translateText(vt.reason);
          return {
            ...vt,
            reason_ko: vtRes.data?.translated_text || vt.reason
          };
        })
      );

      const translatedCitations = await Promise.all(
        rawResult.citations.map(async (cite) => {
          const citeRes = await translateText(cite);
          return citeRes.data?.translated_text || cite;
        })
      );

      setHypothesisResult({
        ...rawResult,
        detailed_votes: translatedVotes,
        citations_ko: translatedCitations,
        translated: true
      });
    } catch (err) {
      console.error("Failed to translate hypothesis:", err);
    } finally {
      setIsTranslating(false);
    }
  };

  const translateChatHistory = async (history) => {
    setIsTranslating(true);
    try {
      const updatedHistory = await Promise.all(
        history.map(async (ch) => {
          if (ch.translated) return ch;
          const qRes = await translateText(ch.question);
          let fKo = null;
          if (ch.feedback) {
            const fRes = await translateText(ch.feedback);
            fKo = fRes.data?.translated_text;
          }
          return {
            ...ch,
            question_ko: qRes.data?.translated_text || ch.question,
            feedback_ko: fKo || ch.feedback,
            translated: true
          };
        })
      );
      setChatHistory(updatedHistory);
    } catch (err) {
      console.error("Failed to translate chat history:", err);
    } finally {
      setIsTranslating(false);
    }
  };

  const translateCurrentQuestionAndReport = async (q, report) => {
    setIsTranslating(true);
    try {
      if (q && !currentQuestionKo) {
        const qRes = await translateText(q);
        setCurrentQuestionKo(qRes.data?.translated_text || q);
      }
      if (report && !finalReportKo) {
        const rRes = await translateText(report);
        setFinalReportKo(rRes.data?.translated_text || report);
      }
    } catch (err) {
      console.error("Failed to translate current question/report:", err);
    } finally {
      setIsTranslating(false);
    }
  };

  // Watch language toggle to trigger translations if KO is active
  useEffect(() => {
    if (lang === "ko") {
      if (peerReviewResult && !peerReviewResult.translated) {
        translatePeerReview(peerReviewResult);
      }
      if (hypothesisResult && !hypothesisResult.translated) {
        translateHypothesis(hypothesisResult);
      }
      if (chatHistory.length > 0 && chatHistory.some(ch => !ch.translated)) {
        translateChatHistory(chatHistory);
      }
      if ((currentQuestion && !currentQuestionKo) || (finalReport && !finalReportKo)) {
        translateCurrentQuestionAndReport(currentQuestion, finalReport);
      }
    }
  }, [lang, peerReviewResult, hypothesisResult, chatHistory, currentQuestion, finalReport, currentQuestionKo, finalReportKo]);

  // Session Countdown Timer Logic
  useEffect(() => {
    let timerInterval = null;
    if (sessionId && autoDeleteEnabled && countdown > 0) {
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
  }, [sessionId, countdown, autoDeleteEnabled]);

  // Keep-alive Ping to Backend when Auto-Delete is Disabled
  useEffect(() => {
    let pingInterval = null;
    if (sessionId && !autoDeleteEnabled) {
      pingInterval = setInterval(async () => {
        try {
          await keepAliveDefenseSession(sessionId);
          setCountdown(1800);
        } catch (err) {
          console.error("Failed to extend session:", err);
        }
      }, 5 * 60 * 1000);
    }
    return () => {
      if (pingInterval) clearInterval(pingInterval);
    };
  }, [sessionId, autoDeleteEnabled]);

  const resetTimer = useCallback(() => {
    setCountdown(1800);
  }, []);

  const handleSessionExpiry = () => {
    setSessionId(null);
    setFileName("");
    setChunkCount(0);
    setIsSessionExpired(true);
    setPeerReviewResult(null);
    setHypothesisResult(null);
    setChatHistory([]);
    setCurrentQuestion("");
    setCurrentQuestionKo("");
    setCurrentTurn(1);
    setIsDefenseFinished(false);
    setFinalReport(null);
    setFinalReportKo(null);
  };

  // Scroll chat window to bottom on new messages
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory, currentQuestion, isChatting]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

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
      const lowerName = file.name.toLowerCase();
      const isAllowed = file.type === "application/pdf" ||
        file.type === "text/markdown" ||
        file.type === "text/plain" ||
        lowerName.endsWith(".pdf") ||
        lowerName.endsWith(".md") ||
        lowerName.endsWith(".txt") ||
        lowerName.endsWith(".markdown");
      if (!isAllowed) {
        setUploadError(t[lang].allowedFilesError);
        return;
      }
      await processUpload(file);
    }
  };

  const handleFileChange = async (e) => {
    setUploadError("");
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const lowerName = file.name.toLowerCase();
      const isAllowed = file.type === "application/pdf" ||
        file.type === "text/markdown" ||
        file.type === "text/plain" ||
        lowerName.endsWith(".pdf") ||
        lowerName.endsWith(".md") ||
        lowerName.endsWith(".txt") ||
        lowerName.endsWith(".markdown");
      if (!isAllowed) {
        setUploadError(t[lang].allowedFilesError);
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

  const handleRunPeerReview = async (e) => {
    e.preventDefault();
    if (!sessionId) return;
    setIsReviewing(true);
    setReviewError("");
    try {
      const response = await runAcademicPeerReview(sessionId, targetJournal);
      if (response.status === "success" && response.data) {
        setPeerReviewResult(response.data);
        if (lang === "ko") {
          await translatePeerReview(response.data);
        }
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

  const handleVerifyHypothesis = async (e) => {
    e.preventDefault();
    if (!sessionId || !hypothesis.trim()) return;
    setIsVerifying(true);
    setVerifyError("");
    try {
      const response = await verifyHypothesis(sessionId, hypothesis);
      if (response.status === "success" && response.data) {
        setHypothesisResult(response.data);
        if (lang === "ko") {
          await translateHypothesis(response.data);
        }
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

  useEffect(() => {
    if (activeTab === "defense" && sessionId && chatHistory.length === 0 && !currentQuestion && !isChatting) {
      initiateDefense();
    }
  }, [activeTab, sessionId]);

  const initiateDefense = async () => {
    setIsChatting(true);
    setChatError("");
    try {
      const response = await defenseChatArena(sessionId, null);
      if (response.status === "success" && response.data) {
        const data = response.data;
        let qKo = "";
        if (lang === "ko" && data.question) {
          setIsTranslating(true);
          try {
            const qRes = await translateText(data.question);
            qKo = qRes.data?.translated_text || data.question;
          } catch (err) {
            console.error("Translation error during initiateDefense:", err);
          } finally {
            setIsTranslating(false);
          }
        }
        setCurrentQuestion(data.question);
        setCurrentQuestionKo(qKo);
        setCurrentTurn(data.turn);
        setIsDefenseFinished(data.is_finished);
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

    // Append temporary un-graded item to chatHistory immediately to show user's response
    const tempHistoryItem = {
      turn: currentTurn,
      question: currentQuestion,
      question_ko: currentQuestionKo,
      answer: ansToSend,
      score: null,
      feedback: null,
      translated: true
    };
    setChatHistory((prev) => [...prev, tempHistoryItem]);

    try {
      const response = await defenseChatArena(sessionId, ansToSend);
      if (response.status === "success" && response.data) {
        const data = response.data;
        
        let qKo = currentQuestionKo;
        let translatedFeedbackKo = "";
        let nextQuestionKo = "";
        let nextReportKo = "";

        if (lang === "ko") {
          setIsTranslating(true);
          try {
            // 1. Translate current question to Korean if not already done
            if (!qKo && currentQuestion) {
              const qRes = await translateText(currentQuestion);
              qKo = qRes.data?.translated_text || currentQuestion;
            }
            // 2. Translate new feedback/critique
            if (data.feedback) {
              const fbRes = await translateText(data.feedback);
              translatedFeedbackKo = fbRes.data?.translated_text || data.feedback;
            }
            // 3. Translate next question
            if (data.question) {
              const nextQRes = await translateText(data.question);
              nextQuestionKo = nextQRes.data?.translated_text || data.question;
            }
            // 4. Translate final report
            if (data.is_finished && data.final_report) {
              const reportRes = await translateText(data.final_report);
              nextReportKo = reportRes.data?.translated_text || data.final_report;
            }
          } catch (err) {
            console.error("Translation error during handleSendDefenseAnswer:", err);
          } finally {
            setIsTranslating(false);
          }
        }

        // Create new history item with translations embedded
        const gradedHistoryItem = {
          turn: currentTurn,
          question: currentQuestion,
          question_ko: lang === "ko" ? (qKo || currentQuestion) : null,
          answer: ansToSend,
          score: data.score,
          feedback: data.feedback,
          feedback_ko: lang === "ko" ? (translatedFeedbackKo || data.feedback) : null,
          translated: lang === "ko"
        };

        // Replace temporary item with graded item in history list
        setChatHistory((prev) => {
          const list = [...prev];
          if (list.length > 0) {
            list[list.length - 1] = gradedHistoryItem;
          } else {
            list.push(gradedHistoryItem);
          }
          return list;
        });

        setCurrentQuestion(data.question);
        setCurrentQuestionKo(nextQuestionKo);
        setCurrentTurn(data.turn);
        setIsDefenseFinished(data.is_finished);
        if (data.is_finished && data.final_report) {
          setFinalReport(data.final_report);
          setFinalReportKo(nextReportKo);
        }

        resetTimer();
      } else {
        setChatError(response.message || "반론 전송 및 평가에 실패했습니다.");
        // Remove temporary item on error
        setChatHistory((prev) => prev.slice(0, -1));
      }
    } catch (err) {
      console.error(err);
      setChatError(err.response?.data?.message || "심사위원 평가서 수신 도중 오류가 발생했습니다.");
      // Remove temporary item on error
      setChatHistory((prev) => prev.slice(0, -1));
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
    setCurrentQuestionKo("");
    setCurrentTurn(1);
    setIsDefenseFinished(false);
    setFinalReport(null);
    setFinalReportKo(null);
    setIsSessionExpired(false);
    setIsExpiredSession(false);
    router.push("/feature4");
  };

  const getScoreColorClass = (score) => {
    if (score >= 80) return styles.scoreGreen;
    if (score >= 50) return styles.scoreYellow;
    return styles.scoreRed;
  };

  const getVerdictLabel = (verdict) => {
    if (lang === "ko") {
      if (verdict === "SUPPORT") return "지원됨 (참)";
      if (verdict === "REFUTE") return "반박됨 (거짓)";
      return "증거 불충분";
    }
    return verdict;
  };

  return (
    <div className={styles.container} style={{ maxWidth: "1000px" }}>
      {/* Upper Title Panel */}
      <div className={styles.headerSection}>
        <div>
          <h1 className={styles.title}>
            <i className="bi bi-shield-lock-fill"></i> {t[lang].title}
          </h1>
          <p className={styles.subtitle}>
            {t[lang].subtitle}
          </p>
        </div>
        <div className="d-flex align-items-center gap-2">
          {sessionId && (
            <span className={`${styles.monoBadge} ${styles.badgeSecure}`}>
              <i className="bi bi-shield-fill-check"></i> {t[lang].isolatedSandbox}
            </span>
          )}
          <button
            className={styles.langToggleBtn}
            onClick={() => setLang(prev => prev === "ko" ? "en" : "ko")}
            title="Switch Language / 한영 전환"
          >
            <i className="bi bi-globe2 me-1"></i>
            <span>{lang === "ko" ? "EN" : "KO"}</span>
          </button>
        </div>
      </div>

      {/* Expiry / Error Alerts */}
      {isSessionExpired && (
        <div className="alert alert-warning border-0 shadow-sm d-flex align-items-center gap-3 py-3 mb-4" role="alert" style={{ borderRadius: "16px" }}>
          <i className="bi bi-exclamation-triangle-fill text-warning fs-4"></i>
          <div>
            <strong>{t[lang].sessionExpiredTitle}</strong> {t[lang].sessionExpiredDesc}
          </div>
        </div>
      )}

      {/* Main Content (1-Column Layout) */}
      <div className="w-100">
        <div className="d-flex flex-column gap-4">
          
          {/* Read-Only Archive Alert Banner */}
          {isExpiredSession && (
            <div className="alert alert-secondary border-0 shadow-sm d-flex align-items-center gap-3 py-3" role="alert" style={{ borderRadius: "16px" }}>
              <i className="bi bi-info-circle-fill text-secondary fs-4"></i>
              <div className="fs-7 text-secondary">
                <strong>[보안 읽기전용 모드]</strong> 30분 미활동으로 인해 서버 내 PDF 파일 및 벡터 청크가 영구 파쇄되었습니다. 기존 분석 리포트 및 채팅 기록 열람만 가능합니다.
              </div>
            </div>
          )}

          {/* Active Session Timer Banner (Only visible when session is active and NOT expired) */}
          {sessionId && !isExpiredSession && (
            <div className={`${styles.timerBanner} ${!autoDeleteEnabled ? styles.timerBannerPaused : ""}`}>
              <div className={styles.timerLeft}>
                <i className={`bi bi-clock-history ${styles.timerIcon}`}></i>
                <span>{t[lang].sessionTimeoutLabel}</span>
                <span className={styles.timerValue}>
                  {autoDeleteEnabled ? formatTime(countdown) : t[lang].sessionPaused}
                </span>
                <div className="form-check form-switch ms-3 mb-0 d-flex align-items-center gap-2">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    role="switch"
                    id="autoDeleteToggle"
                    checked={autoDeleteEnabled}
                    onChange={(e) => {
                      setAutoDeleteEnabled(e.target.checked);
                      if (e.target.checked) {
                        resetTimer();
                      }
                    }}
                    style={{ cursor: "pointer" }}
                  />
                  <label className="form-check-label fs-7 text-secondary" htmlFor="autoDeleteToggle" style={{ cursor: "pointer", userSelect: "none" }}>
                    {t[lang].autoDeleteLabel}
                  </label>
                </div>
              </div>
              <div className={styles.timerRight}>
                <i className="bi bi-info-circle me-1"></i> {t[lang].extendInfo}
              </div>
            </div>
          )}

          {/* 1. PDF/Markdown Sandbox Upload Zone */}
          {!sessionId && !isExpiredSession ? (
            <div
              className={`${styles.uploadSandbox} ${dragActive ? styles.uploadSandboxHovered : ""}`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById("sandbox-file-input").click()}
              role="button"
              tabIndex={0}
              style={{ padding: "80px 40px" }}
            >
              <input
                type="file"
                id="sandbox-file-input"
                className="d-none"
                accept="application/pdf,text/markdown,text/plain,.md,.txt,.markdown"
                onChange={handleFileChange}
              />
              {isUploading ? (
                <>
                  <div className={`spinner-border ${styles.accentSpinner}`} role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <p className={styles.loadingText}>{t[lang].uploadingText}</p>
                </>
              ) : (
                <>
                  <i className={`bi bi-cloud-arrow-up-fill ${styles.uploadIcon}`}></i>
                  <div className="d-flex flex-column gap-2">
                    <div className={styles.uploadTitle}>{t[lang].dragTitle}</div>
                    <div className={styles.uploadDesc}>
                      {t[lang].dragDesc}
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
                  <i className={`bi ${fileName.toLowerCase().endsWith(".pdf") ? "bi-file-earmark-pdf-fill" : "bi-file-earmark-text-fill"} ${styles.pdfFileIcon}`}></i>
                  <div>
                    <span className={styles.fileName}>{fileName}</span>
                    <div className={styles.chunkCount}>
                      <i className="bi bi-grid-fill me-1"></i> {isExpiredSession ? 0 : chunkCount} {t[lang].embeddingCompleted}
                    </div>
                  </div>
                </div>
                <button className={styles.resetBtn} onClick={resetSession}>
                  <i className="bi bi-trash3-fill me-2"></i> {t[lang].sessionWipeBtn}
                </button>
              </div>

              {/* Tab Selection Navigation */}
              <div className={styles.tabContainer}>
                <button
                  className={`${styles.tabBtn} ${activeTab === "peer_review" ? styles.tabBtnActive : ""}`}
                  onClick={() => setActiveTab("peer_review")}
                >
                  <i className="bi bi-people-fill me-1"></i> {t[lang].peerReviewTab}
                </button>
                <button
                  className={`${styles.tabBtn} ${activeTab === "hypothesis" ? styles.tabBtnActive : ""}`}
                  onClick={() => setActiveTab("hypothesis")}
                >
                  <i className="bi bi-journal-check me-1"></i> {t[lang].hypothesisTab}
                </button>
                <button
                  className={`${styles.tabBtn} ${activeTab === "defense" ? styles.tabBtnActive : ""}`}
                  onClick={() => setActiveTab("defense")}
                >
                  <i className="bi bi-easel3-fill me-1"></i> {t[lang].defenseTab}
                </button>
              </div>

              {/* Tab Contents */}
              <div className={styles.tabContent}>

                {/* Tab 1: Peer Review */}
                {activeTab === "peer_review" && (
                  <div className={styles.panelCard}>
                    <div className={styles.formRow}>
                      <label className={styles.label}>{t[lang].targetJournalLabel}</label>
                      <form onSubmit={handleRunPeerReview} className={styles.inputGroup}>
                        <input
                          type="text"
                          className={styles.textInput}
                          value={targetJournal}
                          onChange={(e) => setTargetJournal(e.target.value)}
                          placeholder={t[lang].targetJournalPlaceholder}
                          disabled={isExpiredSession}
                          required
                        />
                        <button type="submit" className={styles.primaryBtn} disabled={isReviewing || isExpiredSession}>
                          {isReviewing ? (
                            <>
                              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                              {t[lang].reviewingText}
                            </>
                          ) : (
                            <>
                              <i className="bi bi-play-fill"></i> {t[lang].runPeerReviewBtn}
                            </>
                          )}
                        </button>
                      </form>
                    </div>

                    {reviewError && <div className="alert alert-danger mb-0">{reviewError}</div>}

                    {(isReviewing || isTranslating) && (
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

                    {peerReviewResult && !isReviewing && !isTranslating && (
                      <div className="d-flex flex-column gap-4">
                        <div className={styles.reportSummaryCard}>
                          <div className={styles.summaryHeader}>
                            <h3 className={styles.summaryTitle}>
                              <i className="bi bi-file-earmark-bar-graph me-2"></i> {t[lang].peerReviewSummaryTitle}
                            </h3>
                            <span className={styles.scoreBadgeLarge}>
                              Score: {peerReviewResult.overall_score}/100
                            </span>
                          </div>
                          <p className={styles.summaryText}>
                            {lang === "ko" ? (peerReviewResult.summary_ko || peerReviewResult.summary) : peerReviewResult.summary}
                          </p>
                        </div>

                        <div className={styles.opinionGrid}>
                          {peerReviewResult.opinions.map((op, index) => (
                            <div key={index} className={styles.opinionCard}>
                              <div className={styles.opinionHeader}>
                                <span className={styles.agentLabel}>
                                  <i className={`bi ${op.agent_type === "methodology" ? "bi-calculator-fill text-info" :
                                      op.agent_type === "novelty" ? "bi-lightbulb-fill text-warning" : "bi-fonts text-success"
                                    }`}></i>
                                  {op.agent_type === "methodology" && t[lang].methodologyCritique}
                                  {op.agent_type === "novelty" && t[lang].noveltyCritique}
                                  {op.agent_type === "style" && t[lang].styleCritique}
                                </span>
                                <span className={`${styles.opinionScore} ${getScoreColorClass(op.score)}`}>
                                  {op.score} pts
                                </span>
                              </div>
                              <p className={styles.opinionBody}>
                                {lang === "ko" ? (op.feedback_ko || op.feedback) : op.feedback}
                              </p>
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
                    <div className={styles.formRow}>
                      <label className={styles.label}>{t[lang].researchHypothesisLabel}</label>
                      <form onSubmit={handleVerifyHypothesis} className={styles.inputGroup}>
                        <input
                          type="text"
                          className={styles.textInput}
                          value={hypothesis}
                          onChange={(e) => setHypothesis(e.target.value)}
                          placeholder={t[lang].researchHypothesisPlaceholder}
                          disabled={isExpiredSession}
                          minLength={5}
                          required
                        />
                        <button type="submit" className={styles.primaryBtn} disabled={isVerifying || !hypothesis.trim() || isExpiredSession}>
                          {isVerifying ? (
                            <>
                              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                              {t[lang].verifyingText}
                            </>
                          ) : (
                            <>
                              <i className="bi bi-patch-check"></i> {t[lang].verifyHypothesisBtn}
                            </>
                          )}
                        </button>
                      </form>
                    </div>

                    {verifyError && <div className="alert alert-danger mb-0">{verifyError}</div>}

                    {(isVerifying || isTranslating) && (
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

                    {hypothesisResult && !isVerifying && !isTranslating && (
                      <div className="d-flex flex-column gap-4">
                        <div className={styles.gaugeContainer}>
                          <span className={styles.gaugeLabel}>
                            {t[lang].consensusVerdictLabel}
                            <span className={`ms-2 ${hypothesisResult.verdict === "SUPPORT" ? "text-success" :
                                hypothesisResult.verdict === "REFUTE" ? "text-danger" : "text-warning"
                              }`}>
                              {getVerdictLabel(hypothesisResult.verdict)}
                            </span>
                          </span>
                          <div className={styles.gaugeTrack}>
                            <div
                              className={`${styles.gaugeFill} ${hypothesisResult.verdict === "SUPPORT" ? styles.gaugeFillSupport :
                                  hypothesisResult.verdict === "REFUTE" ? styles.gaugeFillRefute : styles.gaugeFillInsufficient
                                }`}
                              style={{ width: `${hypothesisResult.consensus_ratio * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-secondary fs-8">
                            {lang === "ko" ?
                              `의견 합의율: ${(hypothesisResult.consensus_ratio * 100).toFixed(1)}% (찬성 ${hypothesisResult.support_count}, 반대 ${hypothesisResult.refute_count}, 보류 ${hypothesisResult.insufficient_count})` :
                              `Consensus Ratio: ${(hypothesisResult.consensus_ratio * 100).toFixed(1)}% (${hypothesisResult.support_count} Support, ${hypothesisResult.refute_count} Refute, ${hypothesisResult.insufficient_count} Insufficient)`
                            }
                          </span>
                        </div>

                        <div>
                          <h4 className="fs-6 fw-bold mb-3">
                            <i className={`bi bi-fingerprint ${styles.accentIcon} me-2`}></i> {t[lang].selfConsistencyTitle}
                          </h4>
                          <div className={styles.voteList}>
                            {hypothesisResult.detailed_votes.map((vt, index) => (
                              <div key={index} className={styles.voteCard}>
                                <div className={styles.voteHeader}>
                                  <span className={styles.voteTitle}>Round {index + 1}</span>
                                  <span className={`${styles.opinionScore} ${vt.vote === "SUPPORT" ? styles.scoreGreen :
                                      vt.vote === "REFUTE" ? styles.scoreRed : styles.scoreYellow
                                    }`}>
                                    {getVerdictLabel(vt.vote)}
                                  </span>
                                </div>
                                <p className={styles.opinionBody}>
                                  {lang === "ko" ? (vt.reason_ko || vt.reason) : vt.reason}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>

                        {hypothesisResult.citations && hypothesisResult.citations.length > 0 && (
                          <div className={styles.citationSection}>
                            <div className={styles.citationTitle}>
                              <i className={`bi bi-journal-text ${styles.accentIcon} me-2`}></i> {t[lang].citationsTitle}
                            </div>
                            {hypothesisResult.citations.map((cite, idx) => (
                              <div key={idx} className={styles.citationCard}>
                                {lang === "ko" ? (hypothesisResult.citations_ko?.[idx] || cite) : cite}
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

                    {!isDefenseFinished ? (
                      <div className={styles.chatConsole}>
                        <div className={styles.chatMessages}>
                          {chatHistory.map((ch, index) => (
                            <div key={index} className="d-flex flex-column gap-3">
                              <div className={`${styles.messageRow} ${styles.messageRowJudge}`}>
                                <div className={`${styles.bubble} ${styles.bubbleJudge}`}>
                                  <strong className={`d-block ${styles.judgeTitle} mb-1`}>
                                    <i className="bi bi-person-fill-exclamation me-1"></i> {t[lang].judgeActiveTitle} (Turn {ch.turn})
                                  </strong>
                                  <ReactMarkdown>
                                    {lang === "ko" ? (ch.question_ko || ch.question) : ch.question}
                                  </ReactMarkdown>
                                </div>
                              </div>

                              {ch.answer && (
                                <div className={`${styles.messageRow} ${styles.messageRowUser}`}>
                                  <div className={`${styles.bubble} ${styles.bubbleUser}`}>
                                    <strong className={`d-block ${styles.authorTitle} mb-1`}>
                                      <i className="bi bi-person-fill-check me-1"></i> {t[lang].authorActiveTitle}
                                    </strong>
                                    {ch.answer}
                                  </div>
                                </div>
                              )}

                              {ch.score !== null && ch.score !== undefined && (
                                <div className={`${styles.messageRow} ${styles.messageRowJudge} mt-1`}>
                                  <div className={styles.gradingCard}>
                                    <div className={styles.gradingHeader}>
                                      <span className={styles.scoreLabel}>
                                        <i className="bi bi-award-fill me-1"></i> {lang === "ko" ? `디펜스 평가 점수: ${ch.score}/100` : `Defense Score: ${ch.score}/100`}
                                      </span>
                                    </div>
                                    <div className={styles.critiqueText}>
                                      <ReactMarkdown>
                                        {lang === "ko" ? (ch.feedback_ko || ch.feedback) : ch.feedback}
                                      </ReactMarkdown>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}

                          {currentQuestion && !isChatting && !isTranslating && (chatHistory.length === 0 || chatHistory[chatHistory.length - 1].answer) && (
                            <div className={`${styles.messageRow} ${styles.messageRowJudge}`}>
                              <div className={`${styles.bubble} ${styles.bubbleJudge}`}>
                                <strong className={`d-block ${styles.judgeTitle} mb-1`}>
                                  <i className="bi bi-person-fill-exclamation me-1"></i> {t[lang].judgeActiveTitle} (Turn {currentTurn})
                                </strong>
                                <ReactMarkdown>
                                  {lang === "ko" ? (currentQuestionKo || currentQuestion) : currentQuestion}
                                </ReactMarkdown>
                              </div>
                            </div>
                          )}

                          {(isChatting || isTranslating) && (
                            <div className={`${styles.messageRow} ${styles.messageRowJudge}`}>
                              <div className={`${styles.bubble} ${styles.bubbleJudge}`}>
                                <div className={`spinner-border spinner-border-sm ${styles.accentSpinner} me-2`} role="status"></div>
                                <span className="text-secondary fs-8">{t[lang].typingText}</span>
                              </div>
                            </div>
                          )}

                          <div ref={chatBottomRef} />
                        </div>

                        <form onSubmit={handleSendDefenseAnswer} className={styles.chatInputBar}>
                          <textarea
                            ref={textareaRef}
                            className={styles.chatTextArea}
                            placeholder={isExpiredSession ? "읽기 전용 모드에서는 디펜스를 진행할 수 없습니다." : isChatting ? t[lang].loadingText : t[lang].placeholderAnswer}
                            value={userAnswer}
                            onChange={(e) => setUserAnswer(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                handleSendDefenseAnswer(e);
                              }
                            }}
                            disabled={isChatting || isDefenseFinished || isExpiredSession}
                            required
                          />
                          <button
                            type="submit"
                            className={styles.primaryBtn}
                            disabled={isChatting || isDefenseFinished || !userAnswer.trim() || isExpiredSession}
                          >
                            <i className="bi bi-send-fill"></i>
                          </button>
                        </form>
                      </div>
                    ) : (
                      <div className="d-flex w-100 gap-4 align-items-start position-relative">
                        <div className={`${styles.scorecard} flex-grow-1`} style={{ minWidth: 0 }}>
                          <i className={`bi bi-trophy-fill ${styles.trophyIcon}`}></i>
                          <div>
                            <h3 className={styles.scorecardTitle}>{t[lang].oralDefenseTitle}</h3>
                            <p className={styles.scorecardDesc}>
                              {t[lang].oralDefenseDesc}
                            </p>
                          </div>

                          {chatHistory.length > 0 && (
                            <div className={styles.totalAverage}>
                              <span className={styles.avgLabel}>{t[lang].averageDefenseScore}</span>
                              <span className={styles.avgVal}>
                                {(chatHistory.reduce((acc, cur) => acc + (cur.score || 0), 0) / chatHistory.length).toFixed(1)} / 100
                              </span>
                            </div>
                          )}

                          {finalReport && (
                            <div className="w-100 text-start mt-3">
                              <h4 className="fs-6 fw-bold mb-3 text-secondary">
                                <i className="bi bi-file-earmark-text me-2"></i> {t[lang].committeeDecision}
                              </h4>
                              <div className={styles.reportTextWrapper}>
                                <div className={styles.reportText}>
                                  <ReactMarkdown components={mdComponents}>
                                    {activeReportText}
                                  </ReactMarkdown>
                                </div>
                              </div>
                            </div>
                          )}

                          <button className={styles.primaryBtn} onClick={() => {
                            setChatHistory([]);
                            setCurrentQuestion("");
                            setCurrentQuestionKo("");
                            setCurrentTurn(1);
                            setIsDefenseFinished(false);
                            setFinalReport(null);
                            setFinalReportKo(null);
                            initiateDefense();
                          }} disabled={isExpiredSession}>
                            <i className="bi bi-arrow-clockwise"></i> {t[lang].newGameBtn}
                          </button>
                        </div>

                        {finalReport && tocItems.length > 0 && (
                          <div className={styles.tocContainerOutside}>
                            <div className={styles.tocHeader}>
                              <i className="bi bi-list-ul me-1"></i> {lang === "ko" ? "목차 (TOC)" : "Table of Contents"}
                            </div>
                            <div className={styles.tocList}>
                              {tocItems.map((item, idx) => (
                                <a
                                  key={idx}
                                  className={`${styles.tocItem} ${styles[`tocItemL${item.level}`]}`}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    const el = document.getElementById(item.id);
                                    if (el) {
                                      el.scrollIntoView({ behavior: "smooth", block: "start" });
                                    }
                                  }}
                                >
                                  {item.text}
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {chatError && <div className="alert alert-danger mb-0">{chatError}</div>}

                  </div>
                )}

              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default function Feature4ArenaPage() {
  return (
    <Suspense fallback={<LoadingSpinner message="디펜스 아레나 플레이그라운드 로드 중..." />}>
      <DefenseArenaPlayground />
    </Suspense>
  );
}
