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
 * @returns {Promise<object>} { answer, papers, sources }
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

/**
 * Gem과 대화하며 답변을 토큰 단위로 스트리밍 수신합니다.
 * @param {string} gemId
 * @param {{ thread_id: string, message: string }} payload
 * @param {(token: string) => void} onToken
 * @param {(status: string) => void} [onStatus]
 * @param {(papers: Array) => void} [onPapers]
 */
export async function chatWithGemStream(gemId, payload, onToken, onStatus, onPapers) {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;
  const res = await fetch(
    `http://localhost:8000/api/v1/gems/${gemId}/chat/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
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
    try { event = JSON.parse(trimmed); } catch { return; }
    if (event.type === "token") onToken?.(event.data);
    else if (event.type === "status") onStatus?.(event.data);
    else if (event.type === "papers") onPapers?.(event.data);
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
 * Gem에 업로드된 파일 목록을 조회합니다.
 * @param {string} gemId
 * @returns {Promise<Array>} [{ file_id, gem_id, filename, chunk_count, uploaded_at }]
 */
export async function getGemFiles(gemId) {
  const res = await apiClient.get(`/gems/${gemId}/files`);
  return res.data.data;
}

/**
 * Gem에 파일을 업로드하고 RAG 임베딩을 수행합니다.
 * @param {string} gemId
 * @param {File[]} files - 업로드할 파일 배열
 * @returns {Promise<{ processed_files: number, total_chunks: number }>}
 */
export async function uploadGemFiles(gemId, files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const res = await apiClient.post(`/gems/${gemId}/files`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data.data;
}
