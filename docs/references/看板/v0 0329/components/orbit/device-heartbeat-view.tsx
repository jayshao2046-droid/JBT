"use client";

import React, { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
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
  Server,
  Monitor,
  Cpu,
  HardDrive,
  Wifi,
  WifiOff,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Terminal,
  Play,
  Square,
  Eye,
  Download,
  Bell,
  Settings,
  Thermometer,
  Fan,
  Network,
  ArrowUpRight,
  ArrowDownRight,
  RotateCw,
  ExternalLink,
  FileText,
  Zap,
  Timer,
  ChevronRight,
  Loader2,
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
  ReferenceLine,
  Area,
  ComposedChart,
} from "recharts";

// KPI Card Component
interface KPICardProps {
  icon: typeof Server;
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
  icon: typeof Server;
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

// Settings Section Component (same pattern as settings-view)
interface SettingsSectionProps {
  icon: typeof Server;
  title: string;
  description: string;
  children: React.ReactNode;
}

function SettingsSection({ icon: Icon, title, description, children }: SettingsSectionProps) {
  return (
    <div className="card-surface p-5">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shrink-0">
          <Icon className="w-4.5 h-4.5 text-primary" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
        </div>
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

// Settings Row Component
interface SettingsRowProps {
  label: string;
  description?: string;
  children: React.ReactNode;
}

function SettingsRow({ label, description, children }: SettingsRowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border/50 last:border-b-0">
      <div className="flex-1 min-w-0 pr-4">
        <p className="text-xs font-medium text-foreground">{label}</p>
        {description && <p className="text-[11px] text-muted-foreground mt-0.5">{description}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

// Progress Bar Component
function ProgressBar({ value, color = "blue", label }: { value: number; color?: string; label?: string }) {
  const getColor = (val: number) => {
    if (val > 80) return "bg-red-500";
    if (val >= 60) return "bg-amber-500";
    return "bg-emerald-500";
  };

  return (
    <div className="flex items-center gap-2 whitespace-nowrap">
      {label && <span className="text-[10px] text-muted-foreground w-8">{label}</span>}
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", getColor(value))}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-[10px] font-mono text-muted-foreground w-8 text-right">{value}%</span>
    </div>
  );
}

// Device Types
interface Device {
  id: string;
  name: string;
  role: "决策端" | "策略端" | "数据端" | "交易端";
  model: string;
  internalIp: string;
  externalIp: string;
  status: "online" | "offline" | "warning";
  uptime: string;
  lastHeartbeat: string;
  processes: number;
  cpu: number;
  memory: number;
  disk: number;
  networkUp: string;
  networkDown: string;
  temperature: number;
  fanSpeed: "低速" | "中速" | "高速";
  ssdMounted?: string;
}

// Alert Types
interface AlertRecord {
  id: string;
  time: string;
  level: "P0" | "P1" | "P2";
  deviceName: string;
  alertType: "离线" | "心跳超时" | "资源异常";
  content: string;
  duration: string;
  status: "未处理" | "处理中" | "已解决" | "已忽略";
}

// Mock Data
const devices: Device[] = [
  {
    id: "1",
    name: "决策端",
    role: "决策端",
    model: "MacBook Pro 14\" M3 Pro",
    internalIp: "192.168.1.101",
    externalIp: "100.86.182.114",
    status: "online",
    uptime: "72 小时 14 分钟",
    lastHeartbeat: "5 秒前",
    processes: 12,
    cpu: 45,
    memory: 67,
    disk: 58,
    networkUp: "125MB/s",
    networkDown: "285MB/s",
    temperature: 42,
    fanSpeed: "中速",
  },
  {
    id: "2",
    name: "交易端",
    role: "交易端",
    model: "Mac Studio M2 Ultra",
    internalIp: "192.168.1.102",
    externalIp: "100.82.139.52",
    status: "offline",
    uptime: "156 小时 32 分钟",
    lastHeartbeat: "8 秒前",
    processes: 18,
    cpu: 72,
    memory: 84,
    disk: 65,
    networkUp: "85MB/s",
    networkDown: "125MB/s",
    temperature: 48,
    fanSpeed: "中速",
    ssdMounted: "1TB",
  },
  {
    id: "3",
    name: "数据端",
    role: "数据端",
    model: "Mac Mini M1",
    internalIp: "192.168.1.103",
    externalIp: "100.78.156.89",
    status: "online",
    uptime: "312 小时 45 分钟",
    lastHeartbeat: "3 秒前",
    processes: 15,
    cpu: 23,
    memory: 45,
    disk: 42,
    networkUp: "250MB/s",
    networkDown: "350MB/s",
    temperature: 38,
    fanSpeed: "低速",
  },
];

const alertRecords: AlertRecord[] = [
  {
    id: "1",
    time: "03-20 14:30",
    level: "P1",
    deviceName: "决策端",
    alertType: "心跳超时",
    content: "心跳延迟 > 60 秒",
    duration: "5 分钟",
    status: "已解决",
  },
  {
    id: "2",
    time: "03-19 09:15",
    level: "P0",
    deviceName: "交易端",
    alertType: "离线",
    content: "设备失联",
    duration: "15 分钟",
    status: "已解决",
  },
  {
    id: "3",
    time: "03-18 22:00",
    level: "P2",
    deviceName: "数据端",
    alertType: "资源异常",
    content: "内存使用率 > 90%",
    duration: "30 分钟",
    status: "已忽略",
  },
  {
    id: "4",
    time: "03-17 16:45",
    level: "P1",
    deviceName: "交易端",
    alertType: "资源异常",
    content: "CPU 使用率 > 85%",
    duration: "10 分钟",
    status: "已解决",
  },
];

// Heartbeat History Data (24 hours)
const heartbeatHistory = Array.from({ length: 24 }, (_, i) => {
  const hour = i.toString().padStart(2, "0") + ":00";
  // Simulate some anomalies
  const hasAnomaly = i === 9 || i === 14;
  return {
    hour,
    决策端: hasAnomaly && i === 9 ? 120 : Math.random() * 20 + 5,
    策略端: hasAnomaly && i === 14 ? 180 : Math.random() * 25 + 8,
    数据端: Math.random() * 15 + 3,
    isAnomaly: hasAnomaly,
  };
});

export function DeviceHeartbeatView() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [alertFilter, setAlertFilter] = useState("全部");
  
  // Alert config states
  const [heartbeatInterval, setHeartbeatInterval] = useState("30");
  const [timeoutThreshold, setTimeoutThreshold] = useState("60");
  const [offlineThreshold, setOfflineThreshold] = useState("5");
  const [retryCount, setRetryCount] = useState("3");
  const [autoRestart, setAutoRestart] = useState(true);
  const [restartWait, setRestartWait] = useState("5");
  const [restartFailNotify, setRestartFailNotify] = useState(true);
  
  // Notification settings
  const [p0Feishu, setP0Feishu] = useState(true);
  const [p0Email, setP0Email] = useState(true);
  const [p1Feishu, setP1Feishu] = useState(true);
  const [p1Email, setP1Email] = useState(true);
  const [p2Feishu, setP2Feishu] = useState(true);
  const [p2Email, setP2Email] = useState(false);

  // 自动刷新
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date().toLocaleTimeString());

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

  const getStatusColor = (status: Device["status"]) => {
    switch (status) {
      case "online": return "bg-[#3FB950]";
      case "offline": return "bg-[#FF3B30]";
      case "warning": return "bg-amber-500";
    }
  };

  const getStatusText = (status: Device["status"]) => {
    switch (status) {
      case "online": return "在线";
      case "offline": return "离线";
      case "warning": return "异常";
    }
  };

  const getRoleBadgeColor = (role: Device["role"]) => {
    switch (role) {
      case "决策端": return "bg-blue-500/10 text-blue-600 border-blue-500/20";
      case "策略端": return "bg-purple-500/10 text-purple-600 border-purple-500/20";
      case "数据端": return "bg-emerald-500/10 text-emerald-600 border-emerald-500/20";
      case "交易端": return "bg-amber-500/10 text-amber-600 border-amber-500/20";
    }
  };

  const getLevelColor = (level: AlertRecord["level"]) => {
    switch (level) {
      case "P0": return "bg-red-500/10 text-red-600";
      case "P1": return "bg-amber-500/10 text-amber-600";
      case "P2": return "bg-blue-500/10 text-blue-600";
    }
  };

  const getAlertStatusColor = (status: AlertRecord["status"]) => {
    switch (status) {
      case "未处理": return "text-red-600";
      case "处理中": return "text-amber-600";
      case "已解决": return "text-emerald-600";
      case "已忽略": return "text-muted-foreground";
    }
  };

  const filteredAlerts = useMemo(() => {
    if (alertFilter === "全部") return alertRecords;
    return alertRecords.filter(a => a.status === alertFilter);
  }, [alertFilter]);

  // Calculate KPIs
  const onlineCount = devices.filter(d => d.status === "online").length;
  const offlineCount = devices.filter(d => d.status === "offline").length;
  const avgUptime = Math.round(devices.reduce((acc, d) => {
    const hours = parseInt(d.uptime.split(" ")[0]) || 0;
    return acc + hours;
  }, 0) / devices.length);
  const lastHeartbeat = devices.reduce((min, d) => {
    const seconds = parseInt(d.lastHeartbeat) || 999;
    return seconds < min ? seconds : min;
  }, 999);

  return (
    <div className="p-6 space-y-6 max-w-[1600px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">设备心跳监控</h1>
          <p className="text-sm text-muted-foreground mt-1">监控所有设备的运行状态和心跳信息</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>���动刷新</span>
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
          </div>
          <Button variant="outline" size="sm" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            刷新全部
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="w-4 h-4" />
            导出数据
          </Button>
        </div>
      </div>

      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        <KPICard icon={Server} label="设备总数" value={devices.length} subValue="台" />
        <KPICard icon={CheckCircle2} label="在线设备" value={onlineCount} subValue="台" color="green" />
        <KPICard icon={XCircle} label="离线设备" value={offlineCount} subValue="台" color={offlineCount > 0 ? "red" : "default"} />
        <KPICard icon={Clock} label="平均运行时长" value={avgUptime} subValue="小时" color="blue" />
        <KPICard icon={Activity} label="最后心跳" value={lastHeartbeat} subValue="秒前" color="green" />
        <KPICard icon={AlertTriangle} label="异常次数（今日）" value="0" subValue="次" color="default" />
      </div>

      {/* Row 2: Device Cards */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <SectionHeader
          icon={Monitor}
          title="设备列表"
          description="点击设备卡片查看详细信息"
        />
        <div className="overflow-x-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {devices.map((device) => (
              <motion.div
                key={device.id}
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className={cn(
                  "card-surface p-4 cursor-pointer transition-all duration-200 hover:shadow-md min-w-[320px]",
                  selectedDevice?.id === device.id && "ring-2 ring-primary"
                )}
                onClick={() => setSelectedDevice(selectedDevice?.id === device.id ? null : device)}
              >
                {/* Header - Only show status badge, not role badge */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className={cn("w-2 h-2 rounded-full", getStatusColor(device.status))} />
                    <span className="text-sm font-semibold text-foreground whitespace-nowrap">{device.name}</span>
                  </div>
                  <span className={cn(
                    "px-2 py-0.5 text-[10px] font-medium rounded whitespace-nowrap flex items-center gap-1",
                    device.status === "online" ? "bg-emerald-500/10 text-emerald-600" :
                    device.status === "offline" ? "bg-red-500/10 text-red-600" :
                    "bg-amber-500/10 text-amber-600"
                  )}>
                    <span className={cn("w-1.5 h-1.5 rounded-full", getStatusColor(device.status))} />
                    {getStatusText(device.status)}
                  </span>
                </div>

                {/* IP Addresses */}
                <div className="space-y-1 mb-3 text-[11px]">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground w-14">内网 IP:</span>
                    <span className="text-foreground font-mono whitespace-nowrap">{device.internalIp}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground w-14">外网 IP:</span>
                    <span className="text-foreground font-mono whitespace-nowrap">{device.externalIp}</span>
                  </div>
                </div>

                {/* Stats - Grid layout */}
                <div className="grid grid-cols-3 gap-2 mb-3 text-[11px]">
                  <div className="whitespace-nowrap">
                    <span className="text-muted-foreground block">运行时长</span>
                    <span className="text-foreground font-medium">{device.uptime}</span>
                  </div>
                  <div className="whitespace-nowrap">
                    <span className="text-muted-foreground block">最后心跳</span>
                    <span className="text-emerald-600 font-medium">{device.lastHeartbeat}</span>
                  </div>
                  <div className="whitespace-nowrap">
                    <span className="text-muted-foreground block">关键进程</span>
                    <span className="text-foreground font-medium">{device.processes} 个</span>
                  </div>
                </div>

                {/* Resource Usage - Longer progress bars */}
                <div className="space-y-1.5 mb-3">
                  <div className="flex items-center gap-2 whitespace-nowrap">
                    <span className="text-[10px] text-muted-foreground w-8">CPU</span>
                    <div className="w-40 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all duration-500", 
                          device.cpu > 80 ? "bg-red-500" : device.cpu >= 60 ? "bg-amber-500" : "bg-emerald-500"
                        )}
                        style={{ width: `${device.cpu}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground w-8 text-right">{device.cpu}%</span>
                  </div>
                  <div className="flex items-center gap-2 whitespace-nowrap">
                    <span className="text-[10px] text-muted-foreground w-8">内存</span>
                    <div className="w-40 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all duration-500", 
                          device.memory > 80 ? "bg-red-500" : device.memory >= 60 ? "bg-amber-500" : "bg-emerald-500"
                        )}
                        style={{ width: `${device.memory}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground w-8 text-right">{device.memory}%</span>
                  </div>
                  <div className="flex items-center gap-2 whitespace-nowrap">
                    <span className="text-[10px] text-muted-foreground w-8">磁盘</span>
                    <div className="w-40 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all duration-500", 
                          device.disk > 80 ? "bg-red-500" : device.disk >= 60 ? "bg-amber-500" : "bg-emerald-500"
                        )}
                        style={{ width: `${device.disk}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground w-8 text-right">{device.disk}%</span>
                  </div>
                </div>

                {/* Network */}
                <div className="flex items-center text-[11px] mb-3 whitespace-nowrap gap-4">
                  <div className="flex items-center gap-1">
                    <ArrowUpRight className="w-3 h-3 text-emerald-600" />
                    <span className="text-foreground font-mono">{device.networkUp}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <ArrowDownRight className="w-3 h-3 text-blue-600" />
                    <span className="text-foreground font-mono">{device.networkDown}</span>
                  </div>
                </div>

                {/* Temperature & Fan */}
                <div className="flex items-center text-[11px] border-t border-border/50 pt-3 gap-4">
                  <div className="flex items-center gap-1">
                    <Thermometer className="w-3 h-3 text-amber-500" />
                    <span className="text-foreground">{device.temperature}°C</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Fan className="w-3 h-3 text-blue-500" />
                    <span className="text-foreground">{device.fanSpeed}</span>
                  </div>
                  {device.ssdMounted && (
                    <div className="flex items-center gap-1">
                      <HardDrive className="w-3 h-3 text-muted-foreground" />
                      <span className="text-foreground whitespace-nowrap">SSD {device.ssdMounted}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
                  <Button variant="outline" size="sm" className="flex-1 h-7 text-xs gap-1">
                    <ExternalLink className="w-3 h-3" />
                    远程连接
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1 h-7 text-xs gap-1">
                    <RotateCw className="w-3 h-3" />
                    重启服务
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1 h-7 text-xs gap-1">
                    <FileText className="w-3 h-3" />
                    查看日志
                  </Button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Row 3: Heartbeat History Chart */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="card-surface p-5"
      >
        <SectionHeader
          icon={Activity}
          title="近 24 小时心跳状态"
          description="各设备心跳延迟趋势，包含异常事件标记"
        />
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={heartbeatHistory} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="anomalyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="hour"
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                label={{ value: "延迟 (秒)", angle: -90, position: "insideLeft", fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "11px",
                }}
                labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 500 }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              
              {/* Reference Lines for Thresholds */}
              <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="5 5" label={{ value: "正常 30s", position: "right", fill: "#22c55e", fontSize: 10 }} />
              <ReferenceLine y={60} stroke="#f59e0b" strokeDasharray="5 5" label={{ value: "警告 60s", position: "right", fill: "#f59e0b", fontSize: 10 }} />
              <ReferenceLine y={300} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "危险 300s", position: "right", fill: "#ef4444", fontSize: 10 }} />
              
              <Line type="monotone" dataKey="决策端" stroke="#3b82f6" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="策略端" stroke="#8b5cf6" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="数据端" stroke="#10b981" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Row 4: Alert Records Table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-surface p-5"
      >
        <SectionHeader
          icon={Bell}
          title="设备告警记录"
          description="设备离线、心跳超时、资源异常等告警"
          action={
            <Select value={alertFilter} onValueChange={setAlertFilter}>
              <SelectTrigger className="w-24 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="全部">全部</SelectItem>
                <SelectItem value="未处理">未处理</SelectItem>
                <SelectItem value="处理中">处理中</SelectItem>
                <SelectItem value="已解决">已解决</SelectItem>
                <SelectItem value="已忽略">已忽略</SelectItem>
              </SelectContent>
            </Select>
          }
        />
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">告警时间</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">级别</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">设备名称</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">告警类型</th>
                <th className="py-3 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">告警内容</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">持续时间</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">状态</th>
                <th className="py-3 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert) => (
                <tr key={alert.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                  <td className="py-3 px-2 whitespace-nowrap font-mono">{alert.time}</td>
                  <td className="py-3 px-2 text-center whitespace-nowrap">
                    <span className={cn("px-2 py-0.5 rounded text-[10px] font-medium", getLevelColor(alert.level))}>
                      {alert.level}
                    </span>
                  </td>
                  <td className="py-3 px-2 whitespace-nowrap text-foreground">{alert.deviceName}</td>
                  <td className="py-3 px-2 whitespace-nowrap">{alert.alertType}</td>
                  <td className="py-3 px-2">{alert.content}</td>
                  <td className="py-3 px-2 text-center whitespace-nowrap font-mono">{alert.duration}</td>
                  <td className="py-3 px-2 text-center whitespace-nowrap">
                    <span className={cn("font-medium", getAlertStatusColor(alert.status))}>{alert.status}</span>
                  </td>
                  <td className="py-3 px-2 text-center whitespace-nowrap">
                    <div className="flex items-center justify-center gap-1">
                      <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                        标记处理
                      </Button>
                      <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                        忽略
                      </Button>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                        <Eye className="w-3 h-3" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 5: Alert Configuration */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="grid grid-cols-1 lg:grid-cols-3 gap-4"
      >
        {/* Heartbeat Detection Config */}
        <SettingsSection
          icon={Timer}
          title="心跳检测"
          description="配置心跳检测参数"
        >
          <SettingsRow label="心跳间隔" description="设备发送心跳的时间间隔">
            <div className="flex items-center gap-1 w-[72px] justify-end">
              <Input
                value={heartbeatInterval}
                onChange={(e) => setHeartbeatInterval(e.target.value)}
                className="w-14 h-7 text-xs text-center"
              />
              <span className="text-xs text-muted-foreground w-4">秒</span>
            </div>
          </SettingsRow>
          <SettingsRow label="超时阈值" description="超过此时间判定为超时">
            <div className="flex items-center gap-1 w-[72px] justify-end">
              <Input
                value={timeoutThreshold}
                onChange={(e) => setTimeoutThreshold(e.target.value)}
                className="w-14 h-7 text-xs text-center"
              />
              <span className="text-xs text-muted-foreground w-4">秒</span>
            </div>
          </SettingsRow>
          <SettingsRow label="离线判定" description="无心跳超过此时间判定为离线">
            <div className="flex items-center gap-1 w-[72px] justify-end">
              <Input
                value={offlineThreshold}
                onChange={(e) => setOfflineThreshold(e.target.value)}
                className="w-14 h-7 text-xs text-center"
              />
              <span className="text-xs text-muted-foreground w-4">秒</span>
            </div>
          </SettingsRow>
          <SettingsRow label="重试次数" description="连接失败后的重试次数">
            <div className="flex items-center gap-1 w-[72px] justify-end">
              <Input
                value={retryCount}
                onChange={(e) => setRetryCount(e.target.value)}
                className="w-14 h-7 text-xs text-center"
              />
              <span className="text-xs text-muted-foreground w-4">次</span>
            </div>
          </SettingsRow>
        </SettingsSection>

        {/* Notification Settings */}
        <SettingsSection
          icon={Bell}
          title="通知设置"
          description="配置各级别告警的通知渠道"
        >
          <SettingsRow label="P0 紧急告警" description="设备离线等紧急情况">
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1.5 text-[11px]">
                <Switch checked={p0Feishu} onCheckedChange={setP0Feishu} className="scale-75" />
                <span>飞书</span>
              </label>
              <label className="flex items-center gap-1.5 text-[11px]">
                <Switch checked={p0Email} onCheckedChange={setP0Email} className="scale-75" />
                <span>邮件</span>
              </label>
            </div>
          </SettingsRow>
          <SettingsRow label="P1 重要告警" description="心跳超时等重要告警">
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1.5 text-[11px]">
                <Switch checked={p1Feishu} onCheckedChange={setP1Feishu} className="scale-75" />
                <span>飞书</span>
              </label>
              <label className="flex items-center gap-1.5 text-[11px]">
                <Switch checked={p1Email} onCheckedChange={setP1Email} className="scale-75" />
                <span>邮件</span>
              </label>
            </div>
          </SettingsRow>
          <SettingsRow label="P2 提示告警" description="资源异常等一般提示">
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1.5 text-[11px]">
                <Switch checked={p2Feishu} onCheckedChange={setP2Feishu} className="scale-75" />
                <span>飞书</span>
              </label>
              <label className="flex items-center gap-1.5 text-[11px]">
                <Switch checked={p2Email} onCheckedChange={setP2Email} className="scale-75" />
                <span>邮件</span>
              </label>
            </div>
          </SettingsRow>
        </SettingsSection>

        {/* Auto Recovery Settings */}
        <SettingsSection
          icon={Zap}
          title="自动恢复"
          description="配置自动恢复策略"
        >
          <SettingsRow label="自动重启服务" description="检测到服务异常时自动重启">
            <Switch checked={autoRestart} onCheckedChange={setAutoRestart} />
          </SettingsRow>
          <SettingsRow label="重启前等待" description="触发重启前的等待时间">
            <div className="flex items-center gap-1">
              <Input
                value={restartWait}
                onChange={(e) => setRestartWait(e.target.value)}
                className="w-16 h-7 text-xs text-center"
                disabled={!autoRestart}
              />
              <span className="text-xs text-muted-foreground">分钟</span>
            </div>
          </SettingsRow>
          <SettingsRow label="重启失败通知" description="自动重启失败时发送通知">
            <Switch checked={restartFailNotify} onCheckedChange={setRestartFailNotify} disabled={!autoRestart} />
          </SettingsRow>
        </SettingsSection>
      </motion.div>
    </div>
  );
}
