"use client"

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";

/**
 * 로그인/회원가입 등 전체화면 페이지와 대시보드 사이드바 레이아웃이 구분될 수 있도록
 * 경로명을 검사하여 Sidebar를 조건부 렌더링하는 레이아웃 래퍼 컴포넌트입니다.
 */
export default function AppLayoutWrapper({ children }) {
  const pathname = usePathname();
  
  // 로그인 및 회원가입 페이지는 사이드바 레이아웃을 제외시킴
  const isAuthPage = pathname === "/login" || pathname === "/join";

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <div className="d-flex min-vh-100 bg-dark text-light" style={{ overflow: "hidden" }}>
      <Sidebar />
      <main className="flex-grow-1 overflow-auto position-relative bg-dark" style={{ height: "100vh" }}>
        {children}
      </main>
    </div>
  );
}
