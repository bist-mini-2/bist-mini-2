"use client"

import styles from "./PaperPanel.module.css";

/**
 * 기능 1(논문 채팅) 전용 참고 논문 패널입니다.
 *
 * 선택된 AI 답변의 참고 논문 카드(papers)를 오른쪽에 표시합니다.
 * 왼쪽 사이드바와 동일한 톤(--sidebar-bg, --card-border)으로, 열고 닫을 수 있습니다.
 * 논문 데이터는 page.js에서 파싱해 papers prop으로 전달받습니다.
 *
 * @param {boolean} open 패널 열림 여부
 * @param {Array} papers 표시할 논문 카드 목록 ({ arxiv_id, title, summary })
 * @param {() => void} onClose 닫기 콜백
 */
export default function PaperPanel({ open, papers, onClose }) {
  return (
    <aside className={`${styles.paperPanel} ${open ? styles.paperPanelOpen : ""}`}>
      <div className={styles.paperPanelInner}>
        <div className={styles.paperPanelHeader}>
          <span className={styles.paperPanelTitle}>
            <i className="bi bi-journal-text"></i> 참고 논문
            {papers.length > 0 && (
              <span className={styles.paperPanelCount}>{papers.length}</span>
            )}
          </span>
          <button
            className={styles.paperPanelClose}
            onClick={onClose}
            aria-label="패널 닫기"
          >
            <i className="bi bi-x-lg"></i>
          </button>
        </div>

        {papers.length === 0 ? (
          <div className={styles.paperPanelEmpty}>
            <i className="bi bi-journals"></i>
            <p>이 답변에는 참고 논문이 없어요.</p>
          </div>
        ) : (
          <div className={styles.paperPanelList}>
            {papers.map((paper, i) => (
              <a
              key = { i }
                className = { styles.paperCard }
                href = {`https://arxiv.org/abs/${paper.arxiv_id}`}
            target="_blank"
            rel="noopener noreferrer"
              >
            <div className={styles.paperCardHead}>
              <i className={`bi bi-file-earmark-text ${styles.paperCardIcon}`}></i>
              <span className={styles.paperCardTitle}>{paper.title}</span>
              <i className={`bi bi-box-arrow-up-right ${styles.paperCardLink}`}></i>
            </div>
            <span className={styles.paperCardArxiv}>{paper.arxiv_id}</span>
            {paper.summary && (
              <p className={styles.paperCardSummary}>{paper.summary}</p>
            )}
          </a>
        ))}
      </div>
        )}
    </div>
    </aside >
  );
}