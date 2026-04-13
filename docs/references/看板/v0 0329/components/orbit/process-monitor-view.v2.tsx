"use client";

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Activity, AlertTriangle, CheckCircle2, XCircle, Pause, Play, Square,
  RotateCw, RefreshCw, Download, Search, Filter, Database, LineChart,
  Shield, Server, Cpu, MemoryStick, HardDrive, Clock, Tag, Eye,
  Settings, Bell, Zap, ChevronRight, BarChart3, List, Loader2, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useToastActions } from "@/components/orbit/toast-provider";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

// ─── Types ────────────────────────────────────────────────────────────────────

type ProcessStatus = "running" | "stopped" | "restarting" | "paused";
type ProcessCategory = "data" | "strategy" | "trade" | "risk" | "system";
type HealthLevel = "normal" | "warning" | "danger";

interface Process {
  id: string;
  name: string;
  chineseName: string;
  pid: number;
  status: ProcessStatus;
  category: ProcessCategory;
  device: string;
  cpu: number;
  memoryMB: number;
  threads: number;
  uptime: string;
  restarts: number;
  health: HealthLevel;
  description: string;
}

interface AlertRecord {
  id: string;
  processName: string;
  level: "P0" | "P1" | "P2";
  alertType: string;
  message: string;
  time: string;
  duration: string;
  status: "未处理" | "处理中" | "已解决";
}

interface HistoryRecord {
  id: string;
  processName: string;
  operationType: "start" | "stop" | "restart" | "pause";
  operator: string;
  time: string;
  result: "success" | "failed";
}

// ─── Mock Data ─────────────────────────────────────────────────────────────────

const processes: Process[] = [
  { id: "p1", name: "data_collector.py", chineseName: "数据采集", pid: 12301, status: "running", category: "data", device: "Mac Mini", cpu: 12, memoryMB: 256, threads: 4, uptime: "48小时", restarts: 0, health: "normal", description: "负责从各数据源采集行情数据" },
  { id: "p2", name: "data_cleaner.py", chineseName: "数据清洗", pid: 12302, status: "running", category: "data", device: "Mac Mini", cpu: 8, memoryMB: 128, threads: 2, uptime: "48小时", restarts: 0, health: "normal", description: "清洗和标准化原始行情数据" },
  { id: "p3", name: "strategy_engine.py", chineseName: "策略引擎", pid: 23401, status: "running", category: "strategy", device: "MacBook Pro", cpu: 45, memoryMB: 1024, threads: 8, uptime: "24小时", restarts: 1, health: "warning", description: "执行策略信号计算和生成" },
  { id: "p4", name: "signal_generator.py", chineseName: "信号生成", pid: 23402, status: "running", category: "strategy", device: "MacBook Pro", cpu: 30, memoryMB: 512, threads: 4, uptime: "24小时", restarts: 0, health: "normal", description: "基于策略生成交易信号" },
  { id: "p5", name: "trade_executor.py", chineseName: "交易执行", pid: 34501, status: "running", category: "trade", device: "Mac Studio", cpu: 25, memoryMB: 768, threads: 6, uptime: "72小时", restarts: 2, health: "warning", description: "执行交易指令和订单管理" },
  { id: "p6", name: "order_manager.py", chineseName: "订单管理", pid: 34502, status: "stopped", category: "trade", device: "Mac Studio", cpu: 0, memoryMB: 0, threads: 0, uptime: "-", restarts: 3, health: "danger", description: "管理订单生命周期" },
  { id: "p7", name: "risk_manager.py", chineseName: "风控管理", pid: 45601, status: "running", category: "risk", device: "Mac Studio", cpu: 18, memoryMB: 384, threads: 3, uptime: "72小时", restarts: 0, health: "normal", description: "实时监控风险指标" },
  { id: "p8", name: "position_tracker.py", chineseName: "持仓跟踪", pid: 45602, status: "running", category: "risk", device: "Mac Studio", cpu: 10, memoryMB: 256, threads: 2, uptime: "72小时", restarts: 0, health: "normal", description: "跟踪实时持仓状态" },
  { id: "p9", name: "service_monitor.py", chineseName: "服务监控", pid: 56701, status: "running", category: "system", device: "Mac Mini", cpu: 5, memoryMB: 128, threads: 2, uptime: "96小时", restarts: 0, health: "normal", description: "监控所有服务健康状态" },
  { id: "p10", name: "log_aggregator.py", chineseName: "日志聚合", pid: 56702, status: "paused", category: "system", device: "Mac Mini", cpu: 0, memoryMB: 64, threads: 1, uptime: "96小时", restarts: 0, health: "warning", description: "聚合和归档系统日志" },
  { id: "p11", name: "ai_inference.py", chineseName: "AI推理", pid: 67801, status: "running", category: "strategy", device: "MacBook Pro", cpu: 78, memoryMB: 2048, threads: 16, uptime: "12小时", restarts: 0, health: "warning", description: "运行AI模型推理预测" },
];

const alertRecords: AlertRecord[] = [
  { id: "a1", processName: "backtest_engine.py", level: "P1", alertType: "进程崩溃", message: "内存溢出导致进程终止", time: "03-20 14:30", duration: "2 小时", status: "未处理" },
  { id: "a2", processName: "api_gateway.py", level: "P0", alertType: "无响应", message: "连续 3 分钟无心跳", time: "03-20 10:15", duration: "2 小时", status: "处理中" },
  { id: "a3", processName: "ai_inference.py", level: "P2", alertType: "资源超限", message: "CPU 使用率达到 92%", time: "03-19 22:00", duration: "30 分钟", status: "已解决" },
  { id: "a4", processName: "strategy_engine.py", level: "P1", alertType: "资源超限", message: "内存使用率 > 85%", time: "03-19 16:45", duration: "15 分钟", status: "已解决" },
];

const historyRecords: HistoryRecord[] = [
  { id: "h1", processName: "order_manager.py", operationType: "restart", operator: "系统自动", time: "2026-03-21 15:30:10", result: "failed" },
  { id: "h2", processName: "strategy_engine.py", operationType: "restart", operator: "admin", time: "2026-03-21 12:00:00", result: "success" },
  { id: "h3", processName: "data_collector.py", operationType: "start", operator: "admin", time: "2026-03-21 08:00:00", result: "success" },
  { id: "h4", processName: "log_aggregator.py", operationType: "pause", operator: "admin", time: "2026-03-21 07:30:00", result: "success" },
  { id: "h5", processName: "trade_executor.py", operationType: "restart", operator: "系统自动", time: "2026-03-20 23:15:00", result: "success" },
];

const resourceTrendData = Array.from({ length: 24 }, (_, i) => ({
  time: `${String(i).padStart(2, "0")}:00`,
  strategy_engine: 10 + Math.random() * 15,
  ai_inference: 15 + Math.random() * 20,
  data_collector: 5 + Math.random() * 10,
  trade_executor: 3 + Math.random() * 5,
}));

// ─── Component ──────────────��──────────────────────────────────────────────────

export function ProcessMonitorViewV2() {
  const toast = useToastActions();
  const [selectedProcesses, setSelectedProcesses] = useState<string[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [deviceFilter, setDeviceFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [confirmDialog, setConfirmDialog] = useState<{ open: boolean; action: string; processes: Process[] }>({ open: false, action: "", processes: [] });
  const [logSheet, setLogSheet] = useState<{ open: boolean; process: Process | null }>({ open: false, process: null });

  // Config states
  const [autoRestart, setAutoRestart] = useState(true);
  const [restartDelay, setRestartDelay] = useState("30");
  const [maxRestarts, setMaxRestarts] = useState("5");
  const [restartNotify, setRestartNotify] = useState(true);
  const [cpuLimit, setCpuLimit] = useState("80");
  const [memoryLimit, setMemoryLimit] = useState("4");
  const [fileLimit, setFileLimit] = useState("1000");
  const [heartbeatEnabled, setHeartbeatEnabled] = useState(true);
  const [heartbeatInterval, setHeartbeatInterval] = useState("30");
  const [heartbeatTimeout, setHeartbeatTimeout] = useState("90");

  // 自动刷新和进程重启
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date().toLocaleTimeString());
  const [showRestartConfirm, setShowRestartConfirm] = useState(false);
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);
  const [isRestarting, setIsRestarting] = useState(false);

  // 自动刷新effect
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setIsRefreshing(true);
      setTimeout(() => {
        setIsRefreshing(false);
        setLastUpdateTime(new Date().toLocaleTimeString());
      }, 800);
    }, 30000); // 每30秒刷新一次
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleRestartProcess = (process: Process) => {
    setSelectedProcess(process);
    setShowRestartConfirm(true);
  };

  const confirmRestart = async () => {
    if (!selectedProcess) return;
    setIsRestarting(true);
    await new Promise(r => setTimeout(r, 1200));
    setIsRestarting(false);
    setShowRestartConfirm(false);
    toast({ title: "进程重启成功", description: `${selectedProcess.chineseName} 已重启` });
  };

  const filteredProcesses = useMemo(() => {
    return processes.filter(p => {
      if (categoryFilter !== "all" && p.category !== categoryFilter) return false;
      if (statusFilter !== "all" && p.status !== statusFilter) return false;
      if (deviceFilter !== "all" && !p.device.toLowerCase().includes(deviceFilter.toLowerCase())) return false;
      if (searchQuery && !p.name.toLowerCase().includes(searchQuery.toLowerCase()) && !p.chineseName.includes(searchQuery) && !String(p.pid).includes(searchQuery)) return false;
      return true;
    });
  }, [categoryFilter, statusFilter, deviceFilter, searchQuery]);

  const stats = useMemo(() => {
    const total = processes.length;
    const running = processes.filter(p => p.status === "running").length;
    const stopped = processes.filter(p => p.status === "stopped").length;
    const highestCpu = processes.reduce((max, p) => p.cpu > max.cpu ? p : max, processes[0]);
    const highestMem = processes.reduce((max, p) => p.memoryMB > max.memoryMB ? p : max, processes[0]);
    const abnormal = processes.filter(p => p.health === "danger").length;
    return { total, running, stopped, highestCpu, highestMem, abnormal };
  }, []);

  const categoryCount = useMemo(() => ({
    all: processes.length,
    data: processes.filter(p => p.category === "data").length,
    strategy: processes.filter(p => p.category === "strategy").length,
    trade: processes.filter(p => p.category === "trade").length,
    risk: processes.filter(p => p.category === "risk").length,
    system: processes.filter(p => p.category === "system").length,
  }), []);

  const getStatusColor = (status: ProcessStatus) => {
    switch (status) {
      case "running": return "bg-emerald-500";
      case "stopped": return "bg-red-500";
      case "restarting": return "bg-amber-500";
      case "paused": return "bg-blue-500";
    }
  };

  const getStatusText = (status: ProcessStatus) => {
    switch (status) {
      case "running": return "运行中";
      case "stopped": return "已停止";
      case "restarting": return "重启中";
      case "paused": return "已暂停";
    }
  };

  const getHealthColor = (health: HealthLevel) => {
    switch (health) {
      case "normal": return "text-emerald-600";
      case "warning": return "text-amber-600";
      case "danger": return "text-red-600";
    }
  };

  const getHealthText = (health: HealthLevel) => {
    switch (health) {
      case "normal": return "正常";
      case "warning": return "警告";
      case "danger": return "危险";
    }
  };

  const getLevelColor = (level: AlertRecord["level"]) => {
    switch (level) {
      case "P0": return "bg-red-500/10 text-red-600 border-red-500/30";
      case "P1": return "bg-amber-500/10 text-amber-600 border-amber-500/30";
      case "P2": return "bg-blue-500/10 text-blue-600 border-blue-500/30";
    }
  };

  const getOperationIcon = (type: HistoryRecord["operationType"]) => {
    switch (type) {
      case "start": return <Play className="w-3 h-3 text-emerald-600" />;
      case "stop": return <Square className="w-3 h-3 text-red-600" />;
      case "restart": return <RotateCw className="w-3 h-3 text-amber-600" />;
      case "pause": return <Pause className="w-3 h-3 text-blue-600" />;
    }
  };

  const getOperationText = (type: HistoryRecord["operationType"]) => {
    switch (type) {
      case "start": return "启动";
      case "stop": return "停止";
      case "restart": return "重启";
      case "pause": return "暂停";
    }
  };

  const handleProcessAction = (action: string, process: Process) => {
    setConfirmDialog({ open: true, action, processes: [process] });
  };

  const handleBatchAction = (batchAction: string) => {
    const selected = processes.filter(p => selectedProcesses.includes(p.id));
    if (selected.length === 0) {
      toast.warning("请先选择进程");
      return;
    }
    setConfirmDialog({ open: true, action: batchAction, processes: selected });
  };

  const executeAction = () => {
    const count = confirmDialog.processes.length;
    const action = confirmDialog.action;
    toast.success(`已对 ${count} 个进程执行${action}操作`);
    setConfirmDialog({ open: false, action: "", processes: [] });
    setSelectedProcesses([]);
  };

  const toggleProcessSelection = (id: string) => {
    setSelectedProcesses(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedProcesses.length === filteredProcesses.length) {
      setSelectedProcesses([]);
    } else {
      setSelectedProcesses(filteredProcesses.map(p => p.id));
    }
  };

  const getCategoryIcon = (category: ProcessCategory) => {
    switch (category) {
      case "data": return Database;
      case "strategy": return LineChart;
      case "trade": return Activity;
      case "risk": return Shield;
      case "system": return Server;
    }
  };

  const SectionHeader = ({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description?: string }) => (
    <div className="flex items-center gap-2 mb-4">
      <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/10">
        <Icon className="w-4 h-4 text-primary" />
      </div>
      <div>
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
    </div>
  );

  const ConfigRow = ({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) => (
    <div className="flex items-center justify-between py-3 border-b border-border/50 last:border-0">
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
      </div>
      <div className="flex-shrink-0 ml-4">{children}</div>
    </div>
  );

  return (
    <div className="p-6 space-y-6 min-w-0">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">进程监控</h1>
          <p className="text-sm text-muted-foreground mt-1">监控和管理所有运行进程的状态</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="flex items-center gap-2 text-xs text-muted-foreground px-3 py-1">
            <span>自动刷新</span>
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
          </div>
          {lastUpdateTime && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              {isRefreshing ? (
                <>
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity }}>
                    <RefreshCw className="w-3 h-3" />
                  </motion.div>
                  更新中...
                </>
              ) : (
                <>
                  <Clock className="w-3 h-3" />
                  最后更新: {lastUpdateTime}
                </>
              )}
            </span>
          )}
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-1"
            onClick={() => {
              setIsRefreshing(true);
              setTimeout(() => {
                setIsRefreshing(false);
                setLastUpdateTime(new Date().toLocaleTimeString());
              }, 800);
            }}
            disabled={isRefreshing}
          >
            <RefreshCw className={cn("w-4 h-4", isRefreshing && "animate-spin")} />
            刷新全部
          </Button>
          <Button variant="outline" size="sm" className="gap-1">
            <Download className="w-4 h-4" />
            导出
          </Button>
        </div>
      </div>

      {/* 进程重启二次确认弹窗 */}
      {showRestartConfirm && selectedProcess && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <motion.div
            className="bg-card rounded-lg border border-border shadow-xl max-w-[540px] w-[90%]"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/30">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <h2 className="text-sm font-semibold text-foreground">确认重启进程？</h2>
              </div>
              <button
                onClick={() => setShowRestartConfirm(false)}
                disabled={isRestarting}
                className="p-1 hover:bg-muted rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-4 space-y-3">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">进程名：</span>
                  <span className="font-medium">{selectedProcess.chineseName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">PID：</span>
                  <span className="font-mono">{selectedProcess.pid}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">设备：</span>
                  <span className="font-medium">{selectedProcess.device}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">当前状态：</span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-[#3FB950]" />
                    运行中
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">CPU 占用：</span>
                  <span className="font-mono">{selectedProcess.cpu}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">内存占用：</span>
                  <span className="font-mono">{Math.round((selectedProcess.memoryMB / 1024) * 100) / 100}%</span>
                </div>
              </div>

              <div className="p-3 bg-amber-500/10 border border-l-4 border-l-amber-500 border-amber-500/20 rounded">
                <p className="text-xs text-amber-700 dark:text-amber-300">
                  ⚠️ 注意：重启过程中该进程将暂停服务约 10-30 秒
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-4 border-t border-border/30 bg-muted/20">
              <button
                onClick={() => setShowRestartConfirm(false)}
                disabled={isRestarting}
                className="flex-1 px-4 py-2 text-sm font-medium text-foreground border border-border rounded-md hover:bg-muted transition-colors disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={confirmRestart}
                disabled={isRestarting}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-600/90 rounded-md transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isRestarting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    重启中...
                  </>
                ) : (
                  '确认重启'
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
