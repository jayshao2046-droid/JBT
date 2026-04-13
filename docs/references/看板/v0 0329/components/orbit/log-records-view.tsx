"use client";
// Log Records View - v2.1
import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ScrollText,
  FileText,
  AlertTriangle,
  Info,
  Bug,
  Bell,
  Search,
  RefreshCw,
  Download,
  Play,
  Pause,
  Trash2,
  Settings,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  X,
  Filter,
  Clock,
  Server,
  Cpu,
  Database,
  Shield,
  Globe,
  HardDrive,
  TrendingUp,
  BarChart3,
  PieChart,
  AlertCircle,
  CheckCircle,
  XCircle,
  Eye,
  Tag,
  Link,
  FileDown,
  Archive,
  RotateCcw,
  Zap,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { cn } from "@/lib/utils";
import { useToastActions } from "@/components/orbit/toast-provider";

// Types
type LogLevel = "ERROR" | "WARNING" | "INFO" | "DEBUG";

interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  module: string;
  process: string;
  pid: number;
  device: string;
  deviceId: string;
  user: string;
  requestId: string;
  message: string;
  details?: Record<string, any>;
  stackTrace?: string;
  errorCode?: string;
  category?: string;
  tags?: string[];
  handled?: boolean;
  handledBy?: string;
  handledAt?: string;
}

interface ErrorStat {
  rank: number;
  errorType: string;
  count: number;
  firstSeen: string;
  lastSeen: string;
}

// Mock Data
const mockLogEntries: LogEntry[] = [
  {
    id: "log_20260321170832456",
    timestamp: "2026-03-21T17:08:32.456Z",
    level: "ERROR",
    module: "交易执行",
    process: "trade_executor.py",
    pid: 77777,
    device: "Mac Studio",
    deviceId: "192.168.1.102",
    user: "system",
    requestId: "req_abc123",
    message: "订单提交失败：rb2405 流动性不足",
    details: {
      symbol: "rb2405",
      direction: "买入",
      quantity: 10,
      price: 3520,
      exchangeMessage: "买一档挂单量不足",
    },
    stackTrace: 'Traceback (most recent call last):\n  File "/app/trade_executor.py", line 256, in submit_order\n    raise LiquidityError("Insufficient liquidity")',
    errorCode: "LIQUIDITY_INSUFFICIENT",
    category: "交易",
    tags: ["生产", "紧急"],
    handled: false,
  },
  {
    id: "log_20260321170625123",
    timestamp: "2026-03-21T17:06:25.123Z",
    level: "WARNING",
    module: "数据采集",
    process: "data_collector.py",
    pid: 88888,
    device: "Mac Mini",
    deviceId: "192.168.1.103",
    user: "admin",
    requestId: "req_def456",
    message: "数据延迟超过阈值：延迟 2.5 秒",
    details: {
      threshold: 2000,
      actual: 2500,
      source: "sina_api",
    },
    category: "数据",
    tags: ["监控"],
    handled: true,
    handledBy: "admin",
    handledAt: "2026-03-21T17:07:00.000Z",
  },
  {
    id: "log_20260321170410789",
    timestamp: "2026-03-21T17:04:10.789Z",
    level: "INFO",
    module: "策略计算",
    process: "strategy_engine.py",
    pid: 99999,
    device: "MacBook Pro",
    deviceId: "192.168.1.101",
    user: "trader",
    requestId: "req_ghi789",
    message: "策略信号生成：做多 IF 合约 50 手",
    details: {
      contract: "IF",
      signal: "long",
      volume: 50,
      confidence: 0.92,
    },
    category: "策略",
    tags: ["生产"],
    handled: true,
  },
  {
    id: "log_20260321170122456",
    timestamp: "2026-03-21T17:01:22.456Z",
    level: "ERROR",
    module: "风控监控",
    process: "risk_manager.py",
    pid: 66666,
    device: "Mac Studio",
    deviceId: "192.168.1.102",
    user: "system",
    requestId: "req_jkl012",
    message: "风险限额超出：当日浮盈亏 -150万，限额 -100万",
    stackTrace: 'File "/app/risk_manager.py", line 156, in check_risk_limit\n    raise RiskLimitExceeded(f"Drawdown limit exceeded")',
    errorCode: "RISK_LIMIT_EXCEEDED",
    category: "风控",
    tags: ["紧急", "风控"],
    handled: false,
  },
  {
    id: "log_20260321165845123",
    timestamp: "2026-03-21T16:58:45.123Z",
    level: "DEBUG",
    module: "系统服务",
    process: "service_monitor.py",
    pid: 55555,
    device: "Mac Mini",
    deviceId: "192.168.1.103",
    user: "system",
    requestId: "req_mno345",
    message: "心跳检测完成：所有服务正常",
    details: {
      servicesChecked: 8,
      servicesHealthy: 8,
      responseTime: 234,
    },
    category: "系统",
    handled: true,
  },
];

const errorStats: ErrorStat[] = [
  { rank: 1, errorType: "LIQUIDITY_INSUFFICIENT", count: 45, firstSeen: "03-15", lastSeen: "03-21" },
  { rank: 2, errorType: "API_TIMEOUT", count: 32, firstSeen: "03-16", lastSeen: "03-21" },
  { rank: 3, errorType: "DATA_FORMAT_ERROR", count: 28, firstSeen: "03-17", lastSeen: "03-20" },
  { rank: 4, errorType: "CONNECTION_LOST", count: 25, firstSeen: "03-15", lastSeen: "03-21" },
  { rank: 5, errorType: "ORDER_REJECTED", count: 18, firstSeen: "03-18", lastSeen: "03-21" },
];

const hourlyLogData = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i.toString().padStart(2, "0")}:00`,
  ERROR: Math.floor(Math.random() * 5),
  WARNING: Math.floor(Math.random() * 20),
  INFO: Math.floor(Math.random() * 500) + 200,
}));

const moduleDistribution = [
  { name: "数据采集", value: 35, color: "#3b82f6" },
  { name: "策略计算", value: 25, color: "#10b981" },
  { name: "交易执行", value: 20, color: "#f59e0b" },
  { name: "风控监控", value: 12, color: "#8b5cf6" },
  { name: "系统服务", value: 8, color: "#6b7280" },
];

// Helper Components
function SectionHeader({ icon: Icon, title, description }: { icon: typeof ScrollText; title: string; description?: string }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
        <Icon className="w-4 h-4 text-primary" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
    </div>
  );
}

function KPICard({ icon: Icon, label, value, color, trend }: { icon: typeof ScrollText; label: string; value: string; color: string; trend?: string }) {
  const colorClasses: Record<string, string> = {
    blue: "bg-blue-500/10 text-blue-600",
    red: "bg-red-500/10 text-red-600",
    yellow: "bg-amber-500/10 text-amber-600",
    gray: "bg-gray-500/10 text-gray-600",
    orange: "bg-orange-500/10 text-orange-600",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-surface p-4"
    >
      <div className="flex items-center gap-3">
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", colorClasses[color])}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-lg font-semibold text-foreground">{value}</p>
        </div>
      </div>
    </motion.div>
  );
}

function SettingsRow({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border/50 last:border-b-0">
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
      {children}
    </div>
  );
}

function getLevelIcon(level: LogLevel) {
  switch (level) {
    case "ERROR": return <XCircle className="w-3.5 h-3.5" />;
    case "WARNING": return <AlertTriangle className="w-3.5 h-3.5" />;
    case "INFO": return <Info className="w-3.5 h-3.5" />;
    case "DEBUG": return <Bug className="w-3.5 h-3.5" />;
  }
}

function getLevelColor(level: LogLevel) {
  switch (level) {
    case "ERROR": return "bg-[#EF4444]/10 text-[#EF4444]"; // 更显著的红色
    case "WARNING": return "bg-[#F59E0B]/10 text-[#F59E0B]"; // 保持黄色
    case "INFO": return "bg-[#3B82F6]/10 text-[#3B82F6]"; // 蓝色
    case "DEBUG": return "bg-gray-500/10 text-gray-600";
  }
}

export function LogRecordsView() {
  const toast = useToastActions();
  
  // Filter states
  const [levelFilters, setLevelFilters] = useState<Record<LogLevel, boolean>>({
    ERROR: true,
    WARNING: true,
    INFO: true,
    DEBUG: false,
  });
  const [timeRange, setTimeRange] = useState("today");
  const [moduleFilter, setModuleFilter] = useState("all");
  const [deviceFilter, setDeviceFilter] = useState("all");
  const [processFilter, setProcessFilter] = useState("all");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Log detail dialog
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  
  // Selected logs for batch operations
  const [selectedLogs, setSelectedLogs] = useState<Set<string>>(new Set());
  
  // Real-time log states
  const [isStreaming, setIsStreaming] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [streamLevelFilters, setStreamLevelFilters] = useState<Record<LogLevel, boolean>>({
    ERROR: true,
    WARNING: true,
    INFO: false,
    DEBUG: false,
  });
  const [streamLogs, setStreamLogs] = useState<LogEntry[]>([]);
  const streamContainerRef = useRef<HTMLDivElement>(null);
  
  // Request ID trace filter state
  const [traceRequestId, setTraceRequestId] = useState<string | null>(null);
  
  // Regex search state
  const [useRegex, setUseRegex] = useState(false);
  
  // Export config states
  const [exportFormat, setExportFormat] = useState("json");
  const [exportRange, setExportRange] = useState("today");
  const [autoArchive, setAutoArchive] = useState(true);
  const [archivePeriod, setArchivePeriod] = useState("weekly");
  const [retentionDays, setRetentionDays] = useState("90");
  const [fileSizeLimit, setFileSizeLimit] = useState("100");
  const [fileCount, setFileCount] = useState("10");
  
  // Alert config states
  const [errorThreshold, setErrorThreshold] = useState("10");
  const [consecutiveErrors, setConsecutiveErrors] = useState("5");
  const [criticalProcessAlert, setCriticalProcessAlert] = useState(true);
  const [deviceOfflineAlert, setDeviceOfflineAlert] = useState(true);

  // Filtered logs with request_id trace support
  const filteredLogs = useMemo(() => {
    return mockLogEntries.filter((log) => {
      // If tracing a request_id, only show logs with that request_id
      if (traceRequestId && log.requestId !== traceRequestId) return false;
      
      if (!levelFilters[log.level]) return false;
      if (moduleFilter !== "all" && log.module !== moduleFilter) return false;
      if (deviceFilter !== "all" && log.device !== deviceFilter) return false;
      if (processFilter !== "all" && log.process !== processFilter) return false;
      
      // Search keyword with regex support
      if (searchKeyword) {
        if (useRegex) {
          try {
            const regex = new RegExp(searchKeyword, "i");
            if (!regex.test(log.message)) return false;
          } catch {
            // Invalid regex, fallback to normal search
            if (!log.message.toLowerCase().includes(searchKeyword.toLowerCase())) return false;
          }
        } else {
          if (!log.message.toLowerCase().includes(searchKeyword.toLowerCase())) return false;
        }
      }
      return true;
    });
  }, [levelFilters, moduleFilter, deviceFilter, processFilter, searchKeyword, useRegex, traceRequestId]);

  // 分页逻辑
  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
  const paginatedLogs = useMemo(() => {
    return filteredLogs.slice(
      (currentPage - 1) * itemsPerPage,
      currentPage * itemsPerPage
    );
  }, [filteredLogs, currentPage, itemsPerPage]);

  // Get all logs with same request_id for trace count
  const traceLogsCount = useMemo(() => {
    if (!traceRequestId) return 0;
    return mockLogEntries.filter(log => log.requestId === traceRequestId).length;
  }, [traceRequestId]);

  // Highlight search keyword in text
  const highlightKeyword = useCallback((text: string) => {
    if (!searchKeyword) return text;
    
    try {
      const regex = useRegex ? new RegExp(`(${searchKeyword})`, "gi") : new RegExp(`(${searchKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, "gi");
      const parts = text.split(regex);
      
      return parts.map((part, index) => 
        regex.test(part) ? (
          <span key={index} className="bg-yellow-500/30 px-0.5 rounded">{part}</span>
        ) : (
          part
        )
      );
    } catch {
      return text;
    }
  }, [searchKeyword, useRegex]);

  // Handle request_id click for trace
  const handleRequestIdClick = (requestId: string) => {
    if (traceRequestId === requestId) {
      setTraceRequestId(null);
    } else {
      setTraceRequestId(requestId);
      toast.info(`正在追踪请求 ${requestId}`);
    }
  };

  // Clear trace filter
  const clearTraceFilter = () => {
    setTraceRequestId(null);
    toast.success("已清除链路筛选");
  };

  // Real-time log stream effect
  useEffect(() => {
    if (!isStreaming) return;
    
    const interval = setInterval(() => {
      // Randomly select a log from mockLogEntries and create a new one with updated timestamp
      const randomLog = mockLogEntries[Math.floor(Math.random() * mockLogEntries.length)];
      const newLog: LogEntry = {
        ...randomLog,
        id: `stream_${Date.now()}`,
        timestamp: new Date().toISOString(),
      };
      
      setStreamLogs(prev => [...prev.slice(-99), newLog]); // Keep last 100 logs
      
      // Auto scroll to bottom
      if (autoScroll && streamContainerRef.current) {
        streamContainerRef.current.scrollTop = streamContainerRef.current.scrollHeight;
      }
    }, 3000);
    
    return () => clearInterval(interval);
  }, [isStreaming, autoScroll]);

  // Clear stream logs
  const clearStreamLogs = () => {
    setStreamLogs([]);
    toast.success("日志流已清空");
  };

  const toggleLevelFilter = (level: LogLevel) => {
    setLevelFilters(prev => ({ ...prev, [level]: !prev[level] }));
  };

  const toggleStreamLevelFilter = (level: LogLevel) => {
    setStreamLevelFilters(prev => ({ ...prev, [level]: !prev[level] }));
  };

  const handleCopyLog = (log: LogEntry) => {
    const text = `[${new Date(log.timestamp).toLocaleString("zh-CN")}] ${log.level} [${log.module}] ${log.message}`;
    navigator.clipboard.writeText(text);
    toast.success("日志已复制到剪贴板");
  };

  const handleExport = () => {
    toast.success("日志导出任务已创建");
  };

  return (
    <div className="space-y-6 p-6 overflow-x-auto min-w-[1200px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">日志记录</h1>
          <p className="text-sm text-muted-foreground">系统日志管理和问题追溯</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-1" onClick={() => toast.success("数据已刷新")}>
            <RefreshCw className="w-3.5 h-3.5" />
            刷新
          </Button>
          <Button variant="outline" size="sm" className="gap-1" onClick={handleExport}>
            <Download className="w-3.5 h-3.5" />
            导出
          </Button>
        </div>
      </div>

      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-6 gap-4">
        <KPICard icon={FileText} label="今日日志" value="125,450" color="blue" />
        <KPICard icon={XCircle} label="ERROR" value="12" color="red" />
        <KPICard icon={AlertTriangle} label="WARNING" value="85" color="yellow" />
        <KPICard icon={Info} label="INFO" value="125,353" color="blue" />
        <KPICard icon={Bug} label="DEBUG" value="0" color="gray" />
        <KPICard icon={Bell} label="待处理告警" value="3" color="orange" />
      </div>

      {/* Row 2: Log Filter */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Filter} title="日志筛选" />
        
        <div className="space-y-4">
          {/* Level filters */}
          <div className="flex items-center gap-4">
            <span className="text-xs text-muted-foreground w-16">日志级别:</span>
            <div className="flex items-center gap-4">
              {(["ERROR", "WARNING", "INFO", "DEBUG"] as LogLevel[]).map((level) => (
                <label key={level} className="flex items-center gap-1.5 cursor-pointer">
                  <Checkbox
                    checked={levelFilters[level]}
                    onCheckedChange={() => toggleLevelFilter(level)}
                  />
                  <span className={cn("text-xs px-1.5 py-0.5 rounded", getLevelColor(level))}>
                    {level}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Time range */}
          <div className="flex items-center gap-4">
            <span className="text-xs text-muted-foreground w-16">时间范围:</span>
            <div className="flex items-center gap-2">
              <Input type="datetime-local" className="w-44 h-8 text-xs" defaultValue="2026-03-21T00:00" />
              <span className="text-xs text-muted-foreground">-</span>
              <Input type="datetime-local" className="w-44 h-8 text-xs" defaultValue="2026-03-21T23:59" />
            </div>
            <div className="flex items-center gap-1">
              {["今日", "近1小时", "近6小时", "近24小时", "自定义"].map((label) => (
                <Button
                  key={label}
                  variant={timeRange === label ? "default" : "outline"}
                  size="sm"
                  className="h-7 text-xs px-2"
                  onClick={() => setTimeRange(label)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>

          {/* Module & Device filters */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">来源模块:</span>
              <Select value={moduleFilter} onValueChange={setModuleFilter}>
                <SelectTrigger className="w-32 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="数据采集">数据采集</SelectItem>
                  <SelectItem value="策略计算">策略计算</SelectItem>
                  <SelectItem value="交易执行">交易执行</SelectItem>
                  <SelectItem value="风控监控">风控监控</SelectItem>
                  <SelectItem value="系统服务">系统服务</SelectItem>
                  <SelectItem value="API 网关">API 网关</SelectItem>
                  <SelectItem value="数据库">数据库</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">设备筛选:</span>
              <Select value={deviceFilter} onValueChange={setDeviceFilter}>
                <SelectTrigger className="w-32 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="Pro">决策端</SelectItem>
                  <SelectItem value="Studio">交易端</SelectItem>
                  <SelectItem value="Mini">数据端</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">进程筛选:</span>
              <Select value={processFilter} onValueChange={setProcessFilter}>
                <SelectTrigger className="w-36 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="data_collector">data_collector</SelectItem>
                  <SelectItem value="strategy_engine">strategy_engine</SelectItem>
                  <SelectItem value="trade_executor">trade_executor</SelectItem>
                  <SelectItem value="risk_monitor">risk_monitor</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Search */}
          <div className="flex items-center gap-4">
            <span className="text-xs text-muted-foreground w-16">关键词:</span>
            <div className="flex items-center gap-2 flex-1">
              <Input
                placeholder={useRegex ? "输入正则表达式..." : "输入关键词搜索..."}
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="flex-1 h-8 text-xs"
              />
              <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                <Checkbox checked={useRegex} onCheckedChange={(c) => setUseRegex(!!c)} />
                <span className="text-muted-foreground whitespace-nowrap">正则</span>
              </label>
              <Button size="sm" className="h-8 gap-1">
                <Search className="w-3.5 h-3.5" />
                搜索
              </Button>
              <Button variant="outline" size="sm" className="h-8" onClick={() => {
                setSearchKeyword("");
                setModuleFilter("all");
                setDeviceFilter("all");
                setProcessFilter("all");
                setTraceRequestId(null);
              }}>
                重置
              </Button>
            </div>
          </div>

          {/* Trace Filter Indicator */}
          {traceRequestId && (
            <div className="flex items-center gap-2 p-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <Link className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-blue-600">
                正在追踪链路: <span className="font-mono">{traceRequestId}</span> (共 {traceLogsCount} 条日志)
              </span>
              <Button variant="ghost" size="sm" className="h-6 px-2 text-xs gap-1 ml-auto" onClick={clearTraceFilter}>
                <X className="w-3 h-3" />
                清除筛选
              </Button>
            </div>
          )}

          {/* Advanced filters toggle */}
          <div>
            <Button
              variant="ghost"
              size="sm"
              className="gap-1 text-xs text-muted-foreground"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              高级筛选
            </Button>
            {showAdvanced && (
              <div className="mt-3 pl-4 border-l-2 border-border/50 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-20">用户筛选:</span>
                  <Select defaultValue="all">
                    <SelectTrigger className="w-32 h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部</SelectItem>
                      <SelectItem value="system">系统</SelectItem>
                      <SelectItem value="admin">管理员</SelectItem>
                      <SelectItem value="trader">交易员</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-20">请求 ID:</span>
                  <Input placeholder="输入 request_id 追踪完整链路" className="w-64 h-8 text-xs" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-20">错误码:</span>
                  <Input placeholder="输入错误码筛选特定错误" className="w-64 h-8 text-xs" />
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Row 3: Log List */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={ScrollText} title="日志列表" description={traceRequestId ? `链路追踪: ${traceLogsCount} 条记录` : `共 ${filteredLogs.length} 条记录`} />
        
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border/50">
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">选择</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">时间戳</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">级别</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">模块</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">进程</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">PID</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">消息</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">设备</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">设备 ID</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">用户</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">请求 ID</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center">
                    <div className="flex flex-col items-center justify-center text-muted-foreground">
                      <ScrollText className="w-8 h-8 mb-3 opacity-30" />
                      <p className="text-sm">暂无日志记录</p>
                    </div>
                  </td>
                </tr>
              ) : paginatedLogs.map((log) => (
                <tr 
                  key={log.id} 
                  className={cn(
                    "border-b border-border/30 hover:bg-muted/30 transition-colors",
                    traceRequestId === log.requestId && "bg-blue-500/5"
                  )}
                >
                  <td className="py-2 px-2 whitespace-nowrap">
                    <Checkbox
                      checked={selectedLogs.has(log.id)}
                      onChange={(checked) => {
                        const newSet = new Set(selectedLogs);
                        if (checked) newSet.add(log.id);
                        else newSet.delete(log.id);
                        setSelectedLogs(newSet);
                      }}
                    />
                  </td>
                  <td className="py-2 px-2 font-mono text-muted-foreground whitespace-nowrap text-[10px]">{new Date(log.timestamp).toLocaleString("zh-CN")}</td>
                  <td className="py-2 px-2 whitespace-nowrap">
                    <span className={cn("inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium", getLevelColor(log.level))}>
                      {getLevelIcon(log.level)}
                      {log.level}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-foreground whitespace-nowrap text-[10px]">{log.module}</td>
                  <td className="py-2 px-2 font-mono text-muted-foreground whitespace-nowrap text-[10px]">{log.process}</td>
                  <td className="py-2 px-2 font-mono text-muted-foreground whitespace-nowrap text-[10px]">{log.pid}</td>
                  <td className="py-2 px-2 text-foreground max-w-sm truncate text-[10px]" title={log.message}>
                    {highlightKeyword(log.message)}
                  </td>
                  <td className="py-2 px-2 text-foreground whitespace-nowrap text-[10px]">{log.device}</td>
                  <td className="py-2 px-2 font-mono text-muted-foreground whitespace-nowrap text-[10px]">{log.deviceId}</td>
                  <td className="py-2 px-2 text-foreground whitespace-nowrap text-[10px]">{log.user}</td>
                  <td className="py-2 px-2 whitespace-nowrap">
                    <button
                      className={cn(
                        "font-mono text-[10px] hover:underline cursor-pointer",
                        traceRequestId === log.requestId ? "text-blue-600 font-medium" : "text-muted-foreground"
                      )}
                      onClick={() => handleRequestIdClick(log.requestId)}
                      title="点击追踪此请求的完整链路"
                    >
                      {log.requestId}
                    </button>
                  </td>
                  <td className="py-2 px-2 whitespace-nowrap">
                    <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]" onClick={() => setSelectedLog(log)}>
                      <Eye className="w-3 h-3 mr-1" />
                      详情
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* 分页器 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 px-3 py-2 border-t border-border/30 bg-muted/20">
              <span className="text-xs text-muted-foreground">
                第 {currentPage} / {totalPages} 页，共 {filteredLogs.length} 条
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-xs bg-muted hover:bg-muted/80 disabled:opacity-50 rounded transition-colors"
                >
                  上一页
                </button>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 text-xs bg-muted hover:bg-muted/80 disabled:opacity-50 rounded transition-colors"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Row 4: Real-time Log Stream */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Activity} title="实时日志流" />
        
        <div className="space-y-3">
          {/* Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant={isStreaming ? "default" : "outline"}
                size="sm"
                className="gap-1"
                onClick={() => setIsStreaming(!isStreaming)}
              >
                {isStreaming ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                {isStreaming ? "暂停" : "开始"}
              </Button>
              <Button variant="outline" size="sm" className="gap-1" onClick={clearStreamLogs}>
                <Trash2 className="w-3.5 h-3.5" />
                清空
              </Button>
              <Button variant="outline" size="sm" className="gap-1">
                <Download className="w-3.5 h-3.5" />
                导出
              </Button>
              <Button variant="outline" size="sm" className="gap-1">
                <Settings className="w-3.5 h-3.5" />
                设置
              </Button>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-1.5 text-xs">
                <Checkbox checked={autoScroll} onCheckedChange={(c) => setAutoScroll(!!c)} />
                <span className="text-muted-foreground">自动滚动</span>
              </label>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">过滤级别:</span>
                {(["ERROR", "WARNING", "INFO", "DEBUG"] as LogLevel[]).map((level) => (
                  <label key={level} className="flex items-center gap-1 cursor-pointer">
                    <Checkbox
                      checked={streamLevelFilters[level]}
                      onCheckedChange={() => toggleStreamLevelFilter(level)}
                    />
                    <span className="text-[10px]">{level}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Streaming indicator */}
          {isStreaming && (
            <div className="flex items-center gap-2 text-xs text-emerald-600">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              正在接收新日志...
            </div>
          )}

          {/* Log stream display */}
          <div 
            ref={streamContainerRef}
            className="bg-muted/30 rounded-lg p-3 h-48 overflow-y-auto font-mono text-xs"
          >
            {(streamLogs.length > 0 ? streamLogs : mockLogEntries).filter(log => streamLevelFilters[log.level]).map((log, index) => (
              <div 
                key={`${log.id}-${index}`} 
                className={cn(
                  "flex items-start gap-2 py-1 hover:bg-muted/50 px-1 rounded",
                  streamLogs.length > 0 && index === streamLogs.length - 1 && "bg-emerald-500/10"
                )}
              >
                <span className="text-muted-foreground whitespace-nowrap text-[10px]">{new Date(log.timestamp).toLocaleTimeString("zh-CN")}</span>
                <span className={cn("px-1 rounded text-[10px] font-medium", getLevelColor(log.level))}>{log.level.padEnd(7)}</span>
                <span className="text-blue-500 text-[10px]">[{log.process}:{log.pid}]</span>
                <span className="text-foreground text-[10px]">{log.message}</span>
              </div>
            ))}
            {streamLogs.length === 0 && !isStreaming && (
              <div className="text-center text-muted-foreground py-4">
                点击"开始"按钮接收实时日志
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Row 5: Charts */}
      <div className="grid grid-cols-2 gap-4">
        {/* Log Trend Chart */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="card-surface p-5"
        >
          <SectionHeader icon={BarChart3} title="近 24 小时日志量趋势" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourlyLogData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    fontSize: "11px",
                  }}
                />
                <Bar dataKey="INFO" stackId="a" fill="#3b82f6" name="INFO" />
                <Bar dataKey="WARNING" stackId="a" fill="#f59e0b" name="WARNING" />
                <Bar dataKey="ERROR" stackId="a" fill="#ef4444" name="ERROR" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Module Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card-surface p-5"
        >
          <SectionHeader icon={PieChart} title="日志模块分布" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie
                  data={moduleDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {moduleDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    fontSize: "11px",
                  }}
                />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Row 6: Error Analysis */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={AlertCircle} title="错误分析（近 7 天）" />
        
        <div className="grid grid-cols-3 gap-6">
          {/* Top 10 Errors */}
          <div className="col-span-2">
            <h4 className="text-xs font-medium text-foreground mb-3">Top 10 高频错误</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left py-2 px-2 text-muted-foreground font-medium">排名</th>
                    <th className="text-left py-2 px-2 text-muted-foreground font-medium">错误类型</th>
                    <th className="text-left py-2 px-2 text-muted-foreground font-medium">次数</th>
                    <th className="text-left py-2 px-2 text-muted-foreground font-medium">首次出现</th>
                    <th className="text-left py-2 px-2 text-muted-foreground font-medium">最近出现</th>
                  </tr>
                </thead>
                <tbody>
                  {errorStats.map((stat) => (
                    <tr key={stat.rank} className="border-b border-border/30">
                      <td className="py-2 px-2">
                        <span className={cn(
                          "w-5 h-5 rounded-full inline-flex items-center justify-center text-[10px] font-medium",
                          stat.rank <= 3 ? "bg-red-500/10 text-red-600" : "bg-muted text-muted-foreground"
                        )}>
                          {stat.rank}
                        </span>
                      </td>
                      <td className="py-2 px-2 font-mono text-foreground">{stat.errorType}</td>
                      <td className="py-2 px-2 text-foreground font-medium">{stat.count}</td>
                      <td className="py-2 px-2 text-muted-foreground">{stat.firstSeen}</td>
                      <td className="py-2 px-2 text-muted-foreground">{stat.lastSeen}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Error Trend Analysis */}
          <div className="space-y-3">
            <h4 className="text-xs font-medium text-foreground">错误趋势分析</h4>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-2 border-b border-border/30">
                <span className="text-muted-foreground">本周 ERROR 总数</span>
                <span className="text-foreground font-medium">125 条 <span className="text-red-500">(+15%)</span></span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border/30">
                <span className="text-muted-foreground">主要错误源</span>
                <span className="text-foreground font-medium">交易执行模块 (45%)</span>
              </div>
              <div className="py-2">
                <span className="text-muted-foreground">建议</span>
                <p className="text-foreground mt-1">检查交易执行逻辑，增加重试机制</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Row 7: Export & Archive Config */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={FileDown} title="日志导出配置" />
        
        <div className="grid grid-cols-3 gap-6">
          {/* Export Settings */}
          <div>
            <h4 className="text-xs font-medium text-foreground mb-3 flex items-center gap-2">
              <Download className="w-3.5 h-3.5 text-primary" />
              导出设置
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">导出格式</span>
                <Select value={exportFormat} onValueChange={setExportFormat}>
                  <SelectTrigger className="w-24 h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="txt">TXT</SelectItem>
                    <SelectItem value="parquet">Parquet</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">导出范围</span>
                <Select value={exportRange} onValueChange={setExportRange}>
                  <SelectTrigger className="w-24 h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="today">今日</SelectItem>
                    <SelectItem value="week">本周</SelectItem>
                    <SelectItem value="month">本月</SelectItem>
                    <SelectItem value="custom">自定义</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">压缩方式</span>
                <Select defaultValue="gzip">
                  <SelectTrigger className="w-24 h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gzip">Gzip</SelectItem>
                    <SelectItem value="zstd">Zstd</SelectItem>
                    <SelectItem value="none">无压缩</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Auto Archive */}
          <div>
            <h4 className="text-xs font-medium text-foreground mb-3 flex items-center gap-2">
              <Archive className="w-3.5 h-3.5 text-primary" />
              自动归档
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">自动归档</span>
                <Switch checked={autoArchive} onCheckedChange={setAutoArchive} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">归档周期</span>
                <Select value={archivePeriod} onValueChange={setArchivePeriod}>
                  <SelectTrigger className="w-24 h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">每日</SelectItem>
                    <SelectItem value="weekly">每周</SelectItem>
                    <SelectItem value="monthly">每月</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">保留天数</span>
                <div className="flex items-center gap-1">
                  <Input value={retentionDays} onChange={(e) => setRetentionDays(e.target.value)} className="w-14 h-7 text-xs text-center" />
                  <span className="text-xs text-muted-foreground">天</span>
                </div>
              </div>
            </div>
          </div>

          {/* Log Rotation */}
          <div>
            <h4 className="text-xs font-medium text-foreground mb-3 flex items-center gap-2">
              <RotateCcw className="w-3.5 h-3.5 text-primary" />
              日志轮转
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">单文件大小限制</span>
                <div className="flex items-center gap-1">
                  <Input value={fileSizeLimit} onChange={(e) => setFileSizeLimit(e.target.value)} className="w-14 h-7 text-xs text-center" />
                  <span className="text-xs text-muted-foreground">MB</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">保留文件数</span>
                <div className="flex items-center gap-1">
                  <Input value={fileCount} onChange={(e) => setFileCount(e.target.value)} className="w-14 h-7 text-xs text-center" />
                  <span className="text-xs text-muted-foreground">个</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">轮转后处理</span>
                <Select defaultValue="compress">
                  <SelectTrigger className="w-24 h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="compress">压缩归档</SelectItem>
                    <SelectItem value="delete">删除</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Row 8: Alert Config */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Bell} title="日志告警配置" />
        
        <div className="grid grid-cols-2 gap-6">
          {/* Trigger Conditions */}
          <div>
            <h4 className="text-xs font-medium text-foreground mb-3 flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-primary" />
              触发条件
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">ERROR 数量超过</span>
                <div className="flex items-center gap-1">
                  <Input value={errorThreshold} onChange={(e) => setErrorThreshold(e.target.value)} className="w-14 h-7 text-xs text-center" />
                  <span className="text-xs text-muted-foreground">条/小时</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">相同错误连续</span>
                <div className="flex items-center gap-1">
                  <Input value={consecutiveErrors} onChange={(e) => setConsecutiveErrors(e.target.value)} className="w-14 h-7 text-xs text-center" />
                  <span className="text-xs text-muted-foreground">次</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">关键进程异常</span>
                <Switch checked={criticalProcessAlert} onCheckedChange={setCriticalProcessAlert} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">设备离线</span>
                <Switch checked={deviceOfflineAlert} onCheckedChange={setDeviceOfflineAlert} />
              </div>
            </div>
          </div>

          {/* Notification Settings */}
          <div>
            <h4 className="text-xs font-medium text-foreground mb-3 flex items-center gap-2">
              <Bell className="w-3.5 h-3.5 text-primary" />
              通知设置
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-red-500 font-medium">P0 紧急</span>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox defaultChecked />短信
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox defaultChecked />电话
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox defaultChecked />飞书
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox defaultChecked />邮件
                  </label>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-amber-500 font-medium">P1 重要</span>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox />短信
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox />电话
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox defaultChecked />飞书
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox defaultChecked />邮件
                  </label>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-blue-500 font-medium">P2 提示</span>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox />短信
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox />电话
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox defaultChecked />飞书
                  </label>
                  <label className="flex items-center gap-1 text-[10px]">
                    <Checkbox />邮件
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Log Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              日志详情
            </DialogTitle>
            <DialogDescription className="sr-only">
              查看日志的详细信息，包括时间、级别、模块、进程等
            </DialogDescription>
          </DialogHeader>
          
          {selectedLog && (
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Info className="w-4 h-4 text-primary" />
                  基本信息
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs bg-muted/30 rounded-lg p-3">
                  <div><span className="text-muted-foreground">日志 ID:</span> <span className="font-mono text-[10px]">{selectedLog.id}</span></div>
                  <div><span className="text-muted-foreground">时间:</span> <span className="font-mono text-[10px]">{new Date(selectedLog.timestamp).toLocaleString("zh-CN")}</span></div>
                  <div><span className="text-muted-foreground">级别:</span> <span className={cn("px-1.5 py-0.5 rounded text-[10px]", getLevelColor(selectedLog.level))}>{selectedLog.level}</span></div>
                  <div><span className="text-muted-foreground">模块:</span> {selectedLog.module}</div>
                  <div><span className="text-muted-foreground">进程:</span> <span className="font-mono text-[10px]">{selectedLog.process} (PID: {selectedLog.pid})</span></div>
                  <div><span className="text-muted-foreground">设备:</span> {selectedLog.device}</div>
                  <div><span className="text-muted-foreground">用户:</span> {selectedLog.user}</div>
                  <div><span className="text-muted-foreground">请求 ID:</span> <span className="font-mono text-[10px]">{selectedLog.requestId}</span></div>
                  {selectedLog.category && <div><span className="text-muted-foreground">分类:</span> {selectedLog.category}</div>}
                  {selectedLog.errorCode && <div><span className="text-muted-foreground">错误码:</span> <span className="font-mono text-[10px]">{selectedLog.errorCode}</span></div>}
                  {selectedLog.deviceId && <div><span className="text-muted-foreground">设备 ID:</span> <span className="font-mono text-[10px]">{selectedLog.deviceId}</span></div>}
                </div>
              </div>

              {/* Log Content */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
                  <ScrollText className="w-4 h-4 text-primary" />
                  日志内容
                </h4>
                <div className="bg-muted/30 rounded-lg p-3 font-mono text-xs whitespace-pre-wrap">
                  [{new Date(selectedLog.timestamp).toLocaleString("zh-CN")}] {selectedLog.level} [{selectedLog.process}]{'\n'}
                  {selectedLog.message}
                  {selectedLog.details && (
                    <>
                      {'\n\n'}详细信息:{'\n'}{JSON.stringify(selectedLog.details, null, 2)}
                    </>
                  )}
                  {selectedLog.tags && selectedLog.tags.length > 0 && (
                    <>
                      {'\n\n'}标签: {selectedLog.tags.join(", ")}
                    </>
                  )}
                </div>
              </div>

              {/* Stack Trace (for ERROR) */}
              {selectedLog.stackTrace && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Bug className="w-4 h-4 text-red-500" />
                    错误堆栈
                  </h4>
                  <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 font-mono text-xs whitespace-pre-wrap text-red-600">
                    {selectedLog.stackTrace}
                  </div>
                </div>
              )}

              {/* Related Info */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Link className="w-4 h-4 text-primary" />
                  关联信息
                </h4>
                <div className="bg-muted/30 rounded-lg p-3 text-xs space-y-1">
                  {selectedLog.handled ? (
                    <div><span className="text-emerald-600 font-medium">✓ 已处理</span> 
                      {selectedLog.handledBy && (
                        <span className="text-muted-foreground ml-2">由 {selectedLog.handledBy} 在 {selectedLog.handledAt}</span>
                      )}
                    </div>
                  ) : (
                    <div className="text-orange-600">⚠ 待处理</div>
                  )}
                  {selectedLog.category && (
                    <div><span className="text-muted-foreground">分类:</span> {selectedLog.category}</div>
                  )}
                  {selectedLog.tags && selectedLog.tags.length > 0 && (
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">标签:</span>
                      <div className="flex gap-1 flex-wrap">
                        {selectedLog.tags.map((tag) => (
                          <span key={tag} className="px-1.5 py-0.5 bg-primary/10 text-primary rounded text-[10px]">{tag}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 pt-2 border-t border-border">
                <Button variant="outline" size="sm" className="gap-1" onClick={() => handleCopyLog(selectedLog)}>
                  <Copy className="w-3.5 h-3.5" />
                  复制全文
                </Button>
                <Button variant="outline" size="sm" className="gap-1">
                  <Download className="w-3.5 h-3.5" />
                  导出日志
                </Button>
                <Button variant="outline" size="sm" className="gap-1">
                  <CheckCircle className="w-3.5 h-3.5" />
                  标记为已处理
                </Button>
                <Button variant="outline" size="sm" className="gap-1">
                  <ExternalLink className="w-3.5 h-3.5" />
                  创建工单
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
