"use client"

import styles from "./MatrixTable.module.css";

/**
 * 대규모 문헌 비교 분석기의 스펙 매트릭스 테이블 컴포넌트입니다.
 * 
 * - 분석 결과가 존재할 경우 논문별 방법론, 해결 문제, 한계점을 표 형태로 시각화합니다.
 * - 결과가 존재하지 않을 때 사용자가 해야 할 작업을 알려주는 카드형 빈 상태(Empty State)를 표출합니다.
 */
export default function MatrixTable({ result }) {
  return (
    <div className="card shadow-sm p-4 border border-light-subtle h-100 d-flex flex-column">
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h5 className="fw-bold text-gradient mb-0">문헌 비교 스펙 매트릭스</h5>
        <span className={styles.monoBadge}>F-01-B-3 구조화 데이터</span>
      </div>

      {result && result.papers && result.papers.length > 0 ? (
        <div className={styles.matrixContainer}>
          <table className={styles.matrixTable}>
            <thead>
              <tr>
                <th className={`${styles.matrixTh} ${styles.colPaper}`}>논문 정보</th>
                <th className={`${styles.matrixTh} ${styles.colProblems}`}>해결된 문제 & 제안 방법론</th>
                <th className={`${styles.matrixTh} ${styles.colLimitations}`}>식별된 한계점 & 공백</th>
              </tr>
            </thead>
            <tbody>
              {result.papers.map((paper, idx) => (
                <tr key={idx}>
                  <td className={`${styles.matrixTd} ${styles.colPaperCell}`}>
                    <div className={styles.paperCellWrapper}>
                      <div className={styles.paperTitle}>{paper.title}</div>
                      <div className={styles.paperMeta}>
                        ArXiv ID: {paper.arxiv_id}
                      </div>
                      <a
                        href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                        target="_blank"
                        rel="noreferrer"
                        className={`${styles.arxivBtn} mt-2`}
                      >
                        <i className="bi bi-link-45deg"></i> ArXiv 이동
                      </a>
                    </div>
                  </td>
                  <td className={styles.matrixTd}>
                    <ul className={styles.listUnstyled}>
                      {paper.problems_solved.map((item, i) => (
                        <li key={i} className="mb-2 d-flex align-items-start">
                          <i className={`bi bi-check-circle-fill text-success me-2 mt-1 flex-shrink-0 ${styles.listIcon}`}></i>
                          <span className="text-secondary small">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </td>
                  <td className={styles.matrixTd}>
                    <ul className={styles.listUnstyled}>
                      {paper.limitations.map((item, i) => (
                        <li key={i} className="mb-2 d-flex align-items-start">
                          <i className={`bi bi-dash-circle-fill text-danger me-2 mt-1 flex-shrink-0 ${styles.listIcon}`}></i>
                          <span className="text-secondary small">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="d-flex flex-column flex-grow-1 justify-content-center align-items-center text-center text-muted py-5">
          <i className="bi bi-grid-3x3-gap-fill fs-2 mb-3 text-secondary"></i>
          <p className="mb-2 fw-bold text-dark fs-5">분석 결과가 아직 없습니다.</p>
          <div className="d-flex align-items-center justify-content-center px-3">
            <p className="small mb-0 text-secondary" style={{ maxWidth: "560px", lineHeight: "1.5" }}>
              상단의 분석 제어판에서 비교 대상 조건 입력 후 '비동기 배치 분석 실행'을 클릭하세요.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
