import { useState, useEffect } from "react";

/**
 * 마인드맵 캔버스의 휠 줌(Zoom) 및 스페이스바+마우스 드래그 팬(Pan) 상태와 
 * 이벤트 리스너 라이프사이클을 전담하여 처리하는 커스텀 훅입니다.
 * 
 * @param {Object} params
 * @param {React.RefObject} params.containerRef SVG 캔버스 외부를 감싸는 컨테이너 Element Ref
 * @returns {Object} 줌/팬 관련 상태 및 핸들러 객체
 */
export default function useZoomPan({ containerRef }) {
  const [scale, setScale] = useState(1.0);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // 휠 스크롤 줌 기능 바인딩 (passive: false로 직접 추가하여 브라우저 기본 스크롤 방지)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheelZoom = (e) => {
      e.preventDefault(); 
      const zoomSpeed = 0.05;
      setScale((prevScale) => {
        const nextScale = e.deltaY < 0 ? prevScale + zoomSpeed : prevScale - zoomSpeed;
        return Math.min(Math.max(nextScale, 0.5), 3.0); 
      });
    };

    container.addEventListener("wheel", handleWheelZoom, { passive: false });
    return () => {
      container.removeEventListener("wheel", handleWheelZoom);
    };
  }, [containerRef]);

  // 스페이스바 키 이벤트 바인딩 (컨테이너 호버 중에만 전역 스페이스바 바인딩)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.code === "Space") {
        e.preventDefault(); 
        setIsSpacePressed(true);
      }
    };

    const handleKeyUp = (e) => {
      if (e.code === "Space") {
        setIsSpacePressed(false);
      }
    };

    if (isHovered) {
      window.addEventListener("keydown", handleKeyDown);
      window.addEventListener("keyup", handleKeyUp);
    }

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [isHovered]);

  const handleMouseDown = (e) => {
    if (isSpacePressed && e.button === 0) {
      setIsPanning(true);
      setDragStart({
        x: e.clientX - panOffset.x,
        y: e.clientY - panOffset.y
      });
    }
  };

  const handleMouseMove = (e) => {
    if (isPanning && isSpacePressed) {
      setPanOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const zoomIn = () => {
    setScale((prev) => Math.min(prev + 0.1, 3.0));
  };

  const zoomOut = () => {
    setScale((prev) => Math.max(prev - 0.1, 0.5));
  };

  const resetZoomAndPan = () => {
    setScale(1.0);
    setPanOffset({ x: 0, y: 0 });
  };

  return {
    scale,
    setScale,
    panOffset,
    setPanOffset,
    isPanning,
    setIsPanning,
    isSpacePressed,
    setIsSpacePressed,
    isHovered,
    setIsHovered,
    dragStart,
    setDragStart,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    zoomIn,
    zoomOut,
    resetZoomAndPan
  };
}
