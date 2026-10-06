import type { NextConfig } from 'next';
const apiOrigin = process.env.API_ORIGIN?.replace(/\/$/, '');
const nextConfig: NextConfig = {
  outputFileTracingRoot: process.cwd(),
  poweredByHeader: false,
  async rewrites() { return apiOrigin ? [{ source: '/api/:path*', destination: `${apiOrigin}/api/:path*` }] : []; },
};
export default nextConfig;
