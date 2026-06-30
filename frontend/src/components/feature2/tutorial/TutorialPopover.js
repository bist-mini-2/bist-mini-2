"use client"

import styles from "./TutorialTour.module.css";

/**
 * 말꼬리 방향에 따라 적절한 SVG 삼각형을 렌더링하는 컴포넌트입니다.
 * paint-order: stroke fill 을 통해 테두리는 측면에만, 베이스는 카드 배경으로 가려집니다.
 *
 * @param {string} dir   - "top" | "bottom" | "left" | "right"
 * @param {object} style - { left?: string } 또는 { top?: string } (JS로 계산된 위치 오프셋)
 */
function ArrowSvg({ dir, style }) {
  if (!dir) return null;

  const pathStyle = {
    fill: "var(--card-bg)",
    stroke: "var(--card-border)",
    strokeWidth: 1.5,
    strokeLinejoin: "round",
    paintOrder: "stroke fill",
  };

  const base = {
    position: "absolute",
    pointerEvents: "none",
    zIndex: 10,
    overflow: "visible",
    display: "block",
  };

  // 수평 위치를 style.left에서 읽고, 수직 고정값은 direction별로 결정
  if (dir === "bottom") {
    // ▼  팝오버 하단 → 아래를 향하는 삼각형 (밑변인 상단 y=0 에는 테두리 없음)
    return (
      <svg
        style={{ ...base, bottom: -7, top: "auto", left: style?.left }}
        width="16" height="8" viewBox="0 0 16 8"
        aria-hidden="true"
      >
        <path d="M0,0 L8,8 L16,0" style={pathStyle} />
      </svg>
    );
  }

  if (dir === "top") {
    // ▲  팝오버 상단 → 위를 향하는 삼각형 (밑변인 하단 y=8 에는 테두리 없음)
    return (
      <svg
        style={{ ...base, top: -7, bottom: "auto", left: style?.left }}
        width="16" height="8" viewBox="0 0 16 8"
        aria-hidden="true"
      >
        <path d="M0,8 L8,0 L16,8" style={pathStyle} />
      </svg>
    );
  }

  if (dir === "left") {
    // ◄  팝오버 좌측 → 왼쪽을 향하는 삼각형 (밑변인 우측 x=8 에는 테두리 없음)
    return (
      <svg
        style={{ ...base, left: -7, right: "auto", top: style?.top }}
        width="8" height="16" viewBox="0 0 8 16"
        aria-hidden="true"
      >
        <path d="M8,0 L0,8 L8,16" style={pathStyle} />
      </svg>
    );
  }

  if (dir === "right") {
    // ►  팝오버 우측 → 오른쪽을 향하는 삼각형 (밑변인 좌측 x=0 에는 테두리 없음)
    return (
      <svg
        style={{ ...base, right: -7, left: "auto", top: style?.top }}
        width="8" height="16" viewBox="0 0 8 16"
        aria-hidden="true"
      >
        <path d="M0,0 L8,8 L0,16" style={pathStyle} />
      </svg>
    );
  }

  return null;
}

/**
 * 튜토리얼 안내 말풍선 (Popover Bubble) UI 컴포넌트입니다.
 *
 * @param {object} currentStep        - 현재 스텝 데이터 ({ title, content })
 * @param {number} currentIndex       - 현재 스텝 인덱스 (0-based)
 * @param {number} totalSteps         - 전체 스텝 수
 * @param {{ top: number, left: number }} popoverPos  - 팝오버 고정 좌표 (fixed)
 * @param {string} arrowDir           - 말꼬리 방향 ("top" | "bottom" | "left" | "right")
 * @param {object} arrowStyle         - 말꼬리 오프셋 스타일 ({ left } 또는 { top })
 * @param {boolean} isTransitionEnabled - 전환 애니메이션 활성화 여부
 * @param {Function} handlePrev       - 이전 스텝 핸들러
 * @param {Function} handleNext       - 다음 스텝 핸들러
 * @param {Function} handleClose      - 투어 종료 핸들러
 */
export default function TutorialPopover({
  currentStep,
  currentIndex,
  totalSteps,
  popoverPos,
  arrowDir,
  arrowStyle,
  isTransitionEnabled,
  handlePrev,
  handleNext,
  handleClose,
}) {
  return (
    <div
      className={styles.popover}
      style={{
        top: popoverPos.top,
        left: popoverPos.left,
        transition: isTransitionEnabled ? undefined : "none",
      }}
    >
      {/* SVG 말꼬리 — CSS border 트릭 대신 SVG로 정확히 렌더링 */}
      <ArrowSvg dir={arrowDir} style={arrowStyle} />

      <div className={styles.popoverHeader}>
        <h4 className={styles.title}>
          <i className={`bi bi-info-circle-fill ${styles.infoIcon}`}></i>
          {currentStep.title}
        </h4>
        <span className={styles.badge}>
          {currentIndex + 1} / {totalSteps}
        </span>
      </div>

      <p className={styles.content}>{currentStep.content}</p>

      <div className={styles.footer}>
        <button className={styles.skipBtn} onClick={handleClose}>
          Skip
        </button>

        <div className={styles.btnGroup}>
          <button
            className={styles.navBtn}
            onClick={handlePrev}
            disabled={currentIndex === 0}
          >
            Prev
          </button>
          <button className={styles.primaryBtn} onClick={handleNext}>
            {currentIndex === totalSteps - 1 ? "Finish" : "Next"}
          </button>
        </div>
      </div>
    </div>
  );
}
