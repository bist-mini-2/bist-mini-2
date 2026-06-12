"use client"

import { useState, useContext } from "react";
import Link from "next/link";
import axios from "axios";
import { AuthContext } from "@/contexts/AuthContext";

/**
 * 사용자 로그인을 제공하는 현대적이고 고급스러운 디자인의 다크 모드 인터페이스 페이지입니다.
 * 
 * OAuth2 규격(application/x-www-form-urlencoded)에 맞추어 백엔드 로그인을 수행하고,
 * 발급받은 토큰 정보를 AuthContext 전역 상태에 갱신합니다.
 */
export default function LoginPage() {
  const { setUser, setAccessToken } = useContext(AuthContext);
  const [mid, setMid] = useState("");
  const [mpassword, setMpassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!mid || !mpassword) {
      setErrorMsg("아이디와 비밀번호를 모두 입력해주세요.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg("");

    try {
      // OAuth2PasswordRequestForm 형식에 맞추어 x-www-form-urlencoded 데이터 준비
      const params = new URLSearchParams();
      params.append("username", mid);
      params.append("password", mpassword);

      const response = await axios.post("/auth/login", params, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      // 백엔드가 성공 래퍼 없이 직접 토큰 스키마를 반환하므로 바로 데이터를 추출합니다.
      const data = response.data; // data = { username, access_token, token_type, role }
      
      setUser(data.username);
      setAccessToken(data.access_token);
    } catch (error) {
      console.error("Login failed:", error);
      if (error.response && error.response.data && error.response.data.message) {
        setErrorMsg(error.response.data.message);
      } else {
        setErrorMsg("로그인에 실패했습니다. 아이디나 비밀번호를 확인해주세요.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="d-flex align-items-center justify-content-center min-vh-100 bg-dark text-light p-4">
      <div 
        className="card border-0 rounded-4 shadow-lg p-5" 
        style={{
          width: "100%",
          maxWidth: "420px",
          backgroundColor: "#171717",
          border: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        <div className="card-body p-0">
          {/* 로고 영역 */}
          <div className="text-center mb-5">
            <div 
              className="d-inline-flex align-items-center justify-content-center rounded-circle bg-success text-white mb-3"
              style={{ width: "48px", height: "48px", fontSize: "1.5rem", fontWeight: "800" }}
            >
              P
            </div>
            <h2 className="fw-bold text-white mb-1">Paper Agent</h2>
            <p className="text-muted small">로그인하여 플랫폼을 이용해 보세요.</p>
          </div>

          {/* 에러 메시지 표시 */}
          {errorMsg && (
            <div 
              className="alert alert-danger border-0 rounded-3 text-center mb-4 small py-2" 
              style={{ backgroundColor: "rgba(239, 68, 68, 0.1)", color: "#f87171" }}
            >
              {errorMsg}
            </div>
          )}

          {/* 로그인 폼 */}
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label text-secondary small fw-semibold">아이디</label>
              <input 
                type="text" 
                className="form-control bg-dark border-secondary text-white rounded-3 shadow-none py-2.5" 
                style={{ borderColor: "rgba(255, 255, 255, 0.15) !important" }}
                placeholder="아이디를 입력하세요 (5자 이상)"
                value={mid}
                onChange={(e) => setMid(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
            
            <div className="mb-4">
              <label className="form-label text-secondary small fw-semibold">비밀번호</label>
              <input 
                type="password" 
                className="form-control bg-dark border-secondary text-white rounded-3 shadow-none py-2.5" 
                placeholder="비밀번호를 입력하세요 (5자 이상)"
                value={mpassword}
                onChange={(e) => setMpassword(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-success w-100 rounded-3 py-2.5 fw-bold mb-3 border-0 transition"
              style={{
                backgroundColor: "#10a37f",
                boxShadow: "0 4px 12px rgba(16, 163, 127, 0.2)"
              }}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              ) : (
                "로그인"
              )}
            </button>
          </form>

          {/* 회원가입 리다이렉트 유도 */}
          <div className="text-center mt-4">
            <span className="text-muted small">계정이 없으신가요? </span>
            <Link href="/join" className="text-success small fw-semibold text-decoration-none hover-underline">
              회원가입
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
