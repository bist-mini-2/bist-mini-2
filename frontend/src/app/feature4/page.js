"use client"

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getDefenseHistoryList, deleteDefenseSession } from "@/apis/defenseArena";
import styles from "./page.module.css";
import LoadingSpinner from "@/components/loading-spinner/LoadingSpinner";
import DeleteConfirmModal from "@/components/feature2/DeleteConfirmModal";

/**
 * 피어리뷰 및 디펜스 아레나 세션 이력 보관함 페이지입니다.
 */
export default function DefenseHistoryInboxPage() {
  const router = useRouter();

  const [historyList, setHistoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedSessionIds, setSelectedSessionIds] = useState([]);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [deletingIds, setDeletingIds] = useState([]);
  const [isExiting, setIsExiting] = useState(false);

  // 이력 데이터 로드
  const loadHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getDefenseHistoryList();
      if (response.status === "success" && response.data) {
        setHistoryList(response.data);
      } else {
        setError("디펜스 이력 목록을 불러오는 데 실패했습니다.");
      }
    } catch (err) {
      console.error("Failed to load defense history list:", err);
      setError("서버와의 연결이 원활하지 않습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // 편집 모드 토글
  const toggleEditMode = () => {
    setIsEditMode((prev) => {
      if (prev) {
        setSelectedSessionIds([]);
      }
      return !prev;
    });
  };

  // 개별 체크박스 토글
  const handleCheckboxChange = (sessionId) => {
    setSelectedSessionIds((prev) => {
      if (prev.includes(sessionId)) {
        return prev.filter((id) => id !== sessionId);
      } else {
        return [...prev, sessionId];
      }
    });
  };

  // 전체 선택 체크박스 토글
  const handleSelectAllChange = (e) => {
    if (e.target.checked) {
      const allIds = historyList.map((item) => item.session_id);
      setSelectedSessionIds(allIds);
    } else {
      setSelectedSessionIds([]);
    }
  };

  // 행 클릭 핸들러 (편집 모드 시 체크박스 토글, 일반 모드 시 디펜스 아레나 상세 복원 페이지 이동)
  const handleRowClick = (item, e) => {
    if (e.target.type === "checkbox" || e.target.closest(`.${styles.historyDeleteBtn}`)) {
      return;
    }
    if (isEditMode) {
      handleCheckboxChange(item.session_id);
    } else {
      setIsExiting(true);
      setTimeout(() => {
        router.push(`/feature4/arena?sessionId=${item.session_id}`);
      }, 500);
    }
  };

  // 선택 삭제 모달 호출
  const handleBulkDelete = () => {
    if (selectedSessionIds.length === 0) return;
    setShowConfirmModal(true);
  };

  // 선택 삭제 실제 처리 실행 (병렬 API 호출)
  const handleBulkDeleteConfirm = async () => {
    setShowConfirmModal(false);
    try {
      setDeletingIds(selectedSessionIds);
      // 백엔드 delete API 병렬 일괄 실행
      await Promise.all(selectedSessionIds.map(id => deleteDefenseSession(id)));
      
      setTimeout(() => {
        setHistoryList((prev) => prev.filter((s) => !selectedSessionIds.includes(s.session_id)));
        setSelectedSessionIds([]);
        setDeletingIds([]);
        setIsEditMode(false);
      }, 400);
    } catch (err) {
      console.error("Failed to delete sessions:", err);
      setError("일부 세션을 삭제하지 못했습니다. 다시 시도해 주십시오.");
      loadHistory();
    }
  };

  // 날짜 포맷 유틸
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString("ko-KR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      });
    } catch (e) {
      return dateString;
    }
  };

  if (loading) {
    return <LoadingSpinner message="디펜스 세션 보관함을 불러오는 중..." />;
  }

  return (
    <div className={`${styles.container} ${isExiting ? styles.pageExiting : ""}`} style={{ maxWidth: "1200px" }}>
      
      {/* Page Header (Matching Feature 2 style) */}
      <div className="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
        <div>
          <h3 className="fw-bold text-gradient mb-1">디펜스 세션 보관함</h3>
          <p className="text-secondary small mb-0">보안 격리 구역에서 분석했던 피어리뷰 리포트 및 모의 디펜스 세션 보관 목록입니다.</p>
        </div>
        <div className="d-flex align-items-center gap-2">
          {historyList.length > 0 && (
            <>
              {isEditMode ? (
                <>
                  <button
                    onClick={handleBulkDelete}
                    className={`btn btn-sm btn-danger rounded-3 py-1.5 fw-bold ${styles.bulkDeleteBtn}`}
                    disabled={selectedSessionIds.length === 0}
                  >
                    <span className={styles.btnLeftArea}>
                      <i className="bi bi-trash-fill"></i> 선택 삭제
                    </span>
                    <span className={styles.btnRightArea}>
                      ({selectedSessionIds.length})
                    </span>
                  </button>
                  <button
                    onClick={toggleEditMode}
                    className="btn btn-sm btn-outline-secondary rounded-3 px-3 py-1.5"
                  >
                    취소
                  </button>
                </>
              ) : (
                <button
                  onClick={toggleEditMode}
                  className="btn btn-sm btn-outline-secondary rounded-3 px-3 py-1.5 d-flex align-items-center gap-1"
                >
                  <i className="bi bi-pencil-square"></i> 선택 삭제
                </button>
              )}
            </>
          )}
          <Link href="/feature4/arena" className={`btn btn-sm d-flex align-items-center gap-1 rounded-3 py-1.5 px-3 ${styles.outlineBtn}`}>
            <i className="bi bi-plus-circle"></i> 새 디펜스 실행
          </Link>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger border-0 shadow-sm d-flex align-items-center gap-2 rounded-3 mb-4" role="alert">
          <i className="bi bi-exclamation-triangle-fill"></i>
          <div>{error}</div>
        </div>
      )}

      {/* History Grid/Table (Matching Feature 2) */}
      {historyList.length > 0 ? (
        <div className="card shadow-sm border border-light-subtle rounded-3 overflow-hidden">
          <div className="table-responsive">
            <table className={`table table-hover align-middle mb-0 ${styles.historyTable}`}>
              <thead className="table-light">
                <tr className={styles.tableHeader}>
                  <th className={`${styles.colCheck} ${isEditMode ? styles.colCheckActive : ""}`}>
                    <div className={styles.checkboxWrapper}>
                      <input
                        type="checkbox"
                        className={styles.customCheckbox}
                        onChange={handleSelectAllChange}
                        checked={historyList.length > 0 && selectedSessionIds.length === historyList.length}
                      />
                    </div>
                  </th>
                  <th className={`px-4 py-3 ${styles.colFileName}`}>학술 문서 파일명</th>
                  <th className={`py-3 ${styles.colBadges}`}>진행 결과 배지</th>
                  <th className={`py-3 ${styles.colSecureStatus}`}>보안 상태</th>
                  <th className={`py-3 ${styles.colTime}`}>분석 요청 시간</th>
                </tr>
              </thead>
              <tbody>
                {historyList.map((item) => {
                  const isSelected = selectedSessionIds.includes(item.session_id);
                  const isDeleting = deletingIds.includes(item.session_id);
                  return (
                    <tr
                      key={item.session_id}
                      onClick={(e) => handleRowClick(item, e)}
                      className={`${styles.tableRowClickable} ${isSelected ? styles.rowSelected : ""} ${isDeleting ? styles.tableRowDeleting : ""}`}
                    >
                      <td className={`${styles.colCheckCell} ${isEditMode ? styles.colCheckCellActive : ""}`}>
                        <div className={styles.checkboxWrapper}>
                          <input
                            type="checkbox"
                            className={styles.customCheckbox}
                            checked={isSelected}
                            onChange={() => handleCheckboxChange(item.session_id)}
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3 fw-semibold">
                        <span className="d-flex align-items-center gap-2">
                          <i className={`bi ${item.file_name.toLowerCase().endsWith(".pdf") ? "bi-file-earmark-pdf-fill text-danger fs-5" : "bi-file-earmark-text-fill text-secondary fs-5"}`}></i>
                          <div className="text-truncate" style={{ maxWidth: "350px" }} title={item.file_name}>
                            {item.file_name}
                          </div>
                        </span>
                      </td>
                      <td className="py-3">
                        <div className="d-flex flex-wrap gap-1">
                          {item.has_peer_review && (
                            <span className="badge bg-success-subtle text-success fs-8">Peer Review</span>
                          )}
                          {item.has_hypothesis && (
                            <span className="badge bg-info-subtle text-info fs-8">Hypothesis</span>
                          )}
                          {item.has_defense && (
                            <span className="badge bg-warning-subtle text-warning fs-8">
                              Defense {item.defense_score !== null ? `(${item.defense_score.toFixed(0)}점)` : ""}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3">
                        {item.is_expired ? (
                          <span className="badge bg-light text-secondary border border-secondary-subtle fs-8">
                            임베딩 파쇄됨
                          </span>
                        ) : (
                          <span className="badge bg-success-subtle text-success fs-8">
                            보안 샌드박스 활성
                          </span>
                        )}
                      </td>
                      <td className="py-3 text-secondary small">
                        <i className="bi bi-clock me-1.5"></i>
                        {formatDate(item.created_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card shadow-sm border border-light-subtle rounded-3 p-5 text-center text-muted">
          <div className="py-5">
            <i className="bi bi-archive fs-1 mb-3 d-block text-secondary"></i>
            <h5 className="fw-bold mb-2">과거 디펜스 이력이 없습니다.</h5>
            <p className="small text-secondary mb-4">보안 격리 구역에서 논문의 취약성을 진단하고 심사위원 압박 모의 디펜스를 기동해 보세요.</p>
            <Link href="/feature4/arena" className={`btn rounded-3 px-4 py-2 ${styles.solidBtn}`}>
              첫 디펜스 실행하기
            </Link>
          </div>
        </div>
      )}

      {/* 삭제 확인 모달 */}
      {showConfirmModal && (
        <DeleteConfirmModal
          selectedCount={selectedSessionIds.length}
          onCancel={() => setShowConfirmModal(false)}
          onConfirm={handleBulkDeleteConfirm}
        />
      )}
    </div>
  );
}
