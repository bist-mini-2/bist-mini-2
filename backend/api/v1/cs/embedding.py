from api.common.config import settings
from langchain_openai import OpenAIEmbeddings


class EmbeddingModelHelper:
    """OpenAI의 text-embedding-3-large 모델을 활용하여 3072차원 임베딩을 제공하는 헬퍼 클래스입니다.
    
    내부적으로 LangChain의 OpenAIEmbeddings 인스턴스를 싱글톤 패턴으로 재사용합니다.
    """
    
    def __init__(self) -> None:
        self._embeddings = None

    def get_embeddings(self) -> OpenAIEmbeddings:
        """LangChain OpenAIEmbeddings 인스턴스를 획득합니다.
        
        API Key는 config의 settings 객체에서 로드됩니다.

        Returns:
            OpenAIEmbeddings: LangChain OpenAI 임베딩 클라이언트 인스턴스.
        """
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                dimensions=3072,
                api_key=settings.OPENAI_API_KEY
            )
        return self._embeddings

    def encode(self, text: str) -> list[float]:
        """입력된 단일 텍스트를 OpenAI text-embedding-3-large API를 이용해 
        3072차원 임베딩 실수 벡터로 인코딩하여 반환합니다.

        Args:
            text (str): 임베딩 벡터를 추출할 입력 문자열.

        Returns:
            list[float]: 3072차원 임베딩 벡터.
        """
        embeddings = self.get_embeddings()
        return embeddings.embed_query(text)


# 모듈 캐싱 메커니즘에 기반한 전역 싱글톤 인스턴스 정의
embedding_helper = EmbeddingModelHelper()
