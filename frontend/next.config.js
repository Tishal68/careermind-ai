/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async headers() {
    const apiOrigin = process.env.NEXT_PUBLIC_API_URL ? new URL(process.env.NEXT_PUBLIC_API_URL).origin : '';
    const scripts = process.env.NODE_ENV === 'development' ? "'self' 'unsafe-inline' 'unsafe-eval'" : "'self' 'unsafe-inline'";
    return [{ source: '/:path*', headers: [
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'X-Frame-Options', value: 'DENY' },
      { key: 'Referrer-Policy', value: 'no-referrer' },
      { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
      { key: 'Content-Security-Policy', value: `default-src 'self'; script-src ${scripts}; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ${apiOrigin}; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'` },
    ] }];
  },
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
        destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/v1/openapi.json`,
      },
    ];
  },
};

module.exports = nextConfig;
