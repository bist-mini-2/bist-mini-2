"use client"

/**
 * 전역 또는 섹션 단위에서 공통으로 사용되는 수직/수평 중앙 정렬 로딩 스피너 컴포넌트입니다.
 * 부모 컨테이너(AppLayoutWrapper의 .content) 기준 절대값(absolute)으로 가로/세로 정중앙에 배치됩니다.
 * 
 * @param {Object} props
 * @param {string} [props.message="로딩 중..."] - 스피너 하단에 노출할 안내 메시지
 */
export default function LoadingSpinner({ message = "로딩 중..." }) {
  return (
    <div className="position-absolute top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center text-muted bg-transparent" style={{ zIndex: 10 }}>
      <div className="spinner-border text-success mb-3" role="status">
        <span className="visually-hidden">Loading...</span>
      </div>
      <span className="fw-medium">{message}</span>
    </div>
  );
}
