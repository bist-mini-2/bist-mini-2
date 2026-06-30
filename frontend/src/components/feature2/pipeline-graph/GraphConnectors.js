import React from "react";

/**
 * 마인드맵 그래프의 6가지 흐름선(QP, PSolved, PLimit, LC, CD, PC-Direct) 커넥터를 
 * 연쇄 트랜지션 효과를 담아 전담하여 렌더링하는 SVG 서브 컴포넌트입니다.
 */
export default function GraphConnectors({
  queryNode,
  paperNodes,
  solvedNodes,
  limitationNodes,
  commonNode,
  directionNodes,
  activeFocusNode,
  getRepulsedCoords,
  getBezierPath,
  isNodeVisible,
  styles
}) {
  return (
    <>
      {/* 1. Query Node -> Papers */}
      {paperNodes.map((paper, idx) => {
        const qCoords = getRepulsedCoords(queryNode.id, queryNode.x, queryNode.y);
        const pCoords = getRepulsedCoords(paper.id, paper.x, paper.y);
        const path = getBezierPath(qCoords.x, qCoords.y, pCoords.x, pCoords.y);
        const visible = isNodeVisible("query") && isNodeVisible(paper.id);
        return (
          <g
            key={`connector-qp-${idx}`}
            style={{
              opacity: visible ? 1 : 0,
              transition: "opacity 0.4s ease",
              transitionDelay: visible ? "0.4s" : "0s",
              pointerEvents: "none"
            }}
          >
            <path d={path} className={styles.connectorBg} />
            <path d={path} className={`${styles.connectorFlow} ${styles.flowQuery}`} />
          </g>
        );
      })}

      {/* 2. Papers -> Solved Sub-nodes */}
      {solvedNodes.map((solved) => {
        const paper = paperNodes.find((n) => n.id === solved.parentId);
        if (!paper) return null;
        const pCoords = getRepulsedCoords(paper.id, paper.x, paper.y);
        const sCoords = getRepulsedCoords(solved.id, solved.x, solved.y);
        const path = getBezierPath(pCoords.x, pCoords.y, sCoords.x, sCoords.y);
        const visible = isNodeVisible(paper.id) && isNodeVisible(solved.id);
        return (
          <g
            key={`connector-psolved-${solved.id}`}
            style={{
              opacity: visible ? 1 : 0,
              transition: "opacity 0.4s ease",
              transitionDelay: visible ? "0.4s" : "0s",
              pointerEvents: "none"
            }}
          >
            <path d={path} className={styles.connectorBg} />
            <path d={path} className={`${styles.connectorFlow} ${styles.flowDirection}`} />
          </g>
        );
      })}

      {/* 3. Papers -> Limitation Sub-nodes */}
      {limitationNodes.map((limit) => {
        const paper = paperNodes.find((n) => n.id === limit.parentId);
        if (!paper) return null;
        const pCoords = getRepulsedCoords(paper.id, paper.x, paper.y);
        const lCoords = getRepulsedCoords(limit.id, limit.x, limit.y);
        const path = getBezierPath(pCoords.x, pCoords.y, lCoords.x, lCoords.y);
        const visible = isNodeVisible(paper.id) && isNodeVisible(limit.id);
        return (
          <g
            key={`connector-plimit-${limit.id}`}
            style={{
              opacity: visible ? 1 : 0,
              transition: "opacity 0.4s ease",
              transitionDelay: visible ? "0.4s" : "0s",
              pointerEvents: "none"
            }}
          >
            <path d={path} className={styles.connectorBg} />
            <path d={path} className={`${styles.connectorFlow} ${styles.flowLimit}`} />
          </g>
        );
      })}

      {/* 4. Limitation Sub-nodes -> Common GAP Node */}
      {limitationNodes.map((limit) => {
        const lCoords = getRepulsedCoords(limit.id, limit.x, limit.y);
        const cCoords = getRepulsedCoords(commonNode.id, commonNode.x, commonNode.y);
        const path = getBezierPath(lCoords.x, lCoords.y, cCoords.x, cCoords.y);
        const visible = isNodeVisible(limit.id) && isNodeVisible("common");
        return (
          <g
            key={`connector-lc-${limit.id}`}
            style={{
              opacity: visible ? 1 : 0,
              transition: "opacity 0.4s ease",
              transitionDelay: visible ? "0.4s" : "0s",
              pointerEvents: "none"
            }}
          >
            <path d={path} className={styles.connectorBg} />
            <path d={path} className={`${styles.connectorFlow} ${styles.flowLimit}`} />
          </g>
        );
      })}

      {/* 5. Common Limitations -> Suggested Directions */}
      {directionNodes.map((dir, idx) => {
        const cCoords = getRepulsedCoords(commonNode.id, commonNode.x, commonNode.y);
        const dCoords = getRepulsedCoords(dir.id, dir.x, dir.y);
        const path = getBezierPath(cCoords.x, cCoords.y, dCoords.x, dCoords.y);
        const visible = isNodeVisible("common") && isNodeVisible(dir.id);
        return (
          <g
            key={`connector-cd-${idx}`}
            style={{
              opacity: visible ? 1 : 0,
              transition: "opacity 0.4s ease",
              transitionDelay: visible ? "0.4s" : "0s",
              pointerEvents: "none"
            }}
          >
            <path d={path} className={styles.connectorBg} />
            <path d={path} className={`${styles.connectorFlow} ${styles.flowCommon}`} />
          </g>
        );
      })}

      {/* 6. Direct Connectors (Paper Nodes -> Common GAP Node) */}
      {paperNodes.map((paper, idx) => {
        const pCoords = getRepulsedCoords(paper.id, paper.x, paper.y);
        const cCoords = getRepulsedCoords(commonNode.id, commonNode.x, commonNode.y);
        const path = getBezierPath(pCoords.x, pCoords.y, cCoords.x, cCoords.y);
        const visible = !activeFocusNode || activeFocusNode === "common";
        const opacityVal = activeFocusNode === "common" ? 0.35 : (visible ? 1.0 : 0);

        return (
          <g
            key={`connector-pc-direct-${idx}`}
            style={{
              opacity: opacityVal,
              transition: "opacity 0.4s ease-out",
              transitionDelay: activeFocusNode && visible ? "0.4s" : "0s",
              pointerEvents: "none"
            }}
          >
            <path d={path} className={styles.connectorBg} />
            <path d={path} className={`${styles.connectorFlow} ${styles.flowPaper}`} style={{ strokeDasharray: "4, 12" }} />
          </g>
        );
      })}
    </>
  );
}
