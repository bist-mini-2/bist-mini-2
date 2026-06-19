/**
 * PipelineGraph 마인드맵의 2D 레이아웃 배치 계산 및 동적 척력(Repulsion) 연산을 전담하는 순수 유틸리티 모듈입니다.
 */

/**
 * 5단계 레이아웃 구조의 초기 배치 좌표를 계산합니다.
 * 
 * @param {Object} params
 * @param {Object} params.result ResearchGapMatrix 결과 DTO 데이터
 * @param {string} params.query 사용자가 검색한 원본 질의어
 * @param {number} params.canvasWidth 캔버스 너비
 * @param {number} params.canvasHeight 캔버스 높이
 * @returns {Object} 레이아웃 노드 데이터 객체
 */
export function calculateGraphLayout({ result, query, canvasWidth, canvasHeight }) {
  const papers = result?.papers || [];
  const commonLimitations = result?.common_limitations || [];
  const suggestedDirections = result?.suggested_directions || [];

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
  const R_papers = 280;
  const paperAngleRange = 2.4;
  const paperNodes = [];
  for (let i = 0; i < papers.length; i++) {
    const paper = papers[i];
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
      childAngles = [0];
    } else if (totalChildren > 1) {
      const maxSpread = Math.PI * 0.8;
      const spreadAngle = Math.min(maxSpread, (totalChildren - 1) * (Math.PI * 0.22));
      const startAngle = -spreadAngle / 2;
      const angleGap = spreadAngle / (totalChildren - 1);
      for (let j = 0; j < totalChildren; j++) {
        childAngles.push(startAngle + j * angleGap);
      }
    }

    // Solved 노드 생성
    for (let j = 0; j < numSolved; j++) {
      const angle = childAngles[j];
      const currentR = R_child;

      solvedNodes.push({
        id: `solved-${i}-${j}`,
        parentId: `paper-${i}`,
        parentX: paper.x,
        parentY: paper.y,
        x: paper.x + currentR * Math.cos(angle),
        y: paper.y + currentR * Math.sin(angle),
        r: 28,
        angle: angle,
        title: numSolved > 1 ? `Solved ${j + 1}` : "Solved",
        content: solvedList[j] || "해결 과제 정보가 없습니다.",
        problems_solved: solvedList
      });
    }

    // Limitation 노드 생성
    for (let j = 0; j < numLimit; j++) {
      const angle = childAngles[numSolved + j];
      const currentR = R_child;

      limitationNodes.push({
        id: `limitation-${i}-${j}`,
        parentId: `paper-${i}`,
        parentX: paper.x,
        parentY: paper.y,
        x: paper.x + currentR * Math.cos(angle),
        y: paper.y + currentR * Math.sin(angle),
        r: 28,
        angle: angle,
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

  return {
    queryNode,
    paperNodes,
    solvedNodes,
    limitationNodes,
    commonNode,
    directionNodes
  };
}

/**
 * 동일 레벨 형제 노드를 외곽으로 밀어내는 동적 척력(Repulsion) 좌표를 계산합니다.
 * 
 * @param {Object} params
 * @param {string|null} params.activeFocusNode 현재 카메라 포커싱된 기준 노드 ID
 * @param {Object} params.layoutData calculateGraphLayout에서 반환된 레이아웃 데이터
 * @param {string} params.nodeId 계산 타겟 노드 ID
 * @param {number} params.origX 타겟 노드의 기본 x좌표
 * @param {number} params.origY 타겟 노드의 기본 y좌표
 * @returns {Object} { x, y } 보정된 척력 좌표
 */
export function getRepulsedCoords({ activeFocusNode, layoutData, nodeId, origX, origY }) {
  if (!activeFocusNode) return { x: origX, y: origY };
  if (activeFocusNode === nodeId) return { x: origX, y: origY };

  const { queryNode, paperNodes, solvedNodes, limitationNodes, commonNode, directionNodes } = layoutData;

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
      const R_common_child = 240 + totalLimit * 4;
      const spreadAngle = Math.PI * 0.85;
      const startAngle = Math.PI - spreadAngle / 2;
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
    const pushFactor = 2.8;
    return {
      x: focusNode.x + dx * pushFactor,
      y: focusNode.y + dy * focusNode.r / 100 ? focusNode.y + dy * pushFactor : focusNode.y + dy * pushFactor
    };
  }

  // 만약 paper 노드가 포커싱되어 있으면, query 노드는 450px 만큼 왼쪽으로 밀어서 충돌이나 겹침 방지
  if (activeFocusNode.startsWith("paper-") && nodeId === "query") {
    return { x: origX - 450, y: origY };
  }

  return { x: origX, y: origY };
}

/**
 * 노드가 포커싱 상태일 때 원형 크기를 동적으로 확장(1.4배)하여 렌더링 반경을 반환합니다.
 * 
 * @param {Object} params
 * @param {string|null} params.activeFocusNode 현재 카메라 포커싱된 기준 노드 ID
 * @param {string} params.nodeId 타겟 노드 ID
 * @param {number} params.baseRadius 기본 반경
 * @returns {number} 팽창된 반경
 */
export function getCircleRadius({ activeFocusNode, nodeId, baseRadius }) {
  if (activeFocusNode === nodeId) {
    return baseRadius * 1.4;
  }
  return baseRadius;
}
