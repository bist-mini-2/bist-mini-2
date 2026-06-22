"use client"

import { useState, useEffect, useRef } from "react";
import { chatWithGem, getGemMessages } from "@/apis/gemsApi";

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

/** 논문 출처 슬라이드 패널 */
function GemPaperPanel({ open, papers, onClose }) {
  return (
    <aside className={`gem-paper-panel${open ? " gem-paper-panel-open" : ""}`}>
      <div className="gem-paper-panel-inner">
        <div className="gem-paper-panel-header">
          <span className="gem-paper-panel-title">
            <i className="bi bi-journal-text"></i> 참고 논문
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
            <p>이 답변에는 참고 논문이 없어요.</p>
          </div>
        ) : (
          <div className="gem-paper-panel-list">
            {papers.map((paper, i) => (
              <a
                key={i}
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
                <span className="gem-paper-card-arxiv">{paper.arxiv_id}</span>
                {paper.summary && (
                  <p className="gem-paper-card-summary">{paper.summary}</p>
                )}
              </a>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

/** AI 메시지 버블 — 논문 버튼 포함 */
function AssistantBubble({ msg, palette, initials, onOpenPapers }) {
  const papers = msg.papers || [];
  return (
    <div className="gem-msg gem-msg-assistant">
      <div className="gem-msg-avatar" style={{ background: palette.bg }}>{initials}</div>
      <div className="gem-msg-bubble-wrap">
        <div className="gem-msg-bubble">{msg.content}</div>
        {papers.length > 0 && (
          <button
            className="gem-msg-papers-btn"
            onClick={() => onOpenPapers(papers)}
          >
            <i className="bi bi-journals me-1"></i>
            논문 {papers.length}편
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

  // 논문 패널 상태
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelPapers, setPanelPapers] = useState([]);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const palette = getPalette(gem.gem_id);

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
    setMessages((prev) => [...prev, { role: "user", content: text, papers: [] }]);
    setLoading(true);
    try {
      const result = await chatWithGem(gem.gem_id, { thread_id: threadId, message: text });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, papers: result.papers || [] },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "오류가 발생했습니다. 잠시 후 다시 시도해주세요.", papers: [] },
      ]);
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
              {loading && (
                <div className="gem-msg gem-msg-assistant">
                  <div className="gem-msg-avatar" style={{ background: palette.bg }}>{initials}</div>
                  <div className="gem-msg-bubble gem-msg-typing">
                    <span></span><span></span><span></span>
                  </div>
                </div>
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

      {/* 논문 패널 */}
      <GemPaperPanel
        open={panelOpen}
        papers={panelPapers}
        onClose={() => setPanelOpen(false)}
      />
    </div>
  );
}
