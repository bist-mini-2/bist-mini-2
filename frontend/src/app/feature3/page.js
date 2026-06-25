"use client"

import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { getGems, createGem, updateGem, deleteGem, uploadGemFiles } from "@/apis/gemsApi";
import GemCard from "@/components/feature3/GemCard";
import GemEditor from "@/components/feature3/GemEditor";
import GemChatPanel from "@/components/feature3/GemChatPanel";
import styles from "./page.module.css";

const THREAD_STORAGE_KEY = "gem_thread_map";

/** localStorage에서 gemId → threadId 맵을 불러옵니다. */
function loadThreadMap() {
  try {
    return JSON.parse(localStorage.getItem(THREAD_STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

/** gemId → threadId 맵을 localStorage에 저장합니다. */
function saveThreadMap(map) {
  try {
    localStorage.setItem(THREAD_STORAGE_KEY, JSON.stringify(map));
  } catch {}
}

/** gemId에 해당하는 threadId를 가져오거나, 없으면 새로 생성해 저장 후 반환합니다. */
function getOrCreateThreadId(gemId) {
  const map = loadThreadMap();
  if (map[gemId]) return map[gemId];
  const tid = `${gemId}_${Date.now()}`;
  map[gemId] = tid;
  saveThreadMap(map);
  return tid;
}

/** 삭제된 gemId의 threadId를 localStorage에서 제거합니다. */
function removeThreadId(gemId) {
  const map = loadThreadMap();
  delete map[gemId];
  saveThreadMap(map);
}

export default function Feature3Page() {
  const [gems, setGems] = useState([]);
  const [listLoading, setListLoading] = useState(true);
  const [error, setError] = useState(null);

  const [view, setView] = useState("store"); // "store" | "editor" | "chat"
  const [editorTarget, setEditorTarget] = useState(null);
  const [selectedGem, setSelectedGem] = useState(null);
  const [threadId, setThreadId] = useState(null);
  const [saving, setSaving] = useState(false);

  // 최신 gems 목록을 searchParams effect에서 참조하기 위한 ref
  const gemsRef = useRef([]);

  const searchParams = useSearchParams();
  const router = useRouter();

  const loadGems = useCallback(async () => {
    setListLoading(true);
    setError(null);
    try {
      const data = await getGems();
      setGems(data);
      gemsRef.current = data;
      return data;
    } catch {
      setError("Gem 목록을 불러오지 못했습니다.");
      return [];
    } finally {
      setListLoading(false);
    }
  }, []);

  // 초기 로드
  useEffect(() => {
    loadGems();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // searchParams(gemId)가 바뀔 때마다 해당 Gem 채팅으로 이동
  useEffect(() => {
    const gemId = searchParams.get("gemId");
    if (!gemId) return;

    const openGem = (data) => {
      const gem = data.find((g) => g.gem_id === gemId);
      if (!gem) return;
      const tid = getOrCreateThreadId(gemId);
      setSelectedGem(gem);
      setThreadId(tid);
      setView("chat");
    };

    if (gemsRef.current.length > 0) {
      openGem(gemsRef.current);
    } else {
      loadGems().then(openGem);
    }
  }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

  const openCreate = () => { setEditorTarget(null); setView("editor"); };
  const openEdit = (gem) => { setEditorTarget(gem); setView("editor"); };

  const openChat = (gem) => {
    // localStorage에서 이전 threadId를 가져오거나 새로 생성 — 페이지 새로고침 후에도 동일 스레드 재사용
    const tid = getOrCreateThreadId(gem.gem_id);
    setSelectedGem(gem);
    setThreadId(tid);
    setView("chat");
    router.replace("/feature3");
  };

  const backToStore = () => {
    setView("store");
    setEditorTarget(null);
    setSelectedGem(null);
    setThreadId(null);
    if (searchParams.get("gemId")) {
      router.replace("/feature3");
    }
  };

  const handleSave = async (payload) => {
    // files는 API로 보내지 않고 별도 업로드
    const { files, ...gemPayload } = payload;
    setSaving(true);
    try {
      if (editorTarget) {
        const updated = await updateGem(editorTarget.gem_id, gemPayload);
        // 파일이 있으면 업로드 후 목록 새로고침 (has_files 반영)
        if (files && files.length > 0) {
          await uploadGemFiles(editorTarget.gem_id, files);
          await loadGems();
        } else {
          setGems((prev) => prev.map((g) => (g.gem_id === updated.gem_id ? updated : g)));
          gemsRef.current = gemsRef.current.map((g) => (g.gem_id === updated.gem_id ? updated : g));
        }
      } else {
        const created = await createGem(gemPayload);
        if (files && files.length > 0) {
          await uploadGemFiles(created.gem_id, files);
          await loadGems();
        } else {
          setGems((prev) => [created, ...prev]);
          gemsRef.current = [created, ...gemsRef.current];
        }
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
      gemsRef.current = gemsRef.current.filter((g) => g.gem_id !== gemId);
      // 삭제된 Gem의 thread 정보도 localStorage에서 제거
      removeThreadId(gemId);
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
