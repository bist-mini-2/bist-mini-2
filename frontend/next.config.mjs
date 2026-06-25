/** @type {import('next').NextConfig} */
const isElectron = process.env.BUILD_TARGET === "electron";

const nextConfig = {
  ...(isElectron
    ? { output: "export", distDir: "out", images: { unoptimized: true } }
    : {}),
  trailingSlash: true, // file:// 환경에서 라우트 폴더 매핑 안정화
  allowedDevOrigins: ['192.168.5.13'],
};

export default nextConfig;
