"use client"

import { createPortal } from "react-dom";
import styles from "@/app/feature2/page.module.css";

/**
 * 이력 일괄 삭제 작업을 확인하기 위해 사용되는 포털(Portal) 기반 커스텀 모달 컴포넌트입니다.
 * 
 * @param {number} selectedCount - 선택된 삭제 대상 개수
 * @param {Function} onCancel    - 취소 핸들러
 * @param {Function} onConfirm   - 확인 및 삭제 처리 핸들러
 */
export default function DeleteConfirmModal({ selectedCount, onCancel, onConfirm }) {
  return createPortal(
    <div className={styles.modalOverlay} onClick={onCancel}>
      <div className={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.warningIconWrapper}>
            <i className={`bi bi-exclamation-triangle-fill ${styles.warningIcon}`}></i>
          </div>
          <h5 className={styles.modalTitle}>분석 이력 삭제</h5>
        </div>
        <div className={styles.modalBody}>
          <p className={styles.modalMainText}>
            선택한 <strong>{selectedCount}개</strong>의 분석 보고서 이력을 삭제하시겠습니까?
          </p>
          <p className={styles.modalSubText}>
            이 작업은 되돌릴 수 없으며, 모든 관련 데이터가 물리적으로 완전히 소거됩니다.
          </p>
        </div>
        <div className={styles.modalFooter}>
          <button
            onClick={onCancel}
            className={`btn ${styles.modalBtn} ${styles.modalCancelBtn}`}
          >
            아니오
          </button>
          <button
            onClick={onConfirm}
            className={`btn ${styles.modalBtn} ${styles.modalConfirmBtn}`}
          >
            삭제하기
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
