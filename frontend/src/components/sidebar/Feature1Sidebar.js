"use client"

/**
 * 기능 1 전용 사이드바 컴포넌트 (내용 비워둠)
 */
export default function Feature1Sidebar({ isCollapsed }) {
  if (isCollapsed) return null;

  return (
    <div>
      {/* 기능 1 전용 내용 */}
    </div>
  );
}
