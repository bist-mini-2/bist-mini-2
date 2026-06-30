import { apiClient } from "./axiosConfig";
import { isMockMode } from "./mockConfig";
import * as mockService from "./mockService";

/**
 * 신규 회원을 플랫폼에 가입시킵니다.
 * 
 * @param {object} joinData - 가입할 회원 정보 (mid, mname, memail, mpassword, menabled, mrole)
 * @returns {Promise<object>} 회원 가입 성공 응답 데이터
 */
async function join(joinData) {
  if (isMockMode) {
    return mockService.join(joinData);
  }
  const response = await apiClient.post("/member/join", joinData);
  return response.data;
}

const memberApi = {
  join,
};

export default memberApi;
