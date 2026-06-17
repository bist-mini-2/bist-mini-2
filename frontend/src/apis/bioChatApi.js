import { apiClient } from "./axiosConfig";

/**
 * 새로운 채팅방(세션)을 생성합니다.
 *
 * @param {string} title 채팅방 제목
 * @returns {Promise<object>} API 응답 객체 (data: { session_id, title, created_at })
 */
export async function createSession(title) {
  const response = await apiClient.post("/chat/sessions", { title });
  return response.data;
}

/**
 * 현재 로그인한 사용자의 채팅방 목록을 조회합니다.
 *
 * @returns {Promise<object>} API 응답 객체 (data: [{ session_id, title, created_at }])
 */
export async function getSessions() {
  const response = await apiClient.get("/chat/sessions");
  return response.data;
}

/**
 * 채팅방을 삭제합니다(대화 기록 포함).
 *
 * @param {string} sessionId 채팅방 고유 ID
 * @returns {Promise<object>} API 응답 객체
 */
export async function deleteSession(sessionId) {
  const response = await apiClient.delete(`/chat/sessions/${sessionId}`);
  return response.data;
}

/**
 * 채팅방에 메시지를 전송하고 RAG 기반 답변을 받습니다.
 *
 * @param {string} sessionId 채팅방 고유 ID
 * @param {string} message 사용자 질문 내용
 * @returns {Promise<object>} API 응답 객체 (data: { answer, sources: [{ arxiv_id, title }] })
 */
export async function sendMessage(sessionId, message) {
  const response = await apiClient.post(`/chat/sessions/${sessionId}/messages`, { message });
  return response.data;
}

/**
 * 채팅방 제목을 변경합니다.
 *
 * @param {string} sessionId 채팅방 고유 ID
 * @param {string} title 새 제목
 * @returns {Promise<object>} API 응답 객체 (data: { session_id, title, created_at })
 */
export async function renameSession(sessionId, title) {
  const response = await apiClient.patch(`/chat/sessions/${sessionId}`, { title });
  return response.data;
}

/**
 * 채팅방의 대화 내역을 순서대로 조회합니다.
 *
 * @param {string} sessionId 채팅방 고유 ID
 * @returns {Promise<object>} API 응답 객체 (data: [{ role, content }])
 */
export async function getMessages(sessionId) {
  const response = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
  return response.data;
}