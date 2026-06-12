"use client"

import { useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import styles from "./page.module.css";

/**
 * 기능 2(Feature 2) 전용 메인 페이지 컴포넌트입니다.
 * 
 * 물리적 하위 폴더 기반 라우팅(/feature2)으로 동작하며, 
 * 화면 중앙에 'page2 화면입니다' 문구와 로그인 사용자 정보를 표출합니다.
 */
export default function Feature2Page() {
  const { user } = useContext(AuthContext);

  return (
    <div className={`d-flex align-items-center justify-content-center h-100 ${styles.container}`}>
      <div className={`glass-card p-5 text-center ${styles.card}`}>
        <div className="mono-badge mb-3">
          <i className="bi bi-terminal-fill"></i> console.log("feature_2")
        </div>
        <h2 className="fw-bold mb-3 text-gradient">page2 화면입니다</h2>
        <div className={`p-3 rounded bg-light border ${styles.details}`}>
          <div className="d-flex justify-content-between mb-2">
            <span className="text-muted">status:</span>
            <span className="text-success fw-semibold">ACTIVE</span>
          </div>
          <div className="d-flex justify-content-between">
            <span className="text-muted">current_user:</span>
            <span className="fw-semibold text-dark">{user || "Guest"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
