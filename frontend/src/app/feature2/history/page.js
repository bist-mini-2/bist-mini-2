"use client"

import { useState, useEffect, useContext } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "./page.module.css";
import { listUserTasks, bulkDeleteTasks } from "@/apis/researchGap";
import { AuthContext } from "@/contexts/AuthContext";
import StatusBadge from "@/components/StatusBadge";

/**
 * 대규모 문헌 비교 분석기 작업 이력 페이지입니다.
 */
export default function ResearchGapHistoryPage() {
  const { accessToken } = useContext(AuthContext);
  const router = useRouter();

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedTaskIds, setSelectedTaskIds] = useState([]);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [deletingIds, setDeletingIds] = useState([]);

  // 마운트 여부 설정 (Portal용)
  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // 이력 로드
  useEffect(() => {
    async function loadHistory() {
      if (!accessToken) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const res = await listUserTasks();
        if (res.status === "success") {
          setTasks(res.data || []);
        } else {
          setError("작업 이력을 불러오지 못했습니다.");
        }
      } catch (err) {
        console.error("Failed to load history:", err);
        setError("서버와의 연결이 원활하지 않습니다.");
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, [accessToken]);

  // 실시간 작업 상태 폴링 (PENDING 또는 RUNNING 상태인 작업이 있을 경우 2초 간격 폴링)
  useEffect(() => {
    if (!accessToken) return;

    const hasActiveTask = tasks.some(
      (task) => task.status === "PENDING" || task.status === "RUNNING"
    );

    if (!hasActiveTask) return;

    const intervalId = setInterval(async () => {
      try {
        const res = await listUserTasks();
        if (res.status === "success") {
          setTasks(res.data || []);
        }
      } catch (err) {
        console.error("Failed to poll task history:", err);
      }
    }, 2000);

    return () => clearInterval(intervalId);
  }, [tasks, accessToken]);

  // 상태 뱃지 렌더링 헬퍼
  const renderStatusBadge = (status, progress) => {
    return <StatusBadge status={status} progress={progress} lang="ko" />;
  };

  // 날짜 포맷 헬퍼
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

  // 편집 모드 토글
  const toggleEditMode = () => {
    setIsEditMode((prev) => {
      if (prev) {
        setSelectedTaskIds([]);
      }
      return !prev;
    });
  };

  // 개별 체크박스 토글
  const handleCheckboxChange = (taskId) => {
    setSelectedTaskIds((prev) => {
      if (prev.includes(taskId)) {
        return prev.filter((id) => id !== taskId);
      } else {
        return [...prev, taskId];
      }
    });
  };

  // 전체 선택 체크박스 토글
  const handleSelectAllChange = (e) => {
    if (e.target.checked) {
      const allIds = tasks.map((t) => t.task_id);
      setSelectedTaskIds(allIds);
    } else {
      setSelectedTaskIds([]);
    }
  };

  // 행 클릭 핸들러 (편집 모드 시 체크박스 토글, 일반 모드 시 결과 페이지 이동)
  const handleRowClick = (task, e) => {
    if (e.target.type === "checkbox") {
      return;
    }
    if (isEditMode) {
      handleCheckboxChange(task.task_id);
    } else {
      router.push(`/feature2?taskId=${task.task_id}`);
    }
  };

  // 선택 삭제 실행 핸들러
  const handleBulkDelete = () => {
    if (selectedTaskIds.length === 0) return;
    setShowConfirmModal(true);
  };

  // 실제 선택 삭제 확인 핸들러
  const handleBulkDeleteConfirm = async () => {
    setShowConfirmModal(false);
    try {
      const res = await bulkDeleteTasks(selectedTaskIds);
      if (res.status === "success") {
        setDeletingIds(selectedTaskIds);
        setTimeout(() => {
          setTasks((prev) => prev.filter((t) => !selectedTaskIds.includes(t.task_id)));
          setSelectedTaskIds([]);
          setDeletingIds([]);
          setIsEditMode(false);
        }, 400);
      } else {
        setError("선택 이력 삭제에 실패했습니다.");
      }
    } catch (err) {
      console.error("Failed to delete tasks:", err);
      setError("삭제 중 오류가 발생했습니다.");
    }
  };

  if (loading) {
    return (
      <div className="d-flex flex-column align-items-center justify-content-center min-vh-50 p-5 text-muted">
        <div className="spinner-border text-success mb-3" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <span>분석 이력 데이터를 불러오는 중...</span>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Page Header */}
      <div className="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
        <div>
          <h3 className="fw-bold text-gradient mb-1">분석 보고서 이력</h3>
          <p className="text-secondary small mb-0">지금까지 요청하신 대규모 문헌 비교 분석 및 AI Research Gap 보고서 목록입니다.</p>
        </div>
        <div className="d-flex align-items-center gap-2">
          {tasks.length > 0 && (
            <>
              {isEditMode ? (
                <>
                  <button
                    onClick={handleBulkDelete}
                    className={`btn btn-sm btn-danger rounded-3 py-1.5 fw-bold ${styles.bulkDeleteBtn}`}
                    disabled={selectedTaskIds.length === 0}
                  >
                    <span className={styles.btnLeftArea}>
                      <i className="bi bi-trash-fill"></i> 선택 삭제
                    </span>
                    <span className={styles.btnRightArea}>
                      ({selectedTaskIds.length})
                    </span>
                  </button>
                  <button
                    onClick={toggleEditMode}
                    className={`btn btn-sm rounded-3 px-3 py-1.5 d-flex align-items-center gap-1 ${styles.outlineSecBtn}`}
                  >
                    취소
                  </button>
                </>
              ) : (
                <button
                  onClick={toggleEditMode}
                  className={`btn btn-sm rounded-3 px-3 py-1.5 d-flex align-items-center gap-1 ${styles.outlineSecBtn}`}
                >
                  <i className="bi bi-pencil-square"></i> 선택 삭제
                </button>
              )}
            </>
          )}
          <Link href="/feature2" className={`btn btn-sm d-flex align-items-center gap-1 rounded-3 py-1.5 px-3 ${styles.outlineBtn}`}>
            <i className="bi bi-plus-circle"></i> 새 분석 요청
          </Link>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger border-0 shadow-sm d-flex align-items-center gap-2 rounded-3 mb-4" role="alert">
          <i className="bi bi-exclamation-triangle-fill"></i>
          <div>{error}</div>
        </div>
      )}

      {/* Task List Grid/Table */}
      {tasks.length > 0 ? (
        <div className="card shadow-sm border border-light-subtle rounded-3 overflow-hidden">
          <div className="table-responsive">
            <table className={`table table-hover align-middle mb-0 ${styles.historyTable}`}>
              <thead className={`text-secondary ${styles.tableHeader}`}>
                <tr>
                  <th className={`${styles.colCheck} ${isEditMode ? styles.colCheckActive : ""}`}>
                    <div className={styles.checkboxWrapper}>
                      <input
                        type="checkbox"
                        className={`${styles.customCheckbox} cursor-pointer`}
                        onChange={handleSelectAllChange}
                        checked={tasks.length > 0 && selectedTaskIds.length === tasks.length}
                      />
                    </div>
                  </th>
                  <th className={`px-4 py-3 ${styles.colDomain}`}>학술 도메인</th>
                  <th className={`py-3 ${styles.colQuery}`}>분석 대상 주제 / 키워드</th>
                  <th className={`py-3 ${styles.colStatus}`}>상태</th>
                  <th className={`py-3 ${styles.colTime}`}>요청 시간</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => {
                  const isSelected = selectedTaskIds.includes(task.task_id);
                  const isDeleting = deletingIds.includes(task.task_id);
                  return (
                    <tr
                      key={task.task_id}
                      onClick={(e) => handleRowClick(task, e)}
                      className={`${styles.tableRowClickable} ${isSelected ? styles.rowSelected : ""} ${isDeleting ? styles.tableRowDeleting : ""}`}
                    >
                      <td
                        className={`${styles.colCheckCell} ${isEditMode ? styles.colCheckCellActive : ""}`}
                      >
                        <div className={styles.checkboxWrapper}>
                          <input
                            type="checkbox"
                            className={`${styles.customCheckbox} cursor-pointer`}
                            checked={isSelected}
                            onChange={() => handleCheckboxChange(task.task_id)}
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`badge px-2.5 py-1.5 rounded-pill ${styles.domainBadge} ${task.domain === "cs" ? styles.domainCs : styles.domainBio}`}
                        >
                          {task.domain}
                        </span>
                      </td>
                      <td className="py-3 fw-semibold">
                        <div className={`text-truncate ${styles.queryText}`} title={task.query}>
                          {task.query}
                        </div>
                      </td>
                      <td className="py-3">
                        {renderStatusBadge(task.status, task.progress)}
                      </td>
                      <td className="py-3 text-secondary small">
                        <i className="bi bi-clock me-1.5"></i>{" "}
                        {formatDate(task.created_at)}
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
            <i className="bi bi-clock-history fs-1 mb-3 d-block text-secondary"></i>
            <h5 className="fw-bold mb-2">과거 분석 이력이 없습니다.</h5>
            <p className="small text-secondary mb-4">학술적 공백과 미래 연구 로드맵을 도출하기 위해 첫 번째 대규모 문헌 비교 분석을 실행해 보세요.</p>
            <Link href="/feature2" className={`btn rounded-3 px-4 py-2 ${styles.solidBtn}`}>
              첫 분석 실행하기
            </Link>
          </div>
        </div>
      )}

      {/* 커스텀 삭제 확인 모달 (블러 및 중앙 정렬) */}
      {showConfirmModal && mounted && createPortal(
        <div className={styles.modalOverlay} onClick={() => setShowConfirmModal(false)}>
          <div className={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div className={styles.warningIconWrapper}>
                <i className={`bi bi-exclamation-triangle-fill ${styles.warningIcon}`}></i>
              </div>
              <h5 className={styles.modalTitle}>분석 이력 삭제</h5>
            </div>
            <div className={styles.modalBody}>
              <p className={styles.modalMainText}>
                선택한 <strong>{selectedTaskIds.length}개</strong>의 분석 보고서 이력을 삭제하시겠습니까?
              </p>
              <p className={styles.modalSubText}>
                이 작업은 되돌릴 수 없으며, 모든 관련 데이터가 물리적으로 완전히 소거됩니다.
              </p>
            </div>
            <div className={styles.modalFooter}>
              <button
                onClick={() => setShowConfirmModal(false)}
                className={`btn ${styles.modalBtn} ${styles.modalCancelBtn}`}
              >
                아니오
              </button>
              <button
                onClick={handleBulkDeleteConfirm}
                className={`btn ${styles.modalBtn} ${styles.modalConfirmBtn}`}
              >
                삭제하기
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
