"use client"

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getGems } from "@/apis/gemsApi";

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

function getPalette(id) {
  let hash = 0;
  for (let i = 0; i < (id || "").length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) & 0xffff;
  }
  return GEM_PALETTES[hash % GEM_PALETTES.length];
}

export default function Feature3Sidebar({ isCollapsed }) {
  const [gems, setGems] = useState([]);
  const router = useRouter();

  const fetchGems = useCallback(() => {
    getGems().then(setGems).catch(() => {});
  }, []);

  useEffect(() => {
    fetchGems();
    window.addEventListener("gems-updated", fetchGems);
    return () => window.removeEventListener("gems-updated", fetchGems);
  }, [fetchGems]);

  if (isCollapsed) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "4px", marginTop: "4px" }}>
      <span style={{ fontSize: "0.68rem", fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "#9ca3af", padding: "0 4px 4px" }}>
        My Gems
      </span>
      {gems.length === 0 ? (
        <span style={{ fontSize: "0.75rem", color: "#9ca3af", padding: "0 4px" }}>None</span>
      ) : (
        gems.map((gem) => (
          <div
            key={gem.gem_id}
            onClick={() => router.push(`/feature3?gemId=${gem.gem_id}`)}
            style={{ display: "flex", alignItems: "center", gap: "8px", padding: "5px 6px", borderRadius: "8px", fontSize: "0.8rem", overflow: "hidden", cursor: "pointer", transition: "background 0.15s" }}
            onMouseEnter={(e) => e.currentTarget.style.background = "rgba(0,0,0,0.06)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
          >
            <div style={{ width: 22, height: 22, borderRadius: "50%", background: getPalette(gem.gem_id), flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.6rem", fontWeight: 700, color: "#fff" }}>
              {gem.name.substring(0, 1).toUpperCase()}
            </div>
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>{gem.name}</span>
          </div>
        ))
      )}
    </div>
  );
}
