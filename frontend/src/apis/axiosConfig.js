import axios from "axios";

// 브라우저 환경이라면 현재 접속한 호스트 명(IP 또는 도메인)을 기반으로 백엔드 주소를 동적으로 계산합니다.
let backendUrl = "http://localhost:8000/api/v1";

if (typeof window !== "undefined") {
  const hostname = window.location.hostname;
  if (hostname && hostname !== "localhost" && hostname !== "127.0.0.1") {
    backendUrl = `http://${hostname}:8000/api/v1`;
  }
}

// 전용 API 클라이언트 인스턴스 생성
const apiClient = axios.create({
  baseURL: backendUrl,
});

// Request Interceptor: 모든 요청 전 로컬스토리지에서 토큰을 추출하여 Authorization 헤더에 실어 보냅니다.
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("accessToken");
      if (token) {
        config.headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 기존 인터페이스 호환을 위한 레거시 객체 구성
const legacyConfig = {
  addAuthHeader: () => {},
  removeAuthHeader: () => {},
  apiClient
};

export { apiClient, backendUrl };
export default legacyConfig;
