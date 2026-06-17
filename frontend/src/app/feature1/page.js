"use client"

import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { getMessages, sendMessage } from "@/apis/bioChatApi";
import styles from "./page.module.css";

/**
 * 기능 1: 생명공학·유전체학 논문 RAG 채팅 페이지입니다.
 *
 * URL 쿼리파라미터(?session=)로 선택된 채팅방의 대화를 불러오고,
 * 메시지를 전송하면 RAG 기반 답변과 참고 논문(출처)을 표시합니다.
 * 답변 생성 중에는 세이지 그린 네잎클로버 펄스 인디케이터를 보여줍니다.
 */
export default function Feature1Page() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const scrollRef = useRef(null);
  const textareaRef = useRef(null);

  // 대화 영역을 항상 최신 메시지로 스크롤한다.
  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  // 선택된 채팅방이 바뀌면 해당 방의 대화 내역을 불러온다.
  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    const loadHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const res = await getMessages(sessionId);
        if (!cancelled) {
          const history = (res.data || []).map((item) => ({
            role: item.role,
            content: item.content,
            sources: [],
          }));
          setMessages(history);
        }
      } catch (err) {
        console.error("대화 내역 조회 실패:", err);
        if (!cancelled) setMessages([]);
      } finally {
        if (!cancelled) setIsLoadingHistory(false);
      }
    };
    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending, scrollToBottom]);

  // 입력창 높이를 내용에 맞게 자동 조절한다.
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  };

  // 메시지를 전송하고 RAG 답변을 받는다.
  const handleSend = async () => {
    const text = input.trim();
    if (!text || !sessionId || isSending) return;

    setMessages((prev) => [...prev, { role: "user", content: text, sources: [] }]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsSending(true);

    try {
      const res = await sendMessage(sessionId, text);
      const { answer, sources } = res.data;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: answer, sources: sources || [] },
      ]);
      // 사이드바 목록 갱신(첫 메시지로 방 제목/순서가 바뀔 수 있음)
      window.dispatchEvent(new Event("bio-chat:refresh"));
    } catch (err) {
      console.error("메시지 전송 실패:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
          sources: [],
          isError: true,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  // Enter 전송, Shift+Enter 줄바꿈
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 방이 선택되지 않은 빈 상태 화면
  if (!sessionId) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyClover}>
          <CloverMark size={56} />
        </div>
        <div className="mono-badge mb-3">
          <i className="bi bi-terminal-fill"></i> console.log("bio_rag")
        </div>
        <h2 className={`fw-bold mb-2 text-gradient ${styles.emptyTitle}`}>
          생명공학 논문 에이전트
        </h2>
        <p className={styles.emptySubtitle}>
          왼쪽에서 새 채팅을 시작하거나 기존 대화를 선택하세요.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.chatContainer}>
      <div className={styles.messageArea} ref={scrollRef}>
        {isLoadingHistory ? (
          <div className={styles.centerHint}>대화를 불러오는 중…</div>
        ) : messages.length === 0 ? (
          <div className={styles.centerHint}>
            <CloverMark size={40} />
            <p className={styles.centerHintText}>
              유전체학·생명공학에 대해 무엇이든 물어보세요.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))
        )}

        {isSending && <LoadingBubble />}
      </div>

      <div className={styles.inputArea}>
        <div className={styles.inputWrapper}>
          <textarea
            ref={textareaRef}
            className={styles.input}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="유전체 시퀀싱, 유전자 매핑 등 무엇이든 물어보세요…"
            rows={1}
            disabled={isSending}
          />
          <button
            className={styles.sendBtn}
            onClick={handleSend}
            disabled={!input.trim() || isSending}
            aria-label="전송"
          >
            <i className="bi bi-arrow-up"></i>
          </button>
        </div>
        <span className={styles.inputHint}>
          Enter 전송 · Shift+Enter 줄바꿈
        </span>
      </div>
    </div>
  );
}

/**
 * 사용자/AI 메시지 말풍선. AI 메시지에는 참고 논문(출처)을 뱃지로 표시한다.
 */
function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`${styles.messageRow} ${isUser ? styles.messageRowUser : ""}`}>
      {!isUser && (
        <div className={styles.aiAvatar}>
          <CloverMark size={20} animated={false} />
        </div>
      )}
      <div className={styles.bubbleGroup}>
        <div
          className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAi} ${message.isError ? styles.bubbleError : ""}`}
        >
          {message.content}
        </div>
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className={styles.sources}>
            <span className={styles.sourcesLabel}>
              <i className="bi bi-journal-text"></i> 참고 논문
            </span>
            <div className={styles.sourceBadges}>
              {message.sources.map((src, i) => (
                <a
                  key={i}
                  className={styles.sourceBadge}
                  href={`https://arxiv.org/abs/${src.arxiv_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={src.title}
                >
                  <span className={styles.sourceArxiv}>{src.arxiv_id}</span>
                  <span className={styles.sourceTitle}>{src.title}</span>
                  <i className={`bi bi-box-arrow-up-right ${styles.sourceLinkIcon}`}></i>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 답변 생성 중 표시되는 로딩 말풍선. 클로버 펄스 인디케이터를 포함한다.
 */
function LoadingBubble() {
  return (
    <div className={styles.messageRow}>
      <div className={styles.aiAvatar}>
        <CloverMark size={20} animated={false} />
      </div>
      <div className={styles.loadingBubble}>
        <div className={styles.cloverLoader}>
          <CloverMark size={28} />
        </div>
        <span className={styles.loadingText}>답변 생성 중</span>
      </div>
    </div>
  );
}

/**
 * 세이지 그린 네잎클로버 마크.
 *
 * @param {number} size 픽셀 크기
 * @param {boolean} animated true면 펄스+회전 애니메이션, false면 정적 표시
 */
function CloverMark({ size = 44, animated = true }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className={animated ? styles.cloverAnimated : ""}
      role="img"
      aria-label="생명공학 에이전트"
    >
      <g className={styles.cloverShape}>
        <path d="M50 50 C50 30, 30 22, 22 30 C14 38, 22 50, 50 50 Z" fill="var(--accent-color)" />
        <path d="M50 50 C70 50, 78 30, 70 22 C62 14, 50 22, 50 50 Z" fill="var(--accent-color)" />
        <path d="M50 50 C50 70, 70 78, 78 70 C86 62, 78 50, 50 50 Z" fill="var(--accent-color)" />
        <path d="M50 50 C30 50, 22 70, 30 78 C38 86, 50 78, 50 50 Z" fill="var(--accent-color)" />
        <circle cx="50" cy="50" r="6" fill="var(--accent-color)" opacity="0.7" />
      </g>
    </svg>
  );
}