"use client"

import ReactMarkdown from "react-markdown";
import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { getMessages, sendMessage, sendMessageStream, createSession, generateTitle } from "@/apis/bioChatApi";
import PaperPanel from "@/components/feature1/PaperPanel";
import styles from "./page.module.css";

/**
 * Chat Hub: 생명공학·천문학·컴퓨터과학 논문 RAG 통합 채팅 페이지입니다.
 *
 * 메시지를 전송하면 RAG 기반 답변과 참고 논문(papers)·검색 출처(sources)를 표시합니다.
 * 참고 논문은 각 답변 아래 "논문 N편" 버튼을 누르면 오른쪽 PaperPanel에 열립니다.
 * 검색 출처는 답변 아래 인라인으로 표시됩니다.
 */
export default function Feature1Page() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams.get("session");

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [panelIndex, setPanelIndex] = useState(null); // 오른쪽 패널에 띄울 메시지 index (null이면 닫힘)
  const [streamStatus, setStreamStatus] = useState(null); // 스트리밍 중 도구 상태: web_search|paper_search|datetime|null

  const scrollRef = useRef(null);
  const textareaRef = useRef(null);
  const sendingRef = useRef(false);
  const isCreatingSessionRef = useRef(false);

  // 대화 영역을 항상 최신 메시지로 스크롤한다.
  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  // 선택된 채팅방이 바뀌면 해당 방의 대화 내역을 불러온다.
  useEffect(() => {
    setPanelIndex(null); // 방이 바뀌면 논문 패널은 닫는다.
    if (!sessionId) {
      setMessages([]);
      return;
    }
    if (isCreatingSessionRef.current) {
      isCreatingSessionRef.current = false;
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
            sources: item.sources || []
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

  // 메시지를 전송한다. 방이 없으면 먼저 새 방을 만들고(질문 내용을 제목으로) 전송한다.
  const handleSend = async () => {
    const text = input.trim();
    if (!text || sendingRef.current) return;
    sendingRef.current = true;
    setIsSending(true);
    setStreamStatus(null); 

    let activeSessionId = sessionId;
    let isNewSession = false;   // ← 새 방인지 표시

    if (!activeSessionId) {
      try {
        const title = text.length > 30 ? text.slice(0, 30) + "…" : text;
        const res = await createSession(title);
        activeSessionId = res.data.session_id;
        isNewSession = true;   // ← 새 방 생성됨
        isCreatingSessionRef.current = true;   // ← 세션 생성 직후 라우트 이동 시 loadHistory 방지
        router.replace(`/feature1?session=${activeSessionId}`);
      } catch (err) {
        console.error("방 생성 실패:", err);
        sendingRef.current = false;
        setIsSending(false);
        return;
      }
    }

    setMessages((prev) => [...prev, { role: "user", content: text, sources: [] }]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    try {
      // 빈 assistant 메시지를 먼저 추가하고, 토큰이 올 때마다 여기에 누적해 타이핑 효과를 낸다.
      setMessages((prev) => [...prev, { role: "assistant", content: "", sources: [] }]);

      await sendMessageStream(activeSessionId, text, (token) => {
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last && last.role === "assistant") {
            next[next.length - 1] = { ...last, content: last.content + token };
          }
          return next;
        });
      },
      (status) => setStreamStatus(status),
    );

      // 스트리밍이 끝나면 검색된 출처(sources)를 다시 불러와 마지막 답변에 붙인다.
      try {
        const res = await getMessages(activeSessionId);
        const history = res.data || [];
        const lastItem = history[history.length - 1];
        if (lastItem && lastItem.role === "assistant" && lastItem.sources?.length) {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === "assistant") {
              next[next.length - 1] = { ...last, sources: lastItem.sources };
            }
            return next;
          });
        }
      } catch (err) {
        console.error("출처 조회 실패:", err);
      }

      // 새 방이면 AI 제목 생성 (실패해도 대화엔 영향 없음)
      if (isNewSession) {
        try {
          await generateTitle(activeSessionId, text);
        } catch (err) {
          console.error("제목 생성 실패:", err);
        }
      }
      window.dispatchEvent(new Event("bio-chat:refresh"));
    } catch (err) {
      // ... 기존 에러 처리
    } finally {
      sendingRef.current = false;
      setIsSending(false);
      setStreamStatus(null); 
    }
  };

  // Enter 전송, Shift+Enter 줄바꿈
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 패널에 띄울 논문(papers) — 선택된 메시지가 AI 답변일 때만 파싱한다.
  const selectedPapers =
    panelIndex !== null ? (messages[panelIndex]?.sources || []) : [];

  // 아직 첫 토큰이 안 온 상태인지 (= 로딩만 보여줄 시점)
  const lastMessage = messages[messages.length - 1];
  const isWaitingFirstToken =
    isSending && (!lastMessage || lastMessage.role !== "assistant" || lastMessage.content === "");

  // 같은 버튼 다시 누르면 닫고, 다른 버튼 누르면 그 메시지로 교체한다.
  const togglePanel = (idx) =>
    setPanelIndex((prev) => (prev === idx ? null : idx));

  // 입력 영역(공통) — 빈 화면과 대화 화면 모두에서 사용
  const inputArea = (
    <div className={styles.inputArea}>
      <div className={styles.inputWrapper}>
        <textarea
          ref={textareaRef}
          className={styles.input}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="생명공학·천문학·컴퓨터공학 논문, 무엇이든 물어보세요…"
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
  );

  // 방이 선택되지 않은 빈 상태 — 가운데 환영 문구 + 하단 입력창(Claude 스타일)
  if (!sessionId) {
    return (
      <div className={styles.chatContainer}>
        <div className={styles.emptyState}>
          <div className={styles.emptyClover}>
            <CloverMark size={56} />
          </div>
          <div className="mono-badge mb-3">
            <i className="bi bi-terminal-fill"></i> console.log("paper_agent")
          </div>
          <h2 className={`fw-bold mb-2 text-gradient ${styles.emptyTitle}`}>
            논문 에이전트
          </h2>
          <p className={styles.emptySubtitle}>
            생명공학·천문학·컴퓨터공학 논문에 대해 무엇이든 물어보세요.
            <br />
            질문하면 새 대화가 자동으로 시작됩니다.
          </p>
        </div>
        {inputArea}
      </div>
    );
  }

  return (
    <div className={styles.layout}>
      <div className={styles.chatContainer}>
        <div className={styles.messageArea} ref={scrollRef}>
          {isLoadingHistory ? (
            <div className={styles.centerHint}>대화를 불러오는 중…</div>
          ) : messages.length === 0 ? (
            <div className={styles.centerHint}>
              <CloverMark size={40} />
              <p className={styles.centerHintText}>
                무엇이든 물어보세요.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <MessageBubble
                key={idx}
                index={idx}
                message={msg}
                isActive={panelIndex === idx}
                onTogglePanel={() => togglePanel(idx)}
              />
            ))
          )}

          {isWaitingFirstToken && <LoadingBubble status={streamStatus}/>}
        </div>

        {inputArea}
      </div>

      <PaperPanel
        open={panelIndex !== null}
        papers={selectedPapers}
        onClose={() => setPanelIndex(null)}
      />
    </div>
  );
}

/**
 * AI 답변의 content를 파싱한다.
 * structured output(JSON 문자열)이면 {explanation, papers}로,
 * 옛날 일반 텍스트면 그대로 explanation에 담아 반환한다(하위 호환).
 */
function parseAnswer(content) {
  if (typeof content !== "string") {
    return { explanation: "", papers: [] };
  }
  const trimmed = content.trim();
  if (trimmed.startsWith("{")) {
    try {
      const parsed = JSON.parse(trimmed);
      return {
        explanation: parsed.explanation ?? "",
        papers: Array.isArray(parsed.papers) ? parsed.papers : [],
      };
    } catch {
      // 파싱 실패 시 일반 텍스트로 폴백
    }
  }
  return { explanation: content, papers: [] };
}

/**
 * 사용자/AI 메시지 말풍선.
 * AI 메시지는 설명(explanation) + "논문 N편" 패널 토글 버튼 + 검색 출처(sources)를 표시한다.
 * 참고 논문 카드 자체는 오른쪽 PaperPanel에서 렌더링한다.
 */
function MessageBubble({ message, index, isActive, onTogglePanel }) {
  const isUser = message.role === "user";

  // 아직 토큰이 안 온 빈 답변 말풍선은 렌더하지 않는다 (로딩은 LoadingBubble이 담당)
  if (!isUser && !message.isError && (message.content ?? "").trim() === "") {
    return null;
  }

  // 설명 텍스트 (AI 답변이 혹시 JSON이면 explanation만 추출, 평문이면 그대로)
  const explanation = isUser ? message.content : parseAnswer(message.content).explanation;

  // 참고 논문 = 실제 검색된 출처(sources). 패널/버튼이 이걸 사용한다.
  const refPapers = !isUser && Array.isArray(message.sources) ? message.sources : [];

  return (
    <div className={`${styles.messageRow} ${isUser ? styles.messageRowUser : ""}`}>
      {!isUser && (
        <div className={styles.aiAvatar}>
          <CloverMark size={20} animated={false} />
        </div>
      )}
      <div className={styles.bubbleGroup}>
        <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAi} ${message.isError ? styles.bubbleError : ""}`}>
          {isUser ? (
            message.content
          ) : (
            <div className={styles.markdown}>
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* 논문 N편 보기 버튼 — 누르면 오른쪽 패널이 열린다 */}
        {refPapers.length > 0 && (
          <button
            className={`${styles.paperTrigger} ${isActive ? styles.paperTriggerActive : ""}`}
            onClick={onTogglePanel}
            aria-pressed={isActive}
          >
            <i className="bi bi-journal-text"></i>
            논문 {refPapers.length}편
            <i className={`bi ${isActive ? "bi-chevron-right" : "bi-chevron-left"} ${styles.paperTriggerChevron}`}></i>
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * 답변 생성 중 표시되는 로딩 말풍선. 클로버 펄스 인디케이터를 포함한다.
 */
function LoadingBubble({ status }) {
  const text =
    status === "web_search" ? "웹 검색 중" :
    status === "paper_search" ? "논문 검색 중" :
    status === "datetime" ? "날짜 확인 중" :
    "답변 생성 중";
  return (
    <div className={styles.messageRow}>
      <div className={styles.aiAvatar}>
        <CloverMark size={20} animated={false} />
      </div>
      <div className={styles.loadingBubble}>
        <div className={styles.cloverLoader}>
          <CloverMark size={28} />
        </div>
        <span className={styles.loadingText}>{text}</span>
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
      aria-label="논문 에이전트"
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