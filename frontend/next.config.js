/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    // Local CPU inference can take longer than Next's default 30 seconds.
    proxyTimeout: 210000,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    // Proxy /api/v1 calls to the internal FastAPI server running on port 8000
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/v1/:path*`,
      },
      {
        source: '/docs',
        destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/docs`,
      },
      {
        source: '/openapi.json',
        destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/openapi.json`,
      },
    ];
  },
};

module.exports = nextConfig;
