import { apiClient } from "./axiosConfig";

/**
 * Gem 목록을 조회합니다.
 * @returns {Promise<Array>} Gem 배열
 */
export async function getGems() {
  const res = await apiClient.get("/gems");
  return res.data.data;
}

/**
 * 새 Gem을 생성합니다.
 * @param {object} payload - { name, db_sources, system_prompt }
 * @returns {Promise<object>} 생성된 Gem 객체
 */
export async function createGem(payload) {
  const res = await apiClient.post("/gems", payload);
  return res.data.data;
}

/**
 * Gem을 수정합니다. 전달된 필드만 업데이트됩니다.
 * @param {string} gemId
 * @param {object} payload - { name?, db_sources?, system_prompt? }
 * @returns {Promise<object>} 수정된 Gem 객체
 */
export async function updateGem(gemId, payload) {
  const res = await apiClient.put(`/gems/${gemId}`, payload);
  return res.data.data;
}

/**
 * Gem을 삭제합니다.
 * @param {string} gemId
 */
export async function deleteGem(gemId) {
  await apiClient.delete(`/gems/${gemId}`);
}

/**
 * 특정 Gem과 대화합니다.
 * @param {string} gemId
 * @param {object} payload - { thread_id, message }
 * @returns {Promise<object>} { answer, sources }
 */
export async function chatWithGem(gemId, payload) {
  const res = await apiClient.post(`/gems/${gemId}/chat`, payload);
  return res.data.data;
}

/**
 * Gem 대화 스레드의 이전 대화 내역을 불러옵니다.
 * @param {string} gemId
 * @param {string} threadId
 * @returns {Promise<Array>} [{ role, content }]
 */
export async function getGemMessages(gemId, threadId) {
  const res = await apiClient.get(`/gems/${gemId}/chat/${threadId}/messages`);
  return res.data.data;
}
