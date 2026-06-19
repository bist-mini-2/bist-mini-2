"use client"

import { useState, useEffect, useRef } from "react";
import styles from "./PipelineGraph.module.css";

/**
 * 대화형 유기적 원형 그래프 (Circular Focus Graph) 컴포넌트입니다.
 * 원형 노드 배치, 노드 포커스 시 카메라 줌-인/이동, 자식 노드 동적 전개 기능이 탑재되었습니다.
 * 
 * @param {Object} props
 * @param {Object} props.result ResearchGapMatrix 결과 DTO 데이터
 * @param {string} props.query 사용자가 검색한 원본 질의어
 */
export default function PipelineGraph({ result, query }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeFocusNode, setActiveFocusNode] = useState(null); // 'query', 'paper-i', 'solved-i', 'limitation-i', 'common', 'direction-i'

  // 줌 & 팬 상태 관리
  const [scale, setScale] = useState(1.0);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const containerRef = useRef(null);

  // 휠 스크롤 줌 기능 바인딩 (passive: false로 직접 추가하여 브라우저 기본 스크롤 방지)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheelZoom = (e) => {
      e.preventDefault(); // 브라우저 창 스크롤 방지
      const zoomSpeed = 0.05;
      setScale((prevScale) => {
        const nextScale = e.deltaY < 0 ? prevScale + zoomSpeed : prevScale - zoomSpeed;
        return Math.min(Math.max(nextScale, 0.5), 3.0); // 0.5배 ~ 3.0배 제한
      });
    };

    container.addEventListener("wheel", handleWheelZoom, { passive: false });
    return () => {
      container.removeEventListener("wheel", handleWheelZoom);
    };
  }, []);

  // 스페이스바 키 이벤트 바인딩 (컨테이너 호버 중에만 전역 스페이스바 바인딩)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.code === "Space") {
        e.preventDefault(); // 브라우저 스페이스바 스크롤 방지
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

  if (!result || !result.papers || result.papers.length === 0) {
    return null;
  }

  const papers = result.papers;
  const commonLimitations = result.common_limitations || [];
  const suggestedDirections = result.suggested_directions || [];

  // SVG 캔버스 고정 해상도 좌표계 (1460 x 780)
  const canvasWidth = 1460;
  const canvasHeight = 780;

  // --- 레이아웃 좌표 계산 알고리즘 ---

  // 1단계: Query Node (중앙 좌측)
  const queryNode = {
    id: "query",
    x: 180,
    y: 390,
    r: 45,
    title: "연구 질문 / 검색 쿼리",
    content: query || "입력된 검색어"
  };

  // 2단계: 수집된 논문 노드들 (Query 노드 주변에 방사형 반원 궤도 배치)
  const R_papers = 280; // Query 노드로부터의 반경
  const paperAngleRange = 2.4; // 논문들이 퍼질 총 각도 폭 (라디안)
  const paperNodes = [];
  for (let i = 0; i < papers.length; i++) {
    const paper = papers[i];
    // -1.2 ~ +1.2 라디안 범위로 우측으로 고르게 방사형 배치
    const angle = papers.length > 1
      ? -paperAngleRange / 2 + i * (paperAngleRange / (papers.length - 1))
      : 0;
    
    paperNodes.push({
      id: `paper-${i}`,
      x: queryNode.x + R_papers * Math.cos(angle),
      y: queryNode.y + R_papers * Math.sin(angle),
      r: 38,
      title: paper.title,
      similarity: paper.similarity,
      problems_solved: paper.problems_solved || [],
      limitations: paper.limitations || [],
      arxiv_id: paper.arxiv_id || "arXiv id"
    });
  }

  // 3단계: 하위 서브 노드들 (Solved 및 Limitation 노드)
  // 클릭된 논문 주변에 넓게 부채꼴 형태로 전개되도록 설정
  const solvedNodes = [];
  const limitationNodes = [];
  for (let i = 0; i < papers.length; i++) {
    const paper = paperNodes[i];

    const solvedList = paper.problems_solved || [];
    const limitList = paper.limitations || [];
    const numSolved = solvedList.length;
    const numLimit = limitList.length;
    const totalChildren = numSolved + numLimit;

    // 자식 노드가 많을수록 전개 반경을 넓힘
    const R_child = 190 + totalChildren * 12;

    // 자식 노드들의 균등 각도 분배 (Solved/Limitation 구분 없이 통합 부채꼴 배치)
    let childAngles = [];
    if (totalChildren === 1) {
      childAngles = [0]; // 1개일 때는 우측 정면 배치
    } else if (totalChildren > 1) {
      // 자식 개수가 많을수록 넓게 펼치며, 최대 144도 (Math.PI * 0.8) 범위로 제한해 Query 노드 침범을 원천 차단
      const maxSpread = Math.PI * 0.8; 
      const spreadAngle = Math.min(maxSpread, (totalChildren - 1) * (Math.PI * 0.22));
      const startAngle = -spreadAngle / 2;
      const angleGap = spreadAngle / (totalChildren - 1);
      for (let j = 0; j < totalChildren; j++) {
        childAngles.push(startAngle + j * angleGap);
      }
    }

    // Solved 노드 생성 (통합 인덱스 0 ~ numSolved-1 배치)
    for (let j = 0; j < numSolved; j++) {
      const angle = childAngles[j];
      const currentR = R_child; // 균일한 동심원상 배치

      solvedNodes.push({
        id: `solved-${i}-${j}`,
        parentId: `paper-${i}`,
        parentX: paper.x,
        parentY: paper.y,
        x: paper.x + currentR * Math.cos(angle),
        y: paper.y + currentR * Math.sin(angle),
        r: 28,
        angle: angle, // 각도 정보 보관
        title: numSolved > 1 ? `Solved ${j + 1}` : "Solved",
        content: solvedList[j] || "해결 과제 정보가 없습니다.",
        problems_solved: solvedList
      });
    }

    // Limitation 노드 생성 (통합 인덱스 numSolved ~ totalChildren-1 배치)
    for (let j = 0; j < numLimit; j++) {
      const angle = childAngles[numSolved + j];
      const currentR = R_child; // 균일한 동심원상 배치

      limitationNodes.push({
        id: `limitation-${i}-${j}`,
        parentId: `paper-${i}`,
        parentX: paper.x,
        parentY: paper.y,
        x: paper.x + currentR * Math.cos(angle),
        y: paper.y + currentR * Math.sin(angle),
        r: 28,
        angle: angle, // 각도 정보 보관
        title: numLimit > 1 ? `Limitation ${j + 1}` : "Limitation",
        content: limitList[j] || "한계점 정보가 없습니다.",
        limitations: limitList
      });
    }
  }

  // 4단계: 공통 한계점 노드 (중앙 우측 배치)
  const commonNode = {
    id: "common",
    x: 820,
    y: 390,
    r: 52,
    title: "공통 연구 공백 (GAP)",
    items: commonLimitations
  };

  // 5단계: 추천 방향 노드들 (오른쪽 열 수직 배치)
  const dirX = 1180;
  const dirPaddingTop = 100;
  const dirAvailableHeight = canvasHeight - dirPaddingTop * 2;
  const dirGap = suggestedDirections.length > 1
    ? dirAvailableHeight / (suggestedDirections.length - 1)
    : 0;

  const directionNodes = [];
  for (let i = 0; i < suggestedDirections.length; i++) {
    directionNodes.push({
      id: `direction-${i}`,
      x: dirX,
      y: dirPaddingTop + i * dirGap,
      r: 44,
      title: `추천 연구 주제 ${i + 1}`,
      content: suggestedDirections[i],
      index: i
    });
  }

  // --- 동적 척력(Repulsion) 및 크기 확장 헬퍼 함수 ---

  // 노드 원형 크기 동적 확장 (포커스 시 1.4배 확장)
  const getCircleRadius = (nodeId, baseRadius) => {
    if (activeFocusNode === nodeId) {
      return baseRadius * 1.4;
    }
    return baseRadius;
  };

  // 동일 레벨 형제 노드 외곽으로 튕겨내는 척력 좌표 계산
  const getRepulsedCoords = (nodeId, origX, origY) => {
    if (!activeFocusNode) return { x: origX, y: origY };
    if (activeFocusNode === nodeId) return { x: origX, y: origY }; // 자기 자신은 고정

    // 포커싱된 기준 노드 좌표 구하기
    let focusNode = null;
    if (activeFocusNode === "query") focusNode = queryNode;
    else if (activeFocusNode === "common") focusNode = commonNode;
    else if (activeFocusNode.startsWith("paper-")) {
      focusNode = paperNodes.find(n => n.id === activeFocusNode);
    } else if (activeFocusNode.startsWith("direction-")) {
      focusNode = directionNodes.find(n => n.id === activeFocusNode);
    } else if (activeFocusNode.startsWith("solved-")) {
      focusNode = solvedNodes.find(n => n.id === activeFocusNode);
    } else if (activeFocusNode.startsWith("limitation-")) {
      focusNode = limitationNodes.find(n => n.id === activeFocusNode);
    }

    if (!focusNode) return { x: origX, y: origY };

    // 공통 연구 공백(Common GAP) 노드가 포커싱되었을 때의 특별한 위치 재정의 로직
    if (activeFocusNode === "common" && nodeId.startsWith("limitation-")) {
      const totalLimit = limitationNodes.length;
      const selfIdx = limitationNodes.findIndex(n => n.id === nodeId);
      
      if (selfIdx !== -1) {
        // 공통 GAP 노드의 좌측 반원 범위 (약 120도 ~ 240도, 즉 Math.PI * 0.65 ~ Math.PI * 1.35)로 분배
        const R_common_child = 240 + totalLimit * 4; // 자식 개수에 따라 살짝 팽창
        const spreadAngle = Math.PI * 0.75; // 135도 폭
        const startAngle = Math.PI - spreadAngle / 2; // 약 112.5도
        const angleGap = totalLimit > 1 ? spreadAngle / (totalLimit - 1) : 0;
        const angle = startAngle + selfIdx * angleGap;
        
        return {
          x: focusNode.x + R_common_child * Math.cos(angle),
          y: focusNode.y + R_common_child * Math.sin(angle)
        };
      }
    }

    // 형제 노드 여부 검사 (같은 계열)
    const isBrother = 
      (activeFocusNode.startsWith("paper-") && nodeId.startsWith("paper-")) ||
      (activeFocusNode.startsWith("direction-") && nodeId.startsWith("direction-")) ||
      (activeFocusNode.startsWith("solved-") && nodeId.startsWith("solved-")) ||
      (activeFocusNode.startsWith("limitation-") && nodeId.startsWith("limitation-"));

    if (isBrother) {
      const dx = origX - focusNode.x;
      const dy = origY - focusNode.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const pushFactor = 2.8; // 2.8배 먼 곳으로 튕김
      return {
        x: focusNode.x + dx * pushFactor,
        y: focusNode.y + dy * pushFactor
      };
    }

    // 만약 paper 노드가 포커싱되어 있으면, query 노드는 450px 만큼 왼쪽으로 밀어서 충돌이나 겹침 방지
    if (activeFocusNode.startsWith("paper-") && nodeId === "query") {
      return { x: origX - 450, y: origY };
    }

    return { x: origX, y: origY };
  };

  // --- 카메라 포커싱 & 가시성 규칙 (Visibility rules) ---

  const focusOnNode = (nodeId, x, y) => {
    const targetScale = nodeId === "common" ? 1.1 : 1.2;
    if (activeFocusNode === nodeId) {
      // 포커스 리셋
      setScale(1.0);
      setPanOffset({ x: 0, y: 0 });
      setActiveFocusNode(null);
    } else {
      // 카메라 줌인 무빙 공식 적용
      const newX = canvasWidth / 2 - x * targetScale;
      const newY = canvasHeight / 2 - y * targetScale;
      setPanOffset({ x: newX, y: newY });
      setScale(targetScale);
      setActiveFocusNode(nodeId);
    }
  };

  // 노드 가시성 여부 확인
  const isNodeVisible = (nodeId) => {
    if (!activeFocusNode) {
      // 대기 상태(포커스 없음) 시: Solved/Limitation 자식 노드만 숨김
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

  // 베지어 곡선 생성 헬퍼 함수
  const getBezierPath = (x1, y1, x2, y2) => {
    const controlX = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${controlX} ${y1}, ${controlX} ${y2}, ${x2} ${y2}`;
  };

  // 노드 카드 클릭 핸들러
  const handleNodeClick = (e, node) => {
    e.stopPropagation();
    if (isSpacePressed) return;
    if (!isNodeVisible(node.id)) return;
    // 척력이 적용된 실제 렌더링 좌표를 구하여 카메라 시점 중심으로 이동시킵니다.
    const repulsed = getRepulsedCoords(node.id, node.x, node.y);
    focusOnNode(node.id, repulsed.x, repulsed.y);
    setSelectedNode((prev) => (prev?.type === node.id ? null : { type: node.id, data: node }));
  };

  // 마우스 드래그 앤 팬 이벤트 핸들러
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
    setActiveFocusNode(null);
  };

  let cursorClass = "";
  if (isSpacePressed) {
    cursorClass = isPanning ? styles.grabbingCursor : styles.grabCursor;
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
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => {
          setIsHovered(false);
          setIsPanning(false);
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        {/* Floating Zoom & Control Toolbar */}
        <div className={styles.controlToolbar}>
          <button type="button" className={styles.toolBtn} onClick={zoomIn} title="확대">
            <i className="bi bi-zoom-in"></i>
          </button>
          <button type="button" className={styles.toolBtn} onClick={zoomOut} title="축소">
            <i className="bi bi-zoom-out"></i>
          </button>
          <button type="button" className={styles.toolBtn} onClick={resetZoomAndPan} title="초기화">
            <i className="bi bi-arrow-counterclockwise"></i>
          </button>
          <div className={styles.toolDivider}></div>
          <span className={styles.zoomText}>{Math.round(scale * 100)}%</span>
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
              transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${scale})`,
              transformOrigin: "0 0"
            }}
            className={styles.zoomGroup}
          >
            {/* 1. 커넥터 라인들 (배경선 + 흐름선) */}
            
            {/* Query Node -> Papers */}
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

            {/* Papers -> Sub-nodes (Solved / Limitation) */}
            {solvedNodes.map((solved, idx) => {
              const paper = paperNodes.find(n => n.id === solved.parentId);
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
            {limitationNodes.map((limit, idx) => {
              const paper = paperNodes.find(n => n.id === limit.parentId);
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

            {/* Limitation Sub-nodes -> Common Limitations */}
            {limitationNodes.map((limit, idx) => {
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

            {/* Common Limitations -> Directions */}
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

            {/* Direct Connectors (Paper Nodes -> Common GAP Node) when no node is focused */}
            {paperNodes.map((paper, idx) => {
              const pCoords = getRepulsedCoords(paper.id, paper.x, paper.y);
              const cCoords = getRepulsedCoords(commonNode.id, commonNode.x, commonNode.y);
              const path = getBezierPath(pCoords.x, pCoords.y, cCoords.x, cCoords.y);
              const visible = !activeFocusNode || activeFocusNode === "common";
              
              // 루트 상태(activeFocusNode === null)일 때는 1.0으로 선명하게 표시,
              // 공통 공백(common) 포커스 상태일 때는 0.35로 희미하게 처리
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

            {/* 2. 원형 노드들 (Circle Nodes) */}

            {/* Query Node */}
            {(() => {
              const coords = getRepulsedCoords(queryNode.id, queryNode.x, queryNode.y);
              const r = getCircleRadius(queryNode.id, queryNode.r);
              const visible = isNodeVisible(queryNode.id);
              const isSelected = selectedNode?.type === queryNode.id;
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
                    className={`${styles.circleNode} ${styles.queryCircle} ${isSelected ? styles.selected : ""}`}
                    filter="url(#neon-glow-query)"
                    onClick={(e) => handleNodeClick(e, queryNode)}
                  />
                  <foreignObject
                    x={coords.x - (isSelected ? 150 : 110)}
                    y={coords.y + r + 10}
                    width={isSelected ? 300 : 220}
                    height={isSelected ? 200 : 80}
                    pointerEvents={visible ? "auto" : "none"}
                    className={styles.foreignObjectWrapper}
                  >
                    <div className={styles.topLabelContainer} style={{ pointerEvents: visible ? "auto" : "none" }} onClick={(e) => handleNodeClick(e, queryNode)}>
                      <div className={styles.queryTitle}>
                        {queryNode.title}
                      </div>
                      <div className={isSelected ? styles.queryContentExpanded : styles.queryContent}>
                        {queryNode.content}
                      </div>
                    </div>
                  </foreignObject>
                </g>
              );
            })()}

            {/* Paper Nodes */}
            {paperNodes.map((paper, idx) => {
              const visible = isNodeVisible(paper.id);
              const coords = getRepulsedCoords(paper.id, paper.x, paper.y);
              const r = getCircleRadius(paper.id, paper.r);
              const isSelected = selectedNode?.type === paper.id;
              return (
                <g
                  key={paper.id}
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
                    className={`${styles.circleNode} ${styles.paperCircle} ${isSelected ? styles.selected : ""}`}
                    filter="url(#neon-glow-paper)"
                    onClick={(e) => handleNodeClick(e, paper)}
                  />
                  <foreignObject
                    x={coords.x - (isSelected ? 140 : 85)}
                    y={coords.y + r + 8}
                    width={isSelected ? 280 : 170}
                    height={isSelected ? 150 : 60}
                    pointerEvents={visible ? "auto" : "none"}
                    className={styles.foreignObjectWrapper}
                  >
                    <div className={styles.topLabelContainer} style={{ pointerEvents: visible ? "auto" : "none" }} onClick={(e) => handleNodeClick(e, paper)}>
                      <div className={isSelected ? styles.paperTitleExpanded : styles.paperTitle}>
                        {paper.title}
                      </div>
                    </div>
                  </foreignObject>
                </g>
              );
            })}

            {/* Solved Sub-nodes */}
            {solvedNodes.map((solved, idx) => {
              const visible = isNodeVisible(solved.id);
              const coords = getRepulsedCoords(solved.id, solved.x, solved.y);
              const r = getCircleRadius(solved.id, solved.r);
              const isFocused = activeFocusNode === solved.id;

              // 실제 부모와 자식 간의 척력 적용 후 좌표 기준 엣지 진행각 계산
              const pCoords = getRepulsedCoords(solved.parentId, solved.parentX, solved.parentY);
              const dx = coords.x - pCoords.x;
              const dy = coords.y - pCoords.y;
              const actualAngle = Math.atan2(dy, dx);

              // 방사형 텍스트 레이블 중심점 및 영역 좌표 연산
              const foWidth = isFocused ? 260 : 150;
              const foHeight = isFocused ? 180 : 110;
              const contentHeight = 65;
              const margin = 15;
              const visualBias = 6 * (Math.sin(actualAngle) + 1);

              const d = r + margin + visualBias + (foWidth / 2) * Math.abs(Math.cos(actualAngle)) + (contentHeight / 2) * Math.abs(Math.sin(actualAngle));

              const text_cx = coords.x + d * Math.cos(actualAngle);
              const text_cy = coords.y + d * Math.sin(actualAngle);

              // 포커스 상태일 때는 노드 바로 밑에 정직하게 배치, 비포커스일 때만 방사형 배치
              const foX = isFocused ? coords.x - foWidth / 2 : text_cx - foWidth / 2;
              const foY = isFocused ? coords.y + r + 15 : text_cy - foHeight / 2;

              return (
                <g
                  key={solved.id}
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
                    className={`${styles.circleNode} ${styles.solvedCircle} ${selectedNode?.type === solved.id ? styles.selected : ""}`}
                    onClick={(e) => handleNodeClick(e, solved)}
                  />
                  <foreignObject
                    x={foX}
                    y={foY}
                    width={foWidth}
                    height={foHeight}
                    pointerEvents={visible ? "auto" : "none"}
                    className={styles.foreignObjectWrapper}
                  >
                    <div className={styles.topLabelContainer} style={{ pointerEvents: visible ? "auto" : "none" }} onClick={(e) => handleNodeClick(e, solved)}>
                      <div className={styles.solvedTitle}>
                        {solved.title}
                      </div>
                      <div className={styles.solvedContent}>
                        {solved.content}
                      </div>
                    </div>
                  </foreignObject>
                </g>
              );
            })}

            {/* Limitation Sub-nodes */}
            {limitationNodes.map((limit, idx) => {
              const visible = isNodeVisible(limit.id);
              const coords = getRepulsedCoords(limit.id, limit.x, limit.y);
              const r = getCircleRadius(limit.id, limit.r);
              const isFocused = activeFocusNode === limit.id;

              // 실제 부모와 자식 간의 척력 적용 후 좌표 기준 엣지 진행각 계산 (반대방향 배치)
              // 공통 연구 공백(common) 포커스 시에는 공통 노드 기준으로 각도를 계산하여 글상자를 바깥쪽(좌측 외곽)으로 안전하게 밀어냄
              const pCoords = getRepulsedCoords(limit.parentId, limit.parentX, limit.parentY);
              const baseCoords = activeFocusNode === "common" ? getRepulsedCoords("common", commonNode.x, commonNode.y) : pCoords;
              const dx = coords.x - baseCoords.x;
              const dy = coords.y - baseCoords.y;
              const actualAngle = Math.atan2(dy, dx);

              // 방사형 텍스트 레이블 중심점 및 영역 좌표 연산
              const foWidth = isFocused ? 260 : 150;
              const foHeight = isFocused ? 180 : 110;
              const contentHeight = 65;
              const margin = 15;
              const visualBias = 6 * (Math.sin(actualAngle) + 1);

              const d = r + margin + visualBias + (foWidth / 2) * Math.abs(Math.cos(actualAngle)) + (contentHeight / 2) * Math.abs(Math.sin(actualAngle));

              const text_cx = coords.x + d * Math.cos(actualAngle);
              const text_cy = coords.y + d * Math.sin(actualAngle);

              // 포커스 상태일 때는 노드 바로 밑에 정직하게 배치, 비포커스일 때만 방사형 배치
              const foX = isFocused ? coords.x - foWidth / 2 : text_cx - foWidth / 2;
              const foY = isFocused ? coords.y + r + 15 : text_cy - foHeight / 2;

              return (
                <g
                  key={limit.id}
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
                    className={`${styles.circleNode} ${styles.limitCircle} ${selectedNode?.type === limit.id ? styles.selected : ""}`}
                    onClick={(e) => handleNodeClick(e, limit)}
                  />
                  <foreignObject
                    x={foX}
                    y={foY}
                    width={foWidth}
                    height={foHeight}
                    pointerEvents={visible ? "auto" : "none"}
                    className={styles.foreignObjectWrapper}
                  >
                    <div className={styles.topLabelContainer} style={{ pointerEvents: visible ? "auto" : "none" }} onClick={(e) => handleNodeClick(e, limit)}>
                      <div className={styles.limitTitle}>
                        {limit.title}
                      </div>
                      <div className={styles.limitContent}>
                        {limit.content}
                      </div>
                    </div>
                  </foreignObject>
                </g>
              );
            })}

            {/* Common Limitations Node */}
            {(() => {
              const coords = getRepulsedCoords(commonNode.id, commonNode.x, commonNode.y);
              const r = getCircleRadius(commonNode.id, commonNode.r);
              const visible = isNodeVisible(commonNode.id);
              const isSelected = selectedNode?.type === commonNode.id;
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
                    className={`${styles.circleNode} ${styles.commonCircle} ${selectedNode?.type === commonNode.id ? styles.selected : ""}`}
                    filter="url(#neon-glow-common)"
                    onClick={(e) => handleNodeClick(e, commonNode)}
                  />
                  <foreignObject
                    x={coords.x - 90}
                    y={coords.y + r + 10}
                    width={180}
                    height={80}
                    pointerEvents={visible ? "auto" : "none"}
                    className={styles.foreignObjectWrapper}
                  >
                    <div className={styles.topLabelContainer} style={{ pointerEvents: visible ? "auto" : "none" }} onClick={(e) => handleNodeClick(e, commonNode)}>
                      <div className={styles.commonTitle}>
                        {commonNode.title}
                      </div>
                      <div className={styles.commonContent}>
                        공통 공백 {commonLimitations.length}건 도출됨
                      </div>
                    </div>
                  </foreignObject>
                </g>
              );
            })()}

            {/* Suggested Direction Nodes */}
            {directionNodes.map((dir, idx) => {
              const visible = isNodeVisible(dir.id);
              const coords = getRepulsedCoords(dir.id, dir.x, dir.y);
              const r = getCircleRadius(dir.id, dir.r);
              const isSelected = selectedNode?.type === dir.id;
              return (
                <g
                  key={dir.id}
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
                    className={`${styles.circleNode} ${styles.directionCircle} ${isSelected ? styles.selected : ""}`}
                    onClick={(e) => handleNodeClick(e, dir)}
                  />
                  <foreignObject
                    x={coords.x - 100}
                    y={coords.y + r + 8}
                    width={200}
                    height={isSelected ? 180 : 80}
                    pointerEvents={visible ? "auto" : "none"}
                    className={styles.foreignObjectWrapper}
                  >
                    <div className={styles.topLabelContainer} style={{ pointerEvents: visible ? "auto" : "none" }} onClick={(e) => handleNodeClick(e, dir)}>
                      <div className={isSelected ? styles.directionTitleExpanded : styles.directionTitle}>
                        {dir.title}
                      </div>
                      <div className={isSelected ? styles.directionContentTextExpanded : styles.directionContentText}>
                        {dir.content}
                      </div>
                    </div>
                  </foreignObject>
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {/* 3. 선택 노드의 상세 정보 패널 */}
      <div className={`card shadow-sm p-4 border border-light-subtle ${styles.detailPanel}`}>
        {!selectedNode ? (
          <div className={styles.placeholderPanel}>
            <i className="bi bi-info-circle me-2"></i>
            마인드맵의 원형 노드를 클릭하여 해당 부모 노드로 줌인(Camera Focus)하고, 방사형으로 전개되는 상세 분석 정보를 검토해보세요.
          </div>
        ) : (
          <div className={styles.activePanel}>
            {selectedNode.type === "query" && (
              <div>
                <h4 className={styles.panelTitle}>
                  <i className="bi bi-search text-info me-2"></i>
                  입력 검색 쿼리 상세
                </h4>
                <div className={styles.panelContentBox}>
                  <strong>사용자 질의어:</strong>
                  <p className={styles.queryContent}>{selectedNode.data.content}</p>
                  <span className={styles.helperText}>
                    이 키워드를 3072차원 고밀도 벡터로 임베딩하여 로컬 pgvector 라이브러리에서 최신 관련 논문군을 다차원으로 탐색했습니다.
                  </span>
                </div>
              </div>
            )}

            {selectedNode.type.startsWith("paper-") && (
              <div>
                <h4 className={styles.panelTitle}>
                  <i className="bi bi-journal-text text-primary me-2"></i>
                  {selectedNode.data.title} 상세 분석 리포트
                </h4>
                <p className={styles.paperTitleText}><strong>제목:</strong> {selectedNode.data.title}</p>
                <p className={styles.arxivIdText}><strong>ArXiv ID:</strong> {selectedNode.data.arxiv_id}</p>

                <div className="row mt-3">
                  <div className="col-md-6 mb-3">
                    <div className={styles.listSection}>
                      <span className={`${styles.badge} ${styles.badgeSolved}`}>
                        <i className="bi bi-check-circle-fill me-1"></i> 해결 문제 및 제안 방법론
                      </span>
                      <ul className={styles.detailList}>
                        {selectedNode.data.problems_solved.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  <div className="col-md-6 mb-3">
                    <div className={styles.listSection}>
                      <span className={`${styles.badge} ${styles.badgeLimit}`}>
                        <i className="bi bi-slash-circle me-1"></i> 식별된 주요 한계점
                      </span>
                      <ul className={styles.detailList}>
                        {selectedNode.data.limitations.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {selectedNode.type.startsWith("solved-") && (
              <div>
                <h4 className={styles.panelTitle}>
                  <i className="bi bi-check-circle-fill text-success me-2"></i>
                  해결 문제 및 제안 방법론 상세
                </h4>
                <div className={styles.panelContentBox}>
                  <p className="mb-3">선택한 논문이 해결하고자 정의한 핵심 기술적 기여입니다:</p>
                  <ul className={styles.gapList}>
                    {selectedNode.data.problems_solved.map((item, idx) => (
                      <li key={idx}>
                        <i className="bi bi-check2-circle text-success me-2"></i>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {selectedNode.type.startsWith("limitation-") && (
              <div>
                <h4 className={styles.panelTitle}>
                  <i className="bi bi-slash-circle text-danger me-2"></i>
                  식별된 주요 한계점 상세
                </h4>
                <div className={styles.panelContentBox}>
                  <p className="mb-3">선택한 논문에서 향후 개선이 필요하거나 해결되지 않은 주요 제약점입니다:</p>
                  <ul className={styles.gapList}>
                    {selectedNode.data.limitations.map((item, idx) => (
                      <li key={idx}>
                        <i className="bi bi-exclamation-circle text-danger me-2"></i>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {selectedNode.type === "common" && (
              <div>
                <h4 className={styles.panelTitle}>
                  <i className="bi bi-exclamation-triangle-fill text-warning me-2"></i>
                  식별된 공통 연구 공백 (Common Research Gap)
                </h4>
                <div className={styles.panelContentBox}>
                  <p className="mb-3">검색된 후보 연구 논문군을 다차원 종합 분석하여 추출된 핵심 공통 결함 및 향후 극복해야 할 공백 영역입니다:</p>
                  <ul className={styles.gapList}>
                    {selectedNode.data.items.map((item, idx) => (
                      <li key={idx}>
                        <i className="bi bi-patch-exclamation text-danger me-2"></i>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {selectedNode.type.startsWith("direction-") && (
              <div>
                <h4 className={styles.panelTitle}>
                  <i className="bi bi-lightbulb-fill text-success me-2"></i>
                  추천 연구 주제 및 개발 로드맵 {selectedNode.data.index + 1}
                </h4>
                <div className={styles.panelContentBox}>
                  <div className={styles.directionHeader}>
                    <strong>제안 로드맵:</strong>
                  </div>
                  <p className={styles.directionContent}>{selectedNode.data.content}</p>
                  <span className={styles.helperText}>
                    위 공통 한계점(Research Gap)을 극복하고 논리적인 보완 방안을 결합하여 생성형 AI 에이전트가 제시하는 독창적인 연구 아이디어입니다.
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
