"use client"

import { useState, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import styles from "./TutorialTour.module.css";

export default function TutorialTour({ steps = [], matchPath }) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [targetRect, setTargetRect] = useState(null);
  const [popoverPos, setPopoverPos] = useState({ top: 0, left: 0 });
  const [arrowClass, setArrowClass] = useState("");
  const [mounted, setMounted] = useState(false);
  const [isPositionCalculated, setIsPositionCalculated] = useState(false);
  const [isTransitionEnabled, setIsTransitionEnabled] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // 1. Calculate positions dynamically
  const updatePosition = useCallback(() => {
    if (!isOpen || steps.length === 0 || currentIndex >= steps.length) return;

    const currentStep = steps[currentIndex];
    const targetElement = document.querySelector(currentStep.target);

    if (targetElement) {
      const rect = targetElement.getBoundingClientRect();

      // Highlight target coordinates (using viewport-relative coordinates for fixed styling)
      setTargetRect({
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height
      });

      // Calculate popover coordinates based on position option
      const pos = currentStep.position || "bottom";
      let top = 0;
      let left = 0;
      const gap = 14;
      const popoverWidth = 320;
      const popoverHeight = 170; // Reduced to 170 to fit top positioning without triggering bottom auto-flip

      // If target element is extremely large (like a table), cap effective height to keep popover close to target start
      const effectiveHeight = rect.height > 300 ? 100 : rect.height;

      if (pos === "bottom") {
        top = rect.top + effectiveHeight + gap;
        left = rect.left + (rect.width - popoverWidth) / 2;
        setArrowClass(styles.arrowTop);
      } else if (pos === "top") {
        top = rect.top - popoverHeight - gap;
        left = rect.left + (rect.width - popoverWidth) / 2;
        setArrowClass(styles.arrowBottom);
      } else if (pos === "left") {
        top = rect.top + (effectiveHeight - popoverHeight) / 2;
        left = rect.left - popoverWidth - gap;
        setArrowClass(styles.arrowRight);
      } else if (pos === "right") {
        top = rect.top + (effectiveHeight - popoverHeight) / 2;
        left = rect.right + gap;
        setArrowClass(styles.arrowLeft);
      }

      // boundary safety checks to keep popover inside the viewport
      if (left < 10) left = 10;
      if (left + popoverWidth > window.innerWidth - 10) {
        left = window.innerWidth - popoverWidth - 10;
      }
      if (top < 10) {
        top = rect.top + effectiveHeight + gap; // Flip to bottom
        setArrowClass(styles.arrowTop);
      } else if (top + popoverHeight > window.innerHeight - 10 && rect.top - popoverHeight - gap > 10) {
        top = rect.top - popoverHeight - gap; // Flip to top
        setArrowClass(styles.arrowBottom);
      }

      setPopoverPos({ top, left });
      setIsPositionCalculated(true);
      setTimeout(() => {
        setIsTransitionEnabled(true);
      }, 50);
    } else {
      // Fallback: Center of the viewport if target element is not found
      const top = (window.innerHeight - 200) / 2;
      const left = (window.innerWidth - 320) / 2;
      setTargetRect(null);
      setPopoverPos({ top, left });
      setArrowClass("");
      setIsPositionCalculated(true);
      setTimeout(() => {
        setIsTransitionEnabled(true);
      }, 50);
    }
  }, [isOpen, currentIndex, steps]);

  // 2. Listen to global window trigger event from Topbar
  useEffect(() => {
    const handleTrigger = (e) => {
      const { pathname } = e.detail;
      // Start tour if pathname matches the target path configuration
      if (pathname === matchPath || (matchPath && pathname.startsWith(matchPath))) {
        setIsPositionCalculated(false);
        setIsTransitionEnabled(false);
        setIsOpen(true);
        setCurrentIndex(0);
      }
    };

    window.addEventListener("trigger-page-tutorial", handleTrigger);
    return () => {
      window.removeEventListener("trigger-page-tutorial", handleTrigger);
    };
  }, [matchPath]);

  // 3. Auto scroll and recalculate positions when index changes
  useEffect(() => {
    if (!isOpen || steps.length === 0) return;

    // Reset transition state immediately to fade out current step cleanly
    setIsPositionCalculated(false);
    setIsTransitionEnabled(false);

    const currentStep = steps[currentIndex];
    const targetElement = document.querySelector(currentStep.target);

    if (targetElement) {
      targetElement.scrollIntoView({ behavior: "auto", block: "center" });
      
      // Delay computation slightly (50ms) to ensure DOM reflow has completed
      const timer = setTimeout(() => {
        updatePosition();
      }, 50);
      return () => clearTimeout(timer);
    } else {
      updatePosition();
    }
  }, [isOpen, currentIndex, steps, updatePosition]);

  // 4. Bind window events (resize, scroll) to keep coordinates synced
  useEffect(() => {
    if (!isOpen) return;

    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition);
    };
  }, [isOpen, updatePosition]);

  const handleNext = () => {
    if (currentIndex < steps.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      handleClose();
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setTargetRect(null);
    setIsPositionCalculated(false);
    setIsTransitionEnabled(false);
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("tutorial-ended"));
    }
  };

  if (!isOpen || steps.length === 0 || !mounted) return null;

  const currentStep = steps[currentIndex];

  return createPortal(
    <>
      {/* 1. Backdrop Area: Dim screen immediately on isOpen */}
      <div 
        style={{ 
          opacity: isOpen ? 1 : 0, 
          transition: "opacity 0.3s ease",
          pointerEvents: "auto"
        }}
      >
        {/* Transparent click guard backdrop (retains blur filter from styles.overlay) */}
        <div 
          className={styles.overlay} 
          style={{ backgroundColor: "transparent" }} 
          onClick={handleClose}
        ></div>

        {/* Dark Mask: Dims screen immediately, and opens visual window only when coordinates calculated */}
        <div 
          className={styles.highlightMask}
          style={{
            top: isPositionCalculated && targetRect ? targetRect.top - 4 : 0,
            left: isPositionCalculated && targetRect ? targetRect.left - 4 : 0,
            width: isPositionCalculated && targetRect ? targetRect.width + 8 : 0,
            height: isPositionCalculated && targetRect ? targetRect.height + 8 : 0,
            transition: isTransitionEnabled ? undefined : "none"
          }}
        >
          {isPositionCalculated && targetRect && <div className={styles.highlightGlow}></div>}
        </div>
      </div>

      {/* 2. Popover Guidance Bubble: Mounts and fades in only after scroll & position checks */}
      <div 
        style={{ 
          opacity: isPositionCalculated ? 1 : 0, 
          transition: "opacity 0.2s ease",
          pointerEvents: isPositionCalculated ? "auto" : "none"
        }}
      >
        {isPositionCalculated && (
          <div 
            className={styles.popover}
            style={{
              top: popoverPos.top,
              left: popoverPos.left,
              transition: isTransitionEnabled ? undefined : "none"
            }}
          >
            {arrowClass && <div className={`${styles.arrow} ${arrowClass}`}></div>}
            
            <div className={styles.popoverHeader}>
              <h4 className={styles.title}>
                <i className="bi bi-info-circle-fill text-primary"></i>
                {currentStep.title}
              </h4>
              <span className={styles.badge}>
                {currentIndex + 1} / {steps.length}
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
                  {currentIndex === steps.length - 1 ? "Finish" : "Next"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>,
    document.body
  );
}
