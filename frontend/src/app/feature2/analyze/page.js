"use client"

import { Suspense, useState } from "react";
import styles from "./page.module.css";
import ControlPanel from "@/components/feature2/ControlPanel";
import MatrixTable from "@/components/feature2/MatrixTable";
import ResearchGapSynthesis from "@/components/feature2/ResearchGapSynthesis";
import PipelineGraph from "@/components/feature2/pipeline-graph/PipelineGraph";
import useResearchGap from "@/components/feature2/useResearchGap";
import LoadingSpinner from "@/components/loading-spinner/LoadingSpinner";

/**
 * 대규모 문헌 비교 분석기 (Research Gap Analyzer) 내부 핵심 페이지 컨텐츠 컴포넌트입니다.
 * useResearchGap 커스텀 훅을 호출하여 비즈니스 데이터 상태와 컴포넌트 조립을 중개합니다.
 */
function ResearchGapPageContent() {
  const gapState = useResearchGap();
  const [activeTab, setActiveTab] = useState("matrix"); // "matrix" | "graph"

  return (
    <div className={styles.container}>
      {/* Control Header & Task Submission Panel */}
      <ControlPanel
        domain={gapState.domain}
        setDomain={gapState.setDomain}
        query={gapState.query}
        setQuery={gapState.setQuery}
        loading={gapState.loading}
        onSubmit={gapState.handleAnalyze}
        status={gapState.status}
        progress={gapState.progress}
        statusText={gapState.statusText}
        taskId={gapState.taskId}
        error={gapState.error}
        papersCount={gapState.result ? gapState.result.papers?.length : undefined}
        isTranslated={gapState.isTranslated}
        onTranslateToggle={gapState.handleTranslateToggle}
        translateLoading={gapState.translateLoading}
      />

      {/* View Switcher Tabs (Only visible when analysis result exists) */}
      {gapState.result && (
        <div className="d-flex justify-content-center my-4">
          <div className={styles.tabContainer}>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === "matrix" ? styles.tabBtnActive : ""}`}
              onClick={() => setActiveTab("matrix")}
            >
              <i className="bi bi-grid-3x3-gap me-2"></i>
              분석 매트릭스
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === "graph" ? styles.tabBtnActive : ""}`}
              onClick={() => setActiveTab("graph")}
            >
              <i className="bi bi-diagram-3 me-2"></i>
              파이프라인 그래프
            </button>
          </div>
        </div>
      )}

      {/* Tab Content Area */}
      {gapState.result && activeTab === "matrix" && (
        <div className={`${styles.gapContainer} ${styles.fadeIn}`}>
          {/* Left Column: Spec Matrix Table */}
          <MatrixTable result={gapState.displayResult} />

          {/* Right Column: AI Synthesis */}
          <ResearchGapSynthesis result={gapState.displayResult} />
        </div>
      )}

      {gapState.result && activeTab === "graph" && (
        <div className={styles.fadeIn}>
          {/* Visual Pipeline Graph Flow */}
          <PipelineGraph result={gapState.displayResult} query={gapState.query} />
        </div>
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
    <Suspense fallback={<LoadingSpinner message="분석기 로딩 중..." />}>
      <ResearchGapPageContent />
    </Suspense>
  );
}

