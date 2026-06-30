"use client"

import { useState, useEffect, useRef, useContext } from "react";
import { useSearchParams } from "next/navigation";
import { AuthContext } from "@/contexts/AuthContext";
import { NotificationContext } from "@/contexts/NotificationContext";
import { startAnalysis, getTaskStatus, getTaskResult, translateMatrix } from "@/apis/researchGap";

// 튜토리얼용 임의 가데이터 정의
const mockResults = {
  "dummy-task-1": {
    query: "Attention Mechanism in Neural Machine Translation",
    domain: "cs",
    result: {
      papers: [
        {
          title: "Attention Is All You Need",
          arxiv_id: "1706.03762",
          similarity: 0.95,
          problems_solved: [
            {
              summary: "기존 RNN/CNN 기반 시퀀스 모델의 순차적 계산 병목을 해결하고 셀프 어텐션 기반 병렬화 달성",
              source_quote: "The Transformer allows for significantly more parallelization..."
            }
          ],
          limitations: [
            {
              summary: "입력 시퀀스 길이에 비례해 연산 복잡도가 제곱으로 증가(O(N^2))하는 긴 문맥 처리 한계",
              source_quote: "self-attention layers ... requires O(N^2) computations..."
            }
          ]
        },
        {
          title: "Neural Machine Translation by Jointly Learning to Align and Translate",
          arxiv_id: "1409.0473",
          similarity: 0.88,
          problems_solved: [
            {
              summary: "고정 크기 컨텍스트 벡터의 병목을 해결하기 위해 인코더-디코더 정렬 및 어텐션 기법 제안",
              source_quote: "We conjecture that the use of a fixed-length vector is a bottleneck..."
            }
          ],
          limitations: [
            {
              summary: "디코더 매 스텝마다 전체 입력 시퀀스를 참조하는 연산 비용(O(T_x * T_y)) 문제 발생",
              source_quote: "The computational cost of the proposed attention mechanism is proportional to..."
            }
          ]
        }
      ],
      common_limitations: [
        "긴 텍스트 입력 시 어텐션 가중치 맵 생성으로 인한 기하급수적인 연산량 및 메모리 자원 낭비",
        "순차적 시퀀스 처리에 따른 학습 속도 지연 및 대형 말뭉치 훈련의 병목 현상"
      ],
      suggested_directions: [
        "선형 어텐션(Linear Attention) 메커니즘 또는 희소(Sparse) 어텐션을 활용한 연산 효율 최적화 연구",
        "로컬 윈도우 기반 어텐션과 글로벌 토큰 어텐션을 병합한 하이브리드 어텐션 구조 탐색"
      ]
    }
  },
  "dummy-task-2": {
    query: "CRISPR-Cas9 Gene Editing Accuracy and Off-target Effects",
    domain: "bio",
    result: {
      papers: [
        {
          title: "Programmable dual-RNA-guided DNA cleavage in adaptive bacterial immunity",
          arxiv_id: "2209.00123",
          similarity: 0.92,
          problems_solved: [
            {
              summary: "Cas9 단백질이 crRNA와 tracrRNA의 듀얼 가이드 구조에 의해 표적 DNA 서열을 정밀 절단함을 증명",
              source_quote: "Our study reveals a family of RNA-programmable Cas9 endonucleases..."
            }
          ],
          limitations: [
            {
              summary: "표적 서열과 유사한 비표적(Off-target) 서열에 결합하여 원치 않는 유전자 변이를 유발할 위험성",
              source_quote: "Cas9-catalyzed cleavage ... can occur at sites containing mismatches..."
            }
          ]
        }
      ],
      common_limitations: [
        "가이드 RNA의 미스매치 허용으로 인한 비표적 절단 활성 및 세포 유전체 불안정성 유발",
        "생체 내 전달(Delivery) 시 Cas9 단백질의 장기 발현으로 인한 오프타겟 부작용 극대화"
      ],
      suggested_directions: [
        "Cas9 단백질의 하이-피델리티(High-Fidelity) 엔지니어링을 통한 DNA 정밀 인식 유도 연구",
        "일시적 발현 제어가 가능한 고효율 RNP(Ribonucleoprotein) 리포솜 전달 시스템 개발"
      ]
    }
  },
  "dummy-task-3": {
    query: "Zero-Shot Learning in Large Language Models",
    domain: "cs",
    result: {
      papers: [
        {
          title: "Language Models are Few-Shot Learners",
          arxiv_id: "2005.14165",
          similarity: 0.94,
          problems_solved: [
            {
              summary: "파인튜닝 없이 제로샷 및 퓨샷 프롬프팅만으로 다양한 NLP 태스크에서 뛰어난 성능 입증",
              source_quote: "We show that scaling up language models greatly improves task-agnostic, few-shot performance..."
            }
          ],
          limitations: [
            {
              summary: "대형 모델 크기로 인한 추론 비용 문제 및 새로운 지식에 대한 실시간 업데이트 미지원",
              source_quote: "Limitations include: LMs are expensive to run and update..."
            }
          ]
        }
      ],
      common_limitations: [
        "정적인 가중치 정보 한계로 인한 할루시네이션(Hallucination) 및 최신 정보 반영 지연",
        "추론 과정에서 방대한 연산 파라미터 활성화로 인한 하드웨어 비용적 제약"
      ],
      suggested_directions: [
        "지식 그래프 연동형 RAG 및 동적 메모리 네트워크 융합 설계 연구",
        "지식 증류(Knowledge Distillation) 기법 기반 초경량 제로샷 임베디드 모델 최적화"
      ]
    }
  }
};

/**
 * 대규모 문헌 비교 분석기(Research Gap Analyzer)의 비동기 분석 요청, 
 * 진행도 폴링(Polling), 다국어 번역 스위칭 및 상태 제어 로직을 전담하는 커스텀 훅입니다.
 */
export default function useResearchGap() {
  const { accessToken } = useContext(AuthContext);
  const { notifications: globalNotifications } = useContext(NotificationContext);
  const searchParams = useSearchParams();
  const queryTaskId = searchParams.get("taskId");

  // 입력 폼 상태
  const [domain, setDomain] = useState("cs");
  const [query, setQuery] = useState("");

  // 비동기 작업 상태
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [statusText, setStatusText] = useState("");

  // 최종 결과물 상태
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // 번역 관련 상태
  const [isTranslated, setIsTranslated] = useState(false);
  const [translatedResult, setTranslatedResult] = useState(null);
  const [translateLoading, setTranslateLoading] = useState(false);

  // useRef를 활용해 비동기 콜백에서 최신 taskId 및 폴링 제어를 참조합니다.
  const currentTaskIdRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  // URL 쿼리 파라미터로 taskId가 넘어온 경우 해당 태스크 자동 로드 및 폴링. 없는 경우 초기 상태로 리셋.
  useEffect(() => {
    if (queryTaskId) {
      setResult(null);
      setError(null);
      setIsTranslated(false);
      setTranslatedResult(null);
      setTaskId(queryTaskId);
      currentTaskIdRef.current = queryTaskId;
      setLoading(true);

      // 가데이터 태스크 처리
      if (queryTaskId.startsWith("dummy-task-")) {
        const dummyInfo = mockResults[queryTaskId];
        if (queryTaskId === "dummy-task-3") {
          // 실시간으로 진행되는 가데이터 태스크 3번 (RUNNING -> COMPLETED)
          setStatus("RUNNING");
          setProgress(45);
          setStatusText("임베딩 생성 및 벡터 연산 중 (가데이터)...");
          
          let currentProgress = 45;
          const intervalId = setInterval(() => {
            currentProgress += 15;
            if (currentProgress >= 100) {
              clearInterval(intervalId);
              setProgress(100);
              setStatus("COMPLETED");
              setDomain(dummyInfo.domain);
              setQuery(dummyInfo.query);
              setResult(dummyInfo.result);
              setLoading(false);
            } else {
              setProgress(currentProgress);
              if (currentProgress < 65) {
                setStatusText("선택 도메인 RAG 유사도 문헌 추출 중 (가데이터)...");
              } else if (currentProgress < 85) {
                setStatusText("논문별 핵심 해결 과제 및 한계점 추출 중 (가데이터)...");
              } else {
                setStatusText("통합 한계점 매트릭스 도출 및 AI Synthesis 진행 중 (가데이터)...");
              }
            }
          }, 800);

          return () => clearInterval(intervalId);
        } else {
          // 완료된 가데이터 태스크 1, 2번
          setStatus("PENDING");
          setStatusText("선택된 가데이터 분석 데이터를 불러오는 중...");
          
          const timeoutId = setTimeout(() => {
            setStatus("COMPLETED");
            setProgress(100);
            setDomain(dummyInfo.domain);
            setQuery(dummyInfo.query);
            setResult(dummyInfo.result);
            setLoading(false);
          }, 600);

          return () => clearTimeout(timeoutId);
        }
      }

      // 실제 태스크 처리
      setStatus("PENDING");
      setStatusText("선택된 분석 작업 데이터를 불러오는 중...");
      startPolling(queryTaskId);
    } else {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      setDomain("cs");
      setQuery("");
      setLoading(false);
      setTaskId(null);
      currentTaskIdRef.current = null;
      setProgress(0);
      setStatus("");
      setStatusText("");
      setResult(null);
      setError(null);
      setIsTranslated(false);
      setTranslatedResult(null);
      setTranslateLoading(false);
    }
  }, [queryTaskId]);

  // 전역 실시간 알림 피드를 모니터링하여 현재 실행 중인 작업의 완료/실패 알림 수신 시 즉시 데이터 반영
  useEffect(() => {
    if (!taskId) return;
    const latestNotif = globalNotifications[0];
    
    // 만약 현재 대기 중인 작업과 관련된 알림이 도착했다면
    if (latestNotif && latestNotif.task_id === taskId) {
      if (latestNotif.type === "success") {
        console.log("Global notification completed event detected for task:", taskId);
        clearInterval(pollingIntervalRef.current);
        fetchFinalResult(taskId);
      } else if (latestNotif.type === "danger") {
        console.log("Global notification failed event detected for task:", taskId);
        clearInterval(pollingIntervalRef.current);
        setError(latestNotif.message || "분석 배치 작업 처리 중 에러가 발생했습니다.");
        setStatus("FAILED");
        setProgress(100);
        setLoading(false);
      }
    }
  }, [globalNotifications, taskId]);

  // 컴포넌트 언마운트 시 폴링 클리어
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // 최종 분석 결과 조회
  const fetchFinalResult = async (id) => {
    try {
      setStatusText("결과 리포트 분석 완료 및 렌더링 중...");
      const res = await getTaskResult(id);
      if (res.status === "success" && res.data) {
        setResult(res.data.result);
        if (res.data.translated_result) {
          setTranslatedResult(res.data.translated_result);
        }
        if (res.data.query) {
          setQuery(res.data.query);
        }
        setStatus("COMPLETED");
        setProgress(100);
      } else {
        setError("분석 결과를 불러오지 못했습니다.");
        setStatus("FAILED");
      }
    } catch (err) {
      console.error(err);
      setError("결과 조회 중 서버 오류가 발생했습니다.");
      setStatus("FAILED");
    } finally {
      setLoading(false);
    }
  };

  // 배치 작업 진행도 폴링 처리 (SSE 누락 대비 및 정확한 게이지용)
  const startPolling = (id) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const res = await getTaskStatus(id);
        if (res.status === "success" && res.data) {
          const taskData = res.data;
          setProgress(taskData.progress);
          setStatus(taskData.status);

          // 상태 단계별 메세지 매핑
          if (taskData.status === "PENDING") {
            setStatusText("서버 작업 대기 중...");
          } else if (taskData.status === "RUNNING") {
            if (taskData.progress < 30) {
              setStatusText("임베딩 생성 및 벡터 연산 중...");
            } else if (taskData.progress < 60) {
              setStatusText("선택 도메인 RAG 유사도 문헌 추출 중...");
            } else if (taskData.progress < 80) {
              setStatusText("논문별 핵심 해결 과제 및 한계점 추출 중...");
            } else {
              setStatusText("통합 한계점 매트릭스 도출 및 AI Synthesis 진행 중...");
            }
          } else if (taskData.status === "COMPLETED") {
            clearInterval(pollingIntervalRef.current);
            fetchFinalResult(id);
          } else if (taskData.status === "FAILED") {
            clearInterval(pollingIntervalRef.current);
            setError(taskData.error_message || "배치 태스크 처리 중 실패했습니다.");
            setLoading(false);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1500);
  };

  // 번역 토글 핸들러
  const handleTranslateToggle = async () => {
    if (!result || !taskId) return;
    
    if (isTranslated) {
      setIsTranslated(false);
    } else {
      if (translatedResult) {
        setIsTranslated(true);
      } else {
        setTranslateLoading(true);
        try {
          const res = await translateMatrix(taskId);
          if (res.status === "success" && res.data) {
            setTranslatedResult(res.data);
            setIsTranslated(true);
          } else {
            setError("번역 데이터를 불러오지 못했습니다.");
          }
        } catch (err) {
          console.error("Translation error:", err);
          setError("번역 진행 중 오류가 발생했습니다.");
        } finally {
          setTranslateLoading(false);
        }
      }
    }
  };

  // 분석 시작 요청 실행
  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);
    setError(null);
    setIsTranslated(false);
    setTranslatedResult(null);
    setProgress(5);
    setStatus("PENDING");
    setStatusText("태스크 초기화 및 작업 시작 요청 중...");

    try {
      const res = await startAnalysis(domain, query);
      if (res.status === "success" && res.data?.task_id) {
        const newTaskId = res.data.task_id;
        setTaskId(newTaskId);
        currentTaskIdRef.current = newTaskId;
        startPolling(newTaskId);
      } else {
        setError("비동기 분석 작업을 등록하지 못했습니다.");
        setLoading(false);
      }
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.message || err.response?.data?.detail || "서버 연결에 실패했거나 권한이 없습니다.";
      setError(errMsg);
      setLoading(false);
    }
  };

  const displayResult = isTranslated ? translatedResult : result;

  return {
    domain,
    setDomain,
    query,
    setQuery,
    loading,
    taskId,
    progress,
    status,
    statusText,
    result,
    displayResult,
    error,
    isTranslated,
    translateLoading,
    handleTranslateToggle,
    handleAnalyze
  };
}
