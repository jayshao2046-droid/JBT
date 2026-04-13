export const API_ENDPOINTS = {
  SIM_TRADING: '/api/sim-trading',
  BACKTEST: '/api/backtest',
  DECISION: '/api/decision',
  DATA: '/api/data',
} as const;

export const SERVICE_PORTS = {
  SIM_TRADING: 8001,
  BACKTEST: 8002,
  DECISION: 8003,
  DATA: 8004,
} as const;

export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/',
  SETTINGS: '/settings',
  SIM_TRADING: '/sim-trading',
  BACKTEST: '/backtest',
  DECISION: '/decision',
  DATA: '/data',
} as const;
