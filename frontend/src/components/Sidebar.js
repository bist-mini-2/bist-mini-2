"use client"

import { useContext, useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthContext } from "@/contexts/AuthContext";
import styles from "./Sidebar.module.css";

/**
 * 애플리케이션의 핵심 기능을 이동할 수 있도록 지원하는 좌측 사이드 네비게이션 패널입니다.
 * 
 * 와이어프레임(user-main-chat.html)의 스타일링과 요소를 준수하여 제작되었으며,
 * 현재 로그인 사용자 표시 및 로그아웃 기능을 포함합니다.
 */
export default function Sidebar({ isCollapsed, onToggle }) {
  const { user, setUser, setAccessToken } = useContext(AuthContext);
  const pathname = usePathname();
  const router = useRouter();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // 로그아웃 수행 함수
  const handleLogout = () => {
    setUser("");
    setAccessToken("");
    setIsDropdownOpen(false);
    router.push("/login");
  };

  // 드롭다운 외부 클릭 시 자동으로 닫히도록 핸들러 추가
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (isDropdownOpen && !e.target.closest(`.${styles.bottomSection}`)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("click", handleOutsideClick);
    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [isDropdownOpen]);

  // 네비게이션 메뉴 정의
  const menus = [
    { name: "기능 1", path: "/feature1", icon: "bi-gear" },
    { name: "기능 2", path: "/feature2", icon: "bi-tools" },
    { name: "기능 3", path: "/feature3", icon: "bi-bar-chart" }
  ];

  return (
    <aside className={`${styles.sidebar} ${isCollapsed ? styles.sidebarCollapsed : ""}`}>
      {/* 상단 로고 및 토글 버튼 그룹 */}
      <div className="d-flex flex-column gap-3">
        <div className={styles.logoHeader}>
          <div className={styles.logoGroup}>
            <div className={styles.logoCircle}>P</div>
            <span className={styles.logoText}>Paper Agent</span>
          </div>
          <button 
            className={styles.toggleButton} 
            onClick={onToggle} 
            title={isCollapsed ? "사이드바 펼치기" : "사이드바 접기"}
            aria-label="Toggle Sidebar"
          >
            <i className={`bi ${isCollapsed ? "bi-arrow-bar-right" : "bi-arrow-bar-left"}`}></i>
          </button>
        </div>

        {/* 메인 메뉴 영역 */}
        <nav className={styles.menuSection}>
          <ul className={styles.menuList}>
            {menus.map((menu) => {
              const isActive = pathname === menu.path;
              return (
                <li key={menu.path}>
                  <Link
                    href={menu.path}
                    className={`${styles.menuItem} ${isActive ? styles.menuItemActive : ""} ${isCollapsed ? styles.menuItemCollapsed : ""}`}
                  >
                    <i className={`bi ${menu.icon} ${styles.menuIcon}`}></i>
                    <span className={styles.menuText}>{menu.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>

      {/* 하단 사용자 정보 및 세션 영역 */}
      <div className={styles.bottomSection}>
        {isDropdownOpen && (
          <div className={`${styles.dropdownMenu} ${isCollapsed ? styles.dropdownMenuCollapsed : ""}`}>
            {user ? (
              <button className={styles.dropdownItem} onClick={handleLogout}>
                <i className="bi bi-box-arrow-right"></i>
                <span className={styles.dropdownText}>Logout</span>
              </button>
            ) : (
              <Link href="/login" className={styles.dropdownItem} onClick={() => setIsDropdownOpen(false)}>
                <i className="bi bi-box-arrow-in-right"></i>
                <span className={styles.dropdownText}>Login</span>
              </Link>
            )}
          </div>
        )}

        <div className={`${styles.profileCard} ${isCollapsed ? styles.profileCardCollapsed : ""}`} onClick={() => setIsDropdownOpen(!isDropdownOpen)}>
          <div className={styles.profileAvatar}>
            {user ? user.substring(0, 2).toUpperCase() : "G"}
          </div>
          <div className={styles.profileInfo}>
            <span className={styles.profileName}>{user || "Guest"}</span>
            <span className={styles.profileRole}>{user ? "ROLE_USER" : "GUEST"}</span>
          </div>
          <i className={`bi bi-three-dots-vertical ${styles.dotsIcon} ${isCollapsed ? styles.hidden : ""}`}></i>
        </div>
      </div>
    </aside>
  );
}
