"""기밀 유지 보안 격리 구역 내 PDF 업로드, 피어리뷰 시뮬레이션 및 모의 디펜스를 처리하는 서비스 모듈입니다."""

import os
import shutil
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Annotated, List, Tuple, Optional
from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pydantic import Field

from api.common.config import settings
from api.database.config.dbsession import session_maker
from api.database.config.dto_base import BaseDTO
from api.v1.research_gap.embedding import embedding_helper
from api.v1.defense_arena.dao import DefenseArenaDao, DefenseArenaDaoDep
from api.v1.defense_arena.entity import DefenseArenaSessionEntity, DefenseArenaChunkEntity, DefenseHistoryEntity
from api.v1.defense_arena.models import (
    PeerReviewReport, AgentOpinion,
    HypothesisVerificationResult, HypothesisVoteItem,
    DefenseChatResponse, ScoreDTO
)

logger = logging.getLogger(__name__)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads")


class DefenseArenaService:
    """보안 격리 샌드박스 피어 리뷰 및 디펜스 아레나 비즈니스 로직을 처리하는 서비스입니다."""

    def __init__(self, defense_arena_dao: DefenseArenaDaoDep):
        """DefenseArenaService의 인스턴스를 초기화하고 DAO 의존성을 주입합니다.

        Args:
            defense_arena_dao (DefenseArenaDaoDep): 보안 격리 세션 및 대화 내역 저장을 위한 DAO.
        """
        self.logger = logging.getLogger(f"{__name__}.DefenseArenaService")
        self.defense_arena_dao = defense_arena_dao

    async def process_pdf_upload(self, file: UploadFile, mid: str) -> dict:
        """업로드된 PDF 문서를 읽고 격리 텍스트 파싱, 청킹 및 pgvector 임시 임베딩을 수행합니다."""
        session_id = str(uuid.uuid4())
        self.logger.info(f"Processing isolated PDF upload: file_name={file.filename}, session_id={session_id}, mid={mid}")

        # 1. uploads 격리 디렉토리 생성 및 파일 저장
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        session_dir = os.path.join(UPLOAD_DIR, session_id)
        
        filename = file.filename
        if not filename:
            from api.common.exceptions import BusinessException
            raise BusinessException(message="파일명이 누락되었거나 올바르지 않습니다.", error_code="INVALID_FILE_NAME")

        # OS Path Guard (Directory Traversal 방지 검증)
        real_upload_dir = os.path.realpath(UPLOAD_DIR)
        target_path = os.path.realpath(os.path.join(session_dir, filename))
        if not target_path.startswith(real_upload_dir):
            from api.common.exceptions import BusinessException
            raise BusinessException(message="허용되지 않는 파일 업로드 경로 접근 시도입니다.", error_code="PATH_GUARD_VIOLATION")

        os.makedirs(session_dir, exist_ok=True)
        file_path = os.path.join(session_dir, filename)
        
        def save_file_sync():
            """업로드된 임시 파일을 동기 방식으로 물리 저장합니다."""
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        await asyncio.to_thread(save_file_sync)

        # 2. PDF 파싱 및 텍스트 추출 (pypdf)
        def parse_pdf_sync() -> str:
            """물리 저장된 PDF 파일에서 텍스트 내용을 동기 방식으로 추출합니다.

            Returns:
                str: 추출된 전체 텍스트 내용.
            """
            reader = PdfReader(file_path)
            raw_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    raw_text += text + "\n"
            return raw_text

        try:
            raw_text = await asyncio.to_thread(parse_pdf_sync)
        except Exception as e:
            self.logger.error(f"Failed to parse PDF file: {e}")
            # 업로드한 임시 폴더 삭제
            await asyncio.to_thread(shutil.rmtree, session_dir, ignore_errors=True)
            from api.common.exceptions import BusinessException
            raise BusinessException(message=f"PDF 파일 파싱에 실패했습니다: {str(e)}", error_code="PDF_PARSING_FAILED")

        if not raw_text.strip():
            await asyncio.to_thread(shutil.rmtree, session_dir, ignore_errors=True)
            from api.common.exceptions import BusinessException
            raise BusinessException(message="PDF 문서에서 텍스트를 추출할 수 없습니다. 스캔된 이미지 PDF이거나 비어있습니다.", error_code="EMPTY_PDF_CONTENT")

        # 3. 텍스트 청킹 (RecursiveCharacterTextSplitter)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(raw_text)

        # 4. 세션 엔티티 및 청크 엔티티 DB 적재
        session_entity = DefenseArenaSessionEntity(
            session_id=session_id,
            member_id=mid,
            file_name=filename,
            file_path=file_path,
            chunk_count=len(chunks)
        )
        await self.defense_arena_dao.create_session(session_entity)

        # 각 청크의 임베딩 벡터 생성 및 엔티티 일괄 매핑
        chunk_entities = []
        for idx, chunk_text in enumerate(chunks):
            # OpenAI text-embedding-3-large 3072차원 임베딩 생성
            vector = embedding_helper.encode(chunk_text)
            chunk_entities.append(
                DefenseArenaChunkEntity(
                    session_id=session_id,
                    chunk_index=idx,
                    text_chunk=chunk_text,
                    embedding=vector
                )
            )
        
        await self.defense_arena_dao.insert_chunks(chunk_entities)

        return {
            "session_id": session_id,
            "file_name": filename,
            "chunk_count": len(chunks)
        }

    async def run_peer_review(self, session_id: str, target_journal: str, mid: str) -> PeerReviewReport:
        """격리 샌드박스의 문서를 바탕으로 LangGraph/Multi-Agent 기반 3대 에이전트 피어리뷰를 시뮬레이션합니다."""
        # 세션 정보 및 활동 갱신
        session = await self.defense_arena_dao.get_session(session_id)
        if not session or session.member_id != mid:
            from api.common.exceptions import BusinessException
            raise BusinessException(message="격리 세션을 찾을 수 없거나 접근 권한이 없습니다.", error_code="SESSION_NOT_FOUND")
        await self.defense_arena_dao.update_session_activity(session_id)

        # RAG용 청크 추출 (여기서는 문서 전체 요약을 위해 상위 청크 일부를 가져와 피어리뷰에 보냄)
        # 긴 문서의 컨텍스트 초과 방지를 위해 대표 청크 10개를 고정적으로 조회
        from sqlalchemy import select
        # 데이터베이스 세션을 통해 직접 청크 로드
        result = await self.defense_arena_dao.orm_session.execute(
            select(DefenseArenaChunkEntity)
            .where(DefenseArenaChunkEntity.session_id == session_id)
            .order_by(DefenseArenaChunkEntity.chunk_index.asc())
            .limit(10)
        )
        chunk_list = list(result.scalars().all())
        document_context = "\n\n".join([c.text_chunk for c in chunk_list])

        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=settings.OPENAI_API_KEY, temperature=0.2)
        structured_llm = llm.with_structured_output(PeerReviewReport)

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an elite academic peer review board composed of three expert agents:\n"
                "1. Methodology Agent: Reviews mathematical proofs, algorithmic correctness, and experimental setups.\n"
                "2. Novelty Agent: Reviews state-of-the-art literature contrast, novelty of approach, and scientific contribution.\n"
                "3. Academic Style Agent: Reviews clarity, organization, academic vocabulary, and tone.\n\n"
                "Simulate a constructive debate among these three agents regarding the provided paper draft and target journal: '{target_journal}'.\n"
                "Synthesize their individual feedback into the required schema format, scoring each category out of 100.\n"
                "The response must be in English. Structure the output strictly."
            )),
            ("user", "Paper Draft Content Snippets:\n{context}")
        ])

        chain = prompt | structured_llm
        report = await chain.ainvoke({
            "target_journal": target_journal,
            "context": document_context[:15000] # GPT Context 방어용 자르기
        })

        if not isinstance(report, PeerReviewReport):
            raise TypeError(f"Expected PeerReviewReport, got {type(report)}")

        return report

    async def verify_hypothesis(self, session_id: str, hypothesis: str, mid: str) -> HypothesisVerificationResult:
        """자기 일관성(Self-Consistency) 기법을 기반으로 RAG와 투표를 거쳐 가설을 다수결 검증합니다."""
        session = await self.defense_arena_dao.get_session(session_id)
        if not session or session.member_id != mid:
            from api.common.exceptions import BusinessException
            raise BusinessException(message="격리 세션을 찾을 수 없거나 접근 권한이 없습니다.", error_code="SESSION_NOT_FOUND")
        await self.defense_arena_dao.update_session_activity(session_id)

        # 1. 가설을 임베딩하여 격리 세션 내 유사 청크 5개 검색 (RAG)
        hypo_vector = embedding_helper.encode(hypothesis)
        search_results = await self.defense_arena_dao.similarity_search_in_session(session_id, hypo_vector, k=5)
        citations = [r[0].text_chunk for r in search_results]
        citations_context = "\n\n".join([f"[Fact {i+1}]: {c}" for i, c in enumerate(citations)])

        # 2. Self-Consistency를 위한 3회 독립 추론 (각각 온도를 다르게 주어 투표 다양성 보장)
        detailed_votes = []
        support_count = 0
        refute_count = 0
        insufficient_count = 0

        # LLM 독립 호출
        for i in range(3):
            # 온도를 0.5~0.7로 조금 주어 미묘하게 다른 관점을 내도록 함
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.5 + (i * 0.1)
            )
            structured_llm = llm.with_structured_output(HypothesisVoteItem)

            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a rigorous scientific verification engine evaluating a research hypothesis.\n"
                    "Evaluate the user's hypothesis based on the provided facts extracted from their uploaded draft paper.\n"
                    "Your verdict must be one of:\n"
                    "- 'SUPPORT': The facts strongly support this hypothesis.\n"
                    "- 'REFUTE': The facts contradict or refute this hypothesis.\n"
                    "- 'INSUFFICIENT_EVIDENCE': There is not enough evidence in the draft to support or refute this.\n\n"
                    "Response must be structured in the requested format."
                )),
                ("user", "Hypothesis: {hypothesis}\n\nExtracted Facts:\n{context}")
            ])

            chain = prompt | structured_llm
            vote_item = await chain.ainvoke({
                "hypothesis": hypothesis,
                "context": citations_context
            })

            if not isinstance(vote_item, HypothesisVoteItem):
                raise TypeError(f"Expected HypothesisVoteItem, got {type(vote_item)}")

            detailed_votes.append(vote_item)
            
            v = vote_item.vote.upper().strip()
            if v == "SUPPORT":
                support_count += 1
            elif v == "REFUTE":
                refute_count += 1
            else:
                insufficient_count += 1

        # 3. 다수결(Majority Voting) 판정
        votes_map = {
            "SUPPORT": support_count,
            "REFUTE": refute_count,
            "INSUFFICIENT_EVIDENCE": insufficient_count
        }
        verdict = max(votes_map, key=lambda k: votes_map[k])
        consensus_ratio = votes_map[verdict] / 3.0

        return HypothesisVerificationResult(
            verdict=verdict,
            support_count=support_count,
            refute_count=refute_count,
            insufficient_count=insufficient_count,
            consensus_ratio=consensus_ratio,
            detailed_votes=detailed_votes,
            citations=citations
        )

    async def process_defense_chat(self, session_id: str, user_response: Optional[str], mid: str) -> DefenseChatResponse:
        """심사위원 에이전트 모의 디펜스 세션을 턴제(Turn-based)로 실행하고 실시간 채점합니다."""
        session = await self.defense_arena_dao.get_session(session_id)
        if not session or session.member_id != mid:
            from api.common.exceptions import BusinessException
            raise BusinessException(message="격리 세션을 찾을 수 없거나 접근 권한이 없습니다.", error_code="SESSION_NOT_FOUND")
        await self.defense_arena_dao.update_session_activity(session_id)

        # 1. 기존 대화 기록 로드
        histories = await self.defense_arena_dao.get_defense_history(session_id)
        current_turn = len(histories) + 1

        # 심사위원 LLM 인스턴스
        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=settings.OPENAI_API_KEY, temperature=0.7)

        # 2. 첫 턴 시작 (사용자 답변이 없는 상태)
        if not user_response or current_turn == 1:
            # 피어리뷰가 선행되었다고 보고, 세션 정보(문서 요약 등)를 바탕으로 압박 질문을 냅니다.
            # RAG를 통해 문서의 핵심 청크 2개 로드
            from sqlalchemy import select
            result = await self.defense_arena_dao.orm_session.execute(
                select(DefenseArenaChunkEntity)
                .where(DefenseArenaChunkEntity.session_id == session_id)
                .order_by(DefenseArenaChunkEntity.chunk_index.asc())
                .limit(2)
            )
            chunk_list = list(result.scalars().all())
            document_context = "\n\n".join([c.text_chunk for c in chunk_list])

            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a strict, aggressive journal reviewer examining the author's paper draft.\n"
                    "Generate a highly critical, defense-provoking question pointing out a potential methodology flaw, "
                    "novelty gap, or experimental limitation in the provided draft content.\n"
                    "Keep the question academic, sharp, and concise (under 250 characters).\n"
                    "Response must be in English."
                )),
                ("user", "Paper Draft Content:\n{context}")
            ])

            chain = prompt | llm
            question_obj = await chain.ainvoke({"context": document_context})
            question_text = question_obj.content if isinstance(question_obj.content, str) else str(question_obj.content)

            # DB에 첫 질문 레코드 저장
            new_history = DefenseHistoryEntity(
                session_id=session_id,
                turn=1,
                question=question_text,
                answer=None,
                score=None,
                feedback=None
            )
            await self.defense_arena_dao.insert_defense_history(new_history)

            return DefenseChatResponse(
                session_id=session_id,
                turn=1,
                question=question_text,
                score=None,
                feedback=None,
                is_finished=False,
                final_report=None
            )

        # 3. 진행 중인 턴 처리 (사용자가 답변을 보내온 상태)
        # 직전 턴 정보 획득 및 업데이트
        prev_history = await self.defense_arena_dao.get_defense_history_by_turn(session_id, current_turn - 1)
        if not prev_history:
            from api.common.exceptions import BusinessException
            raise BusinessException(message="이전 디펜스 대화 이력을 찾을 수 없습니다.", error_code="PREV_HISTORY_NOT_FOUND")

        # 1) 이전 답변에 대한 실시간 채점 및 크리틱 피드백 수행 (LLM)
        score_llm = llm.with_structured_output(ScoreDTO)
        score_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an academic committee member grading the author's defense response.\n"
                "Analyze the question and the author's response. Evaluate how logically they defended their claim, "
                "acknowledged limitations constructively, or provided valid evidence.\n"
                "Score it out of 100 and provide a sharp, actionable critique in English.\n"
                "Response must be structured."
            )),
            ("user", "Committee's Question: {question}\nAuthor's Defense Response: {answer}")
        ])

        score_chain = score_prompt | score_llm
        grading = await score_chain.ainvoke({
            "question": prev_history.question,
            "answer": user_response
        })

        if not isinstance(grading, ScoreDTO):
            raise TypeError(f"Expected ScoreDTO, got {type(grading)}")

        prev_history.answer = user_response
        prev_history.score = grading.score
        prev_history.feedback = grading.feedback
        await self.defense_arena_dao.update_defense_history(prev_history)

        # 2) 디펜스 최종 세션 종료 여부 결정 (턴 3 도달 시 완료로 설정)
        is_finished = (current_turn - 1 >= 3)
        final_report_text = None

        if is_finished:
            # 대화 전체 이력 종합하여 최종 평가 리포트 합성
            all_histories = await self.defense_arena_dao.get_defense_history(session_id)
            history_summary = "\n\n".join([
                f"Turn {h.turn} Question: {h.question}\n"
                f"Author's Response: {h.answer}\n"
                f"Score: {h.score}/100\n"
                f"Critique: {h.feedback}"
                for h in all_histories if h.answer is not None
            ])

            report_prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are the head of the journal selection board summarizing the author's defense session.\n"
                    "Provide a final, comprehensive defense evaluation report. Critique their strengths, "
                    "re-state remaining gaps, and give a final verdict (e.g., Minor Revision / Major Revision / Reject).\n"
                    "The response must be in English and academic."
                )),
                ("user", "Defense Session Transcripts:\n{summary}")
            ])

            report_chain = report_prompt | llm
            final_report_obj = await report_chain.ainvoke({"summary": history_summary})
            final_report_text = final_report_obj.content if isinstance(final_report_obj.content, str) else str(final_report_obj.content)

            return DefenseChatResponse(
                session_id=session_id,
                turn=current_turn - 1,
                question="모의 디펜스가 모두 종료되었습니다. 최종 스코어카드를 확인해 주십시오.",
                score=grading.score,
                feedback=grading.feedback,
                is_finished=True,
                final_report=final_report_text
            )

        # 3) 다음 턴 압박 질문 생성
        next_question_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a strict academic reviewer in a live oral defense.\n"
                "Follow up on the author's previous answer. Pick on any remaining weak logic, "
                "lack of empirical data, or questionable assumption. Ask the next sharp question.\n"
                "Keep the question academic, critical, and concise (under 250 characters).\n"
                "Response must be in English."
            )),
            ("user", "Previous Question: {prev_question}\nAuthor's Answer: {prev_answer}\nCommittee's Critique: {critique}")
        ])

        next_chain = next_question_prompt | llm
        next_question_obj = await next_chain.ainvoke({
            "prev_question": prev_history.question,
            "prev_answer": user_response,
            "critique": grading.feedback
        })
        next_question_text = next_question_obj.content if isinstance(next_question_obj.content, str) else str(next_question_obj.content)

        # DB에 다음 턴 질문 레코드 미리 생성
        new_next_history = DefenseHistoryEntity(
            session_id=session_id,
            turn=current_turn,
            question=next_question_text,
            answer=None,
            score=None,
            feedback=None
        )
        await self.defense_arena_dao.insert_defense_history(new_next_history)

        return DefenseChatResponse(
            session_id=session_id,
            turn=current_turn,
            question=next_question_text,
            score=grading.score,
            feedback=grading.feedback,
            is_finished=False,
            final_report=None
        )

    async def wipe_out_expired_sessions(self, expire_minutes: int = 30) -> int:
        """30분 동안 미활동 시 세션 PDF 파일 및 pgvector 임시 데이터를 영구 소거(Wipe Out)합니다."""
        # 1. 만료 세션 목록 로드
        expired = await self.defense_arena_dao.list_expired_sessions(expire_minutes)
        if not expired:
            return 0

        self.logger.info(f"Wiping out {len(expired)} expired security sessions...")
        count = 0

        for session in expired:
            session_id = session.session_id
            
            # 2. 로컬 파일 소거 (OS Path Guard 검증 적용)
            session_dir = os.path.join(UPLOAD_DIR, session_id)
            real_upload_dir = os.path.realpath(UPLOAD_DIR)
            target_dir = os.path.realpath(session_dir)

            # OS Path Guard (디렉토리 트래버스 방지)
            if target_dir.startswith(real_upload_dir) and target_dir != real_upload_dir:
                try:
                    await asyncio.to_thread(shutil.rmtree, target_dir, ignore_errors=True)
                except Exception as ex:
                    self.logger.error(f"Failed to delete session directory {target_dir}: {ex}")

            # 3. DB 세션 레코드 삭제 (CASCADE에 의해 defense_arena_chunk, defense_history 자동 일괄 삭제 처리됨)
            success = await self.defense_arena_dao.delete_session(session_id)
            if success:
                count += 1

        self.logger.info(f"Wipe out completed. Total {count} sessions deleted.")
        return count


DefenseArenaServiceDep = Annotated[DefenseArenaService, Depends(DefenseArenaService)]
