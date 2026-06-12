import axios from "axios";

// API 서버의 기본 경로 설정 (FastAPI 백엔드가 구동되는 8000번 포트의 API v1 주소)
axios.defaults.baseURL = "http://localhost:8000/api/v1";

/**
 * 로그인 성공 시 발급받은 JWT Access Token을 모든 요청 헤더에 자동으로 주입합니다.
 * 
 * @param {string} accessToken - JWT 액세스 토큰 문자열
 */
function addAuthHeader(accessToken) {
  axios.defaults.headers.common["Authorization"] = "Bearer " + accessToken;
}

/**
 * 로그아웃 시 공통 요청 헤더에서 Authorization 헤더를 삭제합니다.
 */
function removeAuthHeader() {
  delete axios.defaults.headers.common["Authorization"];
}

const obj = {
  addAuthHeader,
  removeAuthHeader
};

export default obj;
