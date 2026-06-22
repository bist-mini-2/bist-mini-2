"use client"

import styles from "./StatusBadge.module.css";

/**
 * 공통 상태 표시 뱃지 컴포넌트입니다.
 * 
 * - status: "PENDING" | "RUNNING" | "COMPLETED" | "SUCCESS" | "FAILED" | "IDLE"
 * - progress: 진행률 수치 (Optional, RUNNING 상태에서 표시됨)
 * - lang: "ko" | "en" (기본값 "en", 라벨 다국어 매핑용)
 */
export default function StatusBadge({ status, progress, lang = "en" }) {
  const isKo = lang === "ko";
  
  // 1. 상태 노멀라이즈
  const normStatus = (status || "").toUpperCase();
  
  // 2. 상태별 클래스 및 아이콘 매핑
  let badgeClass = styles.idle;
  let icon = null;
  let text = "";
  
  switch (normStatus) {
    case "COMPLETED":
    case "SUCCESS":
      badgeClass = styles.success;
      icon = <i className="bi bi-check-circle-fill"></i>;
      text = isKo ? "분석 완료" : "SUCCESS";
      break;
      
    case "RUNNING":
      badgeClass = styles.running;
      icon = (
        <span
          className={`spinner-border spinner-border-sm ${styles.statusSpinner}`}
          role="status"
          aria-hidden="true"
        ></span>
      );
      text = isKo 
        ? `분석 중${progress !== undefined ? ` (${progress}%)` : ""}` 
        : "RUNNING";
      break;
      
    case "PENDING":
      badgeClass = styles.pending;
      icon = <i className="bi bi-clock"></i>;
      text = isKo ? "대기 중" : "PENDING";
      break;
      
    case "FAILED":
      badgeClass = styles.failed;
      icon = <i className="bi bi-exclamation-triangle-fill"></i>;
      text = isKo ? "분석 실패" : "FAILED";
      break;
      
    case "IDLE":
    default:
      badgeClass = styles.idle;
      icon = <i className="bi bi-dash-circle-fill"></i>;
      text = isKo ? "대기" : "IDLE";
      break;
  }
  
  return (
    <span className={`${styles.statusBadge} ${badgeClass}`}>
      {icon}
      <span>{text}</span>
    </span>
  );
}
