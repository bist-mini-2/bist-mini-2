import React from "react";

/**
 * 마인드맵 내의 각 노드(Query, Paper, Solved, Limitation, Common, Direction)를
 * 척력 및 연쇄 트랜지션, pointer-events 가드를 완벽하게 조화하여 렌더링하는 SVG 서브 컴포넌트입니다.
 */
export default function GraphNode({
  node,
  nodeType, // 'query' | 'paper' | 'solved' | 'limitation' | 'common' | 'direction'
  visible,
  isFocused,
  isSelected,
  coords,
  r,
  styles,
  handleNodeClick,
  activeFocusNode
}) {
  // 노드 타입별 필터 및 클래스 설정
  let circleClass = styles.circleNode;
  let filterUrl = null;

  if (nodeType === "query") {
    circleClass += ` ${styles.queryCircle}`;
    filterUrl = "url(#neon-glow-query)";
  } else if (nodeType === "paper") {
    circleClass += ` ${styles.paperCircle}`;
    filterUrl = "url(#neon-glow-paper)";
  } else if (nodeType === "solved") {
    circleClass += ` ${styles.solvedCircle}`;
  } else if (nodeType === "limitation") {
    circleClass += ` ${styles.limitCircle}`;
  } else if (nodeType === "common") {
    circleClass += ` ${styles.commonCircle}`;
    filterUrl = "url(#neon-glow-common)";
  } else if (nodeType === "direction") {
    circleClass += ` ${styles.directionCircle}`;
  }

  if (isSelected) {
    circleClass += ` ${styles.selected}`;
  }

  // 텍스트 글상자(foreignObject) 위치 및 크기 정밀 계산
  let foX = coords.x;
  let foY = coords.y;
  let foWidth = 180;
  let foHeight = 80;

  if (nodeType === "query") {
    foWidth = isSelected ? 300 : 220;
    foHeight = isSelected ? 200 : 80;
    foX = coords.x - foWidth / 2;
    foY = coords.y + r + 10;
  } else if (nodeType === "paper") {
    foWidth = isSelected ? 280 : 170;
    foHeight = isSelected ? 150 : 60;
    foX = coords.x - foWidth / 2;
    foY = coords.y + r + 8;
  } else if (nodeType === "solved" || nodeType === "limitation") {
    foWidth = isFocused ? 260 : 150;
    foHeight = isFocused ? 180 : 110;

    // 실제 부모와 자식 간의 척력 적용 후 좌표 기준 엣지 진행각 계산
    const margin = 15;
    const contentHeight = 65; 
    let actualAngle = 0;
    
    if (activeFocusNode === "common" && nodeType === "limitation") {
      // 공통 GAP 노드가 중심일 때, GAP 노드(820, 390)에서 limitation 노드를 바라보는 바깥 방향으로 각도 설정
      const commonX = 820;
      const commonY = 390;
      const dx = coords.x - commonX;
      const dy = coords.y - commonY;
      actualAngle = Math.atan2(dy, dx);
    } else if (node.parentX !== undefined) {
      // 척력이 적용된 좌표 기준으로 계산
      const dx = coords.x - node.parentX;
      const dy = coords.y - node.parentY;
      actualAngle = Math.atan2(dy, dx);
    }
    
    const visualBias = 6 * (Math.sin(actualAngle) + 1);
    const d = r + margin + visualBias + (foWidth / 2) * Math.abs(Math.cos(actualAngle)) + (contentHeight / 2) * Math.abs(Math.sin(actualAngle));

    const text_cx = coords.x + d * Math.cos(actualAngle);
    const text_cy = coords.y + d * Math.sin(actualAngle);

    // 포커스 상태일 때는 노드 바로 밑에 정직하게 배치, 비포커스일 때만 방사형 배치
    foX = isFocused ? coords.x - foWidth / 2 : text_cx - foWidth / 2;
    foY = isFocused ? coords.y + r + 15 : text_cy - foHeight / 2;
  } else if (nodeType === "common") {
    foWidth = 180;
    foHeight = 80;
    foX = coords.x - foWidth / 2;
    foY = coords.y + r + 10;
  } else if (nodeType === "direction") {
    foWidth = 200;
    foHeight = isSelected ? 180 : 80;
    foX = coords.x - foWidth / 2;
    foY = coords.y + r + 8;
  }

  // 노드별 상세 내부 HTML 렌더링 함수
  const renderLabelContent = () => {
    switch (nodeType) {
      case "query":
        return (
          <>
            <div className={styles.queryTitle}>{node.title}</div>
            <div className={isSelected ? styles.queryContentExpanded : styles.queryContent}>
              {node.content}
            </div>
          </>
        );
      case "paper":
        return (
          <div className={isSelected ? styles.paperTitleExpanded : styles.paperTitle}>
            {node.title}
          </div>
        );
      case "solved":
        return (
          <>
            <div className={styles.solvedTitle}>{node.title}</div>
            <div className={styles.solvedContent}>{node.content}</div>
          </>
        );
      case "limitation":
        return (
          <>
            <div className={styles.limitTitle}>{node.title}</div>
            <div className={styles.limitContent}>{node.content}</div>
          </>
        );
      case "common":
        return (
          <>
            <div className={styles.commonTitle}>{node.title}</div>
            <div className={styles.commonContent}>
              공통 공백 {node.items?.length || 0}건 도출됨
            </div>
          </>
        );
      case "direction":
        return (
          <>
            <div className={isSelected ? styles.directionTitleExpanded : styles.directionTitle}>
              {node.title}
            </div>
            <div className={isSelected ? styles.directionContentTextExpanded : styles.directionContentText}>
              {node.content}
            </div>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <g
      style={{
        opacity: visible ? 1 : 0,
        pointerEvents: visible ? "auto" : "none",
        transition: "opacity 0.4s ease-out",
        transitionDelay: visible ? "0.4s" : "0s"
      }}
    >
      <circle
        cx={coords.x}
        cy={coords.y}
        r={r}
        className={circleClass}
        filter={filterUrl || undefined}
        onClick={(e) => handleNodeClick(e, node)}
      />
      <foreignObject
        x={foX}
        y={foY}
        width={foWidth}
        height={foHeight}
        pointerEvents={visible ? "auto" : "none"}
        className={styles.foreignObjectWrapper}
      >
        <div
          className={styles.topLabelContainer}
          style={{ pointerEvents: visible ? "auto" : "none" }}
          onClick={(e) => handleNodeClick(e, node)}
        >
          {renderLabelContent()}
        </div>
      </foreignObject>
    </g>
  );
}
