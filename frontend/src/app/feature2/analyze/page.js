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
  const currentDisplayResult = isTutorialActive && !gapState.result ? mockResult : gapState.displayResult;

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
      {hasResult && (
        <div className={`${styles.printReportContainer} d-none d-print-block w-100`}>
          {/* PAGE 1: Cover and Summary */}
          <div className={styles.printPage} style={{ pageBreakAfter: "always" }}>
            <div className="text-center my-5 py-4">
              <div className="mb-4">
                <i className="bi bi-journal-text text-primary" style={{ fontSize: "3.5rem" }}></i>
              </div>
              <h1 className="fw-bold text-dark mb-2" style={{ fontSize: "28pt", letterSpacing: "-1px" }}>Research Gap Analysis Report</h1>
              <h4 className="text-secondary mb-5 font-normal" style={{ fontSize: "14pt", fontWeight: 400 }}>AI 기반 문헌 대조 비교 및 연구 공백 분석 보고서</h4>
              
              <div className="mx-auto my-5 p-4 rounded-3 text-start" style={{ maxWidth: "580px", border: "1px solid #cbd5e1", backgroundColor: "#f8fafc" }}>
                <table className="table table-borderless m-0" style={{ fontSize: "10.5pt", width: "100%" }}>
                  <tbody>
                    <tr>
                      <th className="text-secondary fw-semibold py-1.5" style={{ width: "140px" }}>학술 도메인</th>
                      <td className="text-dark py-1.5">: {isTutorialActive && !gapState.result ? "CS" : (gapState.domain ? gapState.domain.toUpperCase() : "N/A")}</td>
                    </tr>
                    <tr>
                      <th className="text-secondary fw-semibold py-1.5">분석 관심 키워드</th>
                      <td className="text-dark py-1.5">: {isTutorialActive && !gapState.result ? "Transformers and Self-Attention" : (gapState.query || "N/A")}</td>
                    </tr>
                    <tr>
                      <th className="text-secondary fw-semibold py-1.5">비교 분석 문헌수</th>
                      <td className="text-dark py-1.5">: {currentDisplayResult?.papers?.length || 0} 편</td>
                    </tr>
                    <tr>
                      <th className="text-secondary fw-semibold py-1.5">보고서 생성일</th>
                      <td className="text-dark py-1.5">: {new Date().toLocaleDateString()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="mt-5 pt-4">
              <h5 className="fw-bold text-dark mb-3 border-bottom pb-2" style={{ fontSize: "13pt" }}>
                <i className="bi bi-bookmark-star-fill text-primary me-2"></i>
                1. 종합 요약 (Executive Summary)
              </h5>
              <p className="text-secondary mb-4" style={{ fontSize: "10pt", lineHeight: "1.6" }}>
                본 보고서는 학술 연구 공백 분석기(Research Gap Analyzer)를 통해 검색된 핵심 문헌군의 학술 사양 및 스펙 매트릭스를 대조하여 추출된 공식 결과 보고서입니다. 검색어 &apos;{isTutorialActive && !gapState.result ? "Transformers and Self-Attention" : (gapState.query || "N/A")}&apos;를 관통하는 연구 방법론들과 각각의 한계점을 정밀 진단하여 학계 공통의 공백 영역을 체계화했습니다.
              </p>
              
              <h6 className="fw-bold text-dark mb-2.5" style={{ fontSize: "10.5pt" }}>■ 주요 공동 연구 공백 (Common Research Gaps)</h6>
              <div className="p-3 rounded-3" style={{ border: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}>
                <ul className="list-unstyled m-0">
                  {currentDisplayResult?.common_limitations?.map((limit, idx) => (
                    <li key={idx} className="mb-2 last-mb-0 d-flex align-items-start text-secondary" style={{ fontSize: "9.5pt", lineHeight: "1.4" }}>
                      <i className="bi bi-exclamation-circle-fill text-warning me-2 flex-shrink-0" style={{ marginTop: "2px" }}></i>
                      <span>{limit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* PAGE 2: Literature Spec Matrix (Formatted as cleaner Cards per paper for neat printing) */}
          <div className={styles.printPage} style={{ pageBreakAfter: "always" }}>
            <h5 className="fw-bold text-dark mb-4 border-bottom pb-2" style={{ fontSize: "13pt" }}>
              <i className="bi bi-grid-3x3-gap-fill text-primary me-2"></i>
              2. 수집 문헌 개별 스펙 매트릭스 상세 (Detailed Literature Spec Matrix)
            </h5>
            
            {currentDisplayResult?.papers?.map((paper, idx) => (
              <div key={idx} className="mb-4 pb-3" style={{ pageBreakInside: "auto", borderBottom: "1px solid #cbd5e1" }}>
                <div className="d-flex justify-content-between align-items-start mb-2" style={{ pageBreakInside: "avoid" }}>
                  <h6 className="fw-bold text-dark m-0" style={{ fontSize: "11.5pt", lineHeight: "1.4" }}>
                    [{idx + 1}] {paper.title}
                  </h6>
                  <span className="badge bg-light text-secondary border px-2 py-1 flex-shrink-0" style={{ fontSize: "8pt" }}>
                    유사도 {paper.similarity !== undefined ? Math.round(paper.similarity * 100) + '%' : 'N/A'}
                  </span>
                </div>
                <div className="text-muted mb-3" style={{ fontSize: "8.2pt", pageBreakInside: "avoid" }}>
                  ArXiv ID: <a href={`https://arxiv.org/abs/${paper.arxiv_id}`} target="_blank" rel="noreferrer">https://arxiv.org/abs/{paper.arxiv_id}</a>
                </div>
                
                <div className="row g-3" style={{ pageBreakInside: "avoid" }}>
                  {/* 해결된 문제 */}
                  <div className="col-6">
                    <div className="p-3 rounded-3" style={{ backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0", height: "100%" }}>
                      <div className="fw-bold text-success mb-2" style={{ fontSize: "9pt" }}>
                        <i className="bi bi-check-circle-fill me-1.5"></i> 해결된 문제 & 제안 방법론
                      </div>
                      <ul className="m-0 ps-3 text-secondary" style={{ fontSize: "8.5pt", lineHeight: "1.4" }}>
                        {paper.problems_solved.map((item, i) => {
                          const summary = typeof item === "object" && item !== null ? item.summary : item;
                          return <li key={i} className="mb-1">{summary}</li>;
                        })}
                      </ul>
                    </div>
                  </div>
                  
                  {/* 한계점 */}
                  <div className="col-6">
                    <div className="p-3 rounded-3" style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca", height: "100%" }}>
                      <div className="fw-bold text-danger mb-2" style={{ fontSize: "9pt" }}>
                        <i className="bi bi-exclamation-triangle-fill me-1.5"></i> 식별된 한계점 & 공백
                      </div>
                      <ul className="m-0 ps-3 text-secondary" style={{ fontSize: "8.5pt", lineHeight: "1.4" }}>
                        {paper.limitations.map((item, i) => {
                          const summary = typeof item === "object" && item !== null ? item.summary : item;
                          return <li key={i} className="mb-1">{summary}</li>;
                        })}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* RAG 원문 인용구 매핑 */}
                {paper.problems_solved.concat(paper.limitations).some(item => typeof item === "object" && item?.source_quote) && (
                  <div className="mt-3 p-3 rounded-3" style={{ pageBreakInside: "auto", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0" }}>
                    <div className="fw-bold text-secondary mb-2" style={{ fontSize: "8.2pt", pageBreakInside: "avoid" }}>
                      <i className="bi bi-file-earmark-text-fill me-1.5"></i> 논문 원문 근거 인용구 (Verbatim Source Quotes)
                    </div>
                    {paper.problems_solved.concat(paper.limitations).map((item, i) => {
                      if (typeof item === "object" && item !== null && item.source_quote) {
                        return (
                          <div key={i} className="mb-2 last-mb-0 border-start ps-3 py-1" style={{ pageBreakInside: "avoid", borderLeftWidth: "2px", borderLeftColor: "#cbd5e1" }}>
                            <div className="text-secondary fw-semibold" style={{ fontSize: "8.2pt" }}>• {item.summary}</div>
                            <div className="text-muted font-monospace" style={{ fontSize: "8.2pt", fontStyle: "italic", whiteSpace: "pre-wrap" }}>
                              &ldquo;{item.source_quote}&rdquo;
                            </div>
                          </div>
                        );
                      }
                      return null;
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* PAGE 3: Recommended Roadmap */}
          <div className={styles.printPage}>
            <h5 className="fw-bold text-dark mb-4 border-bottom pb-2" style={{ fontSize: "13pt" }}>
              <i className="bi bi-compass-fill text-success me-2"></i>
              3. AI 미래 연구 로드맵 제안 (Future Research Directions)
            </h5>
            <p className="text-secondary mb-4" style={{ fontSize: "10pt", lineHeight: "1.6" }}>
              식별된 학술 공백 영역을 극복하기 위해 AI 모델이 분석 문헌 매트릭스를 기반으로 추천하는 미래 연구 로드맵 주제 및 구체적 연구 과제입니다.
            </p>

            {currentDisplayResult?.suggested_directions?.map((dir, idx) => {
              const match = dir.match(/[:：]|\s+-\s+|\s+–\s+|\s+—\s+/);
              let title = `추천 연구 주제 #${idx + 1}`;
              let description = dir;
              if (match) {
                const index = match.index;
                title = dir.substring(0, index).trim();
                description = dir.substring(index + match[0].length).trim();
              }
              return (
                <div key={idx} className="card p-3 mb-3 rounded-3 border-start" style={{ pageBreakInside: "avoid", borderLeft: "4px solid #198754", backgroundColor: "#f8fafc" }}>
                  <h6 className="fw-bold text-success mb-1.5" style={{ fontSize: "10.5pt" }}>{title}</h6>
                  <p className="m-0 text-secondary" style={{ fontSize: "9pt", lineHeight: "1.4" }}>{description}</p>
                </div>
              );
            })}
          </div>
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

