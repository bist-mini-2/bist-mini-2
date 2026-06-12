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
    <div className="d-flex min-vh-100 text-dark" style={{ overflow: "hidden", backgroundColor: "#ffffff" }}>
      <Sidebar />
      <main 
        className="flex-grow-1 overflow-auto position-relative" 
        style={{ 
          height: "100vh",
          backgroundColor: "#f9f9fb",
          backgroundImage: "radial-gradient(at 0% 0%, rgba(16, 163, 127, 0.05) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.03) 0px, transparent 50%)"
        }}
      >
        {/* Ambient Light 번짐 광원 효과 */}
        <div 
          className="position-absolute" 
          style={{
            width: "400px",
            height: "400px",
            top: "10%",
            left: "10%",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(16, 163, 127, 0.035) 0%, rgba(16, 163, 127, 0) 70%)",
            filter: "blur(60px)",
            pointerEvents: "none",
            zIndex: 0
          }}
        ></div>
        
        <div className="position-relative h-100" style={{ zIndex: 1 }}>
          {children}
        </div>
      </main>
    </div>
  );
}
