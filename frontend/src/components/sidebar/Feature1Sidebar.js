"use client"

import { useState, useEffect, useCallback, useRef } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { getSessions, createSession, deleteSession, renameSession } from "@/apis/bioChatApi";
import styles from "./Feature1Sidebar.module.css";

/**
 * 기능 1(생명공학 논문 채팅) 전용 사이드바입니다.
 *
 * 로그인 사용자의 채팅방 목록을 표시하고, 새 채팅방 생성/이름변경/삭제 기능을 제공합니다.
 * 선택된 채팅방은 URL 쿼리파라미터(?session=)로 대화 페이지와 공유합니다.
 * ⋮ 메뉴는 position:fixed로 띄워 목록 스크롤 영역에 잘리지 않으며,
 * 화면 아래 공간이 부족하면 버튼 위쪽으로 펼쳐집니다.
 */
export default function Feature1Sidebar({ isCollapsed }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeSessionId = searchParams.get("session");

  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  const [menuState, setMenuState] = useState(null); // { id, top, left, openUp } | null
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const editInputRef = useRef(null);

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

  useEffect(() => {
    const handleRefresh = () => loadSessions();
    window.addEventListener("bio-chat:refresh", handleRefresh);
    return () => window.removeEventListener("bio-chat:refresh", handleRefresh);
  }, [loadSessions]);

  // 메뉴 바깥 클릭 / 스크롤 / 리사이즈 시 메뉴 닫기
  useEffect(() => {
    if (!menuState) return;
    const close = () => setMenuState(null);
    window.addEventListener("click", close);
    window.addEventListener("resize", close);
    window.addEventListener("scroll", close, true);
    return () => {
      window.removeEventListener("click", close);
      window.removeEventListener("resize", close);
      window.removeEventListener("scroll", close, true);
    };
  }, [menuState]);

  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

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

  const handleSelect = (sessionId) => {
    if (editingId) return;
    router.push(`${pathname}?session=${sessionId}`);
  };

  // ⋮ 버튼 위치를 계산해 드롭다운을 fixed로 띄운다(공간 부족 시 위로).
  const handleMenuToggle = (e, sessionId) => {
    e.stopPropagation();
    if (menuState && menuState.id === sessionId) {
      setMenuState(null);
      return;
    }
    const rect = e.currentTarget.getBoundingClientRect();
    const MENU_HEIGHT = 84;   // 드롭다운 대략 높이
    const MENU_WIDTH = 140;
    const spaceBelow = window.innerHeight - rect.bottom;
    const openUp = spaceBelow < MENU_HEIGHT + 12;
    setMenuState({
      id: sessionId,
      left: Math.min(rect.right - MENU_WIDTH, window.innerWidth - MENU_WIDTH - 8),
      top: openUp ? rect.top - MENU_HEIGHT - 4 : rect.bottom + 4,
    });
  };

  const handleStartEdit = (e, session) => {
    e.stopPropagation();
    setMenuState(null);
    setEditingId(session.session_id);
    setEditValue(session.title);
  };

  const handleSaveEdit = async (sessionId) => {
    const newTitle = editValue.trim();
    const current = sessions.find((s) => s.session_id === sessionId);
    if (!newTitle || (current && current.title === newTitle)) {
      setEditingId(null);
      return;
    }
    setSessions((prev) =>
      prev.map((s) => (s.session_id === sessionId ? { ...s, title: newTitle } : s))
    );
    setEditingId(null);
    try {
      await renameSession(sessionId, newTitle);
    } catch (err) {
      console.error("이름 변경 실패:", err);
      loadSessions();
    }
  };

  const handleEditKeyDown = (e, sessionId) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSaveEdit(sessionId);
    } else if (e.key === "Escape") {
      setEditingId(null);
    }
  };

  const handleDelete = async (e, sessionId) => {
    e.stopPropagation();
    setMenuState(null);
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

  const activeMenuSession = menuState
    ? sessions.find((s) => s.session_id === menuState.id)
    : null;

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
              className={`${styles.sessionItem} ${activeSessionId === session.session_id ? styles.sessionItemActive : ""} ${menuState?.id === session.session_id ? styles.sessionItemMenuOpen : ""}`}
              onClick={() => handleSelect(session.session_id)}
            >
              <i className={`bi bi-chat-left-text ${styles.sessionIcon}`}></i>

              {editingId === session.session_id ? (
                <input
                  ref={editInputRef}
                  className={styles.editInput}
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => handleEditKeyDown(e, session.session_id)}
                  onBlur={() => handleSaveEdit(session.session_id)}
                  onClick={(e) => e.stopPropagation()}
                  maxLength={100}
                />
              ) : (
                <span className={styles.sessionTitle}>{session.title}</span>
              )}

              {editingId !== session.session_id && (
                <button
                  className={styles.menuBtn}
                  onClick={(e) => handleMenuToggle(e, session.session_id)}
                  title="더보기"
                  aria-label="채팅방 메뉴"
                >
                  <i className="bi bi-three-dots-vertical"></i>
                </button>
              )}
            </li>
          ))
        )}
      </ul>

      {/* fixed 드롭다운 — 목록 overflow에 잘리지 않음 */}
      {menuState && activeMenuSession && (
        <div
          className={styles.dropdown}
          style={{ top: menuState.top, left: menuState.left }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className={styles.dropdownItem}
            onClick={(e) => handleStartEdit(e, activeMenuSession)}
          >
            <i className="bi bi-pencil"></i>
            <span>이름 변경</span>
          </button>
          <button
            className={`${styles.dropdownItem} ${styles.dropdownItemDanger}`}
            onClick={(e) => handleDelete(e, activeMenuSession.session_id)}
          >
            <i className="bi bi-trash3"></i>
            <span>삭제</span>
          </button>
        </div>
      )}
    </div>
  );
}