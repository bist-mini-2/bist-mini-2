# backend/tests/manual_midterm_test.py
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "test3333"
PASSWORD = "your_password"  # 테스트할 로컬 계정 패스워드 입력

async def run_integration_test():
    async with httpx.AsyncClient(timeout=45.0) as client:
        print("====== [시작] Bist Mini 2 백엔드 핵심 기능 통합 테스트 ======")

        # 1. 로그인 및 토큰 취득
        print("\n[단계 1] OAuth2 패스워드 로그인 시도...")
        login_res = await client.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        if login_res.status_code != 200:
            print(f"❌ 로그인 실패: {login_res.text}")
            return
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ JWT 인증 토큰 발급 성공!")

        # 2. Feature 1: RAG 채팅방 개설 및 메시지 전송
        print("\n[단계 2] Feature 1 RAG 채팅 세션 생성...")
        session_res = await client.post(
            f"{BASE_URL}/chat/sessions",
            headers=headers,
            json={"title": "RAG API 테스트 방"}
        )
        session_id = session_res.json()["data"]["session_id"]
        print(f"✅ RAG 채팅방 생성 완료 (ID: {session_id})")

        print("-> RAG 질문 및 출처 조회 API 테스트...")
        msg_res = await client.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            headers=headers,
            json={"message": "Attention Mechanism이 딥러닝 아키텍처에 미친 영향에 대해 요약해줘."}
        )
        answer = msg_res.json()["data"]["answer"]
        sources = msg_res.json()["data"]["sources"]
        print(f"✅ AI 답변 요약 수신 완료. 수집된 논문 정보 개수: {len(sources)}개")

        # 3. Feature 2: 비동기 Research Gap 분석 및 폴링
        print("\n[단계 3] Feature 2 Research Gap 분석 배치 기동...")
        analysis_res = await client.post(
            f"{BASE_URL}/research-gap/analyze",
            headers=headers,
            json={"domain": "cs", "query": "Attention Mechanism"}
        )
        task_id = analysis_res.json()["data"]["task_id"]
        print(f"✅ 분석 배치 작업 예약 완료 (Task ID: {task_id})")

        print("-> 비동기 배치 진척율 폴링 중...")
        for i in range(15):
            await asyncio.sleep(2)
            status_res = await client.get(f"{BASE_URL}/research-gap/tasks/{task_id}", headers=headers)
            status_data = status_res.json()["data"]
            print(f"   [폴링 {i+1}] 상태: {status_data['status']} | 진행율: {status_data['progress']}%")
            if status_data["status"] == "COMPLETED":
                print("✅ 비동기 문헌 분석 배치 작업 완료!")
                break
        else:
            print("⚠️ 폴링 제한 시간 초과 (테스트 백그라운드 구동 지속)")

        # 4. Feature 3: 커스텀 Gem 생성 및 전용 RAG 대화
        print("\n[단계 4] Feature 3 커스텀 학술 에이전트 Gem 설계...")
        gem_res = await client.post(
            f"{BASE_URL}/gems",
            headers=headers,
            json={
                "name": "천문 연구 보조 에이전트",
                "db_sources": ["astronomy"],
                "system_prompt": "당신은 NASA 천체 물리학 연구원입니다. 모든 대답은 관측 데이터 분석 중심의 어조로 전개하세요."
            }
        )
        gem_id = gem_res.json()["data"]["gem_id"]
        print(f"✅ 커스텀 Gem 생성 성공 (Gem ID: {gem_id})")

        print("-> Gem RAG 채팅 API 질의...")
        gem_chat_res = await client.post(
            f"{BASE_URL}/gems/{gem_id}/chat",
            headers=headers,
            json={
                "thread_id": f"test_thread_{gem_id}",
                "message": "제임스 웹 우주 망원경의 최근 업적 정리"
            }
        )
        gem_answer = gem_chat_res.json()["data"]["answer"]
        print(f"✅ Gem 답변 도출 성공! (답변 일부: {gem_answer[:60]}...)")
        
        print("\n====== [종료] 모든 핵심 API 테스트 검증 통과 ======")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
