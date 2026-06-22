"use client"

import { createContext, useState, useEffect, startTransition } from "react";
import { usePathname, useRouter } from "next/navigation";
import { apiClient } from "@/apis/axiosConfig";

// 인증 관련 전역 상태를 관리하기 위한 Context 생성
export const AuthContext = createContext();

/**
 * 애플리케이션의 인증 상태 및 사용자 세션을 전역에서 제공하는 Provider 컴포넌트입니다.
 * 
 * 브라우저 로컬 스토리지에 로그인 세션을 저장하여 리프레시 시 상태를 자동 복원하고,
 * 비로그인 상태에서의 보호된 경로 접근을 통제하여 로그인 페이지로 리다이렉트합니다.
 */
export function AuthContextProvider({ children }) {
  const [user, setUser] = useState("");
  const [accessToken, setAccessToken] = useState("");
  
  // 브라우저 리프레시 시 깜빡임 및 로그인 폼 노출 방지를 위한 로딩 상태
  const [isLoading, setIsLoading] = useState(true);
  
  const router = useRouter();
  const pathname = usePathname();

  // 최초 렌더링 시 로컬 스토리지에서 인증 정보 로드 및 검증
  useEffect(() => {
    const storedUser = localStorage.getItem("user") || "";
    const storedToken = localStorage.getItem("accessToken") || "";

    if (storedToken) {
      // API 클라이언트가 인터셉터를 통해 로컬스토리지의 토큰을 자동으로 헤더에 실어 보냅니다.
      apiClient.get("/auth/me")
        .then(() => {
          startTransition(() => {
            setUser(storedUser);
            setAccessToken(storedToken);
            setIsLoading(false);
          });
        })
        .catch((error) => {
          // 토큰 검증 실패 시 로컬 스토리지 정보를 초기화하고 비인증 상태로 전환
          console.warn("Stored accessToken is invalid or expired. Clearing auth context.", error);
          localStorage.removeItem("user");
          localStorage.removeItem("accessToken");
          startTransition(() => {
            setUser("");
            setAccessToken("");
            setIsLoading(false);
          });
        });
    } else {
      startTransition(() => {
        setIsLoading(false);
      });
    }
  }, []);

  // 인증 상태 변화 시 로컬 스토리지 동기화
  useEffect(() => {
    if (user !== "") {
      localStorage.setItem("user", user);
      localStorage.setItem("accessToken", accessToken);
    } else {
      localStorage.removeItem("user");
      localStorage.removeItem("accessToken");
    }
  }, [user, accessToken]);

  // Response Interceptor: 401 Unauthorized 에러 발생 시 세션 만료 및 강제 로그아웃
  useEffect(() => {
    const interceptor = apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          setUser("");
          setAccessToken("");
        }
        return Promise.reject(error);
      }
    );

    return () => {
      apiClient.interceptors.response.eject(interceptor);
    };
  }, []);

  // 비로그인 사용자 및 로그인 사용자의 경로 접근 제한 (라우트 가드 및 리다이렉션)
  useEffect(() => {
    if (!isLoading) {
      const isAuthPage = pathname === "/login" || pathname === "/join";
      if (!user && !isAuthPage) {
        // 인증되지 않은 사용자가 서비스 화면에 접속하려고 할 때 로그인으로 이동
        router.replace("/login");
      } else if (user && isAuthPage) {
        // 이미 로그인된 사용자가 로그인/가입 화면에 오면 홈(Chat Hub)으로 이동
        router.replace("/");
      }
    }
  }, [user, pathname, isLoading, router]);

  // Context를 통해 하위 컴포넌트에 공급될 데이터 객체
  const value = {
    user,
    accessToken,
    setUser,
    setAccessToken,
  };

  // 마운트 직후 로컬 스토리지 읽기 완료 전에는 로딩 스피너 표시
  if (isLoading) {
    return (
      <div className="loading-overlay">
        <div className="spinner-border loading-spinner" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContextProvider;
