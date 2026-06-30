"use client"

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import styles from "./Sidebar.module.css";

/**
 * 기능 4 (Peer Review & Defense Arena) 전용 서브 사이드바 컴포넌트입니다.
 */
export default function Feature4Sidebar({ isCollapsed }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  
  if (isCollapsed) return null;

  const sessionId = searchParams.get("sessionId");

  const subMenus = [
    { name: "새 디펜스 실행", path: "/feature4/arena", icon: "bi-plus-circle" },
    { name: "디펜스 세션 보관함", path: "/feature4", icon: "bi-clock-history" }
  ];

  return (
    <div className={styles.menuSection} style={{ marginTop: "0" }}>
      <ul className={styles.menuList}>
        {subMenus.map((menu) => {
          const isActive = menu.path === "/feature4/arena"
            ? (pathname === "/feature4/arena" && !sessionId)
            : (pathname === "/feature4" || (pathname === "/feature4/arena" && sessionId));
            
          return (
            <li key={menu.path}>
              <Link
                href={menu.path}
                className={`${styles.menuItem} ${isActive ? styles.menuItemActive : ""}`}
              >
                <i className={`bi ${menu.icon} ${styles.menuIcon}`}></i>
                <span className={styles.menuText}>{menu.name}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
