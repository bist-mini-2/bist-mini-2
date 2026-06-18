"use client"

import { useState, useEffect } from "react";

const DB_SOURCE_OPTIONS = [
  { value: "bio", label: "Bio", sub: "q-bio.GN", icon: "bi-activity", color: "#16a34a", bg: "#dcfce7" },
  { value: "cs", label: "CS", sub: "cs.NE", icon: "bi-cpu-fill", color: "#2563eb", bg: "#dbeafe" },
  { value: "astronomy", label: "Astronomy", sub: "astro-ph.EP", icon: "bi-stars", color: "#d97706", bg: "#fef3c7" },
];

export default function GemCreateModal({ show, onClose, onSubmit, loading, editTarget = null }) {
  const isEditMode = editTarget !== null;

  const [name, setName] = useState("");
  const [selectedSources, setSelectedSources] = useState([]);
  const [systemPrompt, setSystemPrompt] = useState("");

  useEffect(() => {
    if (show && isEditMode) {
      setName(editTarget.name);
      setSelectedSources(editTarget.db_sources);
      setSystemPrompt(editTarget.system_prompt);
    } else if (show && !isEditMode) {
      setName("");
      setSelectedSources([]);
      setSystemPrompt("");
    }
  }, [show, editTarget]);

  const toggleSource = (value) => {
    setSelectedSources((prev) =>
      prev.includes(value) ? prev.filter((s) => s !== value) : [...prev, value]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || selectedSources.length === 0 || !systemPrompt.trim()) return;
    await onSubmit({ name: name.trim(), db_sources: selectedSources, system_prompt: systemPrompt.trim() });
    if (!isEditMode) { setName(""); setSelectedSources([]); setSystemPrompt(""); }
  };

  if (!show) return null;

  const isValid = name.trim() && selectedSources.length > 0 && systemPrompt.trim();

  return (
    <div className="gem-modal-backdrop" onClick={onClose}>
      <div className="gem-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="gem-modal-header">
          <div className="d-flex align-items-center gap-3">
            <div className="gem-modal-icon">
              <i className={`bi ${isEditMode ? "bi-pencil-fill" : "bi-gem"}`}></i>
            </div>
            <div>
              <h4 className="gem-modal-title">
                {isEditMode ? "Gem 수정" : "새 Gem 만들기"}
              </h4>
              <p className="gem-modal-subtitle">
                {isEditMode ? "Gem 설정을 변경합니다." : "맞춤형 AI 연구 비서를 만들어 보세요."}
              </p>
            </div>
          </div>
          <button className="gem-modal-close" onClick={onClose}>
            <i className="bi bi-x-lg"></i>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="gem-modal-body">
            {/* Gem name */}
            <div className="gem-form-group">
              <label className="gem-form-label">Gem 이름</label>
              <input
                type="text"
                className="gem-form-input"
                placeholder="예: 유전체학 전문가, CS 논문 요약가..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={100}
                required
              />
            </div>

            {/* Data source selector */}
            <div className="gem-form-group">
              <label className="gem-form-label">
                데이터 소스
                <span className="gem-form-hint">참조할 논문 DB를 선택하세요</span>
              </label>
              <div className="gem-source-grid">
                {DB_SOURCE_OPTIONS.map((opt) => {
                  const active = selectedSources.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      className={`gem-source-option ${active ? "gem-source-option-active" : ""}`}
                      style={active ? { borderColor: opt.color, background: opt.bg } : {}}
                      onClick={() => toggleSource(opt.value)}
                    >
                      <i
                        className={`bi ${opt.icon} gem-source-icon`}
                        style={{ color: active ? opt.color : "#6b7280" }}
                      ></i>
                      <span className="gem-source-name" style={active ? { color: opt.color } : {}}>
                        {opt.label}
                      </span>
                      <span className="gem-source-sub">{opt.sub}</span>
                      {active && (
                        <i
                          className="bi bi-check-circle-fill gem-source-check"
                          style={{ color: opt.color }}
                        ></i>
                      )}
                    </button>
                  );
                })}
              </div>
              {selectedSources.length === 0 && (
                <p className="gem-form-error">최소 1개 이상 선택하세요.</p>
              )}
            </div>

            {/* System prompt */}
            <div className="gem-form-group">
              <label className="gem-form-label">
                페르소나 설정
                <span className="gem-form-hint">이 Gem이 어떻게 답변할지 정의하세요</span>
              </label>
              <textarea
                className="gem-form-textarea"
                placeholder="예: 당신은 유전체학 분야의 전문 연구 비서입니다. 논문을 쉽게 요약하고 핵심 발견을 설명해주세요."
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                rows={4}
                required
              />
            </div>
          </div>

          {/* Footer */}
          <div className="gem-modal-footer">
            <button type="button" className="gem-btn-secondary" onClick={onClose} disabled={loading}>
              취소
            </button>
            <button
              type="submit"
              className={isEditMode ? "gem-btn-edit" : "gem-btn-primary"}
              disabled={loading || !isValid}
            >
              {loading ? (
                <><span className="spinner-border spinner-border-sm me-2"></span>처리 중...</>
              ) : isEditMode ? (
                <><i className="bi bi-check-lg me-2"></i>저장</>
              ) : (
                <><i className="bi bi-gem me-2"></i>Gem 만들기</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
