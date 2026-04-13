"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  RefreshCw,
  HardDrive,
  Database,
  Server,
  Trash2,
  Download,
  Upload,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Archive,
  FileText,
  BarChart3,
  Activity,
  Settings,
  Zap,
  Calendar,
  FolderOpen,
  HardDriveDownload,
  HardDriveUpload,
  Layers,
  PieChart,
  ScrollText,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from "recharts";

// Storage overview data
const storageOverview = {
  totalCapacity: 2000, // GB
  usedCapacity: 1200, // GB
  availableCapacity: 800, // GB
  usagePercent: 60,
  estimatedDays: 45,
  todayGrowth: 12.5, // GB
  largestFile: { name: 'data_2026.parquet', size: 85 }, // GB
  totalFiles: 125450,
};

// Storage distribution
const storageDistribution = [
  { 
    name: 'Parquet 数据文件', 
    value: 650, 
    percent: 54, 
    color: '#3b82f6',
    sub: [
      { name: '行情数据', value: 320 },
      { name: '基本面数据', value: 180 },
      { name: '宏观数据', value: 90 },
      { name: '另类数据', value: 60 },
    ]
  },
  { 
    name: '日志文件', 
    value: 280, 
    percent: 23, 
    color: '#f97316',
    sub: [
      { name: '系统日志', value: 150 },
      { name: '应用日志', value: 80 },
      { name: '审计日志', value: 50 },
    ]
  },
  { 
    name: '备份文件', 
    value: 220, 
    percent: 18, 
    color: '#22c55e',
    sub: [
      { name: '数据库备份', value: 150 },
      { name: '配置备份', value: 40 },
      { name: '模型备份', value: 30 },
    ]
  },
  { 
    name: '临时文件', 
    value: 50, 
    percent: 5, 
    color: '#ef4444',
    sub: [
      { name: '缓存文件', value: 30 },
      { name: '下载临时', value: 20 },
    ]
  },
];

// NAS Backup Status
const nasBackup = {
  server: '192.168.1.100',
  status: 'normal', // normal/error/disconnected
  lastBackup: '2026-03-21 02:00:35',
  backupSize: 850, // GB
  backupDuration: '2 小时 35 分钟',
  compressionRate: 65, // %
  bandwidth: 125, // MB/s
  nextBackup: '2026-03-22 02:00',
  retentionPolicy: '保留最近 30 天，每月第一个周日全量备份',
};

// Storage Details
const storageDetails = [
  { path: '/data/market/2026/', type: 'Parquet', size: 320, files: 45200, percent: 26, lastModified: '17:08', lastAccessed: '17:08', status: 'normal' },
  { path: '/data/fundamental/', type: 'Parquet', size: 180, files: 28500, percent: 15, lastModified: '09:00', lastAccessed: '17:05', status: 'normal' },
  { path: '/logs/system/', type: '日志', size: 150, files: 12800, percent: 12, lastModified: '17:08', lastAccessed: '17:08', status: 'cleanable' },
  { path: '/backup/daily/', type: '备份', size: 220, files: 30, percent: 18, lastModified: '02:35', lastAccessed: '08:00', status: 'normal' },
  { path: '/tmp/cache/', type: '临时', size: 30, files: 8500, percent: 2.5, lastModified: '17:05', lastAccessed: '17:05', status: 'cleanable' },
  { path: '/models/strategy/', type: '模型', size: 45, files: 125, percent: 3.7, lastModified: '03-20', lastAccessed: '17:00', status: 'normal' },
];

// Cleanup Suggestions
const cleanupSuggestions = {
  tempFiles: {
    total: 65, // GB
    items: [
      { name: '缓存文件', size: 30, reason: '超过 7 天未访问' },
      { name: '下载临时', size: 20, reason: '下载完成的残留文件' },
      { name: '日志压缩', size: 15, reason: '超过 30 天的旧日志' },
    ],
  },
  archivableFiles: {
    total: 335, // GB
    items: [
      { name: '历史行情（>1 年）', size: 180 },
      { name: '旧备份文件（>30 天）', size: 120 },
      { name: '旧模型文件', size: 35 },
    ],
  },
  duplicateFiles: {
    count: 125,
    size: 8.5, // GB
  },
};

// Auto Cleanup Configuration
const autoCleanupConfig = {
  triggerConditions: {
    usageThreshold: 80, // %
    availableThreshold: 200, // GB
    daysThreshold: 30, // days
  },
  cleanupPriority: ['临时文件', '旧日志文件', '旧备份文件', '历史数据'],
  retentionRules: {
    tempFiles: 7, // days
    logFiles: 90, // days
    backupFiles: 30, // days
    historicalData: 365, // days
  },
  notifications: {
    enabled: true,
    channels: ['feishu', 'email'],
    sendReport: true,
  },
};

// Storage nodes
const storageNodes = [
  {
    id: "node-1",
    name: "主存储节点",
    type: "SSD",
    totalCapacity: 1024,
    usedCapacity: 768,
    status: "normal",
    temperature: 42,
    health: 98,
    uptime: "365天",
    lastCheck: "5分钟前",
  },
  {
    id: "node-2",
    name: "备份存储节点",
    type: "HDD",
    totalCapacity: 2048,
    usedCapacity: 512,
    status: "normal",
    temperature: 38,
    health: 95,
    uptime: "180天",
    lastCheck: "5分钟前",
  },
  {
    id: "node-3",
    name: "冷数据归档",
    type: "HDD",
    totalCapacity: 4096,
    usedCapacity: 256,
    status: "normal",
    temperature: 35,
    health: 92,
    uptime: "90天",
    lastCheck: "1小时前",
  },
];

// Database tables
const databaseTables = [
  { name: "daily_quotes", records: 125000000, size: 280, growthRate: 2.5, lastUpdate: "实时" },
  { name: "minute_klines", records: 850000000, size: 420, growthRate: 5.2, lastUpdate: "实时" },
  { name: "tick_data", records: 2500000000, size: 680, growthRate: 8.5, lastUpdate: "实时" },
  { name: "financial_reports", records: 15000000, size: 45, growthRate: 0.8, lastUpdate: "1小时前" },
  { name: "macro_indicators", records: 5000000, size: 12, growthRate: 0.3, lastUpdate: "6小时前" },
  { name: "system_logs", records: 50000000, size: 86, growthRate: 1.2, lastUpdate: "实时" },
];

// Storage trend data (30 days)
const storageTrendData = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  const baseUsed = 1400 + i * 4.5;
  return {
    date: `${date.getMonth() + 1}/${date.getDate()}`,
    used: Math.round(baseUsed + Math.random() * 20),
    written: Math.round(15 + Math.random() * 10),
    deleted: Math.round(5 + Math.random() * 5),
  };
});

// Cleanup tasks
const cleanupTasks = [
  { id: 1, name: "清理过期日志", schedule: "每日 02:00", lastRun: "今日 02:00", freedSpace: 2.5, status: "completed" },
  { id: 2, name: "压缩历史数据", schedule: "每周日 03:00", lastRun: "3天前", freedSpace: 15.8, status: "completed" },
  { id: 3, name: "归档冷数据", schedule: "每月1日", lastRun: "15天前", freedSpace: 45.2, status: "completed" },
  { id: 4, name: "清理临时文件", schedule: "每日 04:00", lastRun: "今日 04:00", freedSpace: 0.8, status: "completed" },
];

// Section Header Component
function SectionHeader({ 
  icon: Icon, 
  title, 
  description 
}: { 
  icon: typeof HardDrive; 
  title: string; 
  description: string;
}) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
        <Icon className="w-4 h-4 text-primary" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <p className="text-[11px] text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

// KPI Card Component
interface KPICardProps {
  icon: typeof HardDrive;
  label: string;
  value: string;
  subValue?: string;
  color?: "default" | "green" | "red" | "yellow" | "blue";
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

// Storage Node Card
function StorageNodeCard({ node }: { node: typeof storageNodes[0] }) {
  const usagePercent = (node.usedCapacity / node.totalCapacity) * 100;
  const statusConfig = {
    normal: { color: "bg-emerald-500", text: "健康" },
    healthy: { color: "bg-emerald-500", text: "健康" },
    warning: { color: "bg-amber-500", text: "警告" },
    error: { color: "bg-red-500", text: "异常" },
  };

  return (
    <div className="card-surface p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <HardDrive className="w-4 h-4 text-primary shrink-0" />
          <h4 className="text-sm font-semibold text-foreground whitespace-nowrap">{node.name}</h4>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground whitespace-nowrap">
            {node.type}
          </span>
          <div className="flex items-center gap-1">
            <span className={cn("w-2 h-2 rounded-full shrink-0", statusConfig[node.status as keyof typeof statusConfig].color)} />
            <span className="text-[10px] text-muted-foreground whitespace-nowrap">{statusConfig[node.status as keyof typeof statusConfig].text}</span>
          </div>
        </div>
      </div>

      <div className="flex-1">
        <div className="flex items-center justify-between text-[11px] mb-1">
          <span className="text-muted-foreground">容量使用</span>
          <span className="font-mono text-foreground">
            {node.usedCapacity} / {node.totalCapacity} GB
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden mb-3">
          <div 
            className={cn(
              "h-full rounded-full transition-all",
              usagePercent > 80 ? "bg-red-500" : usagePercent > 60 ? "bg-amber-500" : "bg-emerald-500"
            )}
            style={{ width: `${usagePercent}%` }}
          />
        </div>

        <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
          <div className="flex items-center justify-between gap-1">
            <span className="text-muted-foreground whitespace-nowrap">温度</span>
            <span className="font-mono text-foreground whitespace-nowrap">{node.temperature}°C</span>
          </div>
          <div className="flex items-center justify-between gap-1">
            <span className="text-muted-foreground whitespace-nowrap">健康度</span>
            <span className="font-mono text-foreground whitespace-nowrap">{node.health}%</span>
          </div>
          <div className="flex items-center justify-between gap-1">
            <span className="text-muted-foreground whitespace-nowrap">运行时间</span>
            <span className="font-mono text-foreground whitespace-nowrap">{node.uptime}</span>
          </div>
          <div className="flex items-center justify-between gap-1">
            <span className="text-muted-foreground whitespace-nowrap">最后检查</span>
            <span className="font-mono text-foreground whitespace-nowrap">{node.lastCheck}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3">
        <Button variant="outline" size="sm" className="flex-1 h-7 text-[10px]">
          <Activity className="w-3 h-3 mr-1" />
          详情
        </Button>
        <Button variant="outline" size="sm" className="h-7 text-[10px] px-2">
          <Settings className="w-3 h-3" />
        </Button>
      </div>
    </div>
  );
}

export function StorageView() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [timeRange, setTimeRange] = useState("30d");

  const formatBytes = (gb: number) => {
    if (gb >= 1024) return `${(gb / 1024).toFixed(1)} TB`;
    return `${gb} GB`;
  };

  const COLORS = storageDistribution.map(d => d.color);

  return (
    <div className="space-y-5 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">存储容量监控</h1>
          <p className="text-xs text-muted-foreground mt-0.5">监控存储使用情况、数据库表空间和清理任务</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">自动刷新</span>
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
          </div>
          <Button variant="outline" size="sm" className="h-8 text-xs">
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            刷新全部
          </Button>
        </div>
      </div>

      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-4 sm:grid-cols-8 gap-3">
        <KPICard icon={HardDrive} label="总容量" value={formatBytes(storageOverview.totalCapacity)} />
        <KPICard icon={Database} label="已使用" value={formatBytes(storageOverview.usedCapacity)} color="blue" />
        <KPICard icon={FolderOpen} label="可用空间" value={formatBytes(storageOverview.availableCapacity)} color="green" />
        <KPICard icon={PieChart} label="使用率" value={`${storageOverview.usagePercent}%`} color="yellow" />
        <KPICard icon={Calendar} label="预计天数" value={`${storageOverview.estimatedDays}`} subValue="天" />
        <KPICard icon={TrendingUp} label="今日增长" value={`${storageOverview.todayGrowth}`} subValue="GB" />
        <KPICard icon={Archive} label="文件总数" value={`${(storageOverview.totalFiles / 1000).toFixed(0)}`} subValue="K" />
        <KPICard icon={HardDrive} label="最大文件" value={`${storageOverview.largestFile.size}`} subValue="GB" />
      </div>

      {/* Row 2: Storage Distribution (40%) & Storage Nodes (60%) */}
      <div className="grid gap-4" style={{ gridTemplateColumns: '2fr 3fr' }}>
        {/* Storage Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-surface p-4"
        >
          <SectionHeader 
            icon={Layers} 
            title="存储分布" 
            description="按数据类型的存储占用"
          />
          <div className="flex items-center gap-6">
            <div className="w-40 h-40">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                  <Pie
                    data={storageDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {storageDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => [`${value} GB`, '容量']}
                    contentStyle={{ 
                      background: 'hsl(var(--card))', 
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '11px'
                    }}
                  />
                </RechartsPieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 space-y-2">
              {storageDistribution.map((item) => {
                const percent = item.percent;
                return (
                  <div key={item.name} className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-sm shrink-0" 
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-[11px] text-foreground flex-1">{item.name}</span>
                    <span className="text-[11px] font-mono text-muted-foreground">{item.value} GB</span>
                    <span className="text-[10px] font-mono text-muted-foreground w-10 text-right">{percent}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* Storage Nodes */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-surface p-4"
        >
          <SectionHeader 
            icon={Server} 
            title="存储节点" 
            description="各存储节点状态监控"
          />
          <div className="overflow-x-auto pb-2">
            <div className="flex gap-3" style={{ minWidth: 'max-content' }}>
              {storageNodes.map(node => (
                <div key={node.id} className="w-[200px] shrink-0">
                  <StorageNodeCard node={node} />
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Row 3: Database Tables */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-surface p-4"
      >
        <SectionHeader 
          icon={Database} 
          title="数据库表空间" 
          description="各数据表的存储占用和增长情况"
        />
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 px-2 text-muted-foreground font-medium">表名</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium">记录数</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium">占用空间</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium">日增长率</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium">最后更新</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {databaseTables.map((table, index) => (
                <tr key={table.name} className={cn("border-b border-border/50", index % 2 === 0 && "bg-muted/20")}>
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-2">
                      <Database className="w-3.5 h-3.5 text-primary" />
                      <span className="font-mono text-foreground">{table.name}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 text-right font-mono text-foreground">
                    {(table.records / 1000000).toFixed(1)}M
                  </td>
                  <td className="py-2.5 px-2 text-right font-mono text-foreground">
                    {table.size} GB
                  </td>
                  <td className="py-2.5 px-2 text-right">
                    <span className={cn(
                      "font-mono",
                      table.growthRate > 5 ? "text-amber-600" : "text-emerald-600"
                    )}>
                      +{table.growthRate}%
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center text-muted-foreground">{table.lastUpdate}</td>
                  <td className="py-2.5 px-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                        <Archive className="w-3 h-3 mr-1" />
                        归档
                      </Button>
                      <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                        <Trash2 className="w-3 h-3 mr-1" />
                        清理
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 4: Storage Path Details & Cleanup Suggestions */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-surface p-4"
      >
        <SectionHeader 
          icon={FolderOpen} 
          title="存储路径详情" 
          description="各数据路径的占用空间和状态"
        />
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 px-2 text-muted-foreground font-medium">路径</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium">类型</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium">容量</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium">文件数</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium">占比</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium">最后修改</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium">最后访问</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium">状态</th>
              </tr>
            </thead>
            <tbody>
              {storageDetails.map((detail, index) => (
                <tr key={detail.path} className={cn("border-b border-border/50", index % 2 === 0 && "bg-muted/20")}>
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-2">
                      <FolderOpen className="w-3.5 h-3.5 text-primary shrink-0" />
                      <span className="font-mono text-foreground">{detail.path}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 text-center text-muted-foreground">{detail.type}</td>
                  <td className="py-2.5 px-2 text-right font-mono text-foreground">{detail.size} GB</td>
                  <td className="py-2.5 px-2 text-right font-mono text-foreground">{(detail.files / 1000).toFixed(0)}K</td>
                  <td className="py-2.5 px-2 text-right font-mono text-foreground">{detail.percent}%</td>
                  <td className="py-2.5 px-2 text-center text-muted-foreground">{detail.lastModified}</td>
                  <td className="py-2.5 px-2 text-center text-muted-foreground">{detail.lastAccessed}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded-full font-medium",
                      detail.status === 'normal' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-amber-500/10 text-amber-600'
                    )}>
                      {detail.status === 'normal' ? '正常' : '可清理'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 5: Storage Trend & Cleanup Suggestions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Storage Trend */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card-surface p-4"
        >
          <div className="flex items-center justify-between mb-4">
            <SectionHeader 
              icon={TrendingUp} 
              title="存储趋势" 
              description="近30日存储变化"
            />
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-24 h-7 text-[11px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">近7天</SelectItem>
                <SelectItem value="30d">近30天</SelectItem>
                <SelectItem value="90d">近90天</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={storageTrendData}>
                <defs>
                  <linearGradient id="usedGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis 
                  tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${value}GB`}
                />
                <Tooltip 
                  contentStyle={{ 
                    background: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '11px'
                  }}
                  formatter={(value: number, name: string) => {
                    const labels: Record<string, string> = { used: '已使用', written: '写入', deleted: '删除' };
                    return [`${value} GB`, labels[name] || name];
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="used" 
                  stroke="#3b82f6" 
                  fill="url(#usedGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card-surface p-4"
        >
          <SectionHeader 
            icon={Server} 
            title="NAS 备份" 
            description="备份服务器状态监控"
          />
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
              <div className="flex items-center gap-2">
                <div className={cn("w-2 h-2 rounded-full", nasBackup.status === 'normal' ? 'bg-emerald-500' : 'bg-red-500')} />
                <span className="text-[11px] font-mono text-foreground">{nasBackup.server}</span>
              </div>
              <span className="text-[10px] px-2 py-1 rounded bg-emerald-500/10 text-emerald-600 font-medium">
                {nasBackup.status === 'normal' ? '正常' : '异常'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-muted-foreground">最后备份</span>
                <span className="font-mono text-foreground">{nasBackup.lastBackup}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">备份大小</span>
                <span className="font-mono text-foreground">{nasBackup.backupSize} GB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">备份耗时</span>
                <span className="font-mono text-foreground">{nasBackup.backupDuration}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">压缩率</span>
                <span className="font-mono text-foreground">{nasBackup.compressionRate}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">带宽</span>
                <span className="font-mono text-foreground">{nasBackup.bandwidth} MB/s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">下次备份</span>
                <span className="font-mono text-foreground">{nasBackup.nextBackup}</span>
              </div>
            </div>
            <div className="flex items-start gap-2 p-2.5 rounded-lg bg-blue-500/5 border border-blue-500/20">
              <div className="w-7 h-7 rounded-md bg-blue-500/10 flex items-center justify-center shrink-0">
                <ScrollText className="w-3.5 h-3.5 text-blue-600" />
              </div>
              <p className="text-[10px] text-blue-600 leading-relaxed self-center"><span className="font-medium">保留策略：</span>{nasBackup.retentionPolicy}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Cleanup Tasks */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="card-surface p-4"
      >
        <SectionHeader 
          icon={Trash2} 
          title="清理任务" 
          description="自动清理任务执行状态"
        />
        <div className="space-y-2">
          {cleanupTasks.map(task => (
            <div key={task.id} className="flex items-center gap-3 p-2.5 rounded-lg bg-muted/30">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                <Trash2 className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[12px] font-medium text-foreground">{task.name}</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                </div>
                <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {task.schedule}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {task.lastRun}
                  </span>
                </div>
              </div>
              <div className="text-right shrink-0">
                <span className="text-[11px] font-mono text-emerald-600">-{task.freedSpace} GB</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <span className="text-[11px] text-emerald-600">本月累计释放空间</span>
          <span className="text-sm font-semibold font-mono text-emerald-600">64.3 GB</span>
        </div>
      </motion.div>

      {/* Row 6: Alerts Configuration */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="card-surface p-4"
      >
        <SectionHeader 
          icon={AlertTriangle} 
          title="容量预警配置" 
          description="设置存储容量预警阈值和通知方式"
        />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/20">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-[12px] font-medium text-red-600">P0 紧急</span>
              <span className="text-[10px] text-muted-foreground ml-auto">{"<"}10%</span>
            </div>
            <p className="text-[11px] text-muted-foreground">飞书 + 邮件</p>
          </div>
          <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-[12px] font-medium text-amber-600">P1 重要</span>
              <span className="text-[10px] text-muted-foreground ml-auto">{"<"}20%</span>
            </div>
            <p className="text-[11px] text-muted-foreground">飞书 + 邮件</p>
          </div>
          <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-[12px] font-medium text-blue-600">P2 提示</span>
              <span className="text-[10px] text-muted-foreground ml-auto">{"<"}30%</span>
            </div>
            <p className="text-[11px] text-muted-foreground">飞书</p>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-between p-3 rounded-lg bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-muted-foreground">自动扩容</span>
              <Switch defaultChecked />
            </div>
            <span className="text-[11px] text-muted-foreground">|</span>
            <span className="text-[11px] text-muted-foreground">剩余空间 {"<"}10% 时自动扩容 500GB</span>
          </div>
          <Button variant="outline" size="sm" className="h-7 text-[10px]">
            <Settings className="w-3 h-3 mr-1" />
            配置
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
