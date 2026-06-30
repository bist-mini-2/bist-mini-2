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

/**
 * 영어로 완성된 매트릭스 데이터를 한국어로 번역 요청 및 캐싱합니다.
 * 
 * @param {string} taskId 작업 고유 UUID
 * @returns {Promise<object>} 번역된 매트릭스 데이터
 */
export async function translateMatrix(taskId) {
  const response = await apiClient.post(`/research-gap/tasks/${taskId}/translate`);
  return response.data;
}

/**
 * 사용자가 요청한 모든 분석 작업 이력 리스트를 조회합니다.
 * 
 * @returns {Promise<object>} API 응답 객체 (태스크 리스트)
 */
export async function listUserTasks() {
  const response = await apiClient.get("/research-gap/tasks");
  return response.data;
}

/**
 * 특정 배치 분석 작업 이력을 삭제합니다.
 * 
 * @param {string} taskId 작업 고유 UUID
 * @returns {Promise<object>} API 응답 객체 (삭제 여부)
 */
export async function deleteTask(taskId) {
  const response = await apiClient.delete(`/research-gap/tasks/${taskId}`);
  return response.data;
}

/**
 * 여러 배치 분석 작업 이력을 선택 일괄 삭제합니다.
 * 
 * @param {string[]} taskIds 작업 고유 UUID 리스트
 * @returns {Promise<object>} API 응답 객체 (deleted_count 포함)
 */
export async function bulkDeleteTasks(taskIds) {
  const response = await apiClient.post("/research-gap/tasks/bulk-delete", { task_ids: taskIds });
  return response.data;
}




