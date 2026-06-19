import logging
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class LlmLoggingHandler(BaseCallbackHandler):
    """LLM의 프롬프트 입출력 내역을 표준 로거로 수집하고 기록하는 커스텀 콜백 핸들러입니다."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("api.v1.cs.llm")

    def on_llm_start(
        self, serialized: dict, prompts: list[str], **kwargs
    ) -> None:
        """LLM 호출 시작 시 프롬프트를 로깅합니다.

        Args:
            serialized (dict): 모델 직렬화 객체 정보.
            prompts (list[str]): 입력 프롬프트 리스트.
            **kwargs: 추가 키워드 인자.
        """
        for prompt in prompts:
            self.logger.info(f"[LLM INPUT PROMPT]\n{prompt}")

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 응답 완료 시 생성 결과를 로깅합니다.

        Args:
            response (LLMResult): LLM 생성 결과 객체.
            **kwargs: 추가 키워드 인자.
        """
        for generation in response.generations:
            for g in generation:
                self.logger.info(f"[LLM OUTPUT ANSWER]\n{g.text}")
