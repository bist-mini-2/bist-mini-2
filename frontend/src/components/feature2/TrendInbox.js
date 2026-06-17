"use client"

import styles from "./TrendInbox.module.css";

/**
 * 대규모 문헌 비교 분석기의 실시간 알림 센터 (Trend Inbox) 컴포넌트입니다.
 * 
 * - 백엔드 비동기 태스크들의 진행 및 완료 상황을 실시간 SSE 이벤트를 통해 수신하고 표출합니다.
 */
export default function TrendInbox({ notifications = [] }) {
  return (
    <div className="card shadow-sm p-4 bg-white border border-light-subtle">
      <h5 className="fw-bold mb-3 d-flex justify-content-between align-items-center">
        <span>
          <i className="bi bi-bell-fill text-warning me-2"></i>실시간 알림 센터
        </span>
        <span className="badge bg-danger rounded-pill">LIVE</span>
      </h5>
      <p className="text-muted small mb-3">
        서버의 백그라운드 태스크에서 발행된 완료 내역이 실시간 SSE 푸시 이벤트로 갱신됩니다.
      </p>
      <div className={styles.inboxContainer}>
        {notifications.length === 0 ? (
          <div className="text-center text-muted py-5">
            <i className="bi bi-cloud-slash-fill fs-2 mb-2 d-block"></i>
            수신된 실시간 완료 알림이 없습니다.
          </div>
        ) : (
          notifications.map((notif, idx) => (
            <div key={idx} className={styles.inboxItem}>
              <div className="d-flex justify-content-between mb-1">
                <span className={`badge ${notif.domain === "cs" ? styles.badgeCs : styles.badgeBio} rounded-pill`}>
                  {notif.domain?.toUpperCase()}
                </span>
                <span className="text-muted small">
                  <i className="bi bi-clock me-1"></i>{" "}
                  {notif.status === "COMPLETED" ? "완료" : "실패"}
                </span>
              </div>
              <div className="fw-bold mb-1 text-dark small">{notif.query}</div>
              <div className="text-secondary small">
                {notif.status === "COMPLETED" ? (
                  <span className="text-success">
                    <i className="bi bi-check-circle-fill me-1"></i> 분석이 최종 종료되었습니다.
                  </span>
                ) : (
                  <span className="text-danger">
                    <i className="bi bi-x-circle-fill me-1"></i> {notif.error_message || "오류 발생"}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
