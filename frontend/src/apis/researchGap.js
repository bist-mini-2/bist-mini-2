import { apiClient } from "./axiosConfig";

/**
 * 대규모 문헌 비교 분석 비동기 작업 요청을 보냅니다.
 * 
 * @param {string} domain 학술 분야 ('cs' 또는 'bio')
 * @param {string} query 검색할 주제/기술 키워드
 * @returns {Promise<object>} API 응답 객체 (task_id 포함)
 */
export async function startAnalysis(domain, query) {
  const response = await apiClient.post("/research-gap/analyze", { domain, query });
  return response.data;
}

/**
 * 배치 분석 작업의 실시간 진행률 및 상태를 조회합니다.
 * 
 * @param {string} taskId 작업 고유 UUID
 * @returns {Promise<object>} API 응답 객체 (상태 및 진행률 %)
 */
export async function getTaskStatus(taskId) {
  const response = await apiClient.get(`/research-gap/tasks/${taskId}`);
  return response.data;
}

/**
 * 완료된 배치 분석의 최종 결과(매트릭스 & 제안서)를 획득합니다.
 * 
 * @param {string} taskId 작업 고유 UUID
 * @returns {Promise<object>} API 응답 객체 (최종 분석 결과)
 */
export async function getTaskResult(taskId) {
  const response = await apiClient.get(`/research-gap/tasks/${taskId}/result`);
  return response.data;
}
