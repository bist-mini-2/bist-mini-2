"use client"

import styles from "./ResearchGapSynthesis.module.css";

/**
 * 대규모 문헌 비교 분석기의 AI Synthesis 및 추천 연구주제 제안 컴포넌트입니다.
 * 
 * - 분석을 바탕으로 분야별 공통 한계점 목록을 정리하여 보여줍니다.
 * - 한계점을 극복하기 위한 미래 연구 로드맵 주제 카드를 파싱하여 렌더링합니다.
 */
export default function ResearchGapSynthesis({ result }) {
  const { common_limitations = [], suggested_directions = [] } = result || {};

  return (
    <div className="card shadow-sm p-4 border border-light-subtle h-100 d-flex flex-column">
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h5 className="fw-bold text-gradient mb-0">AI Research Gap 분석</h5>
        <span className={styles.monoBadge}>
          <i className={`bi bi-lightbulb-fill me-1 ${styles.iconWarning}`}></i> Synthesis
        </span>
      </div>

      {result ? (
        <div key={common_limitations?.[0] || 'synthesis'} className={`d-flex flex-column gap-3 ${styles.fadeIn}`}>
          {/* Synthesis Gaps list */}
          <div>
            {/* <h6 className="fw-bold text-dark mb-2">추출된 문헌 연구 공백</h6> */}
            <div className="text-secondary small">
              {/* <p className="mb-2">분석된 문헌군 전반에서 다음과 같은 공통적인 연구 한계 및 학계 공백이 추출되었습니다:</p> */}
              <ul className={`${styles.listUnstyled} mb-0`}>
                {common_limitations.map((limit, idx) => (
                  <li key={idx} className="mb-2 d-flex align-items-start">
                    <i className={`bi bi-exclamation-circle-fill me-2 flex-shrink-0 ${styles.listIcon} ${styles.iconWarning}`}></i>
                    <span>{limit}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Recommended Topics list */}
          <div>
            <h6 className="fw-bold text-dark mb-2">추천 연구 주제 제안 (Recommended)</h6>
            {suggested_directions.map((dir, idx) => {
              // Parse direction text into title and description based on standard separators
              // Avoid splitting on bare hyphens to prevent issues with words like 'real-world'
              const match = dir.match(/[:：]|\s+-\s+|\s+–\s+|\s+—\s+/);
              let title = `추천 연구 주제 #${idx + 1}`;
              let description = dir;
              if (match) {
                const index = match.index;
                title = dir.substring(0, index).trim();
                description = dir.substring(index + match[0].length).trim();
              }
              return (
                <div key={idx} className={styles.recommendedTopicCard}>
                  <div className={`fw-bold small mb-1 ${styles.recommendedTopicTitle}`}>{title}</div>
                  <p className={`small mb-0 ${styles.recommendedTopicDescription}`}>{description}</p>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="d-flex flex-column flex-grow-1 justify-content-center align-items-center text-center text-muted py-5">
          <i className="bi bi-cpu fs-2 mb-3 text-secondary"></i>
          <p className="mb-2 fw-bold text-dark fs-5">AI 분석 결과가 아직 없습니다.</p>
          <div className="d-flex align-items-center justify-content-center px-3">
            <p className="small mb-0 text-secondary" style={{ maxWidth: "560px", lineHeight: "1.5" }}>
              비교 문헌 분석이 완료되면 이 영역에 공통 한계점 및 미래 연구 주제 제안서가 합성되어 출력됩니다.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
