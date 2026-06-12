import { apiClient } from "./axiosConfig";

/**
 * 사용자 자격 증명(ID, 비밀번호)을 기반으로 로그인을 수행하여 토큰을 발급받습니다.
 * 
 * @param {string} mid - 사용자 아이디
 * @param {string} mpassword - 사용자 비밀번호
 * @returns {Promise<object>} JWT 토큰 및 사용자 정보 데이터
 */
async function login(mid, mpassword) {
  const params = new URLSearchParams();
  params.append("username", mid);
  params.append("password", mpassword);

  const response = await apiClient.post("/auth/login", params, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}

const authApi = {
  login,
};

export default authApi;
