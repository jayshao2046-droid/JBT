export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'trader' | 'analyst' | 'viewer';
  avatar?: string;
  membershipLevel?: 'free' | 'pro' | 'enterprise';
}

export interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error';
  uptime?: number;
  lastCheck: string;
}

export interface SystemStats {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    in: number;
    out: number;
  };
}

export interface TradingSession {
  isOpen: boolean;
  nextOpen?: string;
  nextClose?: string;
  currentPhase?: 'pre-market' | 'trading' | 'post-market' | 'closed';
}

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export interface Alert {
  id: string;
  level: 'critical' | 'warning' | 'info';
  service: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
}
