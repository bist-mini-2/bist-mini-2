"use client"

import { useState, useEffect, useRef } from "react";

const DB_SOURCE_OPTIONS = [
  { value: "bio", label: "Bio", sub: "q-bio.GN", icon: "bi-activity", color: "#16a34a" },
  { value: "cs", label: "CS", sub: "cs.NE", icon: "bi-cpu-fill", color: "#2563eb" },
  { value: "astronomy", label: "Astronomy", sub: "astro-ph.EP", icon: "bi-stars", color: "#d97706" },
];

const GEM_PALETTES = [
  "linear-gradient(135deg,#667eea,#764ba2)",
  "linear-gradient(135deg,#f093fb,#f5576c)",
  "linear-gradient(135deg,#4facfe,#00f2fe)",
  "linear-gradient(135deg,#43e97b,#38f9d7)",
  "linear-gradient(135deg,#fa709a,#fee140)",
  "linear-gradient(135deg,#a18cd1,#fbc2eb)",
  "linear-gradient(135deg,#fda085,#f6d365)",
  "linear-gradient(135deg,#30cfd0,#330867)",
];

function hashPalette(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) & 0xffff;
  return GEM_PALETTES[h % GEM_PALETTES.length];
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function GemEditor({ editTarget, onSave, onBack, loading }) {
  const isEdit = editTarget !== null;

  const [name, setName] = useState("");
  const [selectedSources, setSelectedSources] = useState([]);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [files, setFiles] = useState([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isEdit && editTarget) {
      setName(editTarget.name || "");
      setSelectedSources(editTarget.db_sources || []);
      setSystemPrompt(editTarget.system_prompt || "");
      setFiles([]);
    } else {
      setName("");
      setSelectedSources([]);
      setSystemPrompt("");
      setFiles([]);
    }
  }, [editTarget]);

  const toggleSource = (val) =>
    setSelectedSources((prev) =>
      prev.includes(val) ? prev.filter((s) => s !== val) : [...prev, val]
    );

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files);
    setFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const newFiles = selected.filter((f) => !existingNames.has(f.name));
      return [...prev, ...newFiles];
    });
    e.target.value = "";
  };

  const removeFile = (fileName) => {
    setFiles((prev) => prev.filter((f) => f.name !== fileName));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files);
    setFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const newFiles = dropped.filter((f) => !existingNames.has(f.name));
      return [...prev, ...newFiles];
    });
  };

  const handleSave = () => {
    if (!name.trim() || selectedSources.length === 0 || !systemPrompt.trim()) return;
    onSave({ name: name.trim(), db_sources: selectedSources, system_prompt: systemPrompt.trim(), files });
  };

  const initials = name.trim() ? name.trim().substring(0, 2).toUpperCase() : "";
  const previewBg = name.trim() ? hashPalette(name) : "";
  const isValid = name.trim() && selectedSources.length > 0 && systemPrompt.trim();

  return (
    <div className="gem-editor">
      {/* Top bar — 저장 버튼 없이 뒤로가기 + 제목만 */}
      <div className="gem-editor-topbar">
        <button className="gem-editor-back-btn" onClick={onBack}>
          <i className="bi bi-arrow-left"></i>
        </button>
        <div className="gem-editor-topbar-mid">
          <div className="gem-editor-topbar-icon">
            <i className="bi bi-gem"></i>
          </div>
          <span className="gem-editor-topbar-name">{name || (isEdit ? editTarget?.name : "새 Gem")}</span>
        </div>
        {/* 저장 버튼 자리 — 빈 공간으로 레이아웃 균형 유지 */}
        <div style={{ width: "56px" }} />
      </div>

      {/* Body: left form + right preview */}
      <div className="gem-editor-body">
        {/* Left panel: form */}
        <div className="gem-editor-left">
          {/* Name */}
          <div className="gem-editor-field">
            <label className="gem-editor-label">이름</label>
            <input
              type="text"
              className="gem-editor-input"
              placeholder="Gem의 이름을 지정하세요."
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={100}
            />
          </div>

          {/* Instructions */}
          <div className="gem-editor-field">
            <label className="gem-editor-label">
              요청 사항
              <i className="bi bi-info-circle gem-editor-info" title="이 Gem이 어떻게 동작할지 정의합니다."></i>
            </label>
            <textarea
              className="gem-editor-textarea"
              placeholder="예: 당신은 유전체학 전문 연구 비서입니다. 논문을 쉽게 요약하고 핵심 발견을 설명해주세요."
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={7}
            />
          </div>

          {/* Data source */}
          <div className="gem-editor-field">
            <label className="gem-editor-label">
              데이터 소스
              <i className="bi bi-info-circle gem-editor-info" title="Gem이 참조할 논문 데이터베이스를 선택합니다."></i>
            </label>
            <div className="gem-editor-source-list">
              {DB_SOURCE_OPTIONS.map((opt) => {
                const active = selectedSources.includes(opt.value);
                return (
                  <label
                    key={opt.value}
                    className={`gem-editor-source-row${active ? " gem-editor-source-row-active" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => toggleSource(opt.value)}
                      style={{ display: "none" }}
                    />
                    <i className={`bi ${opt.icon} gem-editor-source-icon`} style={active ? { color: opt.color } : {}}></i>
                    <div className="gem-editor-source-text">
                      <span className="gem-editor-source-name">{opt.label}</span>
                      <span className="gem-editor-source-sub">{opt.sub}</span>
                    </div>
                    {active
                      ? <i className="bi bi-check-circle-fill gem-editor-check" style={{ color: opt.color }}></i>
                      : <i className="bi bi-circle gem-editor-check" style={{ color: "#d1d5db" }}></i>
                    }
                  </label>
                );
              })}
            </div>
          </div>

          {/* File upload */}
          <div className="gem-editor-field">
            <label className="gem-editor-label">
              파일
              <i className="bi bi-info-circle gem-editor-info" title="Gem이 참조할 파일을 추가합니다."></i>
            </label>

            {files.length > 0 && (
              <div className="gem-editor-file-list">
                {files.map((file) => (
                  <div key={file.name} className="gem-editor-file-row">
                    <i className="bi bi-file-earmark-text gem-editor-file-icon"></i>
                    <div className="gem-editor-file-info">
                      <span className="gem-editor-file-name">{file.name}</span>
                      <span className="gem-editor-file-size">{formatFileSize(file.size)}</span>
                    </div>
                    <button
                      type="button"
                      className="gem-editor-file-remove"
                      onClick={() => removeFile(file.name)}
                      title="파일 제거"
                    >
                      <i className="bi bi-x"></i>
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div
              className="gem-editor-dropzone"
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
            >
              <i className="bi bi-cloud-upload gem-editor-dropzone-icon"></i>
              <span className="gem-editor-dropzone-text">파일을 드래그하거나 클릭하여 추가</span>
              <span className="gem-editor-dropzone-hint">PDF, TXT, DOCX 등 지원</span>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              style={{ display: "none" }}
              onChange={handleFileChange}
              accept=".pdf,.txt,.docx,.doc,.md,.csv"
            />
          </div>

          {/* Save button — 파일 추가 섹션 아래 중앙 */}
          <div className="gem-editor-save-row">
            <button
              className="gem-editor-save-btn-bottom"
              onClick={handleSave}
              disabled={loading || !isValid}
            >
              {loading ? (
                <><span className="spinner-border spinner-border-sm me-2"></span>저장 중...</>
              ) : isEdit ? (
                <><i className="bi bi-check-lg me-2"></i>저장</>
              ) : (
                <><i className="bi bi-gem me-2"></i>Gem 만들기</>
              )}
            </button>
          </div>
        </div>

        {/* Right panel: preview */}
        <div className="gem-editor-right">
          <span className="gem-editor-preview-label">미리보기</span>
          {!name.trim() ? (
            <div className="gem-editor-preview-empty">
              <div className="gem-editor-preview-empty-icon">
                <i className="bi bi-gem"></i>
              </div>
              <p>Gem을 미리 보려면 먼저 이름을 지어 주세요.</p>
            </div>
          ) : (
            <div className="gem-editor-preview-card">
              <div className="gem-editor-preview-avatar" style={{ background: previewBg }}>
                {initials}
              </div>
              <h5 className="gem-editor-preview-name">{name}</h5>
              {systemPrompt && (
                <p className="gem-editor-preview-prompt">{systemPrompt}</p>
              )}
              <div className="gem-editor-preview-sources">
                {selectedSources.map((src) => (
                  <span key={src} className={`gem-source-tag gem-source-${src}`}>{src}</span>
                ))}
              </div>
              {files.length > 0 && (
                <div className="gem-editor-preview-files">
                  <i className="bi bi-paperclip"></i>
                  <span>{files.length}개 파일 첨부됨</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
