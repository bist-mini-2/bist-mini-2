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
    <div className="d-flex min-vh-100" style={{ overflow: "hidden", backgroundColor: "var(--background)", color: "var(--foreground)" }}>
      <Sidebar />
      <main 
        className="flex-grow-1 overflow-auto position-relative" 
        style={{ 
          height: "100vh",
          backgroundColor: "var(--background)",
          backgroundImage: "radial-gradient(var(--tertiary-color) 1px, transparent 1px)",
          backgroundSize: "20px 20px",
          backgroundPosition: "0 0"
        }}
      >
        {/* Ambient Light 번짐 광원 효과 */}
        <div 
          className="position-absolute" 
          style={{
            width: "600px",
            height: "600px",
            top: "-100px",
            left: "-100px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(120, 149, 178, 0.08) 0%, rgba(120, 149, 178, 0) 70%)",
            filter: "blur(80px)",
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
