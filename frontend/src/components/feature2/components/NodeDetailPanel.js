import React from "react";

/**
 * 마인드맵 캔버스 하단에 배치되어 클릭한 노드(검색어, 논문, 해결과제, 한계점, 공통GAP, 추천 방향)의
 * 상세 분석 보고서 카드를 유연하고 동적으로 보여주는 서브 컴포넌트입니다.
 */
export default function NodeDetailPanel({ selectedNode, styles }) {
  if (!selectedNode) {
    return (
      <div className={`card shadow-sm p-4 border border-light-subtle ${styles.detailPanel}`}>
        <div className={styles.placeholderPanel}>
          <i className="bi bi-info-circle me-2"></i>
          마인드맵의 원형 노드를 클릭하여 해당 부모 노드로 줌인(Camera Focus)하고, 방사형으로 전개되는 상세 분석 정보를 검토해보세요.
        </div>
      </div>
    );
  }

  return (
    <div className={`card shadow-sm p-4 border border-light-subtle ${styles.detailPanel}`}>
      <div className={styles.activePanel}>
        {/* 1. 검색어 노드 상세 */}
        {selectedNode.type === "query" && (
          <div>
            <h4 className={styles.panelTitle}>
              <i className="bi bi-search text-info me-2"></i>
              입력 검색 쿼리 상세
            </h4>
            <div className={styles.panelContentBox}>
              <strong>사용자 질의어:</strong>
              <p className={styles.queryContent}>{selectedNode.data.content}</p>
              <span className={styles.helperText}>
                이 키워드를 3072차원 고밀도 벡터로 임베딩하여 로컬 pgvector 라이브러리에서 최신 관련 논문군을 다차원으로 탐색했습니다.
              </span>
            </div>
          </div>
        )}

        {/* 2. 논문 노드 상세 리포트 */}
        {selectedNode.type.startsWith("paper-") && (
          <div>
            <h4 className={styles.panelTitle}>
              <i className="bi bi-journal-text text-primary me-2"></i>
              {selectedNode.data.title} 상세 분석 리포트
            </h4>
            <p className={styles.paperTitleText}><strong>제목:</strong> {selectedNode.data.title}</p>
            <p className={styles.arxivIdText}><strong>ArXiv ID:</strong> {selectedNode.data.arxiv_id}</p>

            <div className="row mt-3">
              <div className="col-md-6 mb-3">
                <div className={styles.listSection}>
                  <span className={`${styles.badge} ${styles.badgeSolved}`}>
                    <i className="bi bi-check-circle-fill me-1"></i> 해결 문제 및 제안 방법론
                  </span>
                  <ul className={styles.detailList}>
                    {selectedNode.data.problems_solved.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <div className="col-md-6 mb-3">
                <div className={styles.listSection}>
                  <span className={`${styles.badge} ${styles.badgeLimit}`}>
                    <i className="bi bi-slash-circle me-1"></i> 식별된 주요 한계점
                  </span>
                  <ul className={styles.detailList}>
                    {selectedNode.data.limitations.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 3. 해결과제(Solved) 서브노드 상세 */}
        {selectedNode.type.startsWith("solved-") && (
          <div>
            <h4 className={styles.panelTitle}>
              <i className="bi bi-check-circle-fill text-success me-2"></i>
              해결 문제 및 제안 방법론 상세
            </h4>
            <div className={styles.panelContentBox}>
              <p className="mb-3">선택한 논문이 해결하고자 정의한 핵심 기술적 기여입니다:</p>
              <ul className={styles.gapList}>
                {selectedNode.data.problems_solved.map((item, idx) => (
                  <li key={idx}>
                    <i className="bi bi-check2-circle text-success me-2"></i>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* 4. 한계점(Limitation) 서브노드 상세 */}
        {selectedNode.type.startsWith("limitation-") && (
          <div>
            <h4 className={styles.panelTitle}>
              <i className="bi bi-slash-circle text-danger me-2"></i>
              식별된 주요 한계점 상세
            </h4>
            <div className={styles.panelContentBox}>
              <p className="mb-3">선택한 논문에서 향후 개선이 필요하거나 해결되지 않은 주요 제약점입니다:</p>
              <ul className={styles.gapList}>
                {selectedNode.data.limitations.map((item, idx) => (
                  <li key={idx}>
                    <i className="bi bi-exclamation-circle text-danger me-2"></i>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* 5. 공통 GAP 노드 상세 */}
        {selectedNode.type === "common" && (
          <div>
            <h4 className={styles.panelTitle}>
              <i className="bi bi-exclamation-triangle-fill text-warning me-2"></i>
              식별된 공통 연구 공백 (Common Research Gap)
            </h4>
            <div className={styles.panelContentBox}>
              <p className="mb-3">검색된 후보 연구 논문군을 다차원 종합 분석하여 추출된 핵심 공통 결함 및 향후 극복해야 할 공백 영역입니다:</p>
              <ul className={styles.gapList}>
                {selectedNode.data.items.map((item, idx) => (
                  <li key={idx}>
                    <i className="bi bi-patch-exclamation text-danger me-2"></i>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* 6. 추천 방향(Direction) 노드 상세 */}
        {selectedNode.type.startsWith("direction-") && (
          <div>
            <h4 className={styles.panelTitle}>
              <i className="bi bi-lightbulb-fill text-success me-2"></i>
              추천 연구 주제 및 개발 로드맵 {selectedNode.data.index + 1}
            </h4>
            <div className={styles.panelContentBox}>
              <div className={styles.directionHeader}>
                <strong>제안 로드맵:</strong>
              </div>
              <p className={styles.directionContent}>{selectedNode.data.content}</p>
              <span className={styles.helperText}>
                위 공통 한계점(Research Gap)을 극복하고 논리적인 보완 방안을 결합하여 생성형 AI 에이전트가 제시하는 독창적인 연구 아이디어입니다.
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
