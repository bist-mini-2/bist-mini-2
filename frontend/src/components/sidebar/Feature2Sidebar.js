"use client"

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import styles from "./Sidebar.module.css";

/**
 * 기능 2 (Research Gap Analyzer) 전용 서브 사이드바 컴포넌트입니다.
 */
export default function Feature2Sidebar({ isCollapsed }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  
  if (isCollapsed) return null;

  const taskId = searchParams.get("taskId");

  const subMenus = [
    { name: "새 분석 실행", path: "/feature2/analyze", icon: "bi-plus-circle" },
    { name: "분석 보고서 이력", path: "/feature2", icon: "bi-clock-history" }
  ];

  return (
    <div className={styles.menuSection} style={{ marginTop: "0" }}>
      <ul className={styles.menuList}>
        {subMenus.map((menu) => {
          const isActive = menu.path === "/feature2/analyze"
            ? (pathname === "/feature2/analyze" && !taskId)
            : (pathname === "/feature2" || (pathname === "/feature2/analyze" && taskId));
            
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

