"use client"

import { useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";

/**
 * Chat Hub 메인 대화 포털 인터페이스 페이지입니다.
 * 
 * 와이어프레임(user-main-chat.html)의 스타일 가이드를 적용하여 구축되었으며,
 * 기능 요구사항에 맞게 내부의 연산 및 통신 로직은 비워둔 스켈레톤 디자인만 제공합니다.
 */
export default function ChatHubPage() {
  const { user } = useContext(AuthContext);

  return (
    <div className="d-flex flex-column h-100 bg-dark text-light">
      {/* 상단 헤더 영역 */}
      <header 
        className="d-flex align-items-center justify-content-between px-4" 
        style={{ height: "56px", borderBottom: "1px solid #2f2f2f" }}
      >
        <div className="fw-bold d-flex align-items-center gap-2">
          <span>Paper Agent GPT-4o</span>
          <span style={{ fontSize: "0.75rem", color: "#b4b4b4" }}>▼</span>
        </div>
        <div>
          <button 
            className="btn btn-outline-secondary btn-sm rounded-pill px-3"
            style={{ fontSize: "0.8rem", color: "#ececec", borderColor: "#2f2f2f" }}
            onClick={() => alert("설정 콘솔을 엽니다.")}
          >
            ⚙️ Settings
          </button>
        </div>
      </header>

      {/* 바디 영역 - 대화 내용 웰컴화면 및 입력 창 */}
      <div className="flex-grow-1 d-flex flex-column align-items-center justify-content-between p-4" style={{ overflowY: "auto" }}>
        
        {/* 중앙 웰컴 메시지 */}
        <div className="text-center my-auto p-4" style={{ maxWidth: "580px" }}>
          <div 
            className="d-inline-flex align-items-center justify-content-center rounded-circle bg-success text-white mb-4"
            style={{ width: "64px", height: "64px", fontSize: "2rem", fontWeight: "800" }}
          >
            P
          </div>
          <h2 className="fw-bold text-white mb-3">무엇을 도와드릴까요, {user || "사용자"}님?</h2>
          <p className="text-muted leading-relaxed">
            논문 AI 에이전트를 통해 의학/바이오, 컴퓨터 과학, 자연 과학 등 다양한 학술 도메인의 논문을 검색하고 분석해 보세요.
          </p>
        </div>

        {/* 하단 입력 상자 레이아웃 */}
        <div className="w-100" style={{ maxWidth: "768px" }}>
          <div 
            className="p-3 rounded-4" 
            style={{
              backgroundColor: "#2f2f2f",
              border: "1px solid #3f3f3f",
              boxShadow: "0 4px 16px rgba(0, 0, 0, 0.25)"
            }}
          >
            {/* 텍스트 입력 영역 */}
            <textarea 
              className="form-control bg-transparent border-0 text-white shadow-none p-0" 
              rows={2}
              placeholder="Paper Agent에게 논문 검색 및 분석을 요청해보세요..."
              style={{ resize: "none", fontSize: "0.95rem" }}
              disabled
            />

            {/* 컨트롤 바 */}
            <div className="d-flex align-items-center justify-content-between mt-3 pt-2" style={{ borderTop: "1px solid #3f3f3f" }}>
              <div className="d-flex gap-2">
                <button className="btn btn-dark btn-sm rounded-pill px-3 text-secondary" style={{ backgroundColor: "#212121", border: "1px solid #3f3f3f" }} disabled>
                  🔍 Web Search
                </button>
                <button className="btn btn-dark btn-sm rounded-pill px-3 text-secondary" style={{ backgroundColor: "#212121", border: "1px solid #3f3f3f" }} disabled>
                  📁 Attach File
                </button>
              </div>
              <button 
                className="btn btn-secondary rounded-circle d-flex align-items-center justify-content-center p-0" 
                style={{ width: "32px", height: "32px" }}
                disabled
              >
                ▲
              </button>
            </div>
          </div>
          <p className="text-center text-secondary small mt-3" style={{ fontSize: "0.75rem" }}>
            Paper Agent는 실시간 논문 탐색 결과를 제공하며 실수를 할 수 있습니다. 중요한 정보는 확인해 주세요.
          </p>
        </div>

      </div>
    </div>
  );
}
