"use client"

import { useState, useEffect, useContext } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "./page.module.css";
import { listUserTasks } from "@/apis/researchGap";
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
        <Link href="/feature2" className={`btn btn-sm d-flex align-items-center gap-1 rounded-3 ${styles.outlineBtn}`}>
          <i className="bi bi-plus-circle"></i> 새 분석 요청
        </Link>
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
                  <th className={`px-4 py-3 ${styles.colDomain}`}>학술 도메인</th>
                  <th className={`py-3 ${styles.colQuery}`}>분석 대상 주제 / 키워드</th>
                  <th className={`py-3 ${styles.colStatus}`}>상태</th>
                  <th className={`py-3 ${styles.colTime}`}>요청 시간</th>
                  <th className={`px-4 py-3 ${styles.colAction}`}>동작</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.task_id} className={styles.tableRow}>
                    <td className="px-4 py-3">
                      <span
                        className={`badge px-2.5 py-1.5 rounded-pill ${styles.domainBadge} ${task.domain === "cs" ? styles.domainCs : styles.domainBio}`}
                      >
                        {task.domain}
                      </span>
                    </td>
                    <td className="py-3 fw-semibold text-dark">
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
                    <td className="px-4 py-3">
                      {task.status === "COMPLETED" ? (
                        <button
                          onClick={() => router.push(`/feature2?taskId=${task.task_id}`)}
                          className={`btn btn-sm rounded-3 px-3 py-1 d-inline-flex align-items-center gap-1 ${styles.solidBtn}`}
                        >
                          결과 보기 <i className="bi bi-chevron-right small"></i>
                        </button>
                      ) : (
                        <button
                          onClick={() => router.push(`/feature2?taskId=${task.task_id}`)}
                          className={`btn btn-sm rounded-3 px-3 py-1 d-inline-flex align-items-center gap-1 ${styles.outlineSecBtn}`}
                        >
                          상태 확인 <i className="bi bi-arrow-right-short"></i>
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      ) : (
        <div className="card shadow-sm border border-light-subtle rounded-3 p-5 text-center text-muted">
          <div className="py-5">
            <i className="bi bi-clock-history fs-1 mb-3 d-block text-secondary"></i>
            <h5 className="fw-bold text-dark mb-2">과거 분석 이력이 없습니다.</h5>
            <p className="small text-secondary mb-4">학술적 공백과 미래 연구 로드맵을 도출하기 위해 첫 번째 대규모 문헌 비교 분석을 실행해 보세요.</p>
            <Link href="/feature2" className={`btn rounded-3 px-4 py-2 ${styles.solidBtn}`}>
              첫 분석 실행하기
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
