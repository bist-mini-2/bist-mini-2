import { apiClient } from "./axiosConfig";
import { isMockMode } from "./mockConfig";
import * as mockService from "./mockService";

/**
 * 사용자의 모든 알림 목록을 최신순으로 조회합니다.
 * 
 * @returns {Promise<object>} API 응답 객체 (알림 목록 포함)
 */
export async function listNotifications() {
  if (isMockMode) {
    return mockService.listNotifications();
  }
  const response = await apiClient.get("/notification");
  return response.data;
}

/**
 * 특정 알림을 읽음 처리합니다.
 * 
 * @param {string} id 알림 고유 ID
 * @returns {Promise<object>} API 응답 객체 (성공 여부 포함)
 */
export async function markNotificationAsRead(id) {
  if (isMockMode) {
    return mockService.markNotificationAsRead(id);
  }
  const response = await apiClient.put(`/notification/${id}/read`);
  return response.data;
}

/**
 * 사용자의 모든 미읽음 알림을 일괄 읽음 처리합니다.
 * 
 * @returns {Promise<object>} API 응답 객체 (성공 여부 포함)
 */
export async function markAllNotificationsAsRead() {
  if (isMockMode) {
    return mockService.markAllNotificationsAsRead();
  }
  const response = await apiClient.put("/notification/read-all");
  return response.data;
}

/**
 * 특정 알림을 삭제합니다.
 * 
 * @param {string} id 알림 고유 ID
 * @returns {Promise<object>} API 응답 객체 (성공 여부 포함)
 */
export async function deleteNotification(id) {
  if (isMockMode) {
    return mockService.deleteNotification(id);
  }
  const response = await apiClient.delete(`/notification/${id}`);
  return response.data;
}

/**
 * 사용자의 모든 알림을 삭제합니다.
 * 
 * @returns {Promise<object>} API 응답 객체 (성공 여부 포함)
 */
export async function deleteAllNotifications() {
  if (isMockMode) {
    return mockService.deleteAllNotifications();
  }
  const response = await apiClient.delete("/notification");
  return response.data;
}
