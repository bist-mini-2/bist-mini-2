"use client"

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { chatWithGemStream, getGemMessages } from "@/apis/gemsApi";

const GEM_PALETTES = [
  { bg: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" },
  { bg: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)" },
  { bg: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)" },
  { bg: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)" },
  { bg: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)" },
  { bg: "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)" },
  { bg: "linear-gradient(135deg, #fda085 0%, #f6d365 100%)" },
  { bg: "linear-gradient(135deg, #30cfd0 0%, #330867 100%)" },
];

function getPalette(id) {
  let hash = 0;
  for (let i = 0; i < (id || "").length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) & 0xffff;
  }
  return GEM_PALETTES[hash % GEM_PALETTES.length];
}

const SOURCE_LABEL = { bio: "Bio", cs: "CS", astronomy: "Astro" };

/** 검색 단계 배지 — 세로로 순서대로 쌓임 */
function SearchSteps({ statuses, hasContent, completed }) {
  const hasPaper = statuses.includes("paper_search");
  const hasFile  = statuses.includes("file_search");

  const steps = [
    hasPaper && {
      key:   "paper_search",
      icon:  "bi-journals",
      label: "논문 검색 중",
      done:  completed || hasFile || hasContent,
    },
    hasFile && {
      key:   "file_search",
      icon:  "bi-file-earmark-text",
      label: "파일 검색 중",
      done:  completed || hasContent,
    },
    (hasContent || completed) && {
      key:   "generating",
      icon:  "bi-pencil",
      label: "답변 작성 중",
      done:  completed,
    },
  ].filter(Boolean);

  if (steps.length === 0) return null;

  return (
    <div className="gem-search-steps">
      {steps.map((step) => (
        <div key={step.key} className={`gem-search-step-row ${step.done ? "gem-step-done" : "gem-step-active"}`}>
          <span className="gem-search-step-indicator">
            {step.done
              ? <i className="bi bi-check-circle-fill"></i>
              : <span className="gem-step-spinner"></span>
            }
          </span>
          <i className={`bi ${step.icon} gem-search-step-type-icon`}></i>
          <span className="gem-search-step-label">{step.label}</span>
        </div>
      ))}
    </div>
  );
}

/** 논문 출처 슬라이드 패널 — 파일/논문 구분 */
function GemPaperPanel({ open, papers, onClose }) {
  const paperSources = papers.filter(p => p.type !== "file");
  const fileSources  = papers.filter(p => p.type === "file");

  return (
    <aside className={`gem-paper-panel${open ? " gem-paper-panel-open" : ""}`}>
      <div className="gem-paper-panel-inner">
        <div className="gem-paper-panel-header">
          <span className="gem-paper-panel-title">
            <i className="bi bi-journal-text"></i> 참고 출처
            {papers.length > 0 && (
              <span className="gem-paper-panel-count">{papers.length}</span>
            )}
          </span>
          <button className="gem-paper-panel-close" onClick={onClose}>
            <i className="bi bi-x-lg"></i>
          </button>
        </div>

        {papers.length === 0 ? (
          <div className="gem-paper-panel-empty">
            <i className="bi bi-journals"></i>
            <p>이 답변에는 참고 출처가 없어요.</p>
          </div>
        ) : (
          <div className="gem-paper-panel-list">
            {/* DB 논문 */}
            {paperSources.length > 0 && (
              <>
                <div className="gem-source-section-label">
                  <i className="bi bi-database me-1"></i>논문 DB
                </div>
                {paperSources.map((paper, i) => (
                  <a
                    key={`paper-${i}`}
                    className="gem-paper-card"
                    href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <div className="gem-paper-card-head">
                      <i className="bi bi-file-earmark-text gem-paper-card-icon"></i>
                      <span className="gem-paper-card-title">{paper.title}</span>
                      <i className="bi bi-box-arrow-up-right gem-paper-card-link"></i>
                    </div>
                    <div className="gem-paper-card-meta">
                      <span className="gem-paper-card-arxiv">{paper.arxiv_id}</span>
                      {paper.score != null && (
                        <span className="gem-source-score-badge">
                          <i className="bi bi-graph-up me-1"></i>
                          유사도 {Math.round(paper.score * 100)}%
                        </span>
                      )}
                    </div>
                    {paper.summary && (
                      <p className="gem-paper-card-summary">{paper.summary}</p>
                    )}
                  </a>
                ))}
              </>
            )}

            {/* 업로드 파일 */}
            {fileSources.length > 0 && (
              <>
                <div className="gem-source-section-label">
                  <i className="bi bi-folder2-open me-1"></i>업로드 파일
                </div>
                {fileSources.map((file, i) => (
                  <div key={`file-${i}`} className="gem-paper-card gem-file-card">
                    <div className="gem-paper-card-head">
                      <i className="bi bi-file-earmark-fill gem-paper-card-icon gem-file-icon"></i>
                      <span className="gem-paper-card-title">{file.title}</span>
                      <span className="gem-file-badge">내 파일</span>
                    </div>
                    {file.score != null && (
                      <div className="gem-source-score-row">
                        <span className="gem-source-score-label">유사도</span>
                        <div className="gem-source-score-bar-wrap">
                          <div
                            className="gem-source-score-bar"
                            style={{ width: `${Math.round(file.score * 100)}%` }}
                          />
                        </div>
                        <span className="gem-source-score-pct">{Math.round(file.score * 100)}%</span>
                      </div>
                    )}
                    {file.summary && (
                      <p className="gem-paper-card-summary">{file.summary}</p>
                    )}
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}

/** AI 메시지 버블 */
function AssistantBubble({ msg, palette, initials, onOpenPapers }) {
  const papers    = msg.papers || [];
  const isStreaming = msg.streaming;
  const isEmpty   = !msg.content;
  const statuses  = msg.statuses || [];

  return (
    <div className="gem-msg gem-msg-assistant">
      <div className="gem-msg-avatar" style={{ background: palette.bg }}>{initials}</div>
      <div className="gem-msg-bubble-wrap">
        {/* 검색 단계 배지 — 스트리밍 중·후 모두 표시 */}
        {statuses.length > 0 && (
          <SearchSteps
            statuses={statuses}
            hasContent={!isEmpty}
            completed={!isStreaming}
          />
        )}

        {isStreaming && isEmpty ? (
          <div className="gem-msg-bubble gem-msg-typing">
            <span></span><span></span><span></span>
          </div>
        ) : (
          <div className="gem-msg-bubble gem-msg-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
          </div>
        )}

        {papers.length > 0 && !isStreaming && (
          <button
            className="gem-msg-papers-btn"
            onClick={() => onOpenPapers(papers)}
          >
            {papers.some(p => p.type === "file") && (
              <i className="bi bi-file-earmark-fill me-1 gem-btn-file-icon"></i>
            )}
            {papers.some(p => p.type !== "file") && (
              <i className="bi bi-journals me-1"></i>
            )}
            출처 {papers.length}건
          </button>
        )}
      </div>
    </div>
  );
}

export default function GemChatPanel({ gem, threadId, onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [panelOpen, setPanelOpen] = useState(false);
  const [panelPapers, setPanelPapers] = useState([]);

  const bottomRef = useRef(null);
  const inputRef  = useRef(null);
  const palette   = getPalette(gem.gem_id);

  useEffect(() => {
    if (!gem || !threadId) return;
    setMessages([]);
    setHistoryLoading(true);
    getGemMessages(gem.gem_id, threadId)
      .then((history) => setMessages(history))
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  }, [gem?.gem_id, threadId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user",      content: text, papers: [], statuses: [] },
      { role: "assistant", content: "",   papers: [], statuses: [], streaming: true },
    ]);
    setLoading(true);

    try {
      await chatWithGemStream(
        gem.gem_id,
        { thread_id: threadId, message: text },
        // onToken
        (token) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant" && last.streaming) {
              updated[updated.length - 1] = { ...last, content: last.content + token };
            }
            return updated;
          });
        },
        // onStatus
        (status) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant" && last.streaming) {
              const statuses = last.statuses || [];
              if (!statuses.includes(status)) {
                updated[updated.length - 1] = { ...last, statuses: [...statuses, status] };
              }
            }
            return updated;
          });
        },
        // onPapers
        (papers) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              updated[updated.length - 1] = { ...last, papers };
            }
            return updated;
          });
        },
      );

      // 스트리밍 완료
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant" && last.streaming) {
          updated[updated.length - 1] = { ...last, streaming: false };
        }
        return updated;
      });
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant" && last.streaming) {
          updated[updated.length - 1] = {
            ...last,
            content: "오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            streaming: false,
          };
        }
        return updated;
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const openPapers = (papers) => {
    setPanelPapers(papers);
    setPanelOpen(true);
  };

  const initials = gem.name.trim().substring(0, 2).toUpperCase();

  return (
    <div className="gem-chat-container" style={{ display: "flex", flexDirection: "row", overflow: "hidden" }}>
      {/* 메인 채팅 영역 */}
      <div className="gem-chat-main" style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Header */}
        <div className="gem-chat-header">
          <button className="gem-back-btn" onClick={onBack} title="Back to Gems">
            <i className="bi bi-arrow-left"></i>
          </button>
          <div className="gem-chat-avatar" style={{ background: palette.bg }}>{initials}</div>
          <div className="gem-chat-info">
            <span className="gem-chat-name">{gem.name}</span>
            <div className="gem-chat-sources">
              {gem.db_sources.map((src) => (
                <span key={src} className="gem-chat-source-tag">{SOURCE_LABEL[src] || src}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="gem-chat-messages">
          {historyLoading ? (
            <div className="gem-chat-empty">
              <span className="spinner-border spinner-border-sm text-muted me-2"></span>
              <span className="text-muted small">대화 내역 불러오는 중...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="gem-chat-empty">
              <div className="gem-chat-welcome-avatar" style={{ background: palette.bg }}>{initials}</div>
              <h5 className="gem-chat-welcome-title">{gem.name}</h5>
              <p className="gem-chat-welcome-desc">{gem.system_prompt}</p>
              <p className="gem-chat-welcome-hint">무엇이든 물어보세요.</p>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) =>
                msg.role === "assistant" ? (
                  <AssistantBubble
                    key={idx}
                    msg={msg}
                    palette={palette}
                    initials={initials}
                    onOpenPapers={openPapers}
                  />
                ) : (
                  <div key={idx} className="gem-msg gem-msg-user">
                    <div className="gem-msg-bubble">{msg.content}</div>
                  </div>
                )
              )}
            </>
          )}
          <div ref={bottomRef}></div>
        </div>

        {/* Input */}
        <div className="gem-chat-input-area">
          <form onSubmit={handleSend} className="gem-chat-form">
            <input
              ref={inputRef}
              type="text"
              className="gem-chat-input"
              placeholder={`${gem.name}에게 질문하기...`}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button
              type="submit"
              className="gem-chat-send-btn"
              disabled={loading || !input.trim()}
              style={{ background: input.trim() && !loading ? palette.bg : undefined }}
            >
              <i className="bi bi-arrow-up-short" style={{ fontSize: "1.3rem" }}></i>
            </button>
          </form>
        </div>
      </div>

      {/* 출처 패널 */}
      <GemPaperPanel
        open={panelOpen}
        papers={panelPapers}
        onClose={() => setPanelOpen(false)}
      />
    </div>
  );
}
