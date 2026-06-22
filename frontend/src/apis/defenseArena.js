import { apiClient } from "./axiosConfig";

/**
 * PDF 파일을 보안 격리 샌드박스 영역에 업로드하고 세션을 시작합니다.
 * 
 * @param {File} file 업로드할 PDF 파일 객체
 * @returns {Promise<object>} API 응답 객체 (session_id, file_name, chunk_count 포함)
 */
export async function uploadIsolatedPdf(file) {
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
