"use client"

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import memberApi from "@/apis/memberApi";

/**
 * 신규 회원 가입을 지원하는 다크 모드 폼 인터페이스 페이지입니다.
 * 
 * 사용자로부터 아이디, 이름, 이메일, 비밀번호 정보를 받아
 * JSON 규격으로 백엔드 신규 등록 API(/member/join)를 호출한 후 로그인 화면으로 리다이렉트합니다.
 */
export default function JoinPage() {
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

      alert("회원가입이 완료되었습니다. 로그인 해주세요!");
      router.push("/login");
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
    <div 
      className="d-flex align-items-center justify-content-center min-vh-100 text-light p-4"
      style={{
        backgroundColor: "#080b11",
        backgroundImage: "radial-gradient(at 10% 10%, rgba(16, 163, 127, 0.08) 0px, transparent 50%), radial-gradient(at 90% 90%, rgba(59, 130, 246, 0.06) 0px, transparent 50%)"
      }}
    >
      <div 
        className="card border-0 rounded-4 p-5" 
        style={{
          width: "100%",
          maxWidth: "420px",
          backgroundColor: "rgba(17, 22, 34, 0.65)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.07)",
          boxShadow: "0 20px 45px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div className="card-body p-0">
          {/* 헤더 영역 */}
          <div className="text-center mb-5">
            <div 
              className="d-inline-flex align-items-center justify-content-center rounded-circle text-white mb-3"
              style={{ 
                width: "52px", 
                height: "52px", 
                fontSize: "1.6rem", 
                fontWeight: "800",
                background: "linear-gradient(135deg, #10a37f 0%, #3b82f6 100%)",
                boxShadow: "0 4px 14px rgba(16, 163, 127, 0.3)"
              }}
            >
              P
            </div>
            <h2 className="fw-bold text-white mb-1 text-gradient">계정 생성</h2>
            <p className="text-muted small">Paper Agent 플랫폼 회원으로 등록하세요.</p>
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

          {/* 회원가입 폼 */}
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label text-secondary small fw-semibold">아이디 (ID)</label>
              <input 
                type="text" 
                className="form-control bg-dark border-secondary text-white rounded-3 shadow-none py-2" 
                placeholder="5~20자 사이로 입력하세요"
                value={mid}
                onChange={(e) => setMid(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="mb-3">
              <label className="form-label text-secondary small fw-semibold">이름</label>
              <input 
                type="text" 
                className="form-control bg-dark border-secondary text-white rounded-3 shadow-none py-2" 
                placeholder="2~20자 사이로 입력하세요"
                value={mname}
                onChange={(e) => setMname(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="mb-3">
              <label className="form-label text-secondary small fw-semibold">이메일 주소</label>
              <input 
                type="email" 
                className="form-control bg-dark border-secondary text-white rounded-3 shadow-none py-2" 
                placeholder="example@domain.com"
                value={memail}
                onChange={(e) => setMemail(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
            
            <div className="mb-4">
              <label className="form-label text-secondary small fw-semibold">비밀번호</label>
              <input 
                type="password" 
                className="form-control bg-dark border-secondary text-white rounded-3 shadow-none py-2" 
                placeholder="5~20자 사이로 입력하세요"
                value={mpassword}
                onChange={(e) => setMpassword(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-success w-100 rounded-3 py-2.5 fw-bold mb-3 border-0"
              style={{
                backgroundColor: "#10a37f",
                boxShadow: "0 4px 12px rgba(16, 163, 127, 0.2)"
              }}
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
            <Link href="/login" className="text-success small fw-semibold text-decoration-none hover-underline">
              로그인하기
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
