"use client"

import { useContext, useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { NotificationContext } from "@/contexts/NotificationContext";
import styles from "./NotificationCenter.module.css";

/**
 * 고정 헤더 바(Topbar)에 탑재되어 실시간 알림 목록 열람, 데스크톱 알림 권한 제어,
 * 일괄 처리 기능을 독립적으로 수행하는 알림 센터 UI 컴포넌트입니다.
 */
export default function NotificationCenter() {
  const router = useRouter();
  
  // 알림 컨텍스트 연동
  const {
    notifications,
    unreadCount,
    osPermission,
    isPushEnabled,
    togglePushEnabled,
    markAllAsRead,
    markAsRead,
    clearAll
  } = useContext(NotificationContext);

  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // 알림 팝오버 외부 영역 클릭 시 드롭다운 닫기 처리
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);



  // 알림 개별 클릭 핸들러 (읽음 처리 및 관련 페이지 이동)
  const handleNotifClick = (notif) => {
    markAsRead(notif.id);
    if (notif.task_id) {
      router.push(`/feature2?taskId=${notif.task_id}`);
    }
    setShowDropdown(false);
  };

  // 알림 성격별 아이콘 바인딩
  const getNotifIconClass = (type) => {
    switch (type) {
      case "success": return "bi-check-circle-fill";
      case "danger": return "bi-exclamation-triangle-fill";
      case "warning": return "bi-exclamation-circle-fill";
      default: return "bi-info-circle-fill";
    }
  };

  // 타임스탬프 형식 간소화 포맷터 (HH:mm)
  const formatTime = (isoString) => {
    try {
      const date = new Date(isoString);
      const hours = String(date.getHours()).padStart(2, "0");
      const minutes = String(date.getMinutes()).padStart(2, "0");
      return `${hours}:${minutes}`;
    } catch (e) {
      return "";
    }
  };

  return (
    <div className={styles.notificationWrapper} ref={dropdownRef}>
      <button
        className={`${styles.iconButton} ${showDropdown ? styles.activeButton : ""}`}
        onClick={() => setShowDropdown(!showDropdown)}
        title="알림 센터"
        aria-label="Toggle Notifications"
      >
        <i className="bi bi-bell"></i>
        {unreadCount > 0 && (
          <span className={styles.badge}>{unreadCount}</span>
        )}
      </button>

      {/* 알림 레이아웃 팝오버 */}
      <div className={`${styles.dropdown} ${showDropdown ? styles.open : ""}`}>
        <div className={styles.dropdownHeader}>
          <h6 className="m-0 font-weight-bold">알림 센터</h6>
          {unreadCount > 0 && (
            <button className={styles.markReadBtn} onClick={markAllAsRead}>
              모두 읽음
            </button>
          )}
        </div>

        {/* OS 푸시 알림 설정 토글 */}
        <div className={styles.permissionSection}>
          <div className="d-flex align-items-center justify-content-between w-100">
            <span className={styles.permissionLabel}>
              <i className="bi bi-laptop me-2"></i>OS 데스크톱 알림
            </span>
            <div className="form-check form-switch m-0">
              <input
                className="form-check-input cursor-pointer"
                type="checkbox"
                role="switch"
                id="osNotificationSwitch"
                checked={isPushEnabled}
                onChange={togglePushEnabled}
              />
            </div>
          </div>
          {osPermission !== "granted" && (
            <div className={styles.permissionTip}>
              분석 완료 시 백그라운드에서도 OS 알림 배너를 즉각 띄웁니다.
            </div>
          )}
        </div>

        {/* 알림 수신 히스토리 스크롤 바디 */}
        <div className={styles.dropdownBody}>
          {notifications.length === 0 ? (
            <div className={styles.emptyState}>
              <i className="bi bi-bell-slash text-muted mb-2"></i>
              <span className="text-muted">수신된 알림이 없습니다.</span>
            </div>
          ) : (
            notifications.map((notif) => (
              <div
                key={notif.id}
                className={`${styles.notifItem} ${notif.read ? "" : styles.unread}`}
                onClick={() => handleNotifClick(notif)}
              >
                <div className="d-flex align-items-start gap-2">
                  <span className={`${styles.notifIcon} ${styles[notif.type] || styles.info}`}>
                    <i className={`bi ${getNotifIconClass(notif.type)}`}></i>
                  </span>
                  <div className="flex-grow-1 min-w-0">
                    <div className="d-flex align-items-center justify-content-between mb-1">
                      <span className={styles.notifTitle}>{notif.title}</span>
                      <span className={styles.notifTime}>{formatTime(notif.timestamp)}</span>
                    </div>
                    <p className={styles.notifMessage}>{notif.message}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* 하단 제어 */}
        {notifications.length > 0 && (
          <div className={styles.dropdownFooter}>
            <button className={styles.clearAllBtn} onClick={clearAll}>
              알림 내역 전체 삭제
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
