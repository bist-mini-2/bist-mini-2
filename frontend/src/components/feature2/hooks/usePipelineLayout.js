import { useState } from "react";
import useZoomPan from "./useZoomPan";
import { calculateGraphLayout, getRepulsedCoords, getCircleRadius } from "../utils/graphLayout";

/**
 * PipelineGraph의 레이아웃 좌표 계산, 척력(Repulsion), 카메라 줌-포커싱, 
 * 가시성 규칙(Visibility) 및 마우스/키보드 팬(Pan) 상태 조작을 전담하는 커스텀 훅입니다.
 * 2차 리팩토링을 통해 수학적 기하 연산과 줌/팬 이벤트 상태를 외부 모듈로 위임하였습니다.
 */
export default function usePipelineLayout({ result, query, canvasWidth, canvasHeight, containerRef }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeFocusNode, setActiveFocusNode] = useState(null);

  // 줌 & 팬 상태 관리 훅 호출
  const zoomPan = useZoomPan({ containerRef });

  // 1단계 ~ 5단계 노드 위치 기하학 배치 계산
  const layoutData = calculateGraphLayout({
    result,
    query,
    canvasWidth,
    canvasHeight
  });

  // --- 카메라 포커싱 & 가시성 규칙 (Visibility rules) ---

  const focusOnNode = (nodeId, x, y) => {
    const targetScale = nodeId === "common" ? 1.1 : 1.2;
    if (activeFocusNode === nodeId) {
      zoomPan.setScale(1.0);
      zoomPan.setPanOffset({ x: 0, y: 0 });
      setActiveFocusNode(null);
    } else {
      const newX = canvasWidth / 2 - x * targetScale;
      const newY = canvasHeight / 2 - y * targetScale;
      zoomPan.setPanOffset({ x: newX, y: newY });
      zoomPan.setScale(targetScale);
      setActiveFocusNode(nodeId);
    }
  };

  // 노드 가시성 여부 확인
  const isNodeVisible = (nodeId) => {
    if (!activeFocusNode) {
      return !nodeId.startsWith("solved-") && !nodeId.startsWith("limitation-");
    }

    if (activeFocusNode === nodeId) return true;

    // Query 포커스 시: Query와 논문 노드만 활성화
    if (activeFocusNode === "query") {
      return nodeId === "query" || nodeId.startsWith("paper-");
    }

    // 논문 포커스 시: 해당 논문, Query 및 해당 논문의 자식 노드(Solved/Limitation) 노출
    if (activeFocusNode.startsWith("paper-")) {
      const idx = activeFocusNode.split("-")[1];
      return nodeId === "query" || nodeId === `paper-${idx}` || nodeId.startsWith(`solved-${idx}-`) || nodeId.startsWith(`limitation-${idx}-`);
    }

    // 자식 노드 포커스 시: 해당 자식 노드, 부모 논문 노출. (limitation일 경우에만 Common Gap 추가 노출)
    if (activeFocusNode.startsWith("solved-") || activeFocusNode.startsWith("limitation-")) {
      const parts = activeFocusNode.split("-");
      const parentIdx = parts[1];
      const parentVisible = nodeId === `paper-${parentIdx}`;
      const selfVisible = nodeId === activeFocusNode;
      const commonVisible = activeFocusNode.startsWith("limitation-") && nodeId === "common";
      return parentVisible || selfVisible || commonVisible;
    }

    // Common Gap 포커스 시: Common Gap, 모든 Limitation 자식 노드들, 추천 연구주제 노출
    if (activeFocusNode === "common") {
      return nodeId === "common" || nodeId.startsWith("limitation-") || nodeId.startsWith("direction-");
    }

    // 추천 주제 포커스 시: 해당 주제 및 Common Gap 노출
    if (activeFocusNode.startsWith("direction-")) {
      return nodeId === "common" || nodeId === activeFocusNode;
    }

    return false;
  };

  // 노드 카드 클릭 핸들러
  const handleNodeClick = (e, node) => {
    e.stopPropagation();
    if (zoomPan.isSpacePressed) return;
    if (!isNodeVisible(node.id)) return;
    const repulsed = getRepulsedCoords({
      activeFocusNode,
      layoutData,
      nodeId: node.id,
      origX: node.x,
      origY: node.y
    });
    focusOnNode(node.id, repulsed.x, repulsed.y);
    setSelectedNode((prev) => (prev?.type === node.id ? null : { type: node.id, data: node }));
  };

  // 기존 API 호환을 위해 줌 앤 팬 상태 리셋 데코레이터 정의
  const resetZoomAndPan = () => {
    zoomPan.resetZoomAndPan();
    setActiveFocusNode(null);
  };

  return {
    selectedNode,
    setSelectedNode,
    activeFocusNode,
    setActiveFocusNode,
    
    // useZoomPan 상태 및 액션 노출
    scale: zoomPan.scale,
    setScale: zoomPan.setScale,
    panOffset: zoomPan.panOffset,
    setPanOffset: zoomPan.setPanOffset,
    isPanning: zoomPan.isPanning,
    setIsPanning: zoomPan.setIsPanning,
    isSpacePressed: zoomPan.isSpacePressed,
    setIsSpacePressed: zoomPan.setIsSpacePressed,
    isHovered: zoomPan.isHovered,
    setIsHovered: zoomPan.setIsHovered,
    dragStart: zoomPan.dragStart,
    setDragStart: zoomPan.setDragStart,
    handleMouseDown: zoomPan.handleMouseDown,
    handleMouseMove: zoomPan.handleMouseMove,
    handleMouseUp: zoomPan.handleMouseUp,
    zoomIn: zoomPan.zoomIn,
    zoomOut: zoomPan.zoomOut,
    resetZoomAndPan,

    // 배치 계산된 개별 노드군
    queryNode: layoutData.queryNode,
    paperNodes: layoutData.paperNodes,
    solvedNodes: layoutData.solvedNodes,
    limitationNodes: layoutData.limitationNodes,
    commonNode: layoutData.commonNode,
    directionNodes: layoutData.directionNodes,

    // 유틸 바인딩
    getCircleRadius: (nodeId, baseRadius) => getCircleRadius({
      activeFocusNode,
      nodeId,
      baseRadius
    }),
    getRepulsedCoords: (nodeId, origX, origY) => getRepulsedCoords({
      activeFocusNode,
      layoutData,
      nodeId,
      origX,
      origY
    }),

    isNodeVisible,
    handleNodeClick
  };
}

