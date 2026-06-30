// mockConfig.js
// 브라우저 호스트가 github.io이거나, 쿼리 스트링 또는 로컬스토리지에 mock이 명시되어 있는 경우,
// 혹은 백엔드 서버가 로컬호스트가 아닌 환경(배포 서버 등)에 배포된 상태에서 backendUrl에 연결할 수 없는 경우 작동합니다.
export const isMockMode = typeof window !== "undefined" && (
  window.location.hostname.includes("github.io") ||
  localStorage.getItem("useMock") === "true" ||
  new URLSearchParams(window.location.search).get("mock") === "true" ||
  (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "192.168.5.13")
);

console.log("[Mock Mode Status]:", isMockMode ? "ENABLED (Client-side mocking active)" : "DISABLED (FastAPI Backend active)");
