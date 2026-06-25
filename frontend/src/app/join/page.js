"use client"

import { useState, useContext } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import memberApi from "@/apis/memberApi";
import authApi from "@/apis/authApi";
import { AuthContext } from "@/contexts/AuthContext";
import styles from "./page.module.css";

/**
 * 신규 회원 가입을 지원하는 다크 모드 폼 인터페이스 페이지입니다.
 * 
 * 사용자로부터 아이디, 이름, 이메일, 비밀번호 정보를 받아
 * JSON 규격으로 백엔드 신규 등록 API(/member/join)를 호출한 후 로그인 화면으로 리다이렉트합니다.
 */
export default function JoinPage() {
  const { setUser, setAccessToken } = useContext(AuthContext);
  const [mid, setMid] = useState("");
  const [mname, setMname] = useState("");
  const [memail, setMemail] = useState("");
  const [mpassword, setMpassword] = useState("");
  
  const [errorMsg, setErrorMsg] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!mid || !mname || !memail || !mpassword) {
      setErrorMsg("모든 필드를 채워주세요.");
      return;
    }

    if (mid.length < 5) {
      setErrorMsg("아이디는 최소 5자 이상이어야 합니다.");
      return;
    }

    if (mname.length < 2) {
      setErrorMsg("이름은 최소 2자 이상이어야 합니다.");
      return;
    }

    if (mpassword.length < 5) {
      setErrorMsg("비밀번호는 최소 5자 이상이어야 합니다.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg("");

    try {
      const joinData = {
        mid,
        mname,
        memail,
        mpassword,
        menabled: true,
        mrole: "ROLE_USER"
      };

      await memberApi.join(joinData);

      // 회원가입 완료 후 바로 로그인 실행
      try {
        const loginData = await authApi.login(mid, mpassword);
        setUser(loginData.username);
        setAccessToken(loginData.access_token);
        router.push("/");
      } catch (loginErr) {
        console.error("Auto login failed after registration:", loginErr);
        router.push("/login");
      }
    } catch (error) {
      console.error("Join failed:", error);
      if (error.response && error.response.data && error.response.data.message) {
        setErrorMsg(error.response.data.message);
      } else {
        setErrorMsg("회원가입에 실패했습니다. 다시 시도해주세요.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* 좌측 회원가입 폼 섹션 */}
      <div className={styles.formSection}>
        <div className={`card border-0 p-5 ${styles.card}`}>
          <div className="card-body p-0">
            {/* 헤더 영역 */}
            <div className="text-center mb-5">
              <div className={styles.logoIcon}>
                P
              </div>
              <h2 className="fw-bold text-dark mb-1 text-gradient">계정 생성</h2>
              <p className="text-muted small">Paper Agent 플랫폼 회원으로 등록하세요.</p>
            </div>

            {/* 에러 메시지 표시 */}
            {errorMsg && (
              <div className={`alert text-center mb-4 small py-2 ${styles.errorAlert}`}>
                {errorMsg}
              </div>
            )}

            {/* 회원가입 폼 */}
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label text-muted small fw-semibold">아이디 (ID)</label>
                <input 
                  type="text" 
                  className={`form-control shadow-none py-2.5 ${styles.formInput}`} 
                  placeholder="5~20자 사이로 입력하세요"
                  value={mid}
                  onChange={(e) => setMid(e.target.value)}
                  disabled={isSubmitting}
                />
              </div>

              <div className="mb-3">
                <label className="form-label text-muted small fw-semibold">이름</label>
                <input 
                  type="text" 
                  className={`form-control shadow-none py-2.5 ${styles.formInput}`} 
                  placeholder="2~20자 사이로 입력하세요"
                  value={mname}
                  onChange={(e) => setMname(e.target.value)}
                  disabled={isSubmitting}
                />
              </div>

              <div className="mb-3">
                <label className="form-label text-muted small fw-semibold">이메일 주소</label>
                <input 
                  type="email" 
                  className={`form-control shadow-none py-2.5 ${styles.formInput}`} 
                  placeholder="example@domain.com"
                  value={memail}
                  onChange={(e) => setMemail(e.target.value)}
                  disabled={isSubmitting}
                />
              </div>
              
              <div className="mb-4">
                <label className="form-label text-muted small fw-semibold">비밀번호</label>
                <input 
                  type="password" 
                  className={`form-control shadow-none py-2.5 ${styles.formInput}`} 
                  placeholder="5~20자 사이로 입력하세요"
                  value={mpassword}
                  onChange={(e) => setMpassword(e.target.value)}
                  disabled={isSubmitting}
                />
              </div>

              <button 
                type="submit" 
                className={`btn w-100 py-2.5 fw-bold mb-3 ${styles.submitBtn}`}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                ) : (
                  "가입하기"
                )}
              </button>
            </form>

            {/* 로그인 리다이렉트 유도 */}
            <div className="text-center mt-4">
              <span className="text-muted small">이미 계정이 있으신가요? </span>
              <Link href="/login" className={`small fw-semibold text-decoration-none hover-underline ${styles.redirectLink}`}>
                로그인하기
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
            Start Your Research <br/>
            <span className="text-gradient-accent">Journey Today.</span>
          </h1>
          <p className={styles.visualSubtitle}>
            Create your account to unlock advanced AI writing assistants, automated literature mapping, and collaborative workspaces tailored for modern scholars.
          </p>
        </div>
      </div>
    </div>
  );
}
