/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async headers() {
    const apiOrigin = process.env.NEXT_PUBLIC_API_URL ? new URL(process.env.NEXT_PUBLIC_API_URL).origin : '';
    const isProd = process.env.NODE_ENV === 'production';
    const scripts = isProd ? "'self' 'unsafe-inline'" : "'self' 'unsafe-inline' 'unsafe-eval'";
    const upgradeInsecure = isProd ? '; upgrade-insecure-requests' : '';
    const csp = `default-src 'self'; script-src ${scripts}; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data: https:; font-src 'self' data:; connect-src 'self' ${apiOrigin}; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'${upgradeInsecure}`;
    return [{ source: '/:path*', headers: [
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'X-Frame-Options', value: 'DENY' },
      { key: 'Referrer-Policy', value: 'no-referrer' },
      { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
      { key: 'Content-Security-Policy', value: csp },
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
