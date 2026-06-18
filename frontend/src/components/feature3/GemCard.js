"use client"

const GEM_PALETTES = [
  { bg: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", light: "#ede9fe" },
  { bg: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", light: "#fce7f3" },
  { bg: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)", light: "#e0f2fe" },
  { bg: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)", light: "#d1fae5" },
  { bg: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", light: "#fef3c7" },
  { bg: "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)", light: "#f3e8ff" },
  { bg: "linear-gradient(135deg, #fda085 0%, #f6d365 100%)", light: "#fff7ed" },
  { bg: "linear-gradient(135deg, #30cfd0 0%, #330867 100%)", light: "#e0e7ff" },
];

function getPalette(id) {
  let hash = 0;
  for (let i = 0; i < (id || "").length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) & 0xffff;
  }
  return GEM_PALETTES[hash % GEM_PALETTES.length];
}

const SOURCE_LABEL = { bio: "Bio", cs: "CS", astronomy: "Astro" };

export default function GemCard({ gem, onSelect, onEdit, onDelete }) {
  const palette = getPalette(gem.gem_id);
  const initials = gem.name.trim().substring(0, 2).toUpperCase();

  return (
    <div
      className="gem-card"
      onClick={() => onSelect(gem)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onSelect(gem)}
    >
      {/* Gradient header with avatar */}
      <div className="gem-card-header" style={{ background: palette.bg }}>
        <div className="gem-avatar">{initials}</div>
        <div className="gem-card-actions">
          <button
            className="gem-action-btn"
            title="Edit"
            onClick={(e) => { e.stopPropagation(); onEdit(gem); }}
          >
            <i className="bi bi-pencil-fill"></i>
          </button>
          <button
            className="gem-action-btn gem-action-btn-danger"
            title="Delete"
            onClick={(e) => { e.stopPropagation(); onDelete(gem.gem_id); }}
          >
            <i className="bi bi-trash-fill"></i>
          </button>
        </div>
      </div>

      {/* Card body */}
      <div className="gem-card-body">
        <h6 className="gem-card-name">{gem.name}</h6>
        <p className="gem-card-desc">{gem.system_prompt}</p>
        <div className="gem-card-sources">
          {(gem.db_sources || []).map((src) => (
            <span key={src} className={`gem-source-tag gem-source-${src}`}>
              {SOURCE_LABEL[src] || src}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
