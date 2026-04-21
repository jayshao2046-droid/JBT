'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  RefreshCw, Activity, CheckCircle2, XCircle, AlertCircle,
  Play, Pause,
  Zap, Monitor, Database, Brain, BarChart2,
  Clock, Copy, Terminal, Server, PlugZap,
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────
//  Utility: fetch with timeout + latency measurement
// ─────────────────────────────────────────────────────────────
async function timedFetch<T>(
  url: string,
  options?: RequestInit & { timeoutMs?: number },
): Promise<{ data: T | null; latency: number; ok: boolean; detail: string }> {
  const timeoutMs = options?.timeoutMs ?? 6000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const start = Date.now();
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timer);
    const latency = Date.now() - start;
    if (!res.ok) return { data: null, latency, ok: false, detail: `HTTP ${res.status}` };
    const data = await res.json().catch(() => ({})) as T;
    return { data, latency, ok: true, detail: 'OK' };
  } catch (e: unknown) {
    clearTimeout(timer);
    const latency = Date.now() - start;
    const msg = e instanceof Error ? (e.name === 'AbortError' ? '超时' : e.message) : '连接失败';
    return { data: null, latency, ok: false, detail: msg };
  }
}

// ─────────────────────────────────────────────────────────────
//  Types
// ─────────────────────────────────────────────────────────────
type HealthStatus = 'online' | 'degraded' | 'offline' | 'checking';

interface CheckResult {
  name: string;
  status: 'pass' | 'fail' | 'skip';
  latency: number | null;
  detail: string;
}

interface Metric {
  label: string;
  value: string | null;
  sub?: string;
  accent?: 'green' | 'red' | 'yellow' | 'blue' | 'default';
}

interface ServiceState {
  health: HealthStatus;
  latency: number | null;
  lastCheck: Date | null;
  checks: CheckResult[];
  metrics: Metric[];
  error: string | null;
}

interface ActionResult {
  ok: boolean;
  message: string;
}

interface ActionDef {
  id: string;
  label: string;
  Icon: React.ElementType;
  variant?: 'default' | 'destructive' | 'outline';
  confirm?: string;
  execute: () => Promise<ActionResult>;
}

interface ServiceDef {
  id: string;
  name: string;
  device: string;
  ip: string;
  port: number;
  dockerName: string;
  sshUser: string;
  accentBorder: string;
  accentText: string;
  accentBg: string;
  DeviceIcon: React.ElementType;
  fetchState: () => Promise<Pick<ServiceState, 'health' | 'checks' | 'metrics'>>;
  actions: ActionDef[];
}

// ─────────────────────────────────────────────────────────────
//  Service Definitions
// ─────────────────────────────────────────────────────────────
const SERVICES: ServiceDef[] = [
  // ── 模拟交易 (Alienware) ──────────────────────────────────
  {
    id: 'sim-trading',
    name: '模拟交易',
    device: 'Alienware',
    ip: '192.168.31.223',
    port: 8101,
    dockerName: 'JBT-SIM-8101',
    sshUser: '17621',
    accentBorder: 'border-orange-500/40',
    accentText: 'text-orange-400',
    accentBg: 'bg-orange-500/10',
    DeviceIcon: Monitor,
    async fetchState() {
      const checks: CheckResult[] = [];
      const metrics: Metric[] = [];

      // 1. API Health
      const h = await timedFetch<{ status: string }>('/api/sim-trading/api/v1/health');
      checks.push({ name: 'API 健康', status: h.ok ? 'pass' : 'fail', latency: h.latency, detail: h.ok ? 'OK' : h.detail });

      // 2. System state
      const state = await timedFetch<{ trading_enabled: boolean; active_preset: string; paused_reason: string | null }>(
        '/api/sim-trading/api/v1/system/state',
      );
      checks.push({
        name: '交易状态',
        status: state.ok ? 'pass' : 'fail',
        latency: state.latency,
        detail: state.ok
          ? (state.data?.trading_enabled ? '交易开启' : `已暂停: ${state.data?.paused_reason ?? ''}`)
          : state.detail,
      });
      if (state.ok && state.data) {
        metrics.push({
          label: '交易开关',
          value: state.data.trading_enabled ? '已开启' : '已暂停',
          sub: state.data.active_preset || '默认预设',
          accent: state.data.trading_enabled ? 'green' : 'yellow',
        });
      }

      // 3. CTP Status
      const ctp = await timedFetch<{ md_connected: boolean; td_connected: boolean }>(
        '/api/sim-trading/api/v1/ctp/status',
      );
      const ctpOk = ctp.ok && ctp.data?.md_connected && ctp.data?.td_connected;
      const ctpPartial = ctp.ok && (ctp.data?.md_connected || ctp.data?.td_connected) && !ctpOk;
      checks.push({
        name: 'CTP 连接',
        status: ctpOk ? 'pass' : ctpPartial ? 'fail' : 'fail',
        latency: ctp.latency,
        detail: ctp.ok
          ? `MD:${ctp.data?.md_connected ? '✓' : '✗'} TD:${ctp.data?.td_connected ? '✓' : '✗'}`
          : ctp.detail,
      });
      if (ctp.ok && ctp.data) {
        metrics.push({
          label: 'CTP',
          value: ctpOk ? '全连接' : ctpPartial ? '部分连接' : '断线',
          sub: `MD ${ctp.data.md_connected ? '✓' : '✗'} / TD ${ctp.data.td_connected ? '✓' : '✗'}`,
          accent: ctpOk ? 'green' : 'red',
        });
      }

      // 4. Risk L1
      const risk = await timedFetch<{ l1_status: { trading_allowed: boolean } }>(
        '/api/sim-trading/api/v1/risk/l1',
      );
      checks.push({
        name: '风控 L1',
        status: risk.ok ? 'pass' : 'fail',
        latency: risk.latency,
        detail: risk.ok ? (risk.data?.l1_status?.trading_allowed ? '允许交易' : '风控触发') : risk.detail,
      });
      if (risk.ok && risk.data?.l1_status) {
        metrics.push({
          label: '风控',
          value: risk.data.l1_status.trading_allowed ? '正常' : '触发',
          accent: risk.data.l1_status.trading_allowed ? 'green' : 'red',
        });
      }

      // Overall health
      const passCount = checks.filter(c => c.status === 'pass').length;
      const health: HealthStatus = !h.ok ? 'offline' : passCount >= 3 ? 'online' : 'degraded';
      return { health, checks, metrics };
    },
    actions: [
      {
        id: 'pause',
        label: '暂停交易',
        Icon: Pause,
        variant: 'outline',
        confirm: '确认暂停模拟交易？',
        async execute() {
          const r = await timedFetch<{ result: string }>('/api/sim-trading/api/v1/system/pause', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: '前台手动暂停' }),
          });
          return { ok: r.ok, message: r.ok ? '已暂停交易' : r.detail };
        },
      },
      {
        id: 'resume',
        label: '恢复交易',
        Icon: Play,
        variant: 'outline',
        confirm: '确认恢复模拟交易？',
        async execute() {
          const r = await timedFetch<{ result: string }>('/api/sim-trading/api/v1/system/resume', {
            method: 'POST',
          });
          return { ok: r.ok, message: r.ok ? '已恢复交易' : r.detail };
        },
      },
      {
        id: 'ctp-connect',
        label: 'CTP 重连',
        Icon: PlugZap,
        variant: 'outline',
        confirm: '重新连接 CTP？',
        async execute() {
          await timedFetch('/api/sim-trading/api/v1/ctp/disconnect', { method: 'POST' });
          const r = await timedFetch<{ result: string }>('/api/sim-trading/api/v1/ctp/connect', { method: 'POST' });
          return { ok: r.ok, message: r.ok ? 'CTP 重连已触发' : r.detail };
        },
      },
    ],
  },

  // ── 决策引擎 (Studio) ──────────────────────────────────────
  {
    id: 'decision',
    name: '决策引擎',
    device: 'Studio',
    ip: '192.168.31.142',
    port: 8104,
    dockerName: 'JBT-DECISION-8104',
    sshUser: 'jaybot',
    accentBorder: 'border-blue-500/40',
    accentText: 'text-blue-400',
    accentBg: 'bg-blue-500/10',
    DeviceIcon: Brain,
    async fetchState() {
      const checks: CheckResult[] = [];
      const metrics: Metric[] = [];

      // 1. API Health — 正确路径 /health（经代理后 /api/decision/health）
      const h = await timedFetch<{ status: string; service?: string }>('/api/decision/health');
      checks.push({
        name: 'API 健康',
        status: h.ok ? 'pass' : 'fail',
        latency: h.latency,
        detail: h.ok ? (h.data?.status ?? 'OK') : h.detail,
      });

      // 2. Strategies list
      const strat = await timedFetch<unknown[]>('/api/decision/strategies');
      const stratArr = Array.isArray(strat.data) ? strat.data : [];
      checks.push({
        name: '策略仓库',
        status: strat.ok ? 'pass' : 'fail',
        latency: strat.latency,
        detail: strat.ok ? `${stratArr.length} 条策略` : strat.detail,
      });
      if (strat.ok) {
        metrics.push({ label: '策略数', value: `${stratArr.length} 条`, accent: 'blue' });
      }

      // 3. Signals dashboard
      const sigD = await timedFetch<{ signals?: unknown[] }>('/api/decision/signals/dashboard/signals');
      const sigCount = Array.isArray(sigD.data?.signals) ? sigD.data!.signals.length : null;
      checks.push({
        name: '信号队列',
        status: sigD.ok ? 'pass' : 'skip',
        latency: sigD.latency,
        detail: sigD.ok ? `${sigCount ?? 0} 条信号` : sigD.detail,
      });
      if (sigD.ok) {
        metrics.push({ label: '信号数', value: sigCount !== null ? `${sigCount}` : '—' });
      }

      // 4. Models runtime
      const models = await timedFetch<{ health?: string }>('/api/decision/models/runtime');
      checks.push({
        name: '模型运行时',
        status: models.ok ? 'pass' : 'skip',
        latency: models.latency,
        detail: models.ok ? (models.data?.health ?? 'OK') : models.detail,
      });

      const passCount = checks.filter(c => c.status === 'pass').length;
      const health: HealthStatus = !h.ok ? 'offline' : passCount >= 2 ? 'online' : 'degraded';
      return { health, checks, metrics };
    },
    actions: [
      {
        id: 'check',
        label: '检查调度器',
        Icon: Activity,
        variant: 'outline',
        async execute() {
          const r = await timedFetch<{ status: string }>('/api/decision/health');
          return { ok: r.ok, message: r.ok ? `健康: ${r.data?.status ?? 'ok'}  (${r.latency}ms)` : r.detail };
        },
      },
    ],
  },

  // ── 数据服务 (Mini) ────────────────────────────────────────
  {
    id: 'data',
    name: '数据服务',
    device: 'Mini',
    ip: '192.168.31.76',
    port: 8105,
    dockerName: 'JBT-DATA-8105',
    sshUser: 'jaybot',
    accentBorder: 'border-green-500/40',
    accentText: 'text-green-400',
    accentBg: 'bg-green-500/10',
    DeviceIcon: Database,
    async fetchState() {
      const checks: CheckResult[] = [];
      const metrics: Metric[] = [];

      // 1. API Health
      const h = await timedFetch<{ status: string }>('/api/data/api/v1/health');
      checks.push({ name: 'API 健康', status: h.ok ? 'pass' : 'fail', latency: h.latency, detail: h.ok ? 'OK' : h.detail });

      // 2. Collectors
      // 实际 status 值: success / idle / delayed / warning / stopped
      const col = await timedFetch<{
        collectors: Array<{ id: string; status: string; last_status: string }>;
      }>('/api/data/api/v1/dashboard/collectors');
      if (col.ok && col.data?.collectors) {
        const all = col.data.collectors;
        const total = all.length;
        // success + idle 视为正常，delayed 视为警告，stopped/error 视为故障
        const healthy = all.filter(c => c.status === 'success' || c.status === 'idle').length;
        const delayed = all.filter(c => c.status === 'delayed').length;
        const stopped = all.filter(c => c.status === 'stopped' || c.status === 'error').length;
        const passThreshold = total * 0.6;
        checks.push({
          name: '采集器状态',
          status: healthy >= passThreshold ? 'pass' : stopped > 0 ? 'fail' : 'fail',
          latency: col.latency,
          detail: `正常 ${healthy}/${total}，延迟 ${delayed}，停止 ${stopped}`,
        });
        metrics.push({
          label: '采集器',
          value: `${healthy}/${total} 正常`,
          sub: delayed > 0 ? `${delayed} 个延迟` : undefined,
          accent: healthy >= passThreshold ? 'green' : delayed > 0 ? 'yellow' : 'red',
        });
      } else {
        checks.push({ name: '采集器状态', status: 'fail', latency: col.latency, detail: col.detail });
      }

      // 3. System status
      const sys = await timedFetch<{
        cpu_percent?: number;
        memory_percent?: number;
        disk_usage?: Record<string, { percent: number }>;
      }>('/api/data/api/v1/dashboard/system');
      if (sys.ok && sys.data) {
        const cpu = sys.data.cpu_percent ?? null;
        const mem = sys.data.memory_percent ?? null;
        checks.push({
          name: '系统资源',
          status: cpu !== null && cpu < 90 && mem !== null && mem < 90 ? 'pass' : 'fail',
          latency: sys.latency,
          detail: cpu !== null ? `CPU ${cpu.toFixed(1)}% / MEM ${mem?.toFixed(1) ?? '?'}%` : sys.detail,
        });
        if (cpu !== null) {
          metrics.push({
            label: 'CPU / MEM',
            value: `${cpu.toFixed(1)}% / ${mem?.toFixed(1) ?? '?'}%`,
            accent: cpu > 80 || (mem ?? 0) > 85 ? 'red' : 'green',
          });
        }
      } else {
        checks.push({ name: '系统资源', status: 'skip', latency: sys.latency, detail: sys.detail });
      }

      // 4. News pipeline
      const news = await timedFetch<{ news_items?: unknown[] }>('/api/data/api/v1/dashboard/news');
      checks.push({
        name: '新闻管道',
        status: news.ok ? 'pass' : 'skip',
        latency: news.latency,
        detail: news.ok ? `新闻接口正常` : news.detail,
      });

      const passCount = checks.filter(c => c.status === 'pass').length;
      const health: HealthStatus = !h.ok ? 'offline' : passCount >= 2 ? 'online' : 'degraded';
      return { health, checks, metrics };
    },
    actions: [
      {
        id: 'auto-remediate',
        label: '一键修复',
        Icon: Zap,
        variant: 'outline',
        confirm: '自动修复所有异常采集器？',
        async execute() {
          const r = await timedFetch<{ fixed?: number; message?: string }>(
            '/api/data/api/v1/ops/auto-remediate',
            { method: 'POST' },
          );
          return { ok: r.ok, message: r.ok ? `修复完成：${r.data?.message ?? r.data?.fixed ?? ''}` : r.detail };
        },
      },
    ],
  },

  // ── 回测系统 (Studio) ──────────────────────────────────────
  {
    id: 'backtest',
    name: '回测系统',
    device: 'Studio',
    ip: '192.168.31.142',
    port: 8103,
    dockerName: 'JBT-BACKTEST-8103',
    sshUser: 'jaybot',
    accentBorder: 'border-purple-500/40',
    accentText: 'text-purple-400',
    accentBg: 'bg-purple-500/10',
    DeviceIcon: BarChart2,
    async fetchState() {
      const checks: CheckResult[] = [];
      const metrics: Metric[] = [];

      // 1. API Health
      const h = await timedFetch<{ status: string }>('/api/backtest/api/health');
      checks.push({ name: 'API 健康', status: h.ok ? 'pass' : 'fail', latency: h.latency, detail: h.ok ? 'OK' : h.detail });

      // 2. System status
      const sys = await timedFetch<{
        services?: Array<{ name: string; status: string }>;
        active_jobs?: number;
        queued_count?: number;
      }>('/api/backtest/api/system/status');
      if (sys.ok && sys.data) {
        checks.push({
          name: '系统状态',
          status: 'pass',
          latency: sys.latency,
          detail: `运行服务: ${sys.data.services?.length ?? '—'}`,
        });
      } else {
        checks.push({ name: '系统状态', status: 'fail', latency: sys.latency, detail: sys.detail });
      }

      // 3. Job queue
      const queue = await timedFetch<{ queued_count: number; running: number; total: number }>(
        '/api/backtest/api/v1/strategy-queue/status',
      );
      if (queue.ok && queue.data) {
        checks.push({
          name: '任务队列',
          status: 'pass',
          latency: queue.latency,
          detail: `队列 ${queue.data.queued_count}，运行 ${queue.data.running ?? 0}`,
        });
        metrics.push({
          label: '任务队列',
          value: `${queue.data.queued_count} 排队`,
          sub: `${queue.data.running ?? 0} 运行中`,
          accent: (queue.data.running ?? 0) > 0 ? 'blue' : 'default',
        });
      } else {
        checks.push({ name: '任务队列', status: 'skip', latency: queue.latency, detail: queue.detail });
      }

      // 4. Recent jobs
      const jobs = await timedFetch<{ jobs?: Array<{ status: string }> }>('/api/backtest/api/v1/jobs');
      if (jobs.ok && jobs.data?.jobs) {
        const running = jobs.data.jobs.filter(j => j.status === 'running').length;
        const failed = jobs.data.jobs.filter(j => j.status === 'failed').length;
        checks.push({
          name: '近期任务',
          status: failed === 0 ? 'pass' : 'fail',
          latency: jobs.latency,
          detail: `运行中 ${running}，失败 ${failed}`,
        });
        metrics.push({
          label: '近期任务',
          value: `运行 ${running} / 失败 ${failed}`,
          accent: failed > 0 ? 'red' : 'green',
        });
      } else {
        checks.push({ name: '近期任务', status: 'skip', latency: jobs.latency, detail: jobs.detail });
      }

      const passCount = checks.filter(c => c.status === 'pass').length;
      const health: HealthStatus = !h.ok ? 'offline' : passCount >= 2 ? 'online' : 'degraded';
      return { health, checks, metrics };
    },
    actions: [
      {
        id: 'check-queue',
        label: '检查队列',
        Icon: Activity,
        variant: 'outline',
        async execute() {
          const r = await timedFetch<{ queued_count: number; running: number }>(
            '/api/backtest/api/v1/strategy-queue/status',
          );
          return {
            ok: r.ok,
            message: r.ok
              ? `队列: ${r.data?.queued_count ?? '—'} 排队  ${r.data?.running ?? '—'} 运行中`
              : r.detail,
          };
        },
      },
    ],
  },
];

// ─────────────────────────────────────────────────────────────
//  Status helpers
// ─────────────────────────────────────────────────────────────
function HealthBadge({ status }: { status: HealthStatus }) {
  if (status === 'checking') return (
    <Badge className="bg-muted/60 text-muted-foreground text-xs gap-1">
      <RefreshCw className="w-2.5 h-2.5 animate-spin" /> 检查中
    </Badge>
  );
  if (status === 'online') return (
    <Badge className="bg-green-500/15 text-green-400 border border-green-500/30 text-xs gap-1">
      <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block animate-pulse" /> 在线
    </Badge>
  );
  if (status === 'degraded') return (
    <Badge className="bg-yellow-500/15 text-yellow-400 border border-yellow-500/30 text-xs gap-1">
      <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 inline-block" /> 降级
    </Badge>
  );
  return (
    <Badge className="bg-red-500/15 text-red-400 border border-red-500/30 text-xs gap-1">
      <span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block" /> 离线
    </Badge>
  );
}

function CheckIcon({ status }: { status: CheckResult['status'] }) {
  if (status === 'pass') return <CheckCircle2 className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />;
  if (status === 'fail') return <XCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />;
  return <AlertCircle className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />;
}

function metricAccentClass(accent?: Metric['accent']) {
  switch (accent) {
    case 'green': return 'text-green-400';
    case 'red': return 'text-red-400';
    case 'yellow': return 'text-yellow-400';
    case 'blue': return 'text-blue-400';
    default: return 'text-foreground';
  }
}

// ─────────────────────────────────────────────────────────────
//  SSH Restart helper modal content
// ─────────────────────────────────────────────────────────────
function SshRestartHint({ service }: { service: ServiceDef }) {
  const [copied, setCopied] = useState(false);
  const cmd = `ssh ${service.sshUser}@${service.ip} 'docker restart ${service.dockerName}'`;
  const copy = () => {
    navigator.clipboard.writeText(cmd).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
  };
  return (
    <div className="mt-3 rounded-lg border border-border/60 bg-muted/30 p-3 space-y-2">
      <p className="text-xs text-muted-foreground flex items-center gap-1.5">
        <Terminal className="w-3 h-3" />
        容器重启（需 SSH 权限）
      </p>
      <div className="flex items-center gap-2">
        <code className="flex-1 text-xs text-muted-foreground bg-background/60 rounded px-2 py-1 font-mono break-all">
          {cmd}
        </code>
        <Button size="icon" variant="ghost" className="h-7 w-7 flex-shrink-0" onClick={copy}>
          {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
        </Button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
//  Single Service KPI Card
// ─────────────────────────────────────────────────────────────
const REFRESH_INTERVAL = 30; // seconds

function ServiceKpiCard({ svc }: { svc: ServiceDef }) {
  const [state, setState] = useState<ServiceState>({
    health: 'checking',
    latency: null,
    lastCheck: null,
    checks: [],
    metrics: [],
    error: null,
  });
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [countdown, setCountdown] = useState(REFRESH_INTERVAL);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    setState(prev => ({ ...prev, health: 'checking' }));
    const start = Date.now();
    try {
      const result = await svc.fetchState();
      setState({
        health: result.health,
        latency: Date.now() - start,
        lastCheck: new Date(),
        checks: result.checks,
        metrics: result.metrics,
        error: null,
      });
    } catch (e) {
      setState(prev => ({
        ...prev,
        health: 'offline',
        latency: Date.now() - start,
        lastCheck: new Date(),
        error: e instanceof Error ? e.message : '未知错误',
      }));
    }
    setCountdown(REFRESH_INTERVAL);
  }, [svc]);

  useEffect(() => {
    refresh();
    timerRef.current = setInterval(refresh, REFRESH_INTERVAL * 1000);
    countdownRef.current = setInterval(() => setCountdown(c => Math.max(0, c - 1)), 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [refresh]);

  const handleAction = async (action: ActionDef) => {
    if (action.confirm && !window.confirm(action.confirm)) return;
    setActionLoading(action.id);
    setActionMsg(null);
    const result = await action.execute();
    setActionMsg({ ok: result.ok, text: result.message });
    setActionLoading(null);
    if (result.ok) setTimeout(refresh, 800);
    setTimeout(() => setActionMsg(null), 5000);
  };

  const { DeviceIcon } = svc;
  const passCount = state.checks.filter(c => c.status === 'pass').length;
  const totalCount = state.checks.length;

  return (
    <Card className={cn(
      'bg-transparent backdrop-blur-sm border transition-all duration-300',
      svc.accentBorder,
      state.health === 'offline' && 'opacity-75',
    )}>
      {/* ── Card Header ─────────────────────────────────── */}
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0', svc.accentBg)}>
              <DeviceIcon className={cn('w-4.5 h-4.5', svc.accentText)} style={{ width: 18, height: 18 }} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-foreground text-sm">{svc.name}</span>
                <HealthBadge status={state.health} />
              </div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                  {svc.device}
                </Badge>
                <span className="text-[10px] text-muted-foreground font-mono">{svc.ip}:{svc.port}</span>
              </div>
            </div>
          </div>

          {/* Refresh button + countdown */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <span className="text-[10px] text-muted-foreground tabular-nums">{countdown}s</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={refresh}
              disabled={state.health === 'checking'}
              title="立即刷新"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', state.health === 'checking' && 'animate-spin')} />
            </Button>
          </div>
        </div>

        {/* ── KPI summary row ─────────────────────────────── */}
        <div className="grid grid-cols-3 gap-2 mt-3">
          {/* Latency */}
          <div className="rounded-md bg-muted/30 px-2 py-1.5 text-center">
            <div className="flex items-center justify-center gap-1">
              <Zap className="w-3 h-3 text-yellow-400" />
              <span className={cn('text-sm font-mono font-semibold',
                state.latency === null ? 'text-muted-foreground'
                  : state.latency < 200 ? 'text-green-400'
                    : state.latency < 1000 ? 'text-yellow-400' : 'text-red-400',
              )}>
                {state.latency !== null ? `${state.latency}ms` : '—'}
              </span>
            </div>
            <p className="text-[10px] text-muted-foreground mt-0.5">响应延迟</p>
          </div>

          {/* Check score */}
          <div className="rounded-md bg-muted/30 px-2 py-1.5 text-center">
            <div className="flex items-center justify-center gap-1">
              <Activity className="w-3 h-3 text-muted-foreground" />
              <span className={cn('text-sm font-semibold',
                totalCount === 0 ? 'text-muted-foreground'
                  : passCount === totalCount ? 'text-green-400'
                    : passCount >= totalCount / 2 ? 'text-yellow-400' : 'text-red-400',
              )}>
                {totalCount > 0 ? `${passCount}/${totalCount}` : '—'}
              </span>
            </div>
            <p className="text-[10px] text-muted-foreground mt-0.5">检查通过</p>
          </div>

          {/* Last check */}
          <div className="rounded-md bg-muted/30 px-2 py-1.5 text-center">
            <div className="flex items-center justify-center gap-1">
              <Clock className="w-3 h-3 text-muted-foreground" />
              <span className="text-[11px] text-muted-foreground font-mono">
                {state.lastCheck
                  ? state.lastCheck.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                  : '—'}
              </span>
            </div>
            <p className="text-[10px] text-muted-foreground mt-0.5">上次检查</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        {/* ── Service-specific Metrics ──────────────────── */}
        {state.metrics.length > 0 && (
          <div className="grid grid-cols-2 gap-2">
            {state.metrics.map((m, i) => (
              <div key={i} className="rounded-md border border-border/50 bg-muted/20 px-2.5 py-2">
                <p className="text-[10px] text-muted-foreground mb-0.5">{m.label}</p>
                <p className={cn('text-sm font-semibold', metricAccentClass(m.accent))}>
                  {m.value ?? '—'}
                </p>
                {m.sub && <p className="text-[10px] text-muted-foreground mt-0.5">{m.sub}</p>}
              </div>
            ))}
          </div>
        )}

        {/* ── Action Buttons ────────────────────────────── */}
        {svc.actions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {svc.actions.map((action) => (
              <Button
                key={action.id}
                variant={action.variant ?? 'outline'}
                size="sm"
                className="gap-1.5 text-xs h-7"
                disabled={actionLoading !== null}
                onClick={() => handleAction(action)}
              >
                {actionLoading === action.id
                  ? <RefreshCw className="w-3 h-3 animate-spin" />
                  : <action.Icon className="w-3 h-3" />}
                {action.label}
              </Button>
            ))}
          </div>
        )}

        {/* Action feedback */}
        {actionMsg && (
          <div className={cn(
            'rounded-md px-3 py-2 text-xs flex items-center gap-2',
            actionMsg.ok
              ? 'bg-green-500/10 border border-green-500/30 text-green-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400',
          )}>
            {actionMsg.ok
              ? <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
              : <XCircle className="w-3.5 h-3.5 flex-shrink-0" />}
            {actionMsg.text}
          </div>
        )}

        {/* ── Detail checks (always visible) ───────────── */}
        <div className="space-y-1 pt-1 border-t border-border/40">
          <p className="text-[10px] text-muted-foreground mb-1.5">检查明细</p>
          {state.checks.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-2">暂无检查数据</p>
          ) : (
            state.checks.map((c, i) => (
              <div key={i} className="flex items-center gap-2 rounded-md bg-muted/20 px-2.5 py-1.5">
                <CheckIcon status={c.status} />
                <span className="flex-1 text-xs text-foreground">{c.name}</span>
                <span className="text-[10px] text-muted-foreground max-w-[120px] truncate text-right">
                  {c.detail}
                </span>
                {c.latency !== null && (
                  <span className={cn('text-[10px] font-mono w-12 text-right flex-shrink-0',
                    c.latency < 200 ? 'text-green-400' : c.latency < 1000 ? 'text-yellow-400' : 'text-red-400',
                  )}>
                    {c.latency}ms
                  </span>
                )}
              </div>
            ))
          )}

          {/* SSH restart hint — always visible */}
          <SshRestartHint service={svc} />
        </div>

        {/* Error fallback */}
        {state.error && (
          <div className="rounded-md bg-red-500/10 border border-red-500/20 px-3 py-2">
            <p className="text-xs text-red-400">{state.error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─────────────────────────────────────────────────────────────
//  Exported: ServicesKpiCard (2x2 grid of all 4 services)
// ─────────────────────────────────────────────────────────────
export function ServicesKpiCard() {
  const [globalRefresh, setGlobalRefresh] = useState(0);

  return (
    <div className="space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">服务实例管理</h3>
          <p className="text-xs text-muted-foreground mt-0.5">每 30 秒自动检查 · 前台直连各服务 API</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" /> 在线
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 inline-block" /> 降级
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block" /> 离线
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs h-7"
            onClick={() => setGlobalRefresh(n => n + 1)}
          >
            <RefreshCw className="w-3 h-3" />
            全部刷新
          </Button>
        </div>
      </div>

      {/* 2x2 Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SERVICES.map((svc) => (
          <ServiceKpiCard key={`${svc.id}-${globalRefresh}`} svc={svc} />
        ))}
      </div>

      {/* Footer note */}
      <p className="text-[11px] text-muted-foreground text-center">
        <Server className="w-3 h-3 inline-block mr-1" />
        容器重启需 SSH 权限（展开卡片查看重启命令）· 前台直连各服务 REST API，无需后台中转
      </p>
    </div>
  );
}
