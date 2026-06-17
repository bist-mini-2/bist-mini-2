"use client"

import { useState, useEffect, useCallback } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { getSessions, createSession, deleteSession } from "@/apis/bioChatApi";
import styles from "./Feature1Sidebar.module.css";

/**
 * 기능 1(생명공학 논문 채팅) 전용 사이드바입니다.
 *
 * 로그인 사용자의 채팅방 목록을 표시하고, 새 채팅방 생성/삭제 기능을 제공합니다.
 * 선택된 채팅방은 URL 쿼리파라미터(?session=)로 대화 페이지와 공유합니다.
 * 다른 컴포넌트(페이지)에서 방 생성 후 목록을 갱신할 수 있도록 전역 이벤트(bio-chat:refresh)를 구독합니다.
 */
export default function Feature1Sidebar({ isCollapsed }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeSessionId = searchParams.get("session");

  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  // 채팅방 목록을 서버에서 불러온다.
  const loadSessions = useCallback(async () => {
    try {
      const res = await getSessions();
      setSessions(res.data || []);
    } catch (err) {
      console.error("채팅방 목록 조회 실패:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // 페이지에서 새 메시지로 방이 갱신될 때 목록을 다시 불러오기 위한 이벤트 구독
  useEffect(() => {
    const handleRefresh = () => loadSessions();
    window.addEventListener("bio-chat:refresh", handleRefresh);
    return () => window.removeEventListener("bio-chat:refresh", handleRefresh);
  }, [loadSessions]);

  // 새 채팅방을 생성하고 해당 방으로 이동한다.
  const handleCreate = async () => {
    if (isCreating) return;
    setIsCreating(true);
    try {
      const title = `새 대화 ${new Date().toLocaleString("ko-KR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}`;
      const res = await createSession(title);
      const newSession = res.data;
      setSessions((prev) => [newSession, ...prev]);
      router.push(`${pathname}?session=${newSession.session_id}`);
    } catch (err) {
      console.error("채팅방 생성 실패:", err);
    } finally {
      setIsCreating(false);
    }
  };

  // 채팅방을 선택한다.
  const handleSelect = (sessionId) => {
    router.push(`${pathname}?session=${sessionId}`);
  };

  // 채팅방을 삭제한다. 현재 보고 있는 방이면 선택을 해제한다.
  const handleDelete = async (e, sessionId) => {
    e.stopPropagation();
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (activeSessionId === sessionId) {
        router.push(pathname);
      }
    } catch (err) {
      console.error("채팅방 삭제 실패:", err);
    }
  };

  if (isCollapsed) return null;

  return (
    <div className={styles.container}>
      <button
        className={styles.newChatBtn}
        onClick={handleCreate}
        disabled={isCreating}
      >
        <i className="bi bi-plus-lg"></i>
        <span>새 채팅</span>
      </button>

      <div className={styles.listHeader}>
        <span className={styles.listHeaderLabel}>대화 목록</span>
        <span className={styles.listHeaderCount}>{sessions.length}</span>
      </div>

      <ul className={styles.sessionList}>
        {isLoading ? (
          <li className={styles.emptyHint}>불러오는 중…</li>
        ) : sessions.length === 0 ? (
          <li className={styles.emptyHint}>
            <i className="bi bi-chat-square-dots"></i>
            <span>아직 대화가 없습니다</span>
          </li>
        ) : (
          sessions.map((session) => (
            <li
              key={session.session_id}
              className={`${styles.sessionItem} ${activeSessionId === session.session_id ? styles.sessionItemActive : ""}`}
              onClick={() => handleSelect(session.session_id)}
            >
              <i className={`bi bi-chat-left-text ${styles.sessionIcon}`}></i>
              <span className={styles.sessionTitle}>{session.title}</span>
              <button
                className={styles.deleteBtn}
                onClick={(e) => handleDelete(e, session.session_id)}
                title="삭제"
                aria-label="채팅방 삭제"
              >
                <i className="bi bi-trash3"></i>
              </button>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}