"use client"

import styles from "@/app/feature2/analyze/page.module.css";

/**
 * PDF 및 프린트 전용 보고서 화면을 출력하기 위한 서브 컴포넌트입니다.
 * 화면에는 표시되지 않으며 (d-none), 브라우저 인쇄 모드(d-print-block)에서만 활성화됩니다.
 * 
 * @param {object} result             - 분석 결과물 객체 (papers, common_limitations, suggested_directions)
 * @param {string} domain             - 학술 도메인 ("cs" | "bio" | "astronomy")
 * @param {string} query              - 분석 질의어
 * @param {boolean} isTutorialActive  - 튜토리얼 활성화 여부 (가데이터 구분용)
 */
export default function PrintReport({ result, domain, query, isTutorialActive }) {
  if (!result) return null;

  return (
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
                  <td className="text-dark py-1.5">: {isTutorialActive ? "CS" : (domain ? domain.toUpperCase() : "N/A")}</td>
                </tr>
                <tr>
                  <th className="text-secondary fw-semibold py-1.5">분석 관심 키워드</th>
                  <td className="text-dark py-1.5">: {isTutorialActive ? "Attention Mechanism in Transformer" : (query || "N/A")}</td>
                </tr>
                <tr>
                  <th className="text-secondary fw-semibold py-1.5">비교 분석 문헌수</th>
                  <td className="text-dark py-1.5">: {result?.papers?.length || 0} 편</td>
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
            본 보고서는 학술 연구 공백 분석기(Research Gap Analyzer)를 통해 검색된 핵심 문헌군의 학술 사양 및 스펙 매트릭스를 대조하여 추출된 공식 결과 보고서입니다. 검색어 &apos;{isTutorialActive ? "Attention Mechanism in Transformer" : (query || "N/A")}&apos;를 관통하는 연구 방법론들과 각각의 한계점을 정밀 진단하여 학계 공통의 공백 영역을 체계화했습니다.
          </p>
          
          <h6 className="fw-bold text-dark mb-2.5" style={{ fontSize: "10.5pt" }}>■ 주요 공동 연구 공백 (Common Research Gaps)</h6>
          <div className="p-3 rounded-3" style={{ border: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}>
            <ul className="list-unstyled m-0">
              {result?.common_limitations?.map((limit, idx) => (
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
        
        {result?.papers?.map((paper, idx) => (
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

        {result?.suggested_directions?.map((dir, idx) => {
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
  );
}
