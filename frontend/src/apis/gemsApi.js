import { apiClient } from "./axiosConfig";
import { isMockMode } from "./mockConfig";
import * as mockService from "./mockService";

/**
 * Gem 목록을 조회합니다.
 * @returns {Promise<Array>} Gem 배열
 */
export async function getGems() {
  if (isMockMode) {
    return mockService.getGems();
  }
  const res = await apiClient.get("/gems");
  return res.data.data;
}

/**
 * 새 Gem을 생성합니다.
 * @param {object} payload - { name, db_sources, system_prompt }
 * @returns {Promise<object>} 생성된 Gem 객체
 */
export async function createGem(payload) {
  if (isMockMode) {
    return mockService.createGem(payload);
  }
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
  if (isMockMode) {
    const gem = mockService.getGems().find(g => g.gem_id === gemId);
    if (gem) Object.assign(gem, payload);
    return gem;
  }
  const res = await apiClient.put(`/gems/${gemId}`, payload);
  return res.data.data;
}

/**
 * Gem을 삭제합니다.
 * @param {string} gemId
 */
export async function deleteGem(gemId) {
  if (isMockMode) {
    return mockService.deleteGem(gemId);
  }
  await apiClient.delete(`/gems/${gemId}`);
}

/**
 * 특정 Gem과 대화합니다.
 * @param {string} gemId
 * @param {object} payload - { thread_id, message }
 * @returns {Promise<object>} { answer, papers, sources }
 */
export async function chatWithGem(gemId, payload) {
  if (isMockMode) {
    return {
      answer: "Gem 답변 (Mock)",
      papers: [],
      sources: []
    };
  }
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
  if (isMockMode) {
    return [];
  }
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
  if (isMockMode) {
    onStatus?.("paper_search");
    await new Promise(r => setTimeout(r, 800));
    onStatus?.("file_search");
    await new Promise(r => setTimeout(r, 800));
    onStatus?.("generating");
    
    const text = `사용자 정의 Gem 비서 [NASA JPL 우주론 튜터]의 분석 답변입니다:

업로드해주신 파일(astro_background_cmb.pdf)의 8장에 명시된 고전적인 우주 구성 정보(암흑 물질 27%, 암흑 에너지 68%)와, 최근 천문학 학계(제임스 웹 망원경 관측 및 DESI 등)가 논의하는 우주 팽창 속도 데이터는 매우 흥미로운 상호 대조군을 형성합니다:

1. **시간에 따른 가변성**: 개론서의 68% 암흑 기여도는 우주 상수(Lambda)를 상정하고 있으나, 최근 관측은 상태 방정식 파라미터 $w(z)$ 가 동적으로 진동할 가능성(Dynamic Dark Energy)을 강하게 암시합니다.
2. **CMB와 국소 관측의 Tension**: 우주배경복사 기반 예측값과 초신성 사다리 관측값 간의 허블 상수 불일치(Hubble Tension)에 따라 우주 구성 모델이 미세 조정되고 있습니다.

더 자세히 설명해 드릴까요?`;
    
    const chunks = text.split(" ");
    for (let i = 0; i < chunks.length; i++) {
      onToken?.(chunks[i] + (i === chunks.length - 1 ? "" : " "));
      await new Promise(r => setTimeout(r, 45));
    }
    
    onPapers?.([
      { arxiv_id: "2401.0345", title: "Observational Constraints on Time-varying Dark Energy", summary: "CMB and supernova data comparison.", type: "arxiv" },
      { title: "astro_background_cmb.pdf", summary: "우주 배경 복사(CMB) 및 암흑 에너지 밀도 상태 방정식 분석.", type: "file", score: 0.89 }
    ]);
    return;
  }
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
  if (isMockMode) {
    return mockService.getGemFiles(gemId);
  }
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
  if (isMockMode) {
    const file = files[0];
    const newFile = mockService.uploadGemFile(gemId, file?.name);
    return {
      processed_files: 1,
      total_chunks: newFile.chunk_count
    };
  }
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const res = await apiClient.post(`/gems/${gemId}/files`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data.data;
}
