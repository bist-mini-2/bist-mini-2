import io
import logging
import httpx
from bs4 import BeautifulSoup
import pypdfium2 as pdfium

logger = logging.getLogger(__name__)


class PaperCrawler:
    """학술 논문 본문 데이터를 온디맨드로 수집하는 크롤러 클래스입니다."""

    def __init__(self) -> None:
        """PaperCrawler 인스턴스를 초기화합니다."""
        # 기본 헤더 설정 (크롤러 차단 방지용 User-Agent 설정)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

    async def crawl_paper(self, paper_id: str) -> dict:
        """논문 식별자(ID)를 기준으로 본문 데이터를 크롤링합니다.

        기본적으로 arXiv ID를 판별하여 arXiv HTML 또는 PDF 파싱을 시도합니다.

        Args:
            paper_id (str): 논문 ID (예: "1706.05049" 또는 "2006.11367")

        Returns:
            dict: {"title": str, "full_text": str, "source": str} 구조의 크롤링 결과.
        """
        # 공백 제거 및 소문자화
        clean_id = paper_id.strip()
        logger.info(f"논문 크롤링 시작: ID='{clean_id}'")

        # arXiv ID 규격 여부 확인 (예: YYMM.NNNNN 또는 카테고리/YYMMNNN)
        # 간이 판별: 주로 숫자가 들어가거나 아카이브 고유 형식이면 arXiv로 간주
        if any(char.isdigit() for char in clean_id):
            return await self._crawl_arxiv(clean_id)

        raise ValueError(f"지원하지 않는 논문 ID 규격입니다: {paper_id}")

    async def _crawl_arxiv(self, arxiv_id: str) -> dict:
        """arXiv 논문 크롤링을 처리합니다 (HTML 파싱 선도, 실패 시 PDF 폴백)."""
        # 1. HTML 버전 수집 시도 (arXiv 웹 친화형 HTML 제공 서비스)
        html_url = f"https://arxiv.org/html/{arxiv_id}"
        logger.info(f"arXiv HTML 크롤링 시도: {html_url}")

        async with httpx.AsyncClient(headers=self.headers, timeout=20.0, follow_redirects=True) as client:
            try:
                resp = await client.get(html_url)
                if resp.status_code == 200 and "ltx_page_content" in resp.text:
                    logger.info("arXiv HTML 추출 성공. 파싱을 진행합니다.")
                    result = self._parse_arxiv_html(resp.text)
                    if result.get("full_text"):
                        result["source"] = "arxiv"
                        return result
            except Exception as e:
                logger.warning(f"arXiv HTML 파싱 중 예외 발생 (PDF로 폴백 진행): {e}")

            # 2. PDF 다운로드 및 pypdfium2 파싱 폴백
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            logger.info(f"arXiv PDF 폴백 크롤링 시도: {pdf_url}")
            try:
                resp = await client.get(pdf_url)
                if resp.status_code == 200:
                    logger.info("arXiv PDF 다운로드 성공. pypdfium2를 통해 텍스트를 추출합니다.")
                    full_text = self._parse_pdf_bytes(resp.content)
                    # PDF의 경우 제목을 첫 페이지 첫 두줄 등에서 유추하거나 빈 문자열 처리
                    title = f"arXiv Paper {arxiv_id}"
                    if full_text.strip():
                        # 첫 단락에서 간이 제목 추출 시도
                        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
                        if lines:
                            title = lines[0][:150]
                        return {
                            "title": title,
                            "full_text": full_text,
                            "source": "arxiv",
                        }
            except Exception as e:
                logger.error(f"arXiv PDF 다운로드 및 파싱 실패: {e}")

        raise RuntimeError(f"arXiv 논문 {arxiv_id}의 본문 텍스트 추출에 실패했습니다.")

    def _parse_arxiv_html(self, html_content: str) -> dict:
        """arXiv HTML 페이지 본문을 파싱하여 텍스트를 정제합니다."""
        soup = BeautifulSoup(html_content, "html.parser")

        # 논문 제목 추출
        title_el = soup.find(class_="ltx_title_document") or soup.find("h1", class_="ltx_title")
        title = title_el.get_text().strip() if title_el else "Unknown Title"

        # ltx_page_content 안의 주요 텍스트 영역 수집
        content_el = soup.find(class_="ltx_page_content") or soup.find("article")
        if not content_el:
            content_el = soup

        # 불필요한 메타데이터, 내비게이션, 스타일 영역 제거
        for el in content_el.find_all(class_=["ltx_page_header", "ltx_page_footer", "ltx_bibliography"]):
            el.decompose()

        # 텍스트 노드 추출 및 정제
        paragraphs = []
        for element in content_el.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
            text = element.get_text().strip()
            if text:
                paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)
        return {
            "title": title,
            "full_text": full_text,
        }

    def _parse_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """pypdfium2를 사용하여 PDF 바이너리로부터 텍스트를 고속으로 추출합니다."""
        pdf = pdfium.PdfDocument(io.BytesIO(pdf_bytes))
        pages = []
        for page in pdf:
            textpage = page.get_textpage()
            text = textpage.get_text_range() or ""
            if text.strip():
                pages.append(text)
        return "\n".join(pages)


# 싱글톤 인스턴스
paper_crawler = PaperCrawler()
