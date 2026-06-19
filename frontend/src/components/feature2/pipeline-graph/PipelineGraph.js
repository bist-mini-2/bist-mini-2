"use client"
 
import { useRef } from "react";
import styles from "./PipelineGraph.module.css";
import usePipelineLayout from "./usePipelineLayout";
import GraphConnectors from "./GraphConnectors";
import GraphNode from "./GraphNode";

/**
 * 대화형 유기적 원형 그래프 (Circular Focus Graph) 메인 컴포넌트입니다.
 * 서브 컴포넌트 모듈과 layout 훅을 통합하여 조립합니다.
 * 
 * @param {Object} props
 * @param {Object} props.result ResearchGapMatrix 결과 DTO 데이터
 * @param {string} props.query 사용자가 검색한 원본 질의어
 */
export default function PipelineGraph({ result, query }) {
  const canvasWidth = 1460;
  const canvasHeight = 780;
  const containerRef = useRef(null);

  const layout = usePipelineLayout({
    result,
    query,
    canvasWidth,
    canvasHeight,
    containerRef
  });

  if (!result || !result.papers || result.papers.length === 0) {
    return null;
  }

  // 베지어 곡선 생성 헬퍼 함수
  const getBezierPath = (x1, y1, x2, y2) => {
    const controlX = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${controlX} ${y1}, ${controlX} ${y2}, ${x2} ${y2}`;
  };

  let cursorClass = "";
  if (layout.isSpacePressed) {
    cursorClass = layout.isPanning ? styles.grabbingCursor : styles.grabCursor;
  }

  return (
    <div className={`card shadow-sm p-4 border border-light-subtle ${styles.graphWrapper}`}>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h5 className="fw-bold text-gradient mb-0">분석 파이프라인 흐름 시각화</h5>
        <span className={styles.monoBadge}>Interactive Mindmap</span>
      </div>

      {/* SVG Canvas Container */}
      <div
        ref={containerRef}
        className={`${styles.svgContainer} ${cursorClass}`}
        onMouseEnter={() => layout.setIsHovered(true)}
        onMouseLeave={() => {
          layout.setIsHovered(false);
          layout.setIsPanning(false);
        }}
        onMouseDown={layout.handleMouseDown}
        onMouseMove={layout.handleMouseMove}
        onMouseUp={layout.handleMouseUp}
      >
        {/* Floating Zoom & Control Toolbar */}
        <div className={styles.controlToolbar}>
          <button type="button" className={styles.toolBtn} onClick={layout.zoomIn} title="확대">
            <i className="bi bi-zoom-in"></i>
          </button>
          <button type="button" className={styles.toolBtn} onClick={layout.zoomOut} title="축소">
            <i className="bi bi-zoom-out"></i>
          </button>
          <button type="button" className={styles.toolBtn} onClick={layout.resetZoomAndPan} title="초기화">
            <i className="bi bi-arrow-counterclockwise"></i>
          </button>
          <div className={styles.toolDivider}></div>
          <span className={styles.zoomText}>{Math.round(layout.scale * 100)}%</span>
        </div>

        {/* Short Guideline Indicator */}
        <div className={styles.guideBadge}>
          <i className="bi bi-info-circle-fill me-1"></i>
          <span>노드 클릭 시 카메라 줌-포커싱 | Space+드래그로 캔버스 이동</span>
        </div>

        {/* SVG Canvas Draw */}
        <svg
          viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
          width="100%"
          height="100%"
          className={styles.svgCanvas}
        >
          <defs>
            <filter id="neon-glow-query" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feComponentTransfer in="blur" result="glow1">
                <feFuncA type="linear" slope="0.6"/>
              </feComponentTransfer>
              <feMerge>
                <feMergeNode in="glow1" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            
            <filter id="neon-glow-paper" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feComponentTransfer in="blur" result="glow1">
                <feFuncA type="linear" slope="0.6"/>
              </feComponentTransfer>
              <feMerge>
                <feMergeNode in="glow1" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <filter id="neon-glow-common" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="10" result="blur" />
              <feComponentTransfer in="blur" result="glow1">
                <feFuncA type="linear" slope="0.7"/>
              </feComponentTransfer>
              <feMerge>
                <feMergeNode in="glow1" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Zoom & Pan 조작 대상 그룹 */}
          <g
            style={{
              transform: `translate(${layout.panOffset.x}px, ${layout.panOffset.y}px) scale(${layout.scale})`,
              transformOrigin: "0 0"
            }}
            className={styles.zoomGroup}
          >
            {/* 1. 커넥터 라인들 (배경선 + 흐름선) */}
            <GraphConnectors
              queryNode={layout.queryNode}
              paperNodes={layout.paperNodes}
              solvedNodes={layout.solvedNodes}
              limitationNodes={layout.limitationNodes}
              commonNode={layout.commonNode}
              directionNodes={layout.directionNodes}
              activeFocusNode={layout.activeFocusNode}
              getRepulsedCoords={layout.getRepulsedCoords}
              getBezierPath={getBezierPath}
              isNodeVisible={layout.isNodeVisible}
              styles={styles}
            />

            {/* 2. 원형 노드들 (Circle Nodes) */}
            
            {/* Query Node */}
            <GraphNode
              node={layout.queryNode}
              nodeType="query"
              visible={layout.isNodeVisible(layout.queryNode.id)}
              isFocused={layout.activeFocusNode === layout.queryNode.id}
              isSelected={layout.selectedNode?.type === layout.queryNode.id}
              coords={layout.getRepulsedCoords(layout.queryNode.id, layout.queryNode.x, layout.queryNode.y)}
              r={layout.getCircleRadius(layout.queryNode.id, layout.queryNode.r)}
              styles={styles}
              handleNodeClick={layout.handleNodeClick}
              activeFocusNode={layout.activeFocusNode}
            />

            {/* Paper Nodes */}
            {layout.paperNodes.map((paper) => (
              <GraphNode
                key={paper.id}
                node={paper}
                nodeType="paper"
                visible={layout.isNodeVisible(paper.id)}
                isFocused={layout.activeFocusNode === paper.id}
                isSelected={layout.selectedNode?.type === paper.id}
                coords={layout.getRepulsedCoords(paper.id, paper.x, paper.y)}
                r={layout.getCircleRadius(paper.id, paper.r)}
                styles={styles}
                handleNodeClick={layout.handleNodeClick}
                activeFocusNode={layout.activeFocusNode}
              />
            ))}

            {/* Solved Sub-nodes */}
            {layout.solvedNodes.map((solved) => (
              <GraphNode
                key={solved.id}
                node={solved}
                nodeType="solved"
                visible={layout.isNodeVisible(solved.id)}
                isFocused={layout.activeFocusNode === solved.id}
                isSelected={layout.selectedNode?.type === solved.id}
                coords={layout.getRepulsedCoords(solved.id, solved.x, solved.y)}
                r={layout.getCircleRadius(solved.id, solved.r)}
                styles={styles}
                handleNodeClick={layout.handleNodeClick}
                activeFocusNode={layout.activeFocusNode}
              />
            ))}

            {/* Limitation Sub-nodes */}
            {layout.limitationNodes.map((limit) => (
              <GraphNode
                key={limit.id}
                node={limit}
                nodeType="limitation"
                visible={layout.isNodeVisible(limit.id)}
                isFocused={layout.activeFocusNode === limit.id}
                isSelected={layout.selectedNode?.type === limit.id}
                coords={layout.getRepulsedCoords(limit.id, limit.x, limit.y)}
                r={layout.getCircleRadius(limit.id, limit.r)}
                styles={styles}
                handleNodeClick={layout.handleNodeClick}
                activeFocusNode={layout.activeFocusNode}
              />
            ))}

            {/* Common Limitations Node */}
            <GraphNode
              node={layout.commonNode}
              nodeType="common"
              visible={layout.isNodeVisible(layout.commonNode.id)}
              isFocused={layout.activeFocusNode === layout.commonNode.id}
              isSelected={layout.selectedNode?.type === layout.commonNode.id}
              coords={layout.getRepulsedCoords(layout.commonNode.id, layout.commonNode.x, layout.commonNode.y)}
              r={layout.getCircleRadius(layout.commonNode.id, layout.commonNode.r)}
              styles={styles}
              handleNodeClick={layout.handleNodeClick}
              activeFocusNode={layout.activeFocusNode}
            />

            {/* Suggested Direction Nodes */}
            {layout.directionNodes.map((dir) => (
              <GraphNode
                key={dir.id}
                node={dir}
                nodeType="direction"
                visible={layout.isNodeVisible(dir.id)}
                isFocused={layout.activeFocusNode === dir.id}
                isSelected={layout.selectedNode?.type === dir.id}
                coords={layout.getRepulsedCoords(dir.id, dir.x, dir.y)}
                r={layout.getCircleRadius(dir.id, dir.r)}
                styles={styles}
                handleNodeClick={layout.handleNodeClick}
                activeFocusNode={layout.activeFocusNode}
              />
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}
