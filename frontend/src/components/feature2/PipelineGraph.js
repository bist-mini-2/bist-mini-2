"use client"

import { useState, useEffect, useRef } from "react";
import styles from "./PipelineGraph.module.css";

/**
 * 연구 공백 분석 흐름 시각화 (Pipeline Flow Graph) 컴포넌트입니다.
 * 줌(Zoom) & 팬(Pan) 조작 기능(마우스 휠, 스페이스바+좌클릭 드래그) 및 
 * 우상단 플로팅 컨트롤 툴바가 탑재되었습니다.
 * 
 * @param {Object} props
 * @param {Object} props.result ResearchGapMatrix 결과 DTO 데이터
 * @param {string} props.query 사용자가 검색한 원본 질의어
 */
export default function PipelineGraph({ result, query }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [expandedNodeId, setExpandedNodeId] = useState(null);

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

  // SVG 캔버스 고정 해상도 좌표계 (1300 x 720)
  const canvasWidth = 1300;
  const canvasHeight = 720;

  // 1단계: Query Node (단일 노드, 중앙 y: 360)
  const queryExpanded = expandedNodeId === "query";
  const queryWidth = 220;
  const queryHeight = queryExpanded ? 150 : 70;
  const queryNode = {
    id: "query",
    x: 20,
    y: 360 - queryHeight / 2,
    width: queryWidth,
    height: queryHeight,
    title: "연구 질문 / 검색 쿼리",
    content: query || "입력된 검색어"
  };

  // 2단계: 수집된 논문 노드들 (여러 노드, 동적 간격 분산)
  const topPadding = 35;
  const bottomPadding = 35;
  const availableHeight = canvasHeight - topPadding - bottomPadding;

  const paperHeights = papers.map((_, idx) =>
    expandedNodeId === `paper-${idx}` ? 200 : 85
  );
  const sumPaperHeights = paperHeights.reduce((a, b) => a + b, 0);
  const paperGap = papers.length > 1
    ? (availableHeight - sumPaperHeights) / (papers.length - 1)
    : 0;

  const paperNodes = [];
  let currentPaperY = topPadding;
  for (let i = 0; i < papers.length; i++) {
    const paper = papers[i];
    paperNodes.push({
      id: `paper-${i}`,
      x: 310,
      y: currentPaperY,
      width: 280,
      height: paperHeights[i],
      title: paper.title,
      solved_summary: paper.problems_solved?.[0] || "",
      similarity: paper.similarity,
      problems_solved: paper.problems_solved,
      limitations: paper.limitations
    });
    currentPaperY += paperHeights[i] + paperGap;
  }

  // 3단계: 공통 한계점 노드 (단일 노드, 중앙 y: 360)
  const commonExpanded = expandedNodeId === "common";
  const commonWidth = 280;
  const commonHeight = commonExpanded ? 260 : 120;
  const commonNode = {
    id: "common",
    x: 650,
    y: 360 - commonHeight / 2,
    width: commonWidth,
    height: commonHeight,
    title: "공통 연구 공백 (GAP)",
    items: commonLimitations
  };

  // 4단계: 추천 방향 노드들 (여러 노드, 동적 간격 분산)
  const dirHeights = suggestedDirections.map((_, idx) =>
    expandedNodeId === `direction-${idx}` ? 190 : 85
  );
  const sumDirHeights = dirHeights.reduce((a, b) => a + b, 0);
  
  const dirPaddingTop = 80;
  const dirPaddingBottom = 80;
  const dirAvailableHeight = canvasHeight - dirPaddingTop - dirPaddingBottom;
  const dirGap = suggestedDirections.length > 1
    ? (dirAvailableHeight - sumDirHeights) / (suggestedDirections.length - 1)
    : 0;

  const directionNodes = [];
  let currentDirY = dirPaddingTop;
  for (let i = 0; i < suggestedDirections.length; i++) {
    directionNodes.push({
      id: `direction-${i}`,
      x: 990,
      y: currentDirY,
      width: 280,
      height: dirHeights[i],
      title: `추천 연구 주제 ${i + 1}`,
      content: suggestedDirections[i]
    });
    currentDirY += dirHeights[i] + dirGap;
  }

  // 베지어 곡선 생성 헬퍼 함수
  const getBezierPath = (x1, y1, x2, y2) => {
    const controlX = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${controlX} ${y1}, ${controlX} ${y2}, ${x2} ${y2}`;
  };

  // 노드 카드 클릭 핸들러
  const handleNodeClick = (e, nodeType, data) => {
    // 스페이스바가 눌려있어 드래그 조작 중인 경우 노드 디테일 팝업 클릭 이벤트를 방지합니다.
    if (isSpacePressed) return;
    setExpandedNodeId((prev) => (prev === nodeType ? null : nodeType));
    setSelectedNode({ type: nodeType, data });
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

  // 줌 컨트롤 버튼 핸들러
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

  // 스페이스바 활성화 여부에 따른 커서 클래스 결정
  let cursorClass = "";
  if (isSpacePressed) {
    cursorClass = isPanning ? styles.grabbingCursor : styles.grabCursor;
  }

  return (
    <div className={`card shadow-sm p-4 border border-light-subtle ${styles.graphWrapper}`}>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h5 className="fw-bold text-gradient mb-0">분석 파이프라인 흐름 시각화</h5>
        <span className={styles.monoBadge}>Pipeline Flow</span>
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
        {/* Floating Zoom & Control Toolbar (우상단 배치) */}
        <div className={styles.controlToolbar}>
          <button
            type="button"
            className={styles.toolBtn}
            onClick={zoomIn}
            title="확대"
          >
            <i className="bi bi-zoom-in"></i>
          </button>
          <button
            type="button"
            className={styles.toolBtn}
            onClick={zoomOut}
            title="축소"
          >
            <i className="bi bi-zoom-out"></i>
          </button>
          <button
            type="button"
            className={styles.toolBtn}
            onClick={resetZoomAndPan}
            title="초기화"
          >
            <i className="bi bi-arrow-counterclockwise"></i>
          </button>
          <div className={styles.toolDivider}></div>
          <span className={styles.zoomText}>{Math.round(scale * 100)}%</span>
        </div>

        {/* Short Guideline Indicator (좌하단 안내문) */}
        <div className={styles.guideBadge}>
          <i className="bi bi-info-circle-fill me-1"></i>
          <span>Space + 마우스 드래그로 캔버스 이동 | 휠로 확대/축소</span>
        </div>

        {/* SVG Canvas Draw */}
        <svg
          viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
          width="100%"
          height="100%"
          className={styles.svgCanvas}
        >
          <defs>
            <linearGradient id="grad-query" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--color-query)" />
              <stop offset="100%" stopColor="var(--color-query-hover)" />
            </linearGradient>
            <linearGradient id="grad-paper" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--color-paper)" />
              <stop offset="100%" stopColor="var(--color-paper-hover)" />
            </linearGradient>
            <linearGradient id="grad-common" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--color-common)" />
              <stop offset="100%" stopColor="var(--color-common-hover)" />
            </linearGradient>
            <linearGradient id="grad-direction" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--color-direction)" />
              <stop offset="100%" stopColor="var(--color-direction-hover)" />
            </linearGradient>

            <filter id="glow-light" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Zoom & Pan 조작 대상들을 감싸는 타겟 그룹 */}
          <g
            style={{
              transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${scale})`,
              transformOrigin: "center center"
            }}
            className={styles.zoomGroup}
          >
            {/* 1. 커넥터 라인들 (배경선 + 빛 흐름선) */}
            {/* Query Node -> Papers */}
            {paperNodes.map((paper, idx) => {
              const path = getBezierPath(
                queryNode.x + queryNode.width,
                queryNode.y + queryNode.height / 2,
                paper.x,
                paper.y + paper.height / 2
              );
              return (
                <g key={`connector-qp-${idx}`}>
                  <path d={path} className={styles.connectorBg} />
                  <path d={path} className={`${styles.connectorFlow} ${styles.flowQuery}`} />
                </g>
              );
            })}

            {/* Papers -> Common Limitations */}
            {paperNodes.map((paper, idx) => {
              const path = getBezierPath(
                paper.x + paper.width,
                paper.y + paper.height / 2,
                commonNode.x,
                commonNode.y + commonNode.height / 2
              );
              return (
                <g key={`connector-pc-${idx}`}>
                  <path d={path} className={styles.connectorBg} />
                  <path d={path} className={`${styles.connectorFlow} ${styles.flowPaper}`} />
                </g>
              );
            })}

            {/* Common Limitations -> Directions */}
            {directionNodes.map((dir, idx) => {
              const path = getBezierPath(
                commonNode.x + commonNode.width,
                commonNode.y + commonNode.height / 2,
                dir.x,
                dir.y + dir.height / 2
              );
              return (
                <g key={`connector-cd-${idx}`}>
                  <path d={path} className={styles.connectorBg} />
                  <path d={path} className={`${styles.connectorFlow} ${styles.flowCommon}`} />
                </g>
              );
            })}

            {/* 2. 카드 노드들 (foreignObject) */}
            {/* Query Node */}
            <foreignObject
              x={queryNode.x - 12}
              y={queryNode.y - 12}
              width={queryNode.width + 24}
              height={queryNode.height + 24}
              className={styles.foreignObjectWrapper}
            >
              <div
                className={`${styles.nodeCard} ${styles.queryCard} ${selectedNode?.type === "query" ? styles.selected : ""} ${queryExpanded ? styles.expanded : ""} ${isSpacePressed ? styles.panningModeCard : ""}`}
                onClick={(e) => handleNodeClick(e, "query", { query: queryNode.content })}
              >
                <div className={styles.cardHeader}>
                  <span><i className="bi bi-search me-1"></i> {queryNode.title}</span>
                  <span className={styles.expandIcon}>
                    <i className={`bi bi-chevron-${queryExpanded ? "contract" : "expand"}`}></i>
                  </span>
                </div>
                <div className={styles.queryCardBody}>{queryNode.content}</div>
                {queryExpanded && (
                  <div className={styles.queryExpandedDetail}>
                    <div className={styles.divider}></div>
                    <p className={styles.expandedLabel}>RAG 분석 프로세스</p>
                    <p className={styles.expandedText}>
                      이 질문을 기반으로 고밀도 벡터(3072차원) 검색을 실행하여 관련 논문을 탐색했습니다.
                    </p>
                  </div>
                )}
              </div>
            </foreignObject>

            {/* Paper Nodes */}
            {paperNodes.map((paper, idx) => {
              const isPaperExpanded = expandedNodeId === paper.id;
              return (
                <foreignObject
                  key={paper.id}
                  x={paper.x - 12}
                  y={paper.y - 12}
                  width={paper.width + 24}
                  height={paper.height + 24}
                  className={styles.foreignObjectWrapper}
                >
                  <div
                    className={`${styles.nodeCard} ${styles.paperCard} ${selectedNode?.type === paper.id ? styles.selected : ""} ${isPaperExpanded ? styles.expanded : ""} ${isSpacePressed ? styles.panningModeCard : ""}`}
                    onClick={(e) => handleNodeClick(e, paper.id, paper)}
                  >
                    <div className={styles.cardHeader}>
                      <div className={styles.paperTitleHeader}>
                        <i className="bi bi-journal-text me-1"></i>
                        <span className={styles.paperTitleText} title={paper.title}>{paper.title}</span>
                      </div>
                      <div className="d-flex align-items-center gap-1">
                        {paper.similarity !== undefined && paper.similarity !== null && (
                          <span className={styles.similarityTag}>
                            {Math.round(paper.similarity * 100)}%
                          </span>
                        )}
                        <span className={styles.expandIcon}>
                          <i className={`bi bi-chevron-${isPaperExpanded ? "contract" : "expand"}`}></i>
                        </span>
                      </div>
                    </div>
                    
                    {!isPaperExpanded ? (
                      <div className={styles.cardBody}>
                        <div className={styles.solvedLabel}>
                          <i className="bi bi-check-circle-fill text-success me-1"></i> Solved
                        </div>
                        <div className={styles.solvedContent}>{paper.solved_summary}</div>
                      </div>
                    ) : (
                      <div className={styles.cardExpandedBody}>
                        <div className={styles.expandedSection}>
                          <div className={styles.sectionHeader}>
                            <i className="bi bi-check-circle-fill text-success me-1"></i> Solved
                          </div>
                          <ul className={styles.expandedList}>
                            {paper.problems_solved.slice(0, 3).map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </div>
                        <div className={styles.expandedSection}>
                          <div className={styles.sectionHeader}>
                            <i className="bi bi-slash-circle-fill text-danger me-1"></i> Limitations
                          </div>
                          <ul className={styles.expandedList}>
                            {paper.limitations.slice(0, 3).map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                </foreignObject>
              );
            })}

            {/* Common Limitations Node */}
            <foreignObject
              x={commonNode.x - 12}
              y={commonNode.y - 12}
              width={commonNode.width + 24}
              height={commonNode.height + 24}
              className={styles.foreignObjectWrapper}
            >
              <div
                className={`${styles.nodeCard} ${styles.commonCard} ${selectedNode?.type === "common" ? styles.selected : ""} ${commonExpanded ? styles.expanded : ""} ${isSpacePressed ? styles.panningModeCard : ""}`}
                onClick={(e) => handleNodeClick(e, "common", commonNode)}
              >
                <div className={styles.cardHeader}>
                  <span><i className="bi bi-exclamation-triangle-fill me-1"></i> {commonNode.title}</span>
                  <span className={styles.expandIcon}>
                    <i className={`bi bi-chevron-${commonExpanded ? "contract" : "expand"}`}></i>
                  </span>
                </div>
                <div className={styles.cardBodyList}>
                  {commonLimitations.length > 0 ? (
                    <ul>
                      {commonLimitations.slice(0, commonExpanded ? 4 : 2).map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                      {commonLimitations.length > (commonExpanded ? 4 : 2) && (
                        <li className={styles.moreText}>외 {commonLimitations.length - (commonExpanded ? 4 : 2)}건 더 보기...</li>
                      )}
                    </ul>
                  ) : (
                    <span className={styles.emptyText}>도출된 공통 한계가 없습니다.</span>
                  )}
                </div>
              </div>
            </foreignObject>

            {/* Suggested Direction Nodes */}
            {directionNodes.map((dir, idx) => {
              const isDirExpanded = expandedNodeId === dir.id;
              return (
                <foreignObject
                  key={dir.id}
                  x={dir.x - 12}
                  y={dir.y - 12}
                  width={dir.width + 24}
                  height={dir.height + 24}
                  className={styles.foreignObjectWrapper}
                >
                  <div
                    className={`${styles.nodeCard} ${styles.directionCard} ${selectedNode?.type === dir.id ? styles.selected : ""} ${isDirExpanded ? styles.expanded : ""} ${isSpacePressed ? styles.panningModeCard : ""}`}
                    onClick={(e) => handleNodeClick(e, dir.id, { text: dir.content, index: idx })}
                  >
                    <div className={styles.cardHeader}>
                      <span><i className="bi bi-lightbulb-fill me-1"></i> {dir.title}</span>
                      <span className={styles.expandIcon}>
                        <i className={`bi bi-chevron-${isDirExpanded ? "contract" : "expand"}`}></i>
                      </span>
                    </div>
                    <div className={`${styles.cardBody} ${isDirExpanded ? styles.expandedText : ""}`}>
                      {dir.content}
                    </div>
                  </div>
                </foreignObject>
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
            그래프의 노드 카드를 선택하여 단계별 핵심 데이터와 원문을 상세하게 검토해보세요.
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
                  <p className={styles.queryContent}>{selectedNode.data.query}</p>
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

            {selectedNode.type === "common" && (
              <div>
                <h4 className={styles.panelTitle}>
                  <i className="bi bi-exclamation-triangle-fill text-warning me-2"></i>
                  식별된 공통 연구 공백 (Common Research Gap)
                </h4>
                <div className={styles.panelContentBox}>
                  <p className="mb-3">검색된 5개 후보 연구 논문군을 다차원 종합 분석하여 추출된 핵심 공통 결함 및 향후 극복해야 할 공백 영역입니다:</p>
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
                  <p className={styles.directionContent}>{selectedNode.data.text}</p>
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
