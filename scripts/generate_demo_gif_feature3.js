/**
 * generate_demo_gif_feature3.js
 * 
 * Playwright와 FFmpeg를 사용하여 Feature 3 (Gems Factory) 시나리오를
 * 클라이언트 사이드 Mock Mode를 활성화하여 1920x1080 고해상도로 녹화 및 추출하는 자동화 스크립트입니다.
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
  console.log(`\n🎬 [Scenario: ${name}] 자동화 및 녹화를 시작합니다. (Mock Mode 활성화)`);

  const browser = await chromium.launch({
    headless: true,
    args: ["--start-maximized", "--disable-web-security"]
  });
  
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: OUTPUT_DIR,
      size: { width: 1920, height: 1080 }
    }
  });

  // Client-side Mock Mode 활성화 및 Next.js 개발 오버레이 비활성화
  await context.addInitScript(() => {
    window.localStorage.setItem("useMock", "true");
    
    // Next.js dev overlay badge 숨김 스타일 동적 주입
    const style = document.createElement("style");
    style.innerHTML = `
      nextjs-portal,
      #nextjs-dev-overlay,
      .__next-toast-selector {
        display: none !important;
      }
    `;
    const inject = () => document.head.appendChild(style);
    document.head ? inject() : window.addEventListener("DOMContentLoaded", inject);
  });

  const page = await context.newPage();

  page.on("console", msg => console.log(`[browser-log] ${msg.text()}`));
  page.on("pageerror", err => console.error(`[browser-error] ${err.message}`));
  
  try {
    // 1. 로그인 단계 (Mock 로그인 진행)
    const loginUrl = `${BASE_URL}/login`;
    console.log(`🔗 로그인 페이지 진입: ${loginUrl}`);
    await page.goto(loginUrl);
    await page.waitForLoadState("load");
    await sleep(1500);

    console.log("🔑 로그인 정보 입력 중...");
    await page.fill('input[type="text"]', username);
    await page.fill('input[type="password"]', password);
    await page.click('button:has-text("로그인"), button[type="submit"]');
    
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

  const dummyFilePath = path.join(__dirname, "astro_background_cmb.pdf");
  fs.writeFileSync(dummyFilePath, "%PDF-1.4\n%âãÏÓ\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [ 3 0 R ] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [ 0 0 612 792 ] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000015 00000 n\n0000000074 00000 n\n0000000120 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF");

  const timestamp = Date.now();
  const username = `user_${timestamp}`;
  const password = `pass_${timestamp}`;

  // 1. 회원가입 사전 선행 시나리오 (Mock Mode 활성화 상태)
  console.log(`👤 [Registration] 신규 회원가입 진행 중 (${username})...`);
  const regBrowser = await chromium.launch({
    headless: true,
    args: ["--start-maximized", "--disable-web-security"]
  });
  const regContext = await regBrowser.newContext({ viewport: { width: 1920, height: 1080 } });
  
  // Client-side Mock Mode 활성화 및 Next.js 개발 오버레이 비활성화
  await regContext.addInitScript(() => {
    window.localStorage.setItem("useMock", "true");
    
    // Next.js dev overlay badge 숨김 스타일 동적 주입
    const style = document.createElement("style");
    style.innerHTML = `
      nextjs-portal,
      #nextjs-dev-overlay,
      .__next-toast-selector {
        display: none !important;
      }
    `;
    const inject = () => document.head.appendChild(style);
    document.head ? inject() : window.addEventListener("DOMContentLoaded", inject);
  });

  const regPage = await regContext.newPage();
  
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

  // 2. Feature 3: Gems 커스텀 AI 젬 생성 및 특화 채팅
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

      console.log("🤖 참고 파일 업로드 시뮬레이션...");
      const fileInput = await page.locator('input[type="file"]');
      await fileInput.setInputFiles(dummyFilePath);
      await sleep(1500);

      console.log("🤖 Gem 생성 완료 처리...");
      await page.click('.gem-editor-save-btn-bottom, button:has-text("Gem 만들기")');
      
      console.log("🤖 목록으로 복귀 대기...");
      await sleep(3000);

      console.log("🤖 NASA JPL 우주론 비서 젬 선택...");
      await page.click('.gem-card h6:has-text("NASA"), .gem-card');
      await sleep(2000);

      console.log("🤖 젬 비서에게 질문 전송...");
      const chatInput = await page.locator('input.gem-chat-input');
      // Mock 답변(우주론 분석 결과)과 매칭되는 자연스러운 우주론 질문으로 보정합니다.
      await chatInput.fill("Tell me about dynamic dark energy models and CMB tension.");
      await sleep(1000);
      await page.keyboard.press("Enter");

      console.log("🤖 젬 특화 답변 스트리밍 완료 대기...");
      await page.waitForSelector('input.gem-chat-input:not([disabled])', { timeout: 45000 });
      await sleep(1500); // 답변 완독용 여유 시간

      console.log("🤖 출처 버튼 클릭하여 참고 출처 패널 열기...");
      await page.click('.gem-msg-papers-btn');
      await sleep(3500); // 출처 슬라이드 패널 감상 시간
    }
  );

  console.log("\n🏁 Feature 3 전용 데모 1920x1080 GIF 생성이 완성되었습니다!");
  try {
    fs.unlinkSync(dummyFilePath);
  } catch (e) {}
}

main().catch(console.error);
