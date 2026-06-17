"use client"

import styles from "./ControlPanel.module.css";

/**
 * 대규모 문헌 비교 분석기의 제어판 서브 컴포넌트입니다.
 * 
 * - 비교 도메인 선택 및 분석 키워드 입력을 지원합니다.
 * - 현재 비동기 작업의 진행도와 상태를 직관적인 배지 및 프로그레스 바로 표현합니다.
 */
export default function ControlPanel({
  domain,
  setDomain,
  query,
  setQuery,
  loading,
  onSubmit,
  status,
  progress,
  statusText,
  taskId,
  error,
  papersCount
}) {
  return (
    <div className={`${styles.controlPanel} mb-4`}>
      <form onSubmit={onSubmit}>
        <div className="row align-items-center g-3">
          <div className="col-md-3">
            <label className="form-label text-muted small fw-bold mb-1">비교 도메인 카테고리</label>
            <select
              className={styles.devInput}
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              disabled={loading}
            >
              <option value="cs">컴퓨터 과학 (Computer Science)</option>
              <option value="bio">생명공학 (Biotechnology)</option>
              <option value="astronomy">천문학 (Astronomy)</option>
            </select>
          </div>
          <div className="col-md-6">
            <label className="form-label text-muted small fw-bold mb-1">분석 중점 영역 (Focus Area)</label>
            <input
              type="text"
              className={styles.devInput}
              placeholder="예: '임베딩 차원에 따른 RAG 성능 공백 분석'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="col-md-3">
            <label className="form-label text-muted small fw-bold mb-1" style={{ visibility: "hidden" }}>Spacer</label>
            <button
              type="submit"
              className={`${styles.devBtn} w-100`}
              disabled={loading || !query.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  분석 진행 중...
                </>
              ) : (
                <>
                  <i className="bi bi-play-circle-fill me-1"></i> 비동기 배치 분석 실행
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Active Task Status Row */}
      <div className="d-flex flex-column gap-2 mt-2 pt-2 border-top">
        <div className="d-flex align-items-center gap-3">
          <span className="text-muted small">작업 상태:</span>
          {loading ? (
            <span className={`${styles.statusBadge} ${styles.running}`}>
              <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
              <span>RUNNING</span>
            </span>
          ) : status === "COMPLETED" ? (
            <span className={`${styles.statusBadge} ${styles.success}`}>
              <i className="bi bi-check-circle-fill me-1"></i> SUCCESS
            </span>
          ) : status === "FAILED" ? (
            <span className={`${styles.statusBadge} ${styles.failed}`}>
              <i className="bi bi-exclamation-triangle-fill me-1"></i> FAILED
            </span>
          ) : (
            <span className={`${styles.statusBadge} ${styles.idle}`}>
              <i className="bi bi-dash-circle-fill me-1"></i> IDLE
            </span>
          )}
          
          <span className={styles.monoBadge}>
            Task ID: {taskId || "none"}
          </span>

          {status === "COMPLETED" && papersCount !== undefined ? (
            <span className="text-muted small ms-auto">
              분석 완료 논문 수: <strong>{papersCount}편</strong>
            </span>
          ) : (
            <span className="text-muted small ms-auto">
              분석 완료 논문 수: <strong>-</strong>
            </span>
          )}
        </div>

        {/* Dynamic Progress Bar */}
        {loading && (
          <div className="mt-1">
            <div className="d-flex justify-content-between mb-1">
              <span className={`${styles.accentText} fw-semibold small`}>{statusText}</span>
              <span className="text-secondary fw-semibold small">{progress}%</span>
            </div>
            <div className={styles.progressBarWrapper}>
              <div className={styles.progressBarFill} style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}

        {/* Error Alert Message */}
        {error && (
          <div className="alert alert-danger mt-2 d-flex align-items-center" role="alert">
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            <div>{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
