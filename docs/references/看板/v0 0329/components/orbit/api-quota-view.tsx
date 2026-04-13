"use client";

import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
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
  Wallet,
  CreditCard,
  Receipt,
  Calendar,
  Clock,
  Bot,
  Zap,
  MessageSquare,
  Moon,
  Sparkles,
  Brain,
  TestTube,
  FileText,
  RefreshCw,
  Database,
  Server,
  ArrowRightLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  TrendingUp,
  BarChart3,
  Coins,
  Activity,
  Shield,
  Bell,
  Settings,
  Plus,
  ExternalLink,
  Download,
  Loader2,
  CheckCircle2 as CheckCircleIcon,
  AlertTriangle as AlertIcon,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  Legend,
  Bar,
  BarChart,
} from "recharts";

// KPI Card Component
interface KPICardProps {
  icon: typeof Wallet;
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

// Model Card Component
interface AIModel {
  id: string;
  name: string;
  icon: typeof Bot;
  role: "primary" | "secondary" | "backup";
  remainingTokens: number;
  totalTokens: number;
  todayUsed: number;
  cost: number;
  requestCount: number;
  avgResponse: number;
  status: "normal" | "warning" | "error";
}

function ModelCard({ model, onTest, onSwitch }: { model: AIModel; onTest: () => void; onSwitch: () => void }) {
  const usagePercent = model.totalTokens > 0
    ? ((model.totalTokens - model.remainingTokens) / model.totalTokens) * 100
    : 0;
  
  const roleLabels = {
    primary: { text: "主决策", color: "bg-blue-500/10 text-blue-600 border-blue-500/20" },
    secondary: { text: "二次核验", color: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" },
    backup: { text: "备用", color: "bg-gray-500/10 text-gray-600 border-gray-500/20" },
  };

  const statusColors = {
    normal: "bg-emerald-500",
    warning: "bg-amber-500",
    error: "bg-red-500",
  };

  const Icon = model.icon;

  return (
    <div className="card-surface p-4 h-full flex flex-col">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-lg bg-accent flex items-center justify-center shrink-0">
            <Icon className="w-5 h-5 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-foreground whitespace-nowrap">{model.name}</h4>
              <span className={cn("w-2 h-2 rounded-full shrink-0", statusColors[model.status])} />
            </div>
            <span className={cn("text-[10px] px-1.5 py-0.5 rounded border font-medium whitespace-nowrap", roleLabels[model.role].color)}>
              {roleLabels[model.role].text}
            </span>
          </div>
        </div>
      </div>

      {/* Usage Progress */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-[11px] mb-1">
          <span className="text-muted-foreground whitespace-nowrap">Token 消耗</span>
          <span className="font-mono text-foreground">{usagePercent.toFixed(1)}%</span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div 
            className={cn(
              "h-full rounded-full transition-all",
              usagePercent > 80 ? "bg-red-500" : usagePercent > 50 ? "bg-amber-500" : "bg-emerald-500"
            )}
            style={{ width: `${usagePercent}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-x-2 gap-y-1 mb-3 text-[11px]">
        <div className="flex justify-between">
          <span className="text-muted-foreground">剩余</span>
          <span className="font-mono text-foreground">{(model.remainingTokens / 1000).toFixed(0)}K</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">今日</span>
          <span className="font-mono text-foreground">{(model.todayUsed / 1000).toFixed(0)}K</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">消费</span>
          <span className="font-mono text-foreground">¥{model.cost.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">响应</span>
          <span className="font-mono text-foreground">{model.avgResponse}s</span>
        </div>
      </div>

      {/* Actions - Always at bottom */}
      <div className="flex items-center gap-2 mt-auto">
        <Button variant="outline" size="sm" className="flex-1 h-7 text-[11px]" onClick={onTest}>
          <TestTube className="w-3 h-3 mr-1" />
          测试
        </Button>
        <Button variant="outline" size="sm" className="flex-1 h-7 text-[11px]" onClick={onSwitch}>
          <FileText className="w-3 h-3 mr-1" />
          日志
        </Button>
      </div>
    </div>
  );
}

// Data Source Row Component
interface DataSourceConfig {
  type: string;
  primary: string;
  secondary: string;
  tertiary: string | null;
  current: "primary" | "secondary" | "tertiary";
  status: "normal" | "delayed" | "failed";
  lastCollect: string;
}

function DataSourceRow({ source, onSwitch }: { source: DataSourceConfig; onSwitch: () => void }) {
  const statusConfig = {
    normal: { color: "bg-emerald-500", text: "正常", textColor: "text-emerald-600" },
    delayed: { color: "bg-amber-500", text: "延迟", textColor: "text-amber-600" },
    failed: { color: "bg-red-500", text: "失败", textColor: "text-red-600" },
  };

  const currentConfig = {
    primary: { text: "主", color: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" },
    secondary: { text: "副", color: "bg-amber-500/10 text-amber-600 border-amber-500/20" },
    tertiary: { text: "三", color: "bg-blue-500/10 text-blue-600 border-blue-500/20" },
  };

  return (
    <tr className="border-b border-border/50 hover:bg-muted/30 transition-colors">
      <td className="py-2.5 px-3 text-xs font-medium text-foreground">{source.type}</td>
      <td className="py-2.5 px-3 text-xs text-muted-foreground">{source.primary}</td>
      <td className="py-2.5 px-3 text-xs text-muted-foreground">{source.secondary}</td>
      <td className="py-2.5 px-3 text-xs text-muted-foreground">{source.tertiary || "-"}</td>
      <td className="py-2.5 px-3">
        <span className={cn("text-[10px] px-1.5 py-0.5 rounded border font-medium", currentConfig[source.current].color)}>
          {currentConfig[source.current].text}
        </span>
      </td>
      <td className="py-2.5 px-3">
        <div className="flex items-center gap-1.5">
          <span className={cn("w-2 h-2 rounded-full", statusConfig[source.status].color)} />
          <span className={cn("text-xs", statusConfig[source.status].textColor)}>{statusConfig[source.status].text}</span>
        </div>
      </td>
      <td className="py-2.5 px-3 text-xs text-muted-foreground">{source.lastCollect}</td>
      <td className="py-2.5 px-3">
        <Button variant="outline" size="sm" className="h-6 text-[10px] px-2" onClick={onSwitch}>
          <ArrowRightLeft className="w-3 h-3 mr-1" />
          切换
        </Button>
      </td>
    </tr>
  );
}

// API Provider Card Component
interface APIProvider {
  id: string;
  name: string;
  type: "付费" | "免费";
  totalQuota: number | null;
  usedQuota: number;
  remainingQuota: number | null;
  usagePercent: number;
  resetDate: string | null;
  daysUntilReset: number | null;
  status: "normal" | "warning" | "error";
}

function APIProviderCard({ provider }: { provider: APIProvider }) {
  const statusConfig = {
    normal: { color: "bg-emerald-500", text: "正常" },
    warning: { color: "bg-amber-500", text: "警告" },
    error: { color: "bg-red-500", text: "异常" },
  };

  return (
    <div className="card-surface p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Server className="w-4 h-4 text-primary shrink-0" />
          <h4 className="text-sm font-semibold text-foreground whitespace-nowrap">{provider.name}</h4>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={cn(
            "text-[10px] px-1.5 py-0.5 rounded font-medium whitespace-nowrap",
            provider.type === "付费" ? "bg-blue-500/10 text-blue-600" : "bg-gray-500/10 text-gray-600"
          )}>
            {provider.type}
          </span>
          <div className="flex items-center gap-1">
            <span className={cn("w-2 h-2 rounded-full shrink-0", statusConfig[provider.status].color)} />
            <span className="text-[10px] text-muted-foreground whitespace-nowrap">{statusConfig[provider.status].text}</span>
          </div>
        </div>
      </div>

      <div className="flex-1">
        {provider.totalQuota && (
          <>
            <div className="flex items-center justify-between text-[11px] mb-1">
              <span className="text-muted-foreground whitespace-nowrap">剩余额度</span>
              <span className="font-mono text-foreground whitespace-nowrap">
                {provider.remainingQuota?.toLocaleString()} / {provider.totalQuota.toLocaleString()} 次
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden mb-2">
              <div 
                className={cn(
                  "h-full rounded-full transition-all",
                  provider.usagePercent > 80 ? "bg-red-500" : provider.usagePercent > 50 ? "bg-amber-500" : "bg-emerald-500"
                )}
                style={{ width: `${provider.usagePercent}%` }}
              />
            </div>
            <p className="text-[10px] text-muted-foreground whitespace-nowrap">
              重置日期：{provider.resetDate}（还剩 {provider.daysUntilReset} 天）
            </p>
          </>
        )}

        {!provider.totalQuota && (
          <div>
            <p className="text-[11px] text-muted-foreground whitespace-nowrap">今日使用：{provider.usedQuota.toLocaleString()} 次</p>
            <p className="text-[10px] text-muted-foreground mt-1 whitespace-nowrap">无配额限制</p>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 mt-3">
        <Button variant="outline" size="sm" className="flex-1 h-7 text-[10px]">
          <Plus className="w-3 h-3 mr-1" />
          充值
        </Button>
        <Button variant="outline" size="sm" className="flex-1 h-7 text-[10px]">
          <TestTube className="w-3 h-3 mr-1" />
          测试
        </Button>
        <Button variant="outline" size="sm" className="h-7 text-[10px] px-2">
          <Settings className="w-3 h-3" />
        </Button>
      </div>
    </div>
  );
}

// Mock Data
const accountOverview = {
  balance: 8520.50,
  totalRecharge: 50000,
  totalSpent: 41479.50,
  monthBudget: { used: 8250, limit: 5000, percent: 60 },
  estimatedDays: 45,
};

const aiModels: AIModel[] = [
  {
    id: "deepseek_v3",
    name: "DeepSeek V3",
    icon: Brain,
    role: "primary",
    remainingTokens: 872500,
    totalTokens: 1000000,
    todayUsed: 125000,
    cost: 125.50,
    requestCount: 1258,
    avgResponse: 1.25,
    status: "normal",
  },
  {
    id: "qwen_max",
    name: "Qwen Max",
    icon: MessageSquare,
    role: "secondary",
    remainingTokens: 902500,
    totalTokens: 1000000,
    todayUsed: 97500,
    cost: 98.50,
    requestCount: 758,
    avgResponse: 1.58,
    status: "normal",
  },
  {
    id: "kimi_2_5",
    name: "Kimi 2.5",
    icon: Moon,
    role: "backup",
    remainingTokens: 417500,
    totalTokens: 500000,
    todayUsed: 82500,
    cost: 68.50,
    requestCount: 558,
    avgResponse: 1.85,
    status: "normal",
  },
  {
    id: "gpt_4o",
    name: "GPT-4o",
    icon: Sparkles,
    role: "backup",
    remainingTokens: 250000,
    totalTokens: 500000,
    todayUsed: 45000,
    cost: 89.00,
    requestCount: 320,
    avgResponse: 2.15,
    status: "warning",
  },
  {
    id: "claude_3",
    name: "Claude 3",
    icon: Zap,
    role: "backup",
    remainingTokens: 180000,
    totalTokens: 300000,
    todayUsed: 28000,
    cost: 56.00,
    requestCount: 185,
    avgResponse: 1.95,
    status: "normal",
  },
  {
    id: "glm_4",
    name: "GLM-4",
    icon: Bot,
    role: "backup",
    remainingTokens: 650000,
    totalTokens: 800000,
    todayUsed: 35000,
    cost: 42.00,
    requestCount: 420,
    avgResponse: 1.45,
    status: "normal",
  },
];

const dataSources: DataSourceConfig[] = [
  {
    type: "行情数据",
    primary: "Tushare",
    secondary: "AkShare",
    tertiary: null,
    current: "primary",
    status: "normal",
    lastCollect: "5 秒前",
  },
  {
    type: "宏观数据",
    primary: "Wind",
    secondary: "Choice",
    tertiary: "Tushare",
    current: "secondary",
    status: "delayed",
    lastCollect: "2 分钟前",
  },
  {
    type: "基本面数据",
    primary: "Tushare",
    secondary: "Choice",
    tertiary: null,
    current: "primary",
    status: "normal",
    lastCollect: "1 分钟前",
  },
  {
    type: "交易所数据",
    primary: "交易所",
    secondary: "Tushare",
    tertiary: null,
    current: "primary",
    status: "normal",
    lastCollect: "3 秒前",
  },
  {
    type: "另类数据",
    primary: "Wind",
    secondary: "AkShare",
    tertiary: "Choice",
    current: "primary",
    status: "normal",
    lastCollect: "30 秒前",
  },
];

const apiProviders: APIProvider[] = [
  {
    id: "tushare",
    name: "Tushare Pro",
    type: "付费",
    totalQuota: 10000,
    usedQuota: 8500,
    remainingQuota: 1500,
    usagePercent: 85,
    resetDate: "2026-04-01",
    daysUntilReset: 16,
    status: "warning",
  },
  {
    id: "akshare",
    name: "AkShare",
    type: "免费",
    totalQuota: null,
    usedQuota: 1250,
    remainingQuota: null,
    usagePercent: 0,
    resetDate: null,
    daysUntilReset: null,
    status: "normal",
  },
  {
    id: "wind",
    name: "Wind 金融终端",
    type: "付费",
    totalQuota: 50000,
    usedQuota: 32000,
    remainingQuota: 18000,
    usagePercent: 64,
    resetDate: "2026-04-01",
    daysUntilReset: 16,
    status: "normal",
  },
  {
    id: "choice",
    name: "Choice 东方财富",
    type: "付费",
    totalQuota: 20000,
    usedQuota: 8500,
    remainingQuota: 11500,
    usagePercent: 42.5,
    resetDate: "2026-04-01",
    daysUntilReset: 16,
    status: "normal",
  },
  {
    id: "exchange",
    name: "交易所直连",
    type: "付费",
    totalQuota: 100000,
    usedQuota: 45000,
    remainingQuota: 55000,
    usagePercent: 45,
    resetDate: "2026-04-01",
    daysUntilReset: 16,
    status: "normal",
  },
];

const rechargeRecords = [
  {
    time: "2026-03-15 10:30",
    amount: 10000,
    method: "银行转账",
    transactionId: "TXN20260315001",
    status: "成功",
    note: "季度预算充值",
  },
  {
    time: "2026-02-01 14:20",
    amount: 5000,
    method: "支付宝",
    transactionId: "TXN20260201002",
    status: "成功",
    note: "月度预算充值",
  },
  {
    time: "2026-01-15 09:15",
    amount: 15000,
    method: "微信支付",
    transactionId: "TXN20260115003",
    status: "成功",
    note: "年度预算充值",
  },
  {
    time: "2025-12-20 16:45",
    amount: 8000,
    method: "银行转账",
    transactionId: "TXN20251220004",
    status: "成功",
    note: "API 额度补充",
  },
];

// Token consumption statistics data
const tokenStats = [
  { model: "DeepSeek V3", inputTokens: 85000, outputTokens: 42500, total: 127500, amount: 125.50, requests: 1258, avgResponse: "1.25s" },
  { model: "Qwen Max", inputTokens: 65000, outputTokens: 32500, total: 97500, amount: 98.50, requests: 758, avgResponse: "1.58s" },
  { model: "Kimi 2.5", inputTokens: 55000, outputTokens: 27500, total: 82500, amount: 68.50, requests: 558, avgResponse: "1.85s" },
  { model: "GPT-4o", inputTokens: 30000, outputTokens: 15000, total: 45000, amount: 89.00, requests: 320, avgResponse: "2.15s" },
  { model: "Claude 3", inputTokens: 18000, outputTokens: 10000, total: 28000, amount: 56.00, requests: 185, avgResponse: "1.95s" },
  { model: "GLM-4", inputTokens: 25000, outputTokens: 10000, total: 35000, amount: 42.00, requests: 420, avgResponse: "1.45s" },
];

// Usage trend data (30 days)
const usageTrendData = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  return {
    date: `${date.getMonth() + 1}/${date.getDate()}`,
    deepseek: Math.round(2000 + Math.random() * 1000),
    qwen: Math.round(1500 + Math.random() * 800),
    kimi: Math.round(1000 + Math.random() * 500),
    apiCalls: Math.round(500 + Math.random() * 200),
  };
});

export function APIQuotaView() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [primaryModel, setPrimaryModel] = useState("deepseek_v3");
  const [secondaryModel, setSecondaryModel] = useState<string | null>("qwen_max");
  const [showSwitchDialog, setShowSwitchDialog] = useState(false);
  const [pendingSwitch, setPendingSwitch] = useState<{ type: string; from: string; to: string } | null>(null);
  const [isSwitching, setIsSwitching] = useState(false);
  const [switchResult, setSwitchResult] = useState<{ success: boolean; message: string } | null>(null);

  // Alert settings
  const [alertP0, setAlertP0] = useState(true);
  const [alertP1, setAlertP1] = useState(true);
  const [alertP2, setAlertP2] = useState(false);
  const [autoRenew, setAutoRenew] = useState(true);

  const handleModelTest = (modelId: string) => {
    console.log("Testing model:", modelId);
    // TODO: Implement test logic
  };

  const handleSourceSwitch = (sourceType: string) => {
    const source = dataSources.find(s => s.type === sourceType);
    if (source) {
      setPendingSwitch({
        type: sourceType,
        from: source.current === "primary" ? source.primary : source.secondary,
        to: source.current === "primary" ? source.secondary : source.primary,
      });
      setShowSwitchDialog(true)
    }
  };

  const confirmSwitch = async () => {
    if (!pendingSwitch) return;
    
    setIsSwitching(true);
    setSwitchResult(null);
    
    // 模拟切换操作
    await new Promise(r => setTimeout(r, 1200));
    
    // 模拟成功切换（90%概率成功）
    const isSuccess = Math.random() > 0.1;
    setIsSwitching(false);
    setSwitchResult({
      success: isSuccess,
      message: isSuccess 
        ? `已切换到 ${pendingSwitch.to}` 
        : "切换失败，请重试"
    });
    
    if (isSuccess) {
      setTimeout(() => {
        setShowSwitchDialog(false);
        setPendingSwitch(null);
        setSwitchResult(null);
      }, 2000);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-[1600px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">API 配额与模型管理</h1>
          <p className="text-sm text-muted-foreground mt-1">管理 AI 模型、数据源、API 配额和账户</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>自动刷新</span>
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
          </div>
          <Button variant="outline" size="sm" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            刷新全部
          </Button>
        </div>
      </div>

      {/* Row 1: Account Overview KPIs */}
      <div className="grid grid-cols-5 gap-3">
        <KPICard icon={Wallet} label="账户余额" value={`¥${accountOverview.balance.toLocaleString()}`} color="blue" />
        <KPICard icon={CreditCard} label="累计充值" value={`¥${accountOverview.totalRecharge.toLocaleString()}`} color="green" />
        <KPICard icon={Receipt} label="累计消费" value={`¥${accountOverview.totalSpent.toLocaleString()}`} color="red" />
        <KPICard icon={BarChart3} label="本月预算" value={`${accountOverview.monthBudget.percent}%`} subValue="已用" color="yellow" />
        <KPICard icon={Calendar} label="预计可用" value={accountOverview.estimatedDays} subValue="天" />
      </div>

      {/* Row 2: AI Model Management */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-5"
      >
        <SectionHeader 
          icon={Bot} 
          title="AI 决策模型配置" 
          description="本地策略生成后，通过选择的在线模型进行二次核验"
        />
        
        {/* Model Switcher */}
        <div className="flex items-center gap-6 mb-4 p-3 bg-muted/30 rounded-lg">
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground whitespace-nowrap">主决策模型：</span>
            <Select value={primaryModel} onValueChange={setPrimaryModel}>
              <SelectTrigger className="w-40 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {aiModels.map(m => (
                  <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="h-7 text-[10px]">
              <TestTube className="w-3 h-3 mr-1" />
              测试连接
            </Button>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground whitespace-nowrap">二次核验模型：</span>
            <Select value={secondaryModel || "off"} onValueChange={(v) => setSecondaryModel(v === "off" ? null : v)}>
              <SelectTrigger className="w-40 h-8 text-xs">
                <SelectValue placeholder="关闭" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="off">关闭</SelectItem>
                {aiModels.map(m => (
                  <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="h-7 text-[10px]" disabled={!secondaryModel}>
              <TestTube className="w-3 h-3 mr-1" />
              测试连接
            </Button>
          </div>
        </div>

        {/* Model Cards Grid - Horizontal scroll on narrow screens */}
        <div className="overflow-x-auto pb-2">
          <div className="flex gap-3" style={{ minWidth: 'max-content' }}>
            {aiModels.map(model => (
              <div key={model.id} className="w-[180px] shrink-0">
                <ModelCard 
                  model={model} 
                  onTest={() => handleModelTest(model.id)}
                  onSwitch={() => {}}
                />
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Row 3: Token Consumption Statistics */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="card-surface p-5"
      >
        <SectionHeader 
          icon={Activity} 
          title="Token 消耗统计" 
          description="各模型今日 Token 使用详情"
          action={
            <Button variant="outline" size="sm" className="h-7 text-[10px]">
              <Download className="w-3 h-3 mr-1" />
              导出
            </Button>
          }
        />
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">模型名称</th>
                <th className="py-2.5 px-3 text-right font-medium text-muted-foreground">输入 Token</th>
                <th className="py-2.5 px-3 text-right font-medium text-muted-foreground">输出 Token</th>
                <th className="py-2.5 px-3 text-right font-medium text-muted-foreground">总计</th>
                <th className="py-2.5 px-3 text-right font-medium text-muted-foreground">金额</th>
                <th className="py-2.5 px-3 text-right font-medium text-muted-foreground">请求次数</th>
                <th className="py-2.5 px-3 text-right font-medium text-muted-foreground">平均响应</th>
              </tr>
            </thead>
            <tbody>
              {tokenStats.map((stat, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-muted/30">
                  <td className="py-2.5 px-3 font-medium text-foreground">{stat.model}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-muted-foreground">{stat.inputTokens.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-muted-foreground">{stat.outputTokens.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-foreground">{stat.total.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-foreground">¥{stat.amount.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-muted-foreground">{stat.requests.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-muted-foreground">{stat.avgResponse}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 4: Data Source Management */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-surface p-5"
      >
        <SectionHeader 
          icon={Database} 
          title="数据采集源配置" 
          description="双源/三源采集，主源失败自动切换副源"
        />
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">数据类型</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">主源</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">副源</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">第三源</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">当前</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">状态</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">最后采集</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">操作</th>
              </tr>
            </thead>
            <tbody>
              {dataSources.map((source, i) => (
                <DataSourceRow key={i} source={source} onSwitch={() => handleSourceSwitch(source.type)} />
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 5: API Provider Quotas */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="card-surface p-5"
      >
        <SectionHeader 
          icon={Server} 
          title="API 供应商配额" 
          description="各数据供应商 API 使用情况"
        />
        <div className="overflow-x-auto pb-2">
          <div className="flex gap-3" style={{ minWidth: 'max-content' }}>
            {apiProviders.map(provider => (
              <div key={provider.id} className="w-[220px] shrink-0">
                <APIProviderCard provider={provider} />
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Row 6: Recharge Records */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-surface p-5"
      >
        <SectionHeader 
          icon={Coins} 
          title="充值记录" 
          description="近期充值历史"
          action={
            <Button variant="outline" size="sm" className="h-7 text-[10px]">
              <Plus className="w-3 h-3 mr-1" />
              新增充值
            </Button>
          }
        />
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">充值时间</th>
                <th className="py-2.5 px-3 text-right font-medium text-muted-foreground">充值金额</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">支付方式</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">交易 ID</th>
                <th className="py-2.5 px-3 text-center font-medium text-muted-foreground">状态</th>
                <th className="py-2.5 px-3 text-left font-medium text-muted-foreground">备注</th>
                <th className="py-2.5 px-3 text-center font-medium text-muted-foreground">操作</th>
              </tr>
            </thead>
            <tbody>
              {rechargeRecords.map((record, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-muted/30">
                  <td className="py-2.5 px-3 text-muted-foreground">{record.time}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-foreground">¥{record.amount.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-muted-foreground">{record.method}</td>
                  <td className="py-2.5 px-3 font-mono text-muted-foreground">{record.transactionId}</td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded font-medium",
                      record.status === "成功" ? "bg-emerald-500/10 text-emerald-600" : 
                      record.status === "处理中" ? "bg-amber-500/10 text-amber-600" : "bg-red-500/10 text-red-600"
                    )}>
                      {record.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-muted-foreground">{record.note}</td>
                  <td className="py-2.5 px-3 text-center">
                    <Button variant="ghost" size="sm" className="h-6 text-[10px] px-2">
                      <ExternalLink className="w-3 h-3" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 7: Usage Trend Chart */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="card-surface p-5"
      >
        <SectionHeader 
          icon={TrendingUp} 
          title="近 30 日使用趋势" 
          description="Token 消耗与 API 调用量趋势"
        />
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={usageTrendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
              <XAxis dataKey="date" stroke="rgba(0,0,0,0.4)" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis yAxisId="left" stroke="rgba(0,0,0,0.4)" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis yAxisId="right" orientation="right" stroke="rgba(0,0,0,0.4)" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255,255,255,0.95)', 
                  border: '1px solid rgba(0,0,0,0.1)',
                  borderRadius: '8px',
                  fontSize: '11px'
                }} 
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Area yAxisId="left" type="monotone" dataKey="deepseek" name="DeepSeek" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} />
              <Area yAxisId="left" type="monotone" dataKey="qwen" name="Qwen" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.3} />
              <Area yAxisId="left" type="monotone" dataKey="kimi" name="Kimi" stackId="1" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.3} />
              <Line yAxisId="right" type="monotone" dataKey="apiCalls" name="API 调用" stroke="#EF4444" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Row 8: Alert Settings */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card-surface p-5"
      >
        <SectionHeader 
          icon={Shield} 
          title="配额预警配置" 
          description="配置配额不足时的告警和自动续订"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Alert Levels */}
          <div>
            <h4 className="text-xs font-semibold text-foreground mb-3">预警级别</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-red-500" />
                  <div>
                    <p className="text-xs font-medium text-foreground">P0 紧急 ({'<'}10%)</p>
                    <p className="text-[10px] text-muted-foreground">飞书 + 邮件 + 短信</p>
                  </div>
                </div>
                <Switch checked={alertP0} onCheckedChange={setAlertP0} />
              </div>
              <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  <div>
                    <p className="text-xs font-medium text-foreground">P1 重要 ({'<'}30%)</p>
                    <p className="text-[10px] text-muted-foreground">飞书 + 邮件</p>
                  </div>
                </div>
                <Switch checked={alertP1} onCheckedChange={setAlertP1} />
              </div>
              <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-blue-500" />
                  <div>
                    <p className="text-xs font-medium text-foreground">P2 提示 ({'<'}50%)</p>
                    <p className="text-[10px] text-muted-foreground">飞书</p>
                  </div>
                </div>
                <Switch checked={alertP2} onCheckedChange={setAlertP2} />
              </div>
            </div>
          </div>

          {/* Auto Renewal */}
          <div>
            <h4 className="text-xs font-semibold text-foreground mb-3">自动续订</h4>
            <div className="p-4 bg-muted/30 rounded-lg space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-foreground">开启自动续订</p>
                  <p className="text-[10px] text-muted-foreground">配额低于阈值时自动充值</p>
                </div>
                <Switch checked={autoRenew} onCheckedChange={setAutoRenew} />
              </div>
              {autoRenew && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">触发阈值</span>
                    <Select defaultValue="20">
                      <SelectTrigger className="w-24 h-7 text-[10px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="10">{'<'}10%</SelectItem>
                        <SelectItem value="20">{'<'}20%</SelectItem>
                        <SelectItem value="30">{'<'}30%</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">月度预算上限</span>
                    <Select defaultValue="2000">
                      <SelectTrigger className="w-24 h-7 text-[10px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1000">¥1,000</SelectItem>
                        <SelectItem value="2000">¥2,000</SelectItem>
                        <SelectItem value="5000">¥5,000</SelectItem>
                        <SelectItem value="10000">¥10,000</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Switch Dialog */}
      {showSwitchDialog && pendingSwitch && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {switchResult ? (switchResult.success ? '切换成功' : '切换失败') : '确认切换数据源？'}
            </h3>
            {switchResult ? (
              <div className={cn(
                "flex items-center gap-2",
                switchResult.success ? "text-[#3FB950]" : "text-[#FF3B30]"
              )}>
                {switchResult.success ? (
                  <CheckCircleIcon className="w-5 h-5" />
                ) : (
                  <AlertIcon className="w-5 h-5" />
                )}
                <span>{switchResult.message}</span>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">
                从 <span className="font-medium text-foreground">{pendingSwitch?.from}</span> 切换到{" "}
                <span className="font-medium text-foreground">{pendingSwitch?.to}</span>
              </p>
            )}
          </div>
          <div className="flex gap-2 justify-end">
            {!switchResult ? (
              <>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowSwitchDialog(false);
                    setPendingSwitch(null);
                  }}
                  disabled={isSwitching}
                >
                  取消
                </Button>
                <Button 
                  onClick={confirmSwitch} 
                  disabled={isSwitching}
                  className="flex items-center gap-2"
                >
                  {isSwitching ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      切换中...
                    </>
                  ) : (
                    '确认切换'
                  )}
                </Button>
              </>
            ) : (
              <Button 
                onClick={() => {
                  setShowSwitchDialog(false);
                  setPendingSwitch(null);
                  setSwitchResult(null);
                }}
              >
                关闭
              </Button>
            )}
          </div>
          </div>
        </div>
      )}
    </div>
  );
}
