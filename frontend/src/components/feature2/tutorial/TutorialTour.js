"use client"

import { useState, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import styles from "./TutorialTour.module.css";
import TutorialPopover from "./TutorialPopover";

const POPOVER_WIDTH = 320;
const POPOVER_HEIGHT = 220; // conservative estimate for wrapped Korean text
const GAP = 14;             // gap between target and popover
const SCREEN_MARGIN = 10;   // minimum distance from viewport edges

/**
 * 포커스 타겟의 rect와 스텝 설정을 받아 팝오버 top/left와 말꼬리 방향/오프셋을 계산합니다.
 *
 * @param {DOMRect} rect - 타겟 요소의 뷰포트 기준 bounding rect
 * @param {object} step - 현재 스텝 설정 ({ position, arrowAlign, arrowTarget })
 * @returns {{ top, left, arrowDir, arrowStyle }} - 계산된 위치 및 말꼬리 방향/스타일 정보
 */
function computePosition(rect, step) {
  const { position = "bottom", arrowAlign, arrowTarget } = step;

  const effectiveHeight = rect.height > 300 ? 140 : rect.height;

  let top = 0;
  let left = 0;
  let arrowDir = ""; // "top" | "bottom" | "left" | "right"

  // ── 1단계: 요청된 position으로 기본 좌표 계산 ──────────────────────────
  if (position === "bottom") {
    top = rect.top + effectiveHeight + GAP;
    arrowDir = "top"; // 팝오버가 아래 → 말꼬리가 위쪽(▲)에 위치
    if (arrowAlign === "left") {
      left = rect.left;
    } else if (arrowAlign === "right") {
      left = rect.right - POPOVER_WIDTH;
    } else {
      left = rect.left + (rect.width - POPOVER_WIDTH) / 2;
    }
  } else if (position === "top") {
    const topAnchor = rect.height > 300 ? rect.top + effectiveHeight : rect.top;
    top = topAnchor - POPOVER_HEIGHT - GAP;
    arrowDir = "bottom"; // 팝오버가 위 → 말꼬리가 아래쪽(▼)에 위치
    if (arrowAlign === "left") {
      left = rect.left;
    } else if (arrowAlign === "right") {
      left = rect.right - POPOVER_WIDTH;
    } else {
      left = rect.left + (rect.width - POPOVER_WIDTH) / 2;
    }
  } else if (position === "left") {
    left = rect.left - POPOVER_WIDTH - GAP;
    top = rect.top + (effectiveHeight - POPOVER_HEIGHT) / 2;
    arrowDir = "right"; // 팝오버가 왼쪽 → 말꼬리가 오른쪽(►)에 위치
  } else if (position === "right") {
    left = rect.right + GAP;
    top = rect.top + (effectiveHeight - POPOVER_HEIGHT) / 2;
    arrowDir = "left"; // 팝오버가 오른쪽 → 말꼬리가 왼쪽(◄)에 위치
  }

  // ── 2단계: 뷰포트 경계 클램핑 (수평) ────────────────────────────────────
  if (left < SCREEN_MARGIN) left = SCREEN_MARGIN;
  if (left + POPOVER_WIDTH > window.innerWidth - SCREEN_MARGIN) {
    left = window.innerWidth - POPOVER_WIDTH - SCREEN_MARGIN;
  }

  // ── 3단계: 수직 플리핑 — 공간이 없으면 반대편으로 ────────────────────────
  let finalPos = position;
  if (top < SCREEN_MARGIN) {
    top = rect.top + effectiveHeight + GAP;
    arrowDir = "top";
    finalPos = "bottom";
  } else if (
    top + POPOVER_HEIGHT > window.innerHeight - SCREEN_MARGIN &&
    rect.top - POPOVER_HEIGHT - GAP > SCREEN_MARGIN
  ) {
    top = rect.top - POPOVER_HEIGHT - GAP;
    arrowDir = "bottom";
    finalPos = "top";
  }

  // ── 4단계: 말꼬리 위치 계산 ─────────────────────────────────────────────
  // arrowTarget이 지정된 경우 해당 하위 요소의 중심을 조준, 아니면 자체 계산
  let arrowStyle = {};

  if (finalPos === "bottom" || finalPos === "top") {
    // 말꼬리가 수평으로 위치하는 경우 (left 값 결정)
    let pointX;

    if (arrowTarget) {
      // 서브 셀렉터 방식: 지정한 자식 요소의 중심을 정확히 조준
      const subEl = document.querySelector(arrowTarget);
      pointX = subEl
        ? subEl.getBoundingClientRect().left + subEl.getBoundingClientRect().width / 2
        : rect.left + rect.width / 2;
    } else if (rect.width > POPOVER_WIDTH) {
      // 팝오버보다 넓은 요소(테이블 등): arrowAlign 방향의 내측 포인트를 조준
      if (arrowAlign === "left") {
        pointX = rect.left + 60;
      } else if (arrowAlign === "right") {
        pointX = rect.right - 60;
      } else {
        pointX = rect.left + rect.width / 2;
      }
    } else {
      // 좁은 요소(버튼 등): 정확히 중앙을 조준
      pointX = rect.left + rect.width / 2;
    }

    // 팝오버 카드 내에서의 말꼬리 left 오프셋 (중심 - 8px = 화살표 중심)
    let arrowLeft = pointX - left - 8;

    // 둥근 모서리(border-radius: 12px) 안쪽으로 최소 30px 여백 보장
    arrowLeft = Math.max(30, Math.min(arrowLeft, POPOVER_WIDTH - 46));

    arrowStyle = { left: `${arrowLeft}px`, top: undefined };
  } else {
    // 말꼬리가 수직으로 위치하는 경우 (top 값 결정)
    const pointY = rect.top + effectiveHeight / 2;
    let arrowTop = pointY - top - 8;
    arrowTop = Math.max(30, Math.min(arrowTop, POPOVER_HEIGHT - 46));
    arrowStyle = { top: `${arrowTop}px`, left: undefined };
  }

  return { top, left, arrowDir, arrowStyle };
}

/**
 * 튜토리얼 투어 (TutorialTour) 오버레이 컴포넌트입니다.
 * React Portal을 통해 body 최상단에 렌더링되며,
 * 타겟 요소를 하이라이트하고 가이드 팝오버를 표시합니다.
 *
 * @param {Array} steps - 투어 스텝 배열
 * @param {string} matchPath - 이 투어가 활성화될 pathname
 */
export default function TutorialTour({ steps = [], matchPath }) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [targetRect, setTargetRect] = useState(null);
  const [popoverPos, setPopoverPos] = useState({ top: 0, left: 0 });
  const [arrowDir, setArrowDir] = useState("");
  const [arrowStyle, setArrowStyle] = useState({});
  const [mounted, setMounted] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [isTransitionEnabled, setIsTransitionEnabled] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // ── 좌표 계산 함수 ────────────────────────────────────────────────────────
  const updatePosition = useCallback(() => {
    if (!isOpen || steps.length === 0 || currentIndex >= steps.length) return;

    const step = steps[currentIndex];
    const targetEl = document.querySelector(step.target);

    if (targetEl) {
      const rect = targetEl.getBoundingClientRect();
      const { top, left, arrowDir: ad, arrowStyle: as } = computePosition(rect, step);

      setTargetRect({
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height,
      });
      setPopoverPos({ top, left });
      setArrowDir(ad);
      setArrowStyle(as);
      setIsReady(true);
      setTimeout(() => setIsTransitionEnabled(true), 50);
    } else {
      // 타겟 없을 시 뷰포트 중앙 폴백
      setTargetRect(null);
      setPopoverPos({
        top: (window.innerHeight - POPOVER_HEIGHT) / 2,
        left: (window.innerWidth - POPOVER_WIDTH) / 2,
      });
      setArrowClass("");
      setArrowStyle({});
      setIsReady(true);
      setTimeout(() => setIsTransitionEnabled(true), 50);
    }
  }, [isOpen, currentIndex, steps]);

  // ── 트리거 이벤트 수신 ────────────────────────────────────────────────────
  useEffect(() => {
    const handleTrigger = (e) => {
      const { pathname } = e.detail;
      if (pathname === matchPath || (matchPath && pathname.startsWith(matchPath))) {
        setIsReady(false);
        setIsTransitionEnabled(false);
        setIsOpen(true);
        setCurrentIndex(0);
      }
    };
    window.addEventListener("trigger-page-tutorial", handleTrigger);
    return () => window.removeEventListener("trigger-page-tutorial", handleTrigger);
  }, [matchPath]);

  // ── 스텝 변경 시 스크롤 + 좌표 재계산 ──────────────────────────────────────
  useEffect(() => {
    if (!isOpen || steps.length === 0) return;

    setIsReady(false);
    setIsTransitionEnabled(false);

    const step = steps[currentIndex];
    const targetEl = document.querySelector(step.target);

    if (targetEl) {
      // position=top 스텝은 타겟 상단을 화면에 보이게 스크롤해야 팝오버 위 공간 확보
      const scrollBlock = step.position === "top" ? "start" : "center";
      targetEl.scrollIntoView({ behavior: "auto", block: scrollBlock });
      // 레이아웃 리플로우 완료 후 3회 재계산으로 정확도 보장
      const t1 = setTimeout(() => updatePosition(), 60);
      const t2 = setTimeout(() => updatePosition(), 160);
      const t3 = setTimeout(() => updatePosition(), 360);
      return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
    } else {
      updatePosition();
    }
  }, [isOpen, currentIndex, steps, updatePosition]);

  // ── 리사이즈 시 실시간 재계산 ────────────────────────────────────────────
  useEffect(() => {
    if (!isOpen) return;
    window.addEventListener("resize", updatePosition);
    return () => window.removeEventListener("resize", updatePosition);
  }, [isOpen, updatePosition]);

  const handleNext = () => {
    if (currentIndex < steps.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      handleClose();
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) setCurrentIndex((prev) => prev - 1);
  };

  const handleClose = () => {
    setIsOpen(false);
    setTargetRect(null);
    setIsReady(false);
    setIsTransitionEnabled(false);
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("tutorial-ended"));
    }
  };

  if (!isOpen || steps.length === 0 || !mounted) return null;

  const currentStep = steps[currentIndex];

  return createPortal(
    <>
      {/* 어두운 배경 오버레이 */}
      <div
        className={styles.overlay}
        style={{ backgroundColor: "transparent" }}
        onClick={handleClose}
      />

      {/* 하이라이트 마스크 */}
      {isReady && targetRect && (
        <div
          className={styles.highlightMask}
          style={{
            top: targetRect.top - 4,
            left: targetRect.left - 4,
            width: targetRect.width + 8,
            height: targetRect.height + 8,
            transition: isTransitionEnabled ? undefined : "none",
          }}
        >
          <div className={styles.highlightGlow} />
        </div>
      )}

      {/* 가이드 팝오버 */}
      {isReady && (
        <TutorialPopover
          currentStep={currentStep}
          currentIndex={currentIndex}
          totalSteps={steps.length}
          popoverPos={popoverPos}
          arrowDir={arrowDir}
          arrowStyle={arrowStyle}
          isTransitionEnabled={isTransitionEnabled}
          handlePrev={handlePrev}
          handleNext={handleNext}
          handleClose={handleClose}
        />
      )}
    </>,
    document.body
  );
}
