const { app, BrowserWindow } = require("electron");
const http = require("http");
const fs = require("fs");
const path = require("path");

// 정적 export 결과(out/)는 절대경로 에셋(/_next/...)을 사용하므로 file://로는
// 로드할 수 없다. 대신 main 프로세스에서 out/을 localhost로 서빙하고 loadURL로 진입한다.
const OUT_DIR = path.join(__dirname, "../out");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".map": "application/json; charset=utf-8",
};

// 요청 경로를 out/ 내부의 실제 파일로 안전하게 매핑한다.
// trailingSlash:true 이므로 라우트는 폴더/index.html 형태로 생성된다.
function resolveFile(urlPath) {
  let pathname = decodeURIComponent(urlPath.split("?")[0].split("#")[0]);
  if (pathname.endsWith("/")) pathname += "index.html";

  const candidates = [
    pathname,
    pathname + ".html",
    pathname + "/index.html",
  ];

  for (const candidate of candidates) {
    const full = path.join(OUT_DIR, candidate);
    // 경로 탈출(path traversal) 방지: 반드시 OUT_DIR 내부여야 한다.
    if (!full.startsWith(OUT_DIR)) continue;
    try {
      if (fs.statSync(full).isFile()) return full;
    } catch {
      /* not found, try next candidate */
    }
  }
  return null;
}

function startServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const file = resolveFile(req.url);
      if (file) {
        res.statusCode = 200;
        res.setHeader("Content-Type", MIME[path.extname(file)] || "application/octet-stream");
        fs.createReadStream(file).pipe(res);
        return;
      }
      // 매칭 실패 시 정적 404 페이지로 폴백
      const notFound = path.join(OUT_DIR, "404.html");
      res.statusCode = 404;
      res.setHeader("Content-Type", "text/html; charset=utf-8");
      if (fs.existsSync(notFound)) fs.createReadStream(notFound).pipe(res);
      else res.end("404 Not Found");
    });
    // 127.0.0.1 + 포트 0(임의의 빈 포트)으로 외부 노출 없이 바인딩
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

let server;

function createWindow(port) {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    title: "Paper Agent",
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  });
  // 루트(/)는 /feature1로 redirect 이므로 feature1로 직접 진입
  win.loadURL(`http://127.0.0.1:${port}/feature1/`);
  // 개발 중 디버깅이 필요하면: win.webContents.openDevTools();
}

app.whenReady().then(async () => {
  server = await startServer();
  const { port } = server.address();
  createWindow(port);
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow(port);
  });
});

app.on("window-all-closed", () => {
  if (server) server.close();
  if (process.platform !== "darwin") app.quit();
});
