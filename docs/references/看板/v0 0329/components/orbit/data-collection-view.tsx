"use client";

import React, { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  Database,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Activity,
  Bell,
  Wrench,
  Search,
  RotateCw,
  RefreshCw,
  Play,
  Pause,
  Eye,
  Edit3,
  FileText,
  Download,
  Server,
  Cpu,
  HardDrive,
  Zap,
  Filter,
  MoreHorizontal,
  ChevronRight,
  X,
  CheckSquare,
  Square,
  AlertOctagon,
  Info,
  FileDown,
  Plug,
  BarChart3,
  TrendingUp,
  Radio,
  Loader2,
  Database as DatabaseEmpty,
} from "lucide-react";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
  ReferenceLine,
} from "recharts";

// KPI Card Component
interface KPICardProps {
  icon: typeof Database;
  label: string;
  value: string | number;
  color?: "default" | "green" | "red" | "yellow" | "blue";
  subValue?: string;
}

function KPICard({ icon: Icon, label, value, color = "default", subValue }: KPICardProps) {
  const colorClasses = {
    default: "text-foreground",
    green: "text-[#3FB950]",
    red: "text-[#FF3B30]",
    yellow: "text-amber-600",
    blue: "text-blue-600",
  };

  const iconBgClasses = {
    default: "bg-muted",
    green: "bg-[#3FB950]/10",
    red: "bg-[#FF3B30]/10",
    yellow: "bg-amber-500/10",
    blue: "bg-blue-500/10",
  };

  const iconColorClasses = {
    default: "text-muted-foreground",
    green: "text-[#3FB950]",
    red: "text-[#FF3B30]",
    yellow: "text-amber-600",
    blue: "text-blue-600",
  };

  return (
    <div className="card-surface p-4 flex flex-col items-center justify-center text-center">
      <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center mb-2", iconBgClasses[color])}>
        <Icon className={cn("w-4 h-4", iconColorClasses[color])} />
      </div>
      <p className="text-[11px] text-muted-foreground mb-1 whitespace-nowrap">{label}</p>
      <p className={cn("text-lg font-semibold font-mono whitespace-nowrap flex items-baseline gap-1", colorClasses[color])}>
        {value}
        {subValue && <span className="text-[10px] text-muted-foreground font-normal">{subValue}</span>}
      </p>
    </div>
  );
}

// Section Header Component
interface SectionHeaderProps {
  icon: typeof Database;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

function SectionHeader({ icon: Icon, title, description, action }: SectionHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shrink-0">
          <Icon className="w-4.5 h-4.5 text-primary" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
        </div>
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

// Status Indicator
function StatusIndicator({ status }: { status: "normal" | "delay" | "failed" | "stopped" }) {
  const config = {
    normal: { color: "bg-emerald-500", label: "正常" },
    delay: { color: "bg-amber-500", label: "延迟" },
    failed: { color: "bg-red-500", label: "失败" },
    stopped: { color: "bg-gray-400", label: "停用" },
  };

  return (
    <div className="flex items-center gap-2">
      <span className={cn("w-2.5 h-2.5 rounded-full", config[status].color)} />
      <span className="text-xs text-muted-foreground">{config[status].label}</span>
    </div>
  );
}

// Data Source Types
interface DataSource {
  id: string;
  name: string;
  type: "行情" | "基本面" | "宏观" | "另类" | "交易所";
  provider: string;
  status: "normal" | "delay" | "failed" | "stopped";
  todayCount: number;
  totalCount: number;
  lastCollectTime: string;
  planStartTime: string;
  collectCycle: string;
  failedDuration?: string;
  errorReason?: string;
  processStatus: "运行中" | "已停止" | "重启中";
  lastHeartbeat: string;
}

// Alert Types
interface AlertRecord {
  id: string;
  time: string;
  level: "P0" | "P1" | "P2";
  sourceName: string;
  alertType: string;
  content: string;
  status: "未处理" | "处理中" | "已解决";
}

// Process Types
interface ProcessInfo {
  id: string;
  name: string;
  pid: number;
  cpuUsage: number;
  memoryUsage: number;
  runTime: string;
  status: "运行中" | "已停止" | "重启中";
  startTime: string;
  lastHeartbeat: string;
}

// Mock Data
const dataSources: DataSource[] = [
  {
    id: "1",
    name: "Tushare 行情",
    type: "行情",
    provider: "Tushare",
    status: "normal",
    todayCount: 25450,
    totalCount: 1258450,
    lastCollectTime: "17:08:32",
    planStartTime: "09:00:00",
    collectCycle: "3 秒",
    processStatus: "运行中",
    lastHeartbeat: "5 秒前",
  },
  {
    id: "2",
    name: "AkShare 财经",
    type: "基本面",
    provider: "AkShare",
    status: "delay",
    todayCount: 12850,
    totalCount: 856200,
    lastCollectTime: "17:05:15",
    planStartTime: "09:00:00",
    collectCycle: "5 秒",
    errorReason: "延迟>500ms",
    processStatus: "运行中",
    lastHeartbeat: "8 秒前",
  },
  {
    id: "3",
    name: "Wind 宏观",
    type: "宏观",
    provider: "Wind",
    status: "failed",
    todayCount: 0,
    totalCount: 125400,
    lastCollectTime: "14:30:00",
    planStartTime: "09:00:00",
    collectCycle: "1 分",
    failedDuration: "2 小时 38 分",
    errorReason: "API 限流",
    processStatus: "已停止",
    lastHeartbeat: "2 小时前",
  },
  {
    id: "4",
    name: "Choice 舆情",
    type: "另类",
    provider: "Choice",
    status: "stopped",
    todayCount: 0,
    totalCount: 45200,
    lastCollectTime: "昨日",
    planStartTime: "-",
    collectCycle: "1 时",
    errorReason: "手动停用",
    processStatus: "已停止",
    lastHeartbeat: "-",
  },
  {
    id: "5",
    name: "交易所数据",
    type: "交易所",
    provider: "交易所",
    status: "normal",
    todayCount: 18920,
    totalCount: 2156780,
    lastCollectTime: "17:10:05",
    planStartTime: "09:15:00",
    collectCycle: "1 秒",
    processStatus: "运行中",
    lastHeartbeat: "2 秒前",
  },
  {
    id: "6",
    name: "新浪财经",
    type: "行情",
    provider: "AkShare",
    status: "normal",
    todayCount: 8560,
    totalCount: 456200,
    lastCollectTime: "17:09:45",
    planStartTime: "09:00:00",
    collectCycle: "10 秒",
    processStatus: "运行中",
    lastHeartbeat: "3 秒前",
  },
  {
    id: "7",
    name: "东方财富",
    type: "基本面",
    provider: "Choice",
    status: "normal",
    todayCount: 5230,
    totalCount: 325600,
    lastCollectTime: "17:08:20",
    planStartTime: "09:30:00",
    collectCycle: "30 秒",
    processStatus: "运行中",
    lastHeartbeat: "6 秒前",
  },
];

const alertRecords: AlertRecord[] = [
  {
    id: "1",
    time: "17:08:32",
    level: "P0",
    sourceName: "Wind 宏观",
    alertType: "采集失败",
    content: "API 限流导致采集中断，已持续 2 小时",
    status: "未处理",
  },
  {
    id: "2",
    time: "16:45:10",
    level: "P1",
    sourceName: "AkShare 财经",
    alertType: "延迟过高",
    content: "采集延迟超过 500ms 阈值",
    status: "处理中",
  },
  {
    id: "3",
    time: "15:30:00",
    level: "P2",
    sourceName: "Tushare 行情",
    alertType: "数据异常",
    content: "检测到数据缺失，已自动补录",
    status: "已解决",
  },
];

const processInfos: ProcessInfo[] = [
  {
    id: "1",
    name: "tushare-collector",
    pid: 12345,
    cpuUsage: 12.5,
    memoryUsage: 256,
    runTime: "2 天 5 小时",
    status: "运行中",
    startTime: "03/14 09:00",
    lastHeartbeat: "5 秒前",
  },
  {
    id: "2",
    name: "akshare-collector",
    pid: 12346,
    cpuUsage: 8.2,
    memoryUsage: 185,
    runTime: "1 天 12 小时",
    status: "运行中",
    startTime: "03/15 05:00",
    lastHeartbeat: "8 秒前",
  },
  {
    id: "3",
    name: "wind-collector",
    pid: 12347,
    cpuUsage: 0,
    memoryUsage: 0,
    runTime: "-",
    status: "已停止",
    startTime: "-",
    lastHeartbeat: "2 小时前",
  },
  {
    id: "4",
    name: "exchange-collector",
    pid: 12348,
    cpuUsage: 15.8,
    memoryUsage: 320,
    runTime: "5 天 8 小时",
    status: "运行中",
    startTime: "03/11 09:00",
    lastHeartbeat: "2 秒前",
  },
];

// Trend Data
const trendData = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i.toString().padStart(2, "0")}:00`,
  行情: Math.floor(Math.random() * 50000) + 30000,
  基本面: Math.floor(Math.random() * 20000) + 10000,
  宏观: i >= 14 ? 0 : Math.floor(Math.random() * 5000) + 2000,
  成功率: i >= 14 && i <= 16 ? 85 + Math.random() * 5 : 95 + Math.random() * 5,
  isAbnormal: i >= 14 && i <= 16,
}));

export function DataCollectionView() {
  const [typeFilter, setTypeFilter] = useState("全部");
  const [statusFilter, setStatusFilter] = useState("全部");
  const [providerFilter, setProviderFilter] = useState("全部");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showLogDrawer, setShowLogDrawer] = useState(false);
  const [selectedLogSource, setSelectedLogSource] = useState<DataSource | null>(null);
  const [refreshingIds, setRefreshingIds] = useState<string[]>([]);
  const [restartingIds, setRestartingIds] = useState<string[]>([]);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingSource, setEditingSource] = useState<DataSource | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  
  // 自动刷新和分页
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date().toLocaleTimeString());
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // 自动刷新效果
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

  // Handlers for actions
  const handleRefresh = (source: DataSource) => {
    setRefreshingIds(prev => [...prev, source.id]);
    setTimeout(() => {
      setRefreshingIds(prev => prev.filter(id => id !== source.id));
      setToastMessage(`${source.name} 刷新成功`);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
    }, 1500);
  };

  const handleRestart = (source: DataSource) => {
    setRestartingIds(prev => [...prev, source.id]);
    setTimeout(() => {
      setRestartingIds(prev => prev.filter(id => id !== source.id));
      setToastMessage(`${source.name} 重启完成`);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
    }, 2000);
  };

  const handleEdit = (source: DataSource) => {
    setEditingSource(source);
    setShowEditDialog(true);
  };

  // Filter data sources
  const filteredSources = useMemo(() => {
    return dataSources.filter((source) => {
      if (typeFilter !== "全部" && source.type !== typeFilter) return false;
      if (statusFilter !== "全部") {
        const statusMap: Record<string, DataSource["status"]> = {
          正常: "normal",
          延迟: "delay",
          失败: "failed",
          停用: "stopped",
        };
        if (source.status !== statusMap[statusFilter]) return false;
      }
      if (providerFilter !== "全部" && source.provider !== providerFilter) return false;
      if (searchQuery && !source.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [typeFilter, statusFilter, providerFilter, searchQuery]);

  // 分页逻辑
  const totalPages = Math.ceil(filteredSources.length / itemsPerPage);
  const paginatedSources = useMemo(() => {
    return filteredSources.slice(
      (currentPage - 1) * itemsPerPage,
      currentPage * itemsPerPage
    );
  }, [filteredSources, currentPage, itemsPerPage]);

  const toggleSelectSource = (id: string) => {
    setSelectedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedSources.length === filteredSources.length) {
      setSelectedSources([]);
    } else {
      setSelectedSources(filteredSources.map((s) => s.id));
    }
  };

  const handleViewLog = (source: DataSource) => {
    setSelectedLogSource(source);
    setShowLogDrawer(true);
  };

  return (
    <div className="p-6 space-y-6 max-w-[1600px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">数据采集</h1>
          <p className="text-sm text-muted-foreground mt-1">监控所有数据源的采集状态和性能</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
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
            className="gap-2"
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
        </div>
      </div>

      {/* Row 1: KPI Cards - 2 rows of 4 */}
      <div className="grid grid-cols-4 sm:grid-cols-8 gap-3">
        <KPICard icon={Database} label="数据源总数" value="47" subValue="个" />
        <KPICard icon={CheckCircle2} label="正常运行" value="45" subValue="个" color="green" />
        <KPICard icon={XCircle} label="异常/失败" value="2" subValue="个" color="red" />
        <KPICard icon={TrendingUp} label="成功率" value="95.7%" color="blue" />
        <KPICard icon={BarChart3} label="今日采集量" value="1,258,450" subValue="条" />
        <KPICard icon={Clock} label="平均延迟" value="125ms" />
        <KPICard icon={Bell} label="待处理告警" value="3" subValue="条" color="yellow" />
        <KPICard icon={Wrench} label="自动修复次数" value="12" subValue="次" />
      </div>

      {/* Row 2: Filters */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Filter} title="筛选条件" description="快速定位目标数据源" />
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground shrink-0">数据源类型</span>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-28 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="全部">全部</SelectItem>
                <SelectItem value="行情">行情数据</SelectItem>
                <SelectItem value="基本面">基本面数据</SelectItem>
                <SelectItem value="宏观">宏观数据</SelectItem>
                <SelectItem value="另类">另类数据</SelectItem>
                <SelectItem value="交易所">交易所数据</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground shrink-0">状态筛选</span>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-24 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="全部">全部</SelectItem>
                <SelectItem value="正常">正常</SelectItem>
                <SelectItem value="延迟">延迟</SelectItem>
                <SelectItem value="失败">失败</SelectItem>
                <SelectItem value="停用">停用</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground shrink-0">供应商筛选</span>
            <Select value={providerFilter} onValueChange={setProviderFilter}>
              <SelectTrigger className="w-28 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="全部">全部</SelectItem>
                <SelectItem value="Tushare">Tushare</SelectItem>
                <SelectItem value="AkShare">AkShare</SelectItem>
                <SelectItem value="Wind">Wind</SelectItem>
                <SelectItem value="Choice">Choice</SelectItem>
                <SelectItem value="交易所">交易所</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="输入数据源名称/代码搜索"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-8 text-xs"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setTypeFilter("全部");
              setStatusFilter("全部");
              setProviderFilter("全部");
              setSearchQuery("");
            }}
          >
            重置筛选
          </Button>
        </div>
      </motion.div>

      {/* Row 3: Data Source Table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="card-surface p-5"
      >
        <SectionHeader
          icon={Database}
          title="数据源列表"
          description={`共 ${filteredSources.length} 个数据源`}
          action={
            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground">
                已选择 {selectedSources.length} 项
              </span>
            </div>
          }
        />
        <div className="overflow-x-auto">
          {filteredSources.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <DatabaseEmpty className="w-8 h-8 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">暂无数据源</p>
            </div>
          ) : (
            <>
            <table className="w-full text-xs min-w-[1400px]">
            <thead>
              <tr className="border-b border-border">
                <th className="py-3 px-2 text-left font-medium text-muted-foreground w-8 whitespace-nowrap">
                  <button onClick={toggleSelectAll} className="flex items-center">
                    {selectedSources.length === filteredSources.length && filteredSources.length > 0 ? (
                      <CheckSquare className="w-4 h-4 text-primary" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                  </button>
                </th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">状态</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">数据源名称</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">类型</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">供应商</th>
                <th className="py-3 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">今日采集</th>
                <th className="py-3 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">累计采集</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">最后采集</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">计划开始</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">周期</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">失效时长</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">报错原因</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">进程状态</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">心跳</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">���作</th>
              </tr>
            </thead>
            <tbody>
              {paginatedSources.map((source) => (
                <tr
                  key={source.id}
                  className={cn(
                    "border-b border-border/50 hover:bg-muted/30 transition-colors",
                    selectedSources.includes(source.id) && "bg-primary/5"
                  )}
                >
                  <td className="py-3 px-2 whitespace-nowrap">
                    <button onClick={() => toggleSelectSource(source.id)}>
                      {selectedSources.includes(source.id) ? (
                        <CheckSquare className="w-4 h-4 text-primary" />
                      ) : (
                        <Square className="w-4 h-4 text-muted-foreground" />
                      )}
                    </button>
                  </td>
                  <td className="py-3 px-2 whitespace-nowrap">
                    <StatusIndicator status={source.status} />
                  </td>
                  <td className="py-3 px-2 font-medium text-foreground whitespace-nowrap">{source.name}</td>
                  <td className="py-3 px-2 whitespace-nowrap">
                    <span className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-medium",
                      source.type === "行情" && "bg-blue-500/10 text-blue-600",
                      source.type === "基本面" && "bg-emerald-500/10 text-emerald-600",
                      source.type === "宏观" && "bg-purple-500/10 text-purple-600",
                      source.type === "另类" && "bg-amber-500/10 text-amber-600",
                      source.type === "交易所" && "bg-cyan-500/10 text-cyan-600"
                    )}>
                      {source.type}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-muted-foreground whitespace-nowrap">{source.provider}</td>
                  <td className="py-3 px-2 text-right font-mono whitespace-nowrap">
                    {source.todayCount.toLocaleString()}
                  </td>
                  <td className="py-3 px-2 text-right font-mono text-muted-foreground whitespace-nowrap">
                    {source.totalCount.toLocaleString()}
                  </td>
                  <td className="py-3 px-2 text-center font-mono whitespace-nowrap">{source.lastCollectTime}</td>
                  <td className="py-3 px-2 text-center font-mono text-muted-foreground whitespace-nowrap">
                    {source.planStartTime}
                  </td>
                  <td className="py-3 px-2 text-center whitespace-nowrap">{source.collectCycle}</td>
                  <td className="py-3 px-2 text-center whitespace-nowrap">
                    {source.failedDuration ? (
                      <span className="text-red-600 font-medium">{source.failedDuration}</span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="py-3 px-2 whitespace-nowrap">
                    {source.errorReason ? (
                      <span
                        className="text-amber-600 cursor-help"
                        title={source.errorReason}
                      >
                        {source.errorReason}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="py-3 px-2 text-center whitespace-nowrap">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-[10px] font-medium whitespace-nowrap",
                        source.processStatus === "运行中" && "bg-emerald-500/10 text-emerald-600",
                        source.processStatus === "已停止" && "bg-gray-500/10 text-gray-600",
                        source.processStatus === "重启中" && "bg-amber-500/10 text-amber-600"
                      )}
                    >
                      {source.processStatus}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-center text-muted-foreground whitespace-nowrap">
                    {source.lastHeartbeat}
                  </td>
                  <td className="py-3 px-2 whitespace-nowrap">
                    <div className="flex items-center justify-center gap-1">
                      {source.status === "failed" || source.status === "stopped" ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-xs gap-1"
                          onClick={() => handleRestart(source)}
                          disabled={restartingIds.includes(source.id)}
                        >
                          {restartingIds.includes(source.id) ? (
                            <RefreshCw className="w-3 h-3 animate-spin" />
                          ) : (
                            <Play className="w-3 h-3" />
                          )}
                          {restartingIds.includes(source.id) ? "重启中" : source.status === "stopped" ? "启用" : "重启"}
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-xs gap-1"
                          onClick={() => handleRefresh(source)}
                          disabled={refreshingIds.includes(source.id)}
                        >
                          <RefreshCw className={cn("w-3 h-3", refreshingIds.includes(source.id) && "animate-spin")} />
                          {refreshingIds.includes(source.id) ? "刷新中" : "刷新"}
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs gap-1"
                        onClick={() => handleViewLog(source)}
                      >
                        <FileText className="w-3 h-3" />
                        日志
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs gap-1"
                        onClick={() => handleEdit(source)}
                      >
                        <Edit3 className="w-3 h-3" />
                        编辑
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            </table>
            </>
          )}
        </div>
      </motion.div>

      {/* Row 4: Batch Operations */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Zap} title="批量操作" description="对选中的数据源执行批量操作" />
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="outline" size="sm" className="gap-2" disabled={selectedSources.length === 0}>
            <RotateCw className="w-4 h-4" />
            批量重启失败数据源
          </Button>
          <Button variant="outline" size="sm" className="gap-2" disabled={selectedSources.length === 0}>
            <Plug className="w-4 h-4" />
            批量测试连接
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="w-4 h-4" />
            导出状态报告
          </Button>
          <div className="flex-1" />
          <Button variant="ghost" size="sm" onClick={toggleSelectAll}>
            {selectedSources.length === filteredSources.length ? "取消全选" : "全选"}
          </Button>
        </div>
      </motion.div>

      {/* Row 5: Trend Chart */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="card-surface p-5"
      >
        <SectionHeader
          icon={Activity}
          title="近 24 小时采集量趋势"
          description="按数据类型分组展示，异常时间段标红"
        />
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={{ stroke: "hsl(var(--border))" }}
              />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={{ stroke: "hsl(var(--border))" }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={{ stroke: "hsl(var(--border))" }}
                domain={[80, 100]}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px" }} />
              {trendData.some((d) => d.isAbnormal) && (
                <ReferenceLine yAxisId="left" x="14:00" stroke="#ef4444" strokeDasharray="3 3" />
              )}
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="行情"
                fill="#3b82f6"
                fillOpacity={0.2}
                stroke="#3b82f6"
                strokeWidth={2}
              />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="基本面"
                fill="#8b5cf6"
                fillOpacity={0.2}
                stroke="#8b5cf6"
                strokeWidth={2}
              />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="宏观"
                fill="#f59e0b"
                fillOpacity={0.2}
                stroke="#f59e0b"
                strokeWidth={2}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="成功率"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Row 6: Alert Records */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-surface p-5"
      >
        <SectionHeader
          icon={Bell}
          title="最近告警记录"
          description="显示需要关注的采集异常"
          action={
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              查看全部
              <ChevronRight className="w-4 h-4" />
            </Button>
          }
        />
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="py-3 px-2 text-left font-medium text-muted-foreground">告警时间</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground">级别</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground">数据源名称</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground">告警类型</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground">告警内容</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground">状态</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground">操作</th>
              </tr>
            </thead>
            <tbody>
              {alertRecords.map((alert) => (
                <tr key={alert.id} className="border-b border-border/50 hover:bg-muted/30">
                  <td className="py-3 px-2 font-mono">{alert.time}</td>
                  <td className="py-3 px-2 text-center">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-[10px] font-bold",
                        alert.level === "P0" && "bg-red-500/10 text-red-600",
                        alert.level === "P1" && "bg-amber-500/10 text-amber-600",
                        alert.level === "P2" && "bg-blue-500/10 text-blue-600"
                      )}
                    >
                      {alert.level}
                    </span>
                  </td>
                  <td className="py-3 px-2 font-medium">{alert.sourceName}</td>
                  <td className="py-3 px-2 text-muted-foreground">{alert.alertType}</td>
                  <td className="py-3 px-2 max-w-[300px] truncate" title={alert.content}>
                    {alert.content}
                  </td>
                  <td className="py-3 px-2 text-center">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-[10px]",
                        alert.status === "未处理" && "bg-red-500/10 text-red-600",
                        alert.status === "处理中" && "bg-amber-500/10 text-amber-600",
                        alert.status === "已解决" && "bg-emerald-500/10 text-emerald-600"
                      )}
                    >
                      {alert.status}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <Button variant="ghost" size="sm" className="h-7 px-2 text-xs">
                        标记处理
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 px-2 text-xs">
                        详情
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 7: Process Monitor */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="card-surface p-5"
      >
        <SectionHeader
          icon={Cpu}
          title="采集进程监控"
          description="实时监控所有采集进程的运行状态"
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {processInfos.map((process) => (
            <div
              key={process.id}
              className={cn(
                "p-4 rounded-lg border",
                process.status === "运行中"
                  ? "bg-emerald-500/5 border-emerald-500/20"
                  : process.status === "已停止"
                  ? "bg-gray-500/5 border-gray-500/20"
                  : "bg-amber-500/5 border-amber-500/20"
              )}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{process.name}</span>
                </div>
                <span
                  className={cn(
                    "px-2 py-0.5 rounded text-[10px] font-medium",
                    process.status === "运行中" && "bg-emerald-500/10 text-emerald-600",
                    process.status === "已停止" && "bg-gray-500/10 text-gray-600",
                    process.status === "重启中" && "bg-amber-500/10 text-amber-600"
                  )}
                >
                  {process.status}
                </span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">PID</span>
                  <span className="font-mono">{process.pid}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">CPU</span>
                  <span className="font-mono">{process.cpuUsage}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">内存</span>
                  <span className="font-mono">{process.memoryUsage} MB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">运行时长</span>
                  <span>{process.runTime}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">启动时间</span>
                  <span className="font-mono">{process.startTime}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">最后心跳</span>
                  <span>{process.lastHeartbeat}</span>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
                <Button variant="ghost" size="sm" className="flex-1 h-7 text-xs gap-1">
                  <RotateCw className="w-3 h-3" />
                  重启
                </Button>
                <Button variant="ghost" size="sm" className="flex-1 h-7 text-xs gap-1">
                  <FileText className="w-3 h-3" />
                  日志
                </Button>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Log Drawer */}
      <AnimatePresence>
        {showLogDrawer && selectedLogSource && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40"
              onClick={() => setShowLogDrawer(false)}
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed right-0 top-0 h-full w-[500px] bg-background border-l border-border z-50 overflow-hidden flex flex-col"
            >
              <div className="flex items-center justify-between p-4 border-b border-border">
                <div>
                  <h3 className="font-semibold">{selectedLogSource.name} - 日志</h3>
                  <p className="text-xs text-muted-foreground">实时日志输出</p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setShowLogDrawer(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex-1 overflow-auto p-4 font-mono text-xs bg-muted/30">
                <div className="space-y-1">
                  <p className="text-emerald-600">[17:08:32] INFO: 数据采集完成，本次采集 125 条记录</p>
                  <p className="text-emerald-600">[17:08:29] INFO: 开始采集 Tushare 行情数据...</p>
                  <p className="text-muted-foreground">[17:08:26] DEBUG: 连接到数据源服务器</p>
                  <p className="text-emerald-600">[17:08:23] INFO: 数据采集完成，本次采集 118 条记录</p>
                  <p className="text-amber-600">[17:08:20] WARN: 网络延迟略高，当前 380ms</p>
                  <p className="text-emerald-600">[17:08:17] INFO: 开始采集 Tushare 行情数据...</p>
                  <p className="text-muted-foreground">[17:08:14] DEBUG: 心跳检测正常</p>
                  <p className="text-emerald-600">[17:08:11] INFO: 数据采集完成，本次采集 132 条记录</p>
                  <p className="text-emerald-600">[17:08:08] INFO: 开始采集 Tushare 行情数据...</p>
                  <p className="text-red-600">[17:08:05] ERROR: 连接超时，正在重试...</p>
                  <p className="text-emerald-600">[17:08:02] INFO: 重试成功，恢复正常采集</p>
                </div>
              </div>
              <div className="p-4 border-t border-border flex items-center gap-2">
                <Button variant="outline" size="sm" className="gap-2">
                  <Download className="w-4 h-4" />
                  导出日志
                </Button>
                <Button variant="outline" size="sm" className="gap-2">
                  <RefreshCw className="w-4 h-4" />
                  刷新
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Toast Notification */}
      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-6 right-6 bg-foreground text-background px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span className="text-sm">{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Edit Dialog */}
      <AnimatePresence>
        {showEditDialog && editingSource && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40"
              onClick={() => setShowEditDialog(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-background rounded-xl shadow-xl border border-border z-50 p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold">编辑数据源配置</h3>
                <button
                  onClick={() => setShowEditDialog(false)}
                  className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center hover:bg-muted/80"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">数据源名称</label>
                  <Input defaultValue={editingSource.name} className="h-9" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-muted-foreground mb-1.5 block">数据类型</label>
                    <Select defaultValue={editingSource.type}>
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="行情">行情数据</SelectItem>
                        <SelectItem value="基本面">基本面数据</SelectItem>
                        <SelectItem value="宏观">宏观数据</SelectItem>
                        <SelectItem value="另类">另类数据</SelectItem>
                        <SelectItem value="交易所">交易所数据</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground mb-1.5 block">供应商</label>
                    <Input defaultValue={editingSource.provider} className="h-9" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-muted-foreground mb-1.5 block">计划开始时间</label>
                    <Input defaultValue={editingSource.planStartTime} className="h-9" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground mb-1.5 block">采集周期</label>
                    <Input defaultValue={editingSource.collectCycle} className="h-9" />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-border">
                <Button variant="outline" onClick={() => setShowEditDialog(false)}>
                  取消
                </Button>
                <Button onClick={() => {
                  setShowEditDialog(false);
                  setToastMessage(`${editingSource.name} 配置已保存`);
                  setShowToast(true);
                  setTimeout(() => setShowToast(false), 3000);
                }}>
                  保存配置
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
