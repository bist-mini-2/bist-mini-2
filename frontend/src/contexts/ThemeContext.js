"use client";

import { createContext, useState, useEffect } from "react";

// 테마 상태를 전역에서 관리하기 위한 Context 생성
export const ThemeContext = createContext();

/**
 * 애플리케이션의 테마(라이트/다크) 상태를 관리하고 하위 컴포넌트에 토글 기능을 제공하는 Provider 컴포넌트입니다.
 * 사용자 브라우저의 로컬 스토리지 및 시스템 설정(선호 테마)과 동기화하며, html 태그의 data-theme 속성을 변경합니다.
 */
export function ThemeContextProvider({ children }) {
  const [theme, setTheme] = useState("light");
  const [isMounted, setIsMounted] = useState(false);

  // 컴포넌트 마운트 시 로컬 스토리지 또는 시스템 기본 설정을 기반으로 테마 초기화
  useEffect(() => {
    const storedTheme = localStorage.getItem("theme");
    if (storedTheme === "light" || storedTheme === "dark") {
      setTheme(storedTheme);
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(prefersDark ? "dark" : "light");
    }
    setIsMounted(true);
  }, []);

  // 테마 상태 변경 시 문서 루트 요소의 data-theme 속성 업데이트 및 로컬 스토리지 저장
  useEffect(() => {
    if (isMounted) {
      document.documentElement.setAttribute("data-theme", theme);
      localStorage.setItem("theme", theme);
    }
  }, [theme, isMounted]);

  // 테마 토글 함수
  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export default ThemeContextProvider;
