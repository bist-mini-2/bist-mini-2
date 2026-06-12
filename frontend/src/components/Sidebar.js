"use client"

import { useContext } from "react";
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
export default function Sidebar() {
  const { user, setUser, setAccessToken } = useContext(AuthContext);
  const pathname = usePathname();
  const router = useRouter();

  // 로그아웃 수행 함수
  const handleLogout = () => {
    setUser("");
    setAccessToken("");
    router.push("/login");
  };

  // 새 대화 시작 액션
  const handleNewChat = () => {
    alert("새 대화를 생성합니다. (POST /chat-with-system)");
  };

  // 네비게이션 메뉴 정의
  const menus = [
    { name: "Chat Hub", path: "/", icon: "💬" },
    { name: "Library & Reports", path: "/library", icon: "📚" },
    { name: "Secure Sandbox", path: "/sandbox", icon: "🛡️" },
    { name: "Peer Review Workshop", path: "/peer-review", icon: "🎓" }
  ];

  return (
    <aside className={styles.sidebar}>
      {/* 상단 로고 그룹 */}
      <div className="d-flex flex-column gap-3">
        <div className={styles.logoGroup}>
          <div className={styles.logoCircle}>P</div>
          <span>Paper Agent</span>
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
                    className={`${styles.menuItem} ${isActive ? styles.menuItemActive : ""}`}
                  >
                    <span>{menu.icon}</span>
                    <span>{menu.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* 액션 버튼 영역 */}
        <div className={styles.actionsSection}>
          <button className={styles.actionBtn} onClick={handleNewChat}>
            <span>➕</span>
            <span>New Conversation</span>
          </button>
        </div>

        {/* 히스토리 리스트 (임시 더미 데이터) */}
        <div className={styles.historySection}>
          <div className={styles.historyGroupTitle}>Today</div>
          <ul className={styles.historyList}>
            <li className={styles.historyItem} onClick={() => alert("해당 히스토리로 이동합니다.")}>
              LLM RAG 성능 최적화 논문 비교
            </li>
          </ul>

          <div className={styles.historyGroupTitle} style={{ marginTop: "16px" }}>Yesterday</div>
          <ul className={styles.historyList}>
            <li className={styles.historyItem} onClick={() => alert("해당 히스토리로 이동합니다.")}>
              COVID-19 백신 면역 작용 조사
            </li>
            <li className={styles.historyItem} onClick={() => alert("해당 히스토리로 이동합니다.")}>
              양자 역학적 가설 타당성 검토
            </li>
          </ul>
        </div>
      </div>

      {/* 하단 사용자 정보 및 세션 영역 */}
      <div className={styles.bottomSection}>
        <div className={styles.profileCard}>
          <div className={styles.profileAvatar}>
            {user ? user.substring(0, 2).toUpperCase() : "U"}
          </div>
          <div className={styles.profileInfo}>
            <span className={styles.profileName}>{user || "Guest"}</span>
            <span className={styles.profileRole}>ROLE_USER</span>
          </div>
        </div>
        <button className={styles.logoutBtn} onClick={handleLogout}>
          <span>🔑</span>
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
