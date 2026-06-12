"use client"

import { useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";

/**
 * 기능 2(Feature 2) 전용 메인 페이지 컴포넌트입니다.
 * 
 * 물리적 하위 폴더 기반 라우팅(/feature2)으로 동작하며, 
 * 화면 중앙에 'page2 화면입니다' 문구와 로그인 사용자 정보를 표출합니다.
 */
export default function Feature2Page() {
  const { user } = useContext(AuthContext);

  return (
    <div className="d-flex align-items-center justify-content-center h-100 bg-dark text-light">
      <div className="text-center">
        <h2 className="fw-bold text-white mb-2">page2 화면입니다</h2>
        <p className="text-secondary small">현재 로그인 유저: {user || "Guest"}</p>
      </div>
    </div>
  );
}
