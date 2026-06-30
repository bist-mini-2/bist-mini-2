import { apiClient } from "./axiosConfig";
import { isMockMode } from "./mockConfig";
import * as mockService from "./mockService";

/**
 * PDF 파일을 보안 격리 샌드박스 영역에 업로드하고 세션을 시작합니다.
 * 
 * @param {File} file 업로드할 PDF 파일 객체
 * @returns {Promise<object>} API 응답 객체 (session_id, file_name, chunk_count 포함)
 */
export async function uploadIsolatedPdf(file) {
  if (isMockMode) {
    return mockService.uploadIsolatedPdf(file?.name);
  }
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post("/defense-arena/upload-isolated", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

/**
 * 3대 심층 에이전트 종합 피어리뷰 리포트를 생성합니다.
 * 
 * @param {string} sessionId 세션 UUID
 * @param {string} targetJournal 투고 타겟 저널명
 * @returns {Promise<object>} API 응답 객체 (PeerReviewReport DTO)
 */
export async function runAcademicPeerReview(sessionId, targetJournal) {
  if (isMockMode) {
    return mockService.runAcademicPeerReview(sessionId, targetJournal);
  }
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("target_journal", targetJournal);
  const response = await apiClient.post("/defense-arena/peer-review", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}

/**
 * 자기 일관성(Self-Consistency) 기반으로 연구 가설을 검증합니다.
 * 
 * @param {string} sessionId 세션 UUID
 * @param {string} hypothesis 검증받고자 하는 연구 가설
 * @returns {Promise<object>} API 응답 객체 (HypothesisVerificationResult DTO)
 */
export async function verifyHypothesis(sessionId, hypothesis) {
  if (isMockMode) {
    return mockService.verifyHypothesis(sessionId, hypothesis);
  }
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("hypothesis", hypothesis);
  const response = await apiClient.post("/defense-arena/verify-hypothesis", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}

/**
 * 심사위원 에이전트와 실시간 모의 디펜스를 진행합니다.
 * 
 * @param {string} sessionId 세션 UUID
 * @param {string|null} userResponse 사용자의 답변/반론 텍스트 (첫 턴의 경우 null)
 * @returns {Promise<object>} API 응답 객체 (DefenseChatResponse DTO)
 */
export async function defenseChatArena(sessionId, userResponse) {
  if (isMockMode) {
    return mockService.defenseChatArena(sessionId, userResponse);
  }
  const formData = new FormData();
  formData.append("session_id", sessionId);
  if (userResponse !== undefined && userResponse !== null) {
    formData.append("user_response", userResponse);
  }
  const response = await apiClient.post("/defense-arena/defense/chat", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}

/**
 * 보안 격리 세션의 마지막 활동 시각을 갱신(Ping)하여 만료 시간을 연장합니다.
 * 
 * @param {string} sessionId 세션 UUID
 * @returns {Promise<object>} API 응답 객체
 */
export async function keepAliveDefenseSession(sessionId) {
  if (isMockMode) {
    return { status: "success", message: "session kept alive (mock)" };
  }
  const formData = new FormData();
  formData.append("session_id", sessionId);
  const response = await apiClient.post("/defense-arena/keep-alive", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}

/**
 * 영어 학술 텍스트를 한국어로 번역합니다.
 * 
 * @param {string} text 번역할 영어 학술 텍스트
 * @returns {Promise<object>} 번역 결과 응답 객체 (translated_text 포함)
 */
export async function translateText(text) {
  if (isMockMode) {
    return mockService.translateText(text);
  }
  const formData = new FormData();
  formData.append("text", text);
  const response = await apiClient.post("/defense-arena/translate", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}

/**
 * 사용자의 저장된 디펜스 아레나 히스토리 목록을 조회합니다.
 * 
 * @returns {Promise<object>} API 응답 객체 (SavedSessionDTO 배열 포함)
 */
export async function getDefenseHistoryList() {
  if (isMockMode) {
    return mockService.getDefenseHistoryList();
  }
  const response = await apiClient.get("/defense-arena/history");
  return response.data;
}

/**
 * 특정 보관 세션의 상세 정보를 복원합니다.
 * 
 * @param {string} sessionId 세션 UUID
 * @returns {Promise<object>} API 응답 객체 (SavedSessionDetailResponse DTO)
 */
export async function getDefenseSessionDetail(sessionId) {
  if (isMockMode) {
    return mockService.getDefenseSessionDetail(sessionId);
  }
  const response = await apiClient.get(`/defense-arena/history/${sessionId}`);
  return response.data;
}

/**
 * 특정 보관 세션을 영구 삭제합니다.
 * 
 * @param {string} sessionId 세션 UUID
 * @returns {Promise<object>} API 응답 객체
 */
export async function deleteDefenseSession(sessionId) {
  if (isMockMode) {
    return mockService.deleteDefenseSession(sessionId);
  }
  const response = await apiClient.delete(`/defense-arena/history/${sessionId}`);
  return response.data;
}
