"use client"

import { Suspense, useState, useEffect } from "react";
import styles from "./page.module.css";
import ControlPanel from "@/components/feature2/ControlPanel";
import MatrixTable from "@/components/feature2/MatrixTable";
import ResearchGapSynthesis from "@/components/feature2/ResearchGapSynthesis";
import PipelineGraph from "@/components/feature2/pipeline-graph/PipelineGraph";
import useResearchGap from "@/components/feature2/useResearchGap";
import LoadingSpinner from "@/components/loading-spinner/LoadingSpinner";
import TutorialTour from "@/components/feature2/tutorial/TutorialTour";
import PrintReport from "@/components/feature2/PrintReport";

/**
 * 대규모 문헌 비교 분석기 (Research Gap Analyzer) 내부 핵심 페이지 컨텐츠 컴포넌트입니다.
 * useResearchGap 커스텀 훅을 호출하여 비즈니스 데이터 상태와 컴포넌트 조립을 중개합니다.
 */
function ResearchGapPageContent() {
  const gapState = useResearchGap();
  const [activeTab, setActiveTab] = useState("matrix"); // "matrix" | "graph"
  const [isTutorialActive, setIsTutorialActive] = useState(false);

  useEffect(() => {
    // Sync active tab to matrix during tutorial to ensure matrix targets exist
    if (isTutorialActive) {
      setActiveTab("matrix");
    }
  }, [isTutorialActive]);

  useEffect(() => {
    const handleStart = () => {
      setIsTutorialActive(true);
      setActiveTab("matrix");
    };
    const handleEnd = () => setIsTutorialActive(false);

    window.addEventListener("trigger-page-tutorial", handleStart);
    window.addEventListener("tutorial-ended", handleEnd);
    return () => {
      window.removeEventListener("trigger-page-tutorial", handleStart);
      window.removeEventListener("tutorial-ended", handleEnd);
    };
  }, []);

  const mockResult = {
    papers: [
      {
        title: "Attention Is All You Need",
        arxiv_id: "1706.03762",
        similarity: 0.95,
        problems_solved: [
          {
            summary: "기존 RNN/CNN 기반 시퀀스 모델의 순차적 계산 병목을 해결하고 셀프 어텐션 기반 병렬화 달성",
            source_quote: "The Transformer allows for significantly more parallelization..."
          }
        ],
        limitations: [
          {
            summary: "입력 시퀀스 길이에 비례해 연산 복잡도가 제곱으로 증가(O(N^2))하는 긴 문맥 처리 한계",
            source_quote: "self-attention layers ... requires O(N^2) computations..."
          }
        ]
      }
    ],
    common_limitations: [
      "대규모 긴 문맥(Long-context) 입력 시 연산 및 메모리 자원 소모의 제곱적 증가 현상"
    ],
    suggested_directions: [
      "선형 어텐션(Linear Attention) 메커니즘을 적용한 초거대 언어 모델 효율화 연구"
    ]
  };

  const hasResult = gapState.result || isTutorialActive;
  const currentDisplayResult = isTutorialActive ? mockResult : gapState.displayResult;

  const tutorialSteps = [
    {
      target: ".tutorial-control-panel",
      title: "분석 제어 패널",
      content: "학술 분야(CS/Bio)를 변경하고 주제 키워드를 지정하여 인공지능 연구 공백 분석 파이프라인을 구동하고, 실시간 진행률 확인 및 보고서 번역 처리를 수행할 수 있는 제어판입니다.",
      position: "bottom"
    },
    {
      target: ".tutorial-view-tabs",
      title: "분석 뷰 전환 탭",
      content: "수집된 ArXiv 논문들의 상세 비교 표를 보여주는 '분석 매트릭스' 탭과, 로드맵 탐색 흐름을 마인드맵 노드로 시각화하는 '파이프라인 그래프' 탭을 선택적으로 전환할 수 있습니다.",
      position: "bottom"
    },
    {
      target: ".tutorial-action-toolbar",
      title: "보고서 내보내기",
      content: "생성된 학술 분석 보고서를 범용 마크다운(.md) 파일로 로컬 저장하거나, PDF 인쇄(또는 PNG/SVG 이미지 저장) 기능을 활용하여 출력할 수 있는 유틸리티 툴바입니다.",
      position: "bottom"
    },
    {
      target: ".tutorial-matrix-table",
      title: "문헌 비교 스펙 매트릭스",
      content: "인공지능 RAG를 통해 추출된 개별 학술 논문들의 핵심 정보(제안된 방법론 및 각 논문이 지닌 세부 한계점들)를 표 형태로 대조하여 분석해 줍니다.",
      position: "right"
    },
    {
      target: ".tutorial-synthesis-panel",
      title: "연구 공백 및 방향 제안",
      content: "문헌군 스펙 대조 결과로부터 발견한 핵심 공동 연구 공백(Limitations)을 추출하고, 학계의 미개척 영역을 돌파하기 위해 에이전트가 새롭게 제안하는 구체적인 미래 연구 주제 리스트입니다.",
      position: "left"
    }
  ];

  // 1. Markdown Export Handler
  const handleExportMarkdown = () => {
    if (!gapState.displayResult) return;
    
    const { domain, query, displayResult } = gapState;
    const { papers = [], common_limitations = [], suggested_directions = [] } = displayResult || {};
    
    let md = `# Research Gap Analysis Report\n\n`;
    md += `- **학술 도메인**: ${domain ? domain.toUpperCase() : "N/A"}\n`;
    md += `- **분석 질의어**: ${query || "N/A"}\n`;
    md += `- **생성 일시**: ${new Date().toLocaleString()}\n\n`;
    
    md += `## 1. 문헌 비교 스펙 매트릭스\n\n`;
    md += `| 논문 정보 | 해결된 문제 & 제안 방법론 | 식별된 한계점 & 공백 |\n`;
    md += `| :--- | :--- | :--- |\n`;
    
    papers.forEach(paper => {
      const paperInfo = `**${paper.title}**<br>[ArXiv](https://arxiv.org/abs/${paper.arxiv_id})\\|유사도: ${paper.similarity !== undefined ? Math.round(paper.similarity * 100) + '%' : 'N/A'}`;
      
      const problemsText = paper.problems_solved.map(item => {
        const isObj = typeof item === "object" && item !== null;
        const summary = isObj ? item.summary : item;
        const quote = isObj ? item.source_quote : null;
        return `• ${summary}${quote ? `<br>_> Quote: "${quote.replace(/\n/g, ' ').replace(/"/g, '\\"')}"_` : ''}`;
      }).join('<br><br>');
      
      const limitationsText = paper.limitations.map(item => {
        const isObj = typeof item === "object" && item !== null;
        const summary = isObj ? item.summary : item;
        const quote = isObj ? item.source_quote : null;
        return `• ${summary}${quote ? `<br>_> Quote: "${quote.replace(/\n/g, ' ').replace(/"/g, '\\"')}"_` : ''}`;
      }).join('<br><br>');
      
      // Escape pipe character in content cells to prevent breaking markdown table structure
      const safeInfo = paperInfo.replace(/\|/g, '\\|');
      const safeProblems = problemsText.replace(/\|/g, '\\|');
      const safeLimitations = limitationsText.replace(/\|/g, '\\|');
      
      md += `| ${safeInfo} | ${safeProblems} | ${safeLimitations} |\n`;
    });
    
    md += `\n\n## 2. AI Research Gap 분석\n\n`;
    md += `### 공통적인 연구 한계 및 학계 공백\n`;
    if (common_limitations.length > 0) {
      common_limitations.forEach(limit => {
        md += `- ${limit}\n`;
      });
    } else {
      md += `식별된 공통 한계점이 없습니다.\n`;
    }
    
    md += `\n### 추천 연구 주제 제안\n`;
    if (suggested_directions.length > 0) {
      suggested_directions.forEach((dir, idx) => {
        const match = dir.match(/[:：]|\s+-\s+|\s+–\s+|\s+—\s+/);
        let title = `추천 연구 주제 #${idx + 1}`;
        let description = dir;
        if (match) {
          const index = match.index;
          title = dir.substring(0, index).trim();
          description = dir.substring(index + match[0].length).trim();
        }
        md += `#### ${title}\n${description}\n\n`;
      });
    } else {
      md += `제안된 연구 주제가 없습니다.\n`;
    }
    
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const safeQuery = (query || "analysis").replace(/[^a-zA-Z0-9가-힣]/g, "_").substring(0, 30);
    link.setAttribute("download", `research_gap_${domain || "export"}_${safeQuery}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
 
  // 2. PDF / Print Handler
  const handlePrintReport = () => {
    window.print();
  };
 
  // 3. Graph PNG Export trigger
  const handleExportGraphPng = () => {
    window.dispatchEvent(new CustomEvent("export-graph-png"));
  };
 
  // 4. Graph SVG Export trigger
  const handleExportGraphSvg = () => {
    window.dispatchEvent(new CustomEvent("export-graph-svg"));
  };
 
  return (
    <div className={styles.container}>
      {/* 튜토리얼 가이드 컴포넌트 마운트 */}
      <TutorialTour steps={tutorialSteps} matchPath="/feature2/analyze" />
 
      {/* ----------------- SCREEN ONLY VIEW (Hidden on PDF/Print) ----------------- */}
      <div className="d-print-none w-100">
        {/* Control Header & Task Submission Panel */}
        <div className="tutorial-control-panel">
          <ControlPanel
            domain={isTutorialActive ? "cs" : gapState.domain}
            setDomain={gapState.setDomain}
            query={isTutorialActive ? "Attention Mechanism in Transformer" : gapState.query}
            setQuery={gapState.setQuery}
            loading={isTutorialActive ? false : gapState.loading}
            onSubmit={gapState.handleAnalyze}
            status={isTutorialActive ? "COMPLETED" : gapState.status}
            progress={isTutorialActive ? 100 : gapState.progress}
            statusText={isTutorialActive ? "분석 완료" : gapState.statusText}
            taskId={isTutorialActive ? "tutorial-dummy-task" : gapState.taskId}
            error={gapState.error}
            papersCount={isTutorialActive ? 1 : (gapState.result ? gapState.result.papers?.length : undefined)}
            isTranslated={isTutorialActive ? false : gapState.isTranslated}
            onTranslateToggle={gapState.handleTranslateToggle}
            translateLoading={gapState.translateLoading}
          />
        </div>

        {/* View Switcher & Action Toolbar (Only visible when analysis result exists) */}
        {hasResult && (
          <div className={styles.toolbarContainer}>
            {/* Spacer to center tabs on desktop */}
            <div className={styles.centerSpacer}></div>

            {/* Switcher Tabs */}
            <div className={styles.tabWrapper}>
              <div className={`${styles.tabContainer} tutorial-view-tabs`}>
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
                  disabled={isTutorialActive}
                >
                  <i className="bi bi-diagram-3 me-2"></i>
                  파이프라인 그래프
                </button>
              </div>
            </div>

            {/* Action Export Buttons */}
            <div className={styles.toolbarWrapper}>
              <div className={`${styles.actionToolbar} tutorial-action-toolbar`}>
                {activeTab === "matrix" ? (
                  <>
                    <button
                      type="button"
                      className={styles.exportBtn}
                      onClick={isTutorialActive ? undefined : handleExportMarkdown}
                      title="분석 결과를 마크다운 파일로 다운로드합니다"
                      disabled={isTutorialActive}
                    >
                      <i className="bi bi-file-earmark-arrow-down-fill"></i>
                      Markdown 저장
                    </button>
                    <button
                      type="button"
                      className={styles.exportBtn}
                      onClick={isTutorialActive ? undefined : handlePrintReport}
                      title="보고서를 인쇄하거나 PDF로 저장합니다"
                      disabled={isTutorialActive}
                    >
                      <i className="bi bi-printer-fill"></i>
                      PDF / 인쇄
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      className={styles.exportBtn}
                      onClick={handleExportGraphPng}
                      title="마인드맵 그래프를 PNG 이미지로 다운로드합니다"
                    >
                      <i className="bi bi-file-earmark-image-fill"></i>
                      PNG 저장
                    </button>
                    <button
                      type="button"
                      className={styles.exportBtn}
                      onClick={handleExportGraphSvg}
                      title="마인드맵 그래프를 SVG 벡터 이미지로 다운로드합니다"
                    >
                      <i className="bi bi-filetype-svg"></i>
                      SVG 저장
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab Content Area */}
        {hasResult && activeTab === "matrix" && (
          <div className={`${styles.gapContainer} ${styles.fadeIn}`}>
            {/* Left Column: Spec Matrix Table */}
            <div className="tutorial-matrix-table flex-fill">
              <MatrixTable result={currentDisplayResult} />
            </div>

            {/* Right Column: AI Synthesis */}
            <div className="tutorial-synthesis-panel">
              <ResearchGapSynthesis result={currentDisplayResult} />
            </div>
          </div>
        )}

        {hasResult && activeTab === "graph" && (
          <div className={styles.fadeIn}>
            {/* Visual Pipeline Graph Flow */}
            <PipelineGraph result={currentDisplayResult} query={gapState.query} />
          </div>
        )}
      </div>

      {/* ----------------- PROFESSIONAL PDF/PRINT ONLY VIEW (Shown on Print only) ----------------- */}
      <PrintReport
        result={currentDisplayResult}
        domain={gapState.domain}
        query={gapState.query}
        isTutorialActive={isTutorialActive}
      />
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

