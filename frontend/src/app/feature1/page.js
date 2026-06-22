"use client"

import ReactMarkdown from "react-markdown";
import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { getMessages, sendMessage, sendMessageStream, createSession, generateTitle } from "@/apis/bioChatApi";
import styles from "./page.module.css";

/**
 * Chat Hub: 생명공학·천문학·컴퓨터과학 논문 RAG 통합 채팅 페이지입니다.
 *
 * URL 쿼리파라미터(?session=)로 선택된 채팅방의 대화를 불러오고,
 * 메시지를 전송하면 RAG 기반 답변과 참고 논문(출처)을 표시합니다.
 * 방이 선택되지 않은 상태에서 질문하면 새 방을 자동으로 생성합니다.
 */
export default function Feature1Page() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams.get("session");

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

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
      });

      // 스트리밍이 끝나면 검색된 출처(sources)를 다시 불러와 마지막 답변에 붙인다.
      // (출처는 스트리밍 종료 후 서버 state에 저장되므로 GET /messages로 조회한다)
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
    }
  };

  // Enter 전송, Shift+Enter 줄바꿈
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

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
            <MessageBubble key={idx} message={msg} />
          ))
        )}

        {isSending && <LoadingBubble />}
      </div>

      {inputArea}
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
 * AI 메시지는 설명(explanation) + 논문 카드(papers) + 실제 검색 출처(sources)를 함께 표시한다.
 */
function MessageBubble({ message }) {
  const isUser = message.role === "user";

  // 사용자 메시지는 파싱 없이 그대로, AI 메시지만 파싱
  const { explanation, papers } = isUser
    ? { explanation: message.content, papers: [] }
    : parseAnswer(message.content);

  return (
    <div className={`${styles.messageRow} ${isUser ? styles.messageRowUser : ""}`}>
      {!isUser && (
        <div className={styles.aiAvatar}>
          <CloverMark size={20} animated={false} />
        </div>
      )}
      <div className={styles.bubbleGroup}>
        {/* 설명 말풍선 */}
        <div
          className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAi} ${message.isError ? styles.bubbleError : ""}`}
        >
          {isUser ? (
            message.content
          ) : (
            <div className={styles.markdown}>
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* 논문 카드 (papers) — LLM이 정리한 근거 논문 + 한 줄 요약 */}
        {!isUser && papers.length > 0 && (
          <div className={styles.paperCards}>
            {papers.map((paper, i) => (
              <a
                key={i}
                className={styles.paperCard}
                href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                <div className={styles.paperCardHead}>
                  <i className={`bi bi-file-earmark-text ${styles.paperCardIcon}`}></i>
                  <span className={styles.paperCardTitle}>{paper.title}</span>
                  <i className={`bi bi-box-arrow-up-right ${styles.paperCardLink}`}></i>
                </div>
                <span className={styles.paperCardArxiv}>{paper.arxiv_id}</span>
                {paper.summary && (
                  <p className={styles.paperCardSummary}>{paper.summary}</p>
                )}
              </a>
            ))}
          </div>
        )}

        {/* 실제 검색된 출처 (sources) — 검증 가능한 벡터 검색 결과 */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className={styles.sources}>
            <span className={styles.sourcesLabel}>
              <i className="bi bi-database-check"></i> 검색된 출처
            </span>
            <div className={styles.sourceChips}>
              {message.sources.map((src, i) => (
                <a
                  key={i}
                  className={styles.sourceChip}
                  href={`https://arxiv.org/abs/${src.arxiv_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={src.title}
                >
                  {src.arxiv_id}
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