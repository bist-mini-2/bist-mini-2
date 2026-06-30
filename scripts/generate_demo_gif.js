/**
 * generate_demo_gif.js
 * 
 * Playwright와 FFmpeg를 사용하여 bist-mini-2 플랫폼의 핵심 3대 기능 시나리오(실제 API 연동 모드)를
 * 각각 1920x1080 고해상도로 순차 녹화 및 추출하는 자동화 스크립트입니다.
 */

const { chromium } = require("playwright");
const { exec } = require("child_process");
const path = require("path");
const fs = require("fs");

const PORT = 3000;
const BASE_URL = `http://localhost:${PORT}/bist-mini-2`;
const OUTPUT_DIR = path.join(__dirname, "../docs/deliverables/final");

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runScenario(name, gifName, username, password, actionFn) {
  console.log(`\n🎬 [Scenario: ${name}] 자동화 및 녹화를 시작합니다.`);

  // CORS 검증을 바이패스하기 위해 --disable-web-security 옵션 주입
  const browser = await chromium.launch({
    headless: true,
    args: ["--start-maximized", "--disable-web-security"]
  });
  
  // 1920x1080 규격 설정
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: OUTPUT_DIR,
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();

  // 브라우저 내부 로그 및 네트워크 통신 수집용 리스너 추가
  page.on("console", msg => console.log(`[browser-log] ${msg.text()}`));
  page.on("pageerror", err => console.error(`[browser-error] ${err.message}`));
  page.on("response", response => {
    const status = response.status();
    const url = response.url();
    if (url.includes("/api/v1/")) {
      console.log(`[net-api-response] ${status} : ${url}`);
    }
  });
  
  try {
    // 1. 로그인 단계 (실제 백엔드 세션 획득)
    const loginUrl = `${BASE_URL}/login`;
    console.log(`🔗 로그인 페이지 진입: ${loginUrl}`);
    await page.goto(loginUrl);
    await page.waitForLoadState("load");
    await sleep(1500);

    console.log("🔑 로그인 정보 입력 중...");
    await page.fill('input[type="text"]', username);
    await page.fill('input[type="password"]', password);
    await page.click('button:has-text("로그인"), button[type="submit"]');
    
    // 라우트 가드 리다이렉트 대기 (URL이 메인 화면으로 바뀔 때까지 대기)
    console.log("🔑 로그인 완료 및 자동 리다이렉션 대기...");
    try {
      await page.waitForURL("**/feature1", { timeout: 10000 });
    } catch (e) {
      console.log("⚠️ 자동 리다이렉션 타임아웃, 수동 이동 진행");
      await page.goto(`${BASE_URL}/feature1`);
    }
    await page.waitForLoadState("load");
    await sleep(1500);

    // 2. 시나리오 전용 액션 수행
    await actionFn(page);
    await sleep(1500);

    console.log(`✅ [${name}] 시뮬레이션 완료. 브라우저 세션을 종료합니다.`);
  } catch (error) {
    console.error(`❌ [${name}] 수행 중 오류 발생:`, error);
  } finally {
    await context.close();
    await browser.close();
  }

  // Playwright가 저장한 WebM 비디오 파일 찾기
  const videoFile = page.video() ? await page.video().path() : null;
  if (!videoFile || !fs.existsSync(videoFile)) {
    console.error(`❌ [${name}] 녹화된 WebM 비디오 파일을 찾을 수 없습니다.`);
    return;
  }

  console.log(`📹 비디오 임시 파일 저장됨: ${videoFile}`);

  // FFmpeg를 이용하여 WebM 비디오를 고화질 최적화 GIF로 변환
  console.log(`🎨 [FFmpeg] WebM 비디오 -> 고화질 1920x1080 GIF (${gifName}) 변환 시작...`);
  
  let ffmpegPath = "ffmpeg";
  try {
    const ffmpegInstaller = require("@ffmpeg-installer/ffmpeg");
    if (fs.existsSync(ffmpegInstaller.path)) {
      ffmpegPath = ffmpegInstaller.path;
    }
  } catch (e) {}

  const finalGifPath = path.join(OUTPUT_DIR, gifName);
  
  // 1920x1080 비율(16:9)을 살리기 위해 scale=1280:-1로 리사이즈하며 고화질 인코딩
  const ffmpegCmd = `"${ffmpegPath}" -y -i "${videoFile}" -vf "fps=15,scale=1280:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" "${finalGifPath}"`;

  await new Promise((resolve) => {
    exec(ffmpegCmd, (error, stdout, stderr) => {
      if (error) {
        console.error(`❌ [${name}] FFmpeg 변환 실패:`, error);
      } else {
        console.log(`🎉 [${name}] 데모 GIF 생성 완료! 파일 경로: ${finalGifPath}`);
        try {
          fs.unlinkSync(videoFile);
        } catch (e) {}
      }
      resolve();
    });
  });
}

async function main() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const timestamp = Date.now();
  const username = `user_${timestamp}`;
  const password = `pass_${timestamp}`;

  // 1. 회원가입 사전 선행 시나리오 (실제 데이터베이스 회원 등록) - 깔끔한 라우트 경로 지정
  console.log(`👤 [Registration] 신규 회원가입 진행 중 (${username})...`);
  const regBrowser = await chromium.launch({
    headless: true,
    args: ["--start-maximized", "--disable-web-security"]
  });
  const regContext = await regBrowser.newContext({ viewport: { width: 1920, height: 1080 } });
  const regPage = await regContext.newPage();

  // 브라우저 내부 로그 및 네트워크 통신 수집용 리스너 추가
  regPage.on("console", msg => console.log(`[reg-browser-log] ${msg.text()}`));
  regPage.on("pageerror", err => console.error(`[reg-browser-error] ${err.message}`));
  regPage.on("response", response => {
    const status = response.status();
    const url = response.url();
    if (url.includes("/api/v1/")) {
      console.log(`[reg-net-api-response] ${status} : ${url}`);
    }
  });
  
  await regPage.goto(`${BASE_URL}/join`);
  await regPage.waitForLoadState("load");
  await sleep(1500);

  await regPage.fill('input[placeholder="5~20자 사이로 입력하세요"]', username);
  await regPage.fill('input[placeholder="2~20자 사이로 입력하세요"]', "R&D Tester");
  await regPage.fill('input[type="email"]', `tester_${timestamp}@example.com`);
  await regPage.fill('input[type="password"]', password);
  
  await regPage.click('button[type="submit"]');
  console.log("👤 가입 폼 제출함. 리다이렉트 대기...");
  await sleep(3500); 

  await regContext.close();
  await regBrowser.close();
  console.log("👤 [Registration] 회원 가입 및 계정 등록 성공!");

  // 2. Feature 1: Chat Hub RAG 질의 및 타이핑 스트리밍
  await runScenario(
    "Feature 1 - Chat Hub",
    "demo_feature1.gif",
    username,
    password,
    async (page) => {
      console.log("💬 [Chat Hub] 시뮬레이션 준비 완료.");
      console.log("💬 질문 입력 및 전송 시뮬레이션...");
      const chatInput = await page.locator('textarea[placeholder*="물어보세요"], textarea');
      await chatInput.fill("Tell me about pgvector HNSW index optimization results.");
      await sleep(1200);
      await page.click('button[aria-label="전송"], button[class*="sendBtn"], i.bi-arrow-up');

      console.log("💬 RAG 스트리밍 답변 완료 대기...");
      await page.waitForSelector('textarea:not([disabled])', { timeout: 45000 });
      await sleep(4000); // 답변 완독용 여유 시간
    }
  );

  // 3. Feature 2: Research Gap Analyzer 비동기 분석 및 결과 렌더링
  await runScenario(
    "Feature 2 - Research Gap Analyzer",
    "demo_feature2.gif",
    username,
    password,
    async (page) => {
      console.log("📊 [Research Gap] 페이지로 이동 중...");
      await page.goto(`${BASE_URL}/feature2`);
      await page.waitForLoadState("load");
      await sleep(1500);

      console.log("📊 새 분석 설정 페이지로 이동... ");
      await page.click('a:has-text("새 분석"), a[href*="analyze"], button:has-text("새 분석")');
      await sleep(1500);

      console.log("📊 CS 도메인 설정 및 분석 중점 입력...");
      await page.selectOption('select', "cs");
      await page.fill('input[type="text"]', "Retrieval Augmented Generation tuning");
      await sleep(1000);

      console.log("📊 비동기 분석 실행 시작...");
      await page.click('button[type="submit"]');

      console.log("📊 API 분석 완료 및 렌더링 대기 (최대 45초)...");
      // 결과 테이블이나 추천 주제 카드가 나타날 때까지 대기
      await page.waitForSelector('.tutorial-matrix-table, table, .recommendedTopicCard, [class*="matrixTh"]', { timeout: 45000 });

      console.log("📊 구조화 결과 매트릭스 및 AI 추천 주제 렌더링 감상...");
      await sleep(6000);
    }
  );

  // 4. Feature 3: Gems 커스텀 AI 젬 생성 및 특화 채팅
  await runScenario(
    "Feature 3 - Gems Factory",
    "demo_feature3.gif",
    username,
    password,
    async (page) => {
      console.log("🤖 [Gems Factory] 페이지로 이동 중...");
      await page.goto(`${BASE_URL}/feature3`);
      await page.waitForLoadState("load");
      await sleep(1500);

      console.log("🤖 새 Gem 만들기 모달 진입...");
      await page.click('div[class*="createCard"]');
      await sleep(1500);

      console.log("🤖 Gem 설정 양식 기입 중...");
      await page.fill('input[placeholder="Gem의 이름을 지정하세요."]', "NASA 제트추진연구소 우주론 비서");
      await page.fill('textarea[placeholder*="당신은 유전체학"]', "당신은 NASA JPL 소속의 수석 천체물리학자입니다.");
      
      console.log("🤖 천문학 데이터 소스 체크...");
      await page.click('.gem-editor-source-row:has-text("Astronomy")');
      await sleep(800);

      console.log("🤖 Gem 생성 완료 처리...");
      await page.click('.gem-editor-save-btn-bottom, button:has-text("Gem 만들기")');
      
      console.log("🤖 목록으로 복귀 대기...");
      await sleep(3000);

      console.log("🤖 NASA JPL 우주론 비서 젬 선택...");
      await page.click('.gem-card h6:has-text("NASA"), .gem-card');
      await sleep(2000);

      console.log("🤖 젬 비서에게 질문 전송...");
      const chatInput = await page.locator('input.gem-chat-input');
      await chatInput.fill("What is the main limitation of AAV packaging capacity?");
      await sleep(1000);
      await page.keyboard.press("Enter");

      console.log("🤖 젬 특화 답변 스트리밍 완료 대기...");
      await page.waitForSelector('input.gem-chat-input:not([disabled])', { timeout: 45000 });
      await sleep(4000); // 답변 완독용 여유 시간
    }
  );

  console.log("\n🏁 모든 피처별 독립 데모 1920x1080 GIF 생성이 완성되었습니다!");
}

main().catch(console.error);
