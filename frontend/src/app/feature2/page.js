"use client"

import { useState, useEffect, useRef } from "react";
import styles from "./page.module.css";
import { startAnalysis, getTaskStatus, getTaskResult } from "@/apis/researchGap";
import ControlPanel from "@/components/feature2/ControlPanel";
import MatrixTable from "@/components/feature2/MatrixTable";
import ResearchGapSynthesis from "@/components/feature2/ResearchGapSynthesis";
import TrendInbox from "@/components/feature2/TrendInbox";

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
            setError(taskData.error_message || "배치 태스크 처리 중 실패했습니다.");
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
      const errMsg = err.response?.data?.message || err.response?.data?.detail || "서버 연결에 실패했거나 권한이 없습니다.";
      setError(errMsg);
      setLoading(false);
    }
  };

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
      />

      {/* Bottom Layout Grid */}
      <div className={styles.gapContainer}>
        {/* Left Column: Spec Matrix Table */}
        <MatrixTable result={result} />

        {/* Right Column: AI Synthesis & Trend Inbox */}
        <div className="d-flex flex-column gap-4">
          <ResearchGapSynthesis result={result} />
          <TrendInbox notifications={notifications} />
        </div>
      </div>
    </div>
  );
}
