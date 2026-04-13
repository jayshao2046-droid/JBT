import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/sim-trading/:path*',
        destination: 'http://localhost:8101/:path*',
      },
      {
        source: '/api/backtest/:path*',
        destination: 'http://localhost:8103/:path*',
      },
      {
        source: '/api/data/:path*',
        destination: 'http://localhost:8105/:path*',
      },
      {
        source: '/api/decision/:path*',
        destination: 'http://localhost:8104/:path*',
      },
    ];
  },
};

export default nextConfig;
