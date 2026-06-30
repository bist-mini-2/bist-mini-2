import { apiClient, backendUrl } from "./axiosConfig";
import { isMockMode } from "./mockConfig";
import * as mockService from "./mockService";

/**
 * 새로운 채팅방(세션)을 생성합니다.
 *
 * @param {string} title 채팅방 제목
 * @returns {Promise<object>} API 응답 객체 (data: { session_id, title, created_at })
 */
export async function createSession(title) {
  if (isMockMode) {
    return mockService.createSession(title);
  }
  const response = await apiClient.post("/chat/sessions", { title });
  return response.data;
}

/**
 * 현재 로그인한 사용자의 채팅방 목록을 조회합니다.
 *
 * @returns {Promise<object>} API 응답 객체 (data: [{ session_id, title, created_at }])
 */
export async function getSessions() {
  if (isMockMode) {
    return mockService.getSessions();
  }
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
  if (isMockMode) {
    return mockService.deleteSession(sessionId);
  }
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
  if (isMockMode) {
    return mockService.sendMessage(sessionId, message);
  }
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
  if (isMockMode) {
    return mockService.renameSession(sessionId, title);
  }
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
  if (isMockMode) {
    return mockService.getMessages(sessionId);
  }
  const response = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
  return response.data;
}

/**
 * 채팅방에 메시지를 전송하고 답변을 토큰 단위로 스트리밍 수신합니다(타이핑 효과).
 *
 * @param {string} sessionId 채팅방 고유 ID
 * @param {string} message 사용자 질문 내용
 * @param {(token: string) => void} onToken 토큰이 도착할 때마다 호출되는 콜백
 * @returns {Promise<void>} 스트리밍이 끝나면 resolve됩니다.
 */
export async function sendMessageStream(sessionId, message, onToken, onStatus, image) {
  if (isMockMode) {
    return mockService.sendMessageStream(sessionId, message, onToken, onStatus, image);
  }
  const token =
    typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;
  const res = await fetch(
    `${backendUrl}/chat/sessions/${sessionId}/messages/multi/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(image ? { message, image } : { message }),
    }
  );
  if (!res.ok || !res.body) throw new Error("스트리밍 요청 실패");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const handleLine = (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    let event;
    try {
      event = JSON.parse(trimmed);
    } catch {
      return;
    }
    if (event.type === "token") onToken?.(event.data);
    else if (event.type === "status") onStatus?.(event.data);
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let nl;
    while ((nl = buffer.indexOf("\n")) >= 0) {
      handleLine(buffer.slice(0, nl));
      buffer = buffer.slice(nl + 1);
    }
  }
  handleLine(buffer);
}

/**
 * 첫 질문을 바탕으로 AI가 채팅방 제목을 생성하고 적용합니다.
 *
 * @param {string} sessionId 채팅방 고유 ID
 * @param {string} message 사용자의 첫 질문
 * @returns {Promise<object>} API 응답 객체 (data: { title })
 */
export async function generateTitle(sessionId, message) {
  if (isMockMode) {
    return { data: { title: message.substring(0, 15) + "..." } };
  }
  const response = await apiClient.post(`/chat/sessions/${sessionId}/generate-title`, { message });
  return response.data;
}