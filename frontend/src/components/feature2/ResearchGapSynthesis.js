"use client"

import styles from "./ResearchGapSynthesis.module.css";

/**
 * 대규모 문헌 비교 분석기의 AI Synthesis 및 추천 연구주제 제안 컴포넌트입니다.
 * 
 * - 분석을 바탕으로 분야별 공통 한계점 목록을 정리하여 보여줍니다.
 * - 한계점을 극복하기 위한 미래 연구 로드맵 주제 카드를 파싱하여 렌더링합니다.
 */
export default function ResearchGapSynthesis({ result }) {
  if (!result) return null;

  const { common_limitations = [], suggested_directions = [] } = result;

  return (
    <div className="card shadow-sm p-4 d-flex flex-column gap-3 bg-white border border-light-subtle">
      <div className="d-flex align-items-center justify-content-between mb-2">
        <h5 className="fw-bold text-gradient mb-0">AI Research Gap 분석</h5>
        <span className={styles.monoBadge}>
          <i className="bi bi-lightbulb-fill text-warning me-1"></i> Synthesis
        </span>
      </div>

      {/* Synthesis Gaps list */}
      <div>
        <h6 className="fw-bold text-dark mb-2">추출된 문헌 연구 공백</h6>
        <div className="text-secondary small">
          <p className="mb-2">분석된 문헌군 전반에서 다음과 같은 공통적인 연구 한계 및 학계 공백이 추출되었습니다:</p>
          <ul className={`${styles.listUnstyled} mb-0`}>
            {common_limitations.map((limit, idx) => (
              <li key={idx} className="mb-2 d-flex align-items-start">
                <i className={`bi bi-exclamation-circle-fill text-warning me-2 mt-1 flex-shrink-0 ${styles.listIcon}`}></i>
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
          const parts = dir.split(/[:：\-]/);
          let title = `추천 연구 주제 #${idx + 1}`;
          let description = dir;
          if (parts.length > 1) {
            title = parts[0].trim();
            description = parts.slice(1).join("-").trim();
          }
          return (
            <div key={idx} className={styles.recommendedTopicCard}>
              <div className="fw-bold small mb-1">{title}</div>
              <p className="text-secondary small mb-0">{description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
