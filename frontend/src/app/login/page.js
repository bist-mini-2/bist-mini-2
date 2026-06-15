"use client"

import { useState, useContext } from "react";
import Link from "next/link";
import authApi from "@/apis/authApi";
import { AuthContext } from "@/contexts/AuthContext";
import styles from "./page.module.css";

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
      // API 모듈을 호출하여 인증을 수행합니다.
      const data = await authApi.login(mid, mpassword);
      
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
    <div className={styles.container}>
      {/* 좌측 로그인 폼 섹션 */}
      <div className={styles.formSection}>
        <div className={`card border-0 p-5 ${styles.card}`}>
          <div className="card-body p-0">
            {/* 로고 영역 */}
            <div className="text-center mb-5">
              <div className={styles.logoIcon}>
                P
              </div>
              <h2 className="fw-bold text-dark mb-1 text-gradient">Paper Agent</h2>
              <p className="text-muted small">로그인하여 플랫폼을 이용해 보세요.</p>
            </div>

            {/* 에러 메시지 표시 */}
            {errorMsg && (
              <div className={`alert text-center mb-4 small py-2 ${styles.errorAlert}`}>
                {errorMsg}
              </div>
            )}

            {/* 로그인 폼 */}
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label text-muted small fw-semibold">아이디</label>
                <input 
                  type="text" 
                  className={`form-control shadow-none py-2.5 ${styles.formInput}`} 
                  placeholder="아이디를 입력하세요 (5자 이상)"
                  value={mid}
                  onChange={(e) => setMid(e.target.value)}
                  disabled={isSubmitting}
                />
              </div>
              
              <div className="mb-4">
                <label className="form-label text-muted small fw-semibold">비밀번호</label>
                <input 
                  type="password" 
                  className={`form-control shadow-none py-2.5 ${styles.formInput}`} 
                  placeholder="비밀번호를 입력하세요 (5자 이상)"
                  value={mpassword}
                  onChange={(e) => setMpassword(e.target.value)}
                  disabled={isSubmitting}
                />
              </div>

              <button 
                type="submit" 
                className={`btn w-100 py-2.5 fw-bold mb-3 transition ${styles.submitBtn}`}
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
              <Link href="/join" className={`small fw-semibold text-decoration-none hover-underline ${styles.redirectLink}`}>
                회원가입
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* 우측 비주얼 장식 섹션 */}
      <div className={styles.visualSection}>
        {/* 흐르는 유기적 블롭 그래픽 */}
        <div className={styles.blob1}></div>
        <div className={styles.blob2}></div>
        <div className={styles.blob3}></div>
        
        {/* 비주얼 브랜딩 메시지 */}
        <div className={styles.visualContent}>
          <div className={styles.badge}>
            <i className="bi bi-stars me-2"></i>Next-Gen AI Workspace
          </div>
          <h1 className={styles.visualTitle}>
            Academic Research, <br/>
            <span className="text-gradient-accent">Reimagined.</span>
          </h1>
          <p className={styles.visualSubtitle}>
            Accelerate your literature reviews, organize your citations, and synthesize scientific insights with a modern, beautiful, AI-powered academic workspace.
          </p>
        </div>
      </div>
    </div>
  );
}
