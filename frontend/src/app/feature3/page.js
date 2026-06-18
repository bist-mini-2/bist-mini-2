"use client"

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { getGems, createGem, updateGem, deleteGem } from "@/apis/gemsApi";
import GemCard from "@/components/feature3/GemCard";
import GemEditor from "@/components/feature3/GemEditor";
import GemChatPanel from "@/components/feature3/GemChatPanel";
import styles from "./page.module.css";

export default function Feature3Page() {
  const [gems, setGems] = useState([]);
  const [listLoading, setListLoading] = useState(true);
  const [error, setError] = useState(null);

  const [view, setView] = useState("store"); // "store" | "editor" | "chat"
  const [editorTarget, setEditorTarget] = useState(null);
  const [selectedGem, setSelectedGem] = useState(null);
  const [threadId, setThreadId] = useState(null);
  const [saving, setSaving] = useState(false);

  const searchParams = useSearchParams();
  const router = useRouter();

  const loadGems = useCallback(async () => {
    setListLoading(true);
    setError(null);
    try {
      const data = await getGems();
      setGems(data);
      return data;
    } catch {
      setError("Gem 목록을 불러오지 못했습니다.");
      return [];
    } finally {
      setListLoading(false);
    }
  }, []);

  // On mount: load gems, then check for gemId query param
  useEffect(() => {
    loadGems().then((data) => {
      const gemId = searchParams.get("gemId");
      if (gemId) {
        const gem = data.find((g) => g.gem_id === gemId);
        if (gem) {
          setSelectedGem(gem);
          setThreadId(`${gem.gem_id}_${Date.now()}`);
          setView("chat");
        }
      }
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const openCreate = () => { setEditorTarget(null); setView("editor"); };
  const openEdit = (gem) => { setEditorTarget(gem); setView("editor"); };

  const openChat = (gem) => {
    setSelectedGem(gem);
    setThreadId(`${gem.gem_id}_${Date.now()}`);
    setView("chat");
    router.replace("/feature3");
  };

  const backToStore = () => {
    setView("store");
    setEditorTarget(null);
    setSelectedGem(null);
    setThreadId(null);
    // Only clear URL if there's a gemId query param (coming from sidebar click)
    if (searchParams.get("gemId")) {
      router.replace("/feature3");
    }
  };

  const handleSave = async (payload) => {
    setSaving(true);
    try {
      if (editorTarget) {
        const updated = await updateGem(editorTarget.gem_id, payload);
        setGems((prev) => prev.map((g) => (g.gem_id === updated.gem_id ? updated : g)));
      } else {
        const created = await createGem(payload);
        setGems((prev) => [created, ...prev]);
      }
      window.dispatchEvent(new CustomEvent("gems-updated"));
      backToStore();
    } catch {
      alert(editorTarget ? "Gem 수정에 실패했습니다." : "Gem 생성에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (gemId) => {
    if (!confirm("이 Gem을 삭제하시겠습니까?")) return;
    try {
      await deleteGem(gemId);
      setGems((prev) => prev.filter((g) => g.gem_id !== gemId));
      window.dispatchEvent(new CustomEvent("gems-updated"));
    } catch {
      alert("삭제에 실패했습니다.");
    }
  };

  // Editor view
  if (view === "editor") {
    return (
      <div className={styles.editorView}>
        <GemEditor
          editTarget={editorTarget}
          onSave={handleSave}
          onBack={backToStore}
          loading={saving}
        />
      </div>
    );
  }

  // Chat view
  if (view === "chat" && selectedGem && threadId) {
    return (
      <div className={styles.chatView}>
        <GemChatPanel gem={selectedGem} threadId={threadId} onBack={backToStore} />
      </div>
    );
  }

  // Store view
  return (
    <div className={styles.storeView}>
      <div className={styles.storeHeader}>
        <div>
          <h2 className={styles.storeTitle}>
            <i className="bi bi-gem me-3"></i>Gems
          </h2>
          <p className={styles.storeSubtitle}>
            나만의 AI 연구 비서를 만들어 보세요.
          </p>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className={styles.gemGrid}>
        <div className={styles.createCard} onClick={openCreate} role="button" tabIndex={0}>
          <div className={styles.createCardInner}>
            <div className={styles.createIcon}>
              <i className="bi bi-plus-lg"></i>
            </div>
            <span className={styles.createLabel}>새 Gem 만들기</span>
          </div>
        </div>

        {listLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className={styles.skeletonCard}>
                <div className={styles.skeletonHeader}></div>
                <div className={styles.skeletonBody}>
                  <div className={styles.skeletonLine}></div>
                  <div className={styles.skeletonLineShort}></div>
                </div>
              </div>
            ))
          : gems.map((gem) => (
              <GemCard
                key={gem.gem_id}
                gem={gem}
                onSelect={openChat}
                onEdit={openEdit}
                onDelete={handleDelete}
              />
            ))
        }
      </div>

      {!listLoading && gems.length === 0 && (
        <div className={styles.emptyState}>
          <i className="bi bi-gem"></i>
          <p>아직 만든 Gem이 없습니다.</p>
        </div>
      )}
    </div>
  );
}
