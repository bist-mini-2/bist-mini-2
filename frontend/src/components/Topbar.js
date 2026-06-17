"use client"

import { useContext } from "react";
import { usePathname } from "next/navigation";
import { ThemeContext } from "@/contexts/ThemeContext";
import NotificationCenter from "./notification/NotificationCenter";
import styles from "./Topbar.module.css";

/**
 * 애플리케이션 우측 메인 캔버스 상단에 배치되는 고정 네비게이션 헤더 바(Topbar)입니다.
 * 현재 활성화된 기능의 명칭(브레드크럼)과 시스템 연동 상태 및 테마 전환 기능, 알림 센터 컴포넌트를 렌더링합니다.
 */
export default function Topbar() {
  const pathname = usePathname();
  const { theme, toggleTheme } = useContext(ThemeContext);

  // 경로명에 대응되는 메뉴 타이틀 맵
  const getPageTitle = (path) => {
    switch (path) {
      case "/feature1":
        return "기능 1 (Feature 1)";
      case "/feature2":
        return "기능 2 (Feature 2)";
      case "/feature3":
        return "기능 3 (Feature 3)";
      default:
        return "Dashboard";
    }
  };

  return (
    <header className={styles.topbar}>
      {/* 좌측 브레드크럼 위치 정보 */}
      <div className={styles.leftSection}>
        <span className={styles.breadcrumbParent}>Paper Agent</span>
        <span className={styles.breadcrumbSeparator}>/</span>
        <span className={styles.breadcrumbCurrent}>{getPageTitle(pathname)}</span>
      </div>

      {/* 우측 유저 세션 정보 및 상태 표시 */}
      <div className={styles.rightSection}>
        <div className={styles.statusIndicator}>
          <span className={styles.statusDot}></span>
          <span>System: Active</span>
        </div>

        {/* 테마 전환 토글 버튼 */}
        <button
          className={styles.iconButton}
          onClick={toggleTheme}
          title={theme === "light" ? "다크 모드로 전환" : "라이트 모드로 전환"}
          aria-label="Toggle Theme"
        >
          <i className={`bi ${theme === "light" ? "bi-moon-stars" : "bi-sun"}`}></i>
        </button>

        {/* 도움말 단축 버튼 */}
        <button className={styles.iconButton} title="Help & Documentation">
          <i className="bi bi-question-circle"></i>
        </button>

        {/* 알림 센터 모듈 컴포넌트 */}
        <NotificationCenter />
      </div>
    </header>
  );
}
