"use client"

import { Suspense } from "react";
import styles from "./page.module.css";
import ControlPanel from "@/components/feature2/ControlPanel";
import MatrixTable from "@/components/feature2/MatrixTable";
import ResearchGapSynthesis from "@/components/feature2/ResearchGapSynthesis";
import PipelineGraph from "@/components/feature2/pipeline-graph/PipelineGraph";
import useResearchGap from "@/components/feature2/useResearchGap";

/**
 * 대규모 문헌 비교 분석기 (Research Gap Analyzer) 내부 핵심 페이지 컨텐츠 컴포넌트입니다.
 * useResearchGap 커스텀 훅을 호출하여 비즈니스 데이터 상태와 컴포넌트 조립을 중개합니다.
 */
function ResearchGapPageContent() {
  const gapState = useResearchGap();

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

      {/* Bottom Layout Grid */}
      <div className={styles.gapContainer}>
        {/* Left Column: Spec Matrix Table */}
        <MatrixTable result={gapState.displayResult} />

        {/* Right Column: AI Synthesis */}
        <ResearchGapSynthesis result={gapState.displayResult} />
      </div>

      {/* Visual Pipeline Graph Flow */}
      {gapState.result && (
        <PipelineGraph result={gapState.displayResult} query={gapState.query} />
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

