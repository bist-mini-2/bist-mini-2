"use client"

import styles from "@/app/feature2/page.module.css";

/**
 * 대규모 문헌 비교 분석기 작업 이력 목록 테이블 컴포넌트입니다.
 * 
 * @param {Array} displayTasks         - 표시할 이력 태스크 목록 (실제 또는 튜토리얼 가데이터)
 * @param {boolean} isEditMode         - 편집(삭제) 모드 활성화 여부
 * @param {Array} selectedTaskIds      - 현재 체크박스 선택된 태스크 ID 목록
 * @param {Array} deletingIds          - 현재 애니메이션 삭제 처리 중인 태스크 ID 목록
 * @param {Function} handleSelectAllChange - 헤더 전체선택 체크박스 변경 핸들러
 * @param {Function} handleCheckboxChange  - 개별 행 체크박스 토글 핸들러
 * @param {Function} handleRowClick       - 행 클릭 핸들러 (이동 또는 개별 체크박스 토글)
 * @param {Function} formatDate           - 날짜 포맷팅 유틸 함수
 * @param {Function} renderStatusBadge    - 상태 배지 렌더링 함수
 */
export default function HistoryTable({
  displayTasks,
  isEditMode,
  selectedTaskIds,
  deletingIds,
  handleSelectAllChange,
  handleCheckboxChange,
  handleRowClick,
  formatDate,
  renderStatusBadge,
}) {
  return (
    <div className="card shadow-sm border border-light-subtle rounded-3 overflow-hidden">
      <div className="table-responsive">
        <table className={`table table-hover align-middle mb-0 ${styles.historyTable} tutorial-history-table`}>
          <thead className={`text-secondary ${styles.tableHeader}`}>
            <tr>
              <th className={`${styles.colCheck} ${isEditMode ? styles.colCheckActive : ""}`}>
                <div className={styles.checkboxWrapper}>
                  <input
                    type="checkbox"
                    className={`${styles.customCheckbox} cursor-pointer`}
                    onChange={handleSelectAllChange}
                    checked={displayTasks.length > 0 && selectedTaskIds.length === displayTasks.length}
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
            {displayTasks.map((task) => {
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
  );
}
