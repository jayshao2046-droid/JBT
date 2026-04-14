import type { NextConfig } from "next";

const SIM_TRADING_URL = process.env.SIM_TRADING_URL ?? 'http://localhost:8101';
const BACKTEST_URL    = process.env.BACKTEST_URL    ?? 'http://localhost:8103';
const DATA_URL        = process.env.DATA_URL        ?? 'http://localhost:8105';
const DECISION_URL    = process.env.DECISION_URL    ?? 'http://localhost:8104';

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/sim-trading/:path*',
        destination: `${SIM_TRADING_URL}/:path*`,
      },
      {
        source: '/api/backtest/:path*',
        destination: `${BACKTEST_URL}/:path*`,
      },
      {
        source: '/api/data/:path*',
        destination: `${DATA_URL}/:path*`,
      },
      {
        source: '/api/decision/:path*',
        destination: `${DECISION_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
