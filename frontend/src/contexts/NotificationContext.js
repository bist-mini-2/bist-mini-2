"use client"

import { createContext, useState, useEffect, useContext, useRef } from "react";
import { AuthContext } from "./AuthContext";

export const NotificationContext = createContext();

/**
 * 전역 실시간 SSE 알림 수신 및 브라우저 OS 알림(HTML5 Web Notification)을 처리하는 컨텍스트 프로바이더입니다.
 * 
 * - 로그인된 사용자의 accessToken을 이용하여 중앙 SSE 채널을 구독합니다.
 * - 알림 내역을 로컬 스토리지에 사용자별로 저장하여 페이지 리프레시 후에도 내역을 복원합니다.
 * - 데스크톱 알림 허용 여부를 동적으로 제어(Topbar 스위치)할 수 있도록 허용 상태 및 트리거 메서드를 제공합니다.
 */
export function NotificationContextProvider({ children }) {
  const { user, accessToken } = useContext(AuthContext);
  const [notifications, setNotifications] = useState([]);
  const [osPermission, setOsPermission] = useState("default");
  const [isPushEnabled, setIsPushEnabled] = useState(true);
  
  const eventSourceRef = useRef(null);

  // 1. 컴포넌트 마운트 시 브라우저 Notification 지원 여부, 허용 상태 및 로컬 스토리지에서 푸시 설정 복원
  useEffect(() => {
    if (typeof window !== "undefined") {
      if ("Notification" in window) {
        setOsPermission(Notification.permission);
      }
      const savedPush = localStorage.getItem("os_push_enabled");
      if (savedPush !== null) {
        setIsPushEnabled(savedPush === "true");
      }
    }
  }, []);

  // 2. 로그인 유저 전환 시 해당 유저의 알림 히스토리 로컬스토리지에서 복원
  useEffect(() => {
    if (typeof window !== "undefined" && user) {
      const stored = localStorage.getItem(`notifications_${user}`);
      if (stored) {
        try {
          setNotifications(JSON.parse(stored));
        } catch (e) {
          console.error("Failed to parse notifications from localStorage", e);
          setNotifications([]);
        }
      } else {
        setNotifications([]);
      }
    } else {
      setNotifications([]);
    }
  }, [user]);

  // 3. 알림 상태 변화 시 로컬스토리지에 동기화 저장
  useEffect(() => {
    if (typeof window !== "undefined" && user) {
      localStorage.setItem(`notifications_${user}`, JSON.stringify(notifications));
    }
  }, [notifications, user]);

  // 4. OS 알림 권한 승인 요청 함수
  const requestOSPermission = async () => {
    if (typeof window === "undefined" || !("Notification" in window)) {
      alert("이 브라우저는 데스크톱 알림을 지원하지 않습니다.");
      return "default";
    }

    try {
      const permission = await Notification.requestPermission();
      setOsPermission(permission);
      return permission;
    } catch (err) {
      console.error("Error requesting notification permission:", err);
      return "default";
    }
  };

  // 4-2. OS 푸시 알림 온오프 설정 토글 함수
  const togglePushEnabled = async () => {
    if (isPushEnabled) {
      setIsPushEnabled(false);
      if (typeof window !== "undefined") {
        localStorage.setItem("os_push_enabled", "false");
      }
    } else {
      if (typeof window !== "undefined" && "Notification" in window) {
        if (Notification.permission !== "granted") {
          const permission = await requestOSPermission();
          if (permission === "granted") {
            setIsPushEnabled(true);
            localStorage.setItem("os_push_enabled", "true");
          }
        } else {
          setIsPushEnabled(true);
          localStorage.setItem("os_push_enabled", "true");
        }
      }
    }
  };

  // 5. 알림 추가 및 OS 데스크톱 배너 띄우기 함수
  const triggerNotification = (title, body, type = "info", taskId = null) => {
    const newNotif = {
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      title,
      message: body,
      type,
      timestamp: new Date().toISOString(),
      read: false,
      task_id: taskId,
    };

    setNotifications((prev) => [newNotif, ...prev].slice(0, 50)); // 최대 50개 유지

    // OS 데스크톱 알림 승인 상태 및 사용자가 푸시를 활성화한 경우 팝업 트리거
    if (isPushEnabled && typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
      try {
        const osNotif = new Notification(title, {
          body: body,
          icon: "/static/favicon.ico", // 아이콘 경로 설정
          tag: newNotif.id,
        });

        osNotif.onclick = () => {
          window.focus();
          // 만약 완료된 분석 작업 ID가 있다면 feature2 페이지 등으로 네비게이션도 고려 가능
          if (taskId) {
            window.location.href = `/feature2?taskId=${taskId}`;
          }
        };
      } catch (err) {
        console.error("Failed to trigger OS Desktop notification:", err);
      }
    }
  };

  // 6. 실시간 SSE 연결 관리 (accessToken 유무에 따라 수명 주기 관리)
  useEffect(() => {
    if (!accessToken || !user) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    const sseUrl = `http://localhost:8000/api/v1/notification/stream?accessToken=${accessToken}`;
    logger("Connecting to centralized SSE notification stream...");
    
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("SSE central notification received:", data);

        // 이벤트 유형에 따른 가공 처리
        if (data.event === "task_completed") {
          triggerNotification(
            "연구 공백 분석 완료",
            `[${data.domain.toUpperCase()}] "${data.query}" 주제의 문헌 비교 분석이 완료되었습니다.`,
            "success",
            data.task_id
          );
        } else if (data.event === "task_failed") {
          triggerNotification(
            "연구 공백 분석 실패",
            `[${data.domain.toUpperCase()}] "${data.query}" 분석 중 에러가 발생했습니다: ${data.error_message || "Unknown error"}`,
            "danger",
            data.task_id
          );
        } else {
          // 기타 일반 이벤트
          triggerNotification(
            data.title || "새로운 알림",
            data.message || "서버로부터 알림이 도착했습니다.",
            data.type || "info",
            data.task_id
          );
        }
      } catch (err) {
        console.error("Failed to parse SSE message content:", err);
      }
    };

    es.onerror = (err) => {
      console.error("Central SSE connection error, retrying...", err);
    };

    return () => {
      logger("Cleaning up SSE connection...");
      es.close();
      if (eventSourceRef.current === es) {
        eventSourceRef.current = null;
      }
    };

    function logger(msg) {
      console.log(`[NotificationContext] ${msg}`);
    }
  }, [accessToken, user]);

  // 7. 유틸리티 제어 메서드
  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const markAsRead = (id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  const value = {
    notifications,
    unreadCount,
    osPermission,
    isPushEnabled,
    togglePushEnabled,
    requestOSPermission,
    markAllAsRead,
    markAsRead,
    clearAll,
    triggerNotification, // 수동 테스트/트리거용
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}
