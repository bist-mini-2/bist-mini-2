"use client"

import { useState, useEffect, useRef, useContext, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import styles from "./page.module.css";
import { startAnalysis, getTaskStatus, getTaskResult, translateMatrix } from "@/apis/researchGap";
import { AuthContext } from "@/contexts/AuthContext";
import { NotificationContext } from "@/contexts/NotificationContext";
import ControlPanel from "@/components/feature2/ControlPanel";
import MatrixTable from "@/components/feature2/MatrixTable";
import ResearchGapSynthesis from "@/components/feature2/ResearchGapSynthesis";
import PipelineGraph from "@/components/feature2/PipelineGraph";

/**
 * 대규모 문헌 비교 분석기 (Research Gap Analyzer) 내부 핵심 페이지 컨텐츠 컴포넌트입니다.
 */
function ResearchGapPageContent() {
  const { accessToken } = useContext(AuthContext);
  const { notifications: globalNotifications } = useContext(NotificationContext);
  const searchParams = useSearchParams();
  const queryTaskId = searchParams.get("taskId");

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

  // 번역 관련 상태
  const [isTranslated, setIsTranslated] = useState(false);
  const [translatedResult, setTranslatedResult] = useState(null);
  const [translateLoading, setTranslateLoading] = useState(false);

  // useRef를 활용해 비동기 콜백에서 최신 taskId 및 폴링 제어를 참조합니다.
  const currentTaskIdRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  // URL 쿼리 파라미터로 taskId가 넘어온 경우 해당 태스크 자동 로드 및 폴링
  useEffect(() => {
    if (queryTaskId) {
      setResult(null);
      setError(null);
      setIsTranslated(false);
      setTranslatedResult(null);
      setTaskId(queryTaskId);
      currentTaskIdRef.current = queryTaskId;
      setLoading(true);
      setStatus("PENDING");
      setStatusText("선택된 분석 작업 데이터를 불러오는 중...");
      startPolling(queryTaskId);
    }
  }, [queryTaskId]);

  // 전역 실시간 알림 피드를 모니터링하여 현재 실행 중인 작업의 완료/실패 알림 수신 시 즉시 데이터 반영
  useEffect(() => {
    if (!taskId) return;
    const latestNotif = globalNotifications[0];
    
    // 만약 현재 대기 중인 작업과 관련된 알림이 도착했다면
    if (latestNotif && latestNotif.task_id === taskId) {
      if (latestNotif.type === "success") {
        console.log("Global notification completed event detected for task:", taskId);
        clearInterval(pollingIntervalRef.current);
        fetchFinalResult(taskId);
      } else if (latestNotif.type === "danger") {
        console.log("Global notification failed event detected for task:", taskId);
        clearInterval(pollingIntervalRef.current);
        setError(latestNotif.message || "분석 배치 작업 처리 중 에러가 발생했습니다.");
        setStatus("FAILED");
        setProgress(100);
        setLoading(false);
      }
    }
  }, [globalNotifications, taskId]);

  // 컴포넌트 언마운트 시 폴링 클리어
  useEffect(() => {
    return () => {
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
        if (res.data.translated_result) {
          setTranslatedResult(res.data.translated_result);
        }
        if (res.data.query) {
          setQuery(res.data.query);
        }
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
            setError(taskData.error_message || "배치 태스크 처리 중 실패했습니다.");
            setLoading(false);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1500);
  };

  // 번역 토글 핸들러
  const handleTranslateToggle = async () => {
    if (!result || !taskId) return;
    
    if (isTranslated) {
      setIsTranslated(false);
    } else {
      if (translatedResult) {
        setIsTranslated(true);
      } else {
        setTranslateLoading(true);
        try {
          const res = await translateMatrix(taskId);
          if (res.status === "success" && res.data) {
            setTranslatedResult(res.data);
            setIsTranslated(true);
          } else {
            setError("번역 데이터를 불러오지 못했습니다.");
          }
        } catch (err) {
          console.error("Translation error:", err);
          setError("번역 진행 중 오류가 발생했습니다.");
        } finally {
          setTranslateLoading(false);
        }
      }
    }
  };

  // 분석 시작 요청 실행
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);
    setError(null);
    setIsTranslated(false);
    setTranslatedResult(null);
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
      const errMsg = err.response?.data?.message || err.response?.data?.detail || "서버 연결에 실패했거나 권한이 없습니다.";
      setError(errMsg);
      setLoading(false);
    }
  };

  const displayResult = isTranslated ? translatedResult : result;

  return (
    <div className={styles.container}>
      {/* Control Header & Task Submission Panel */}
      <ControlPanel
        domain={domain}
        setDomain={setDomain}
        query={query}
        setQuery={setQuery}
        loading={loading}
        onSubmit={handleAnalyze}
        status={status}
        progress={progress}
        statusText={statusText}
        taskId={taskId}
        error={error}
        papersCount={result ? result.papers?.length : undefined}
        isTranslated={isTranslated}
        onTranslateToggle={handleTranslateToggle}
        translateLoading={translateLoading}
      />

      {/* Bottom Layout Grid */}
      <div className={styles.gapContainer}>
        {/* Left Column: Spec Matrix Table */}
        <MatrixTable result={displayResult} />

        {/* Right Column: AI Synthesis */}
        <ResearchGapSynthesis result={displayResult} />
      </div>

      {/* Visual Pipeline Graph Flow */}
      {result && (
        <PipelineGraph result={displayResult} query={query} />
      )}
    </div>
  );
}

/**
 * 대규모 문헌 비교 분석기 (Research Gap Analyzer) 페이지 컴포넌트입니다.
 * URL 쿼리 분석용 useSearchParams 사용을 위해 Suspense 경계로 감싸 컴파일 에러를 방지합니다.
 */
export default function ResearchGapPage() {
  return (
    <Suspense fallback={
      <div className="d-flex flex-column align-items-center justify-content-center p-5 text-muted">
        <div className="spinner-border text-success mb-3" role="status">
          <span className="visually-hidden">Loading page...</span>
        </div>
        <span>분석기 로딩 중...</span>
      </div>
    }>
      <ResearchGapPageContent />
    </Suspense>
  );
}
