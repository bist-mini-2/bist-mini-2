/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  basePath: '/bist-mini-2',
  allowedDevOrigins: ['192.168.5.13'],
  devIndicators: {
    appIsrStatus: false,
  },
};

export default nextConfig;
