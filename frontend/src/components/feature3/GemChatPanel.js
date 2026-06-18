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

export default function GemChatPanel({ gem, threadId, onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
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
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const result = await chatWithGem(gem.gem_id, { thread_id: threadId, message: text });
      setMessages((prev) => [...prev, { role: "assistant", content: result.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "오류가 발생했습니다. 잠시 후 다시 시도해주세요." }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const initials = gem.name.trim().substring(0, 2).toUpperCase();

  return (
    <div className="gem-chat-container">
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

      {/* Messages area */}
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
            {messages.map((msg, idx) => (
              <div key={idx} className={`gem-msg gem-msg-${msg.role}`}>
                {msg.role === "assistant" && (
                  <div className="gem-msg-avatar" style={{ background: palette.bg }}>{initials}</div>
                )}
                <div className="gem-msg-bubble">{msg.content}</div>
              </div>
            ))}
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

      {/* Input area */}
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
  );
}
