"use client";

import { useState } from "react";
import {
  Shield,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  Database,
  Wifi,
  WifiOff,
  RefreshCw,
  Bell,
  Calendar,
  FileText,
  Settings,
  Star,
  Eye,
  EyeOff,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

// ============================================
// 实时风险指标模块
// ============================================
interface RiskMetric {
  label: string;
  value: number;
  max: number;
  unit: string;
  status: "normal" | "warning" | "danger";
}

const riskMetrics: RiskMetric[] = [
  { label: "保证金使用率", value: 45.2, max: 100, unit: "%", status: "normal" },
  { label: "当日回撤", value: 3.5, max: 10, unit: "%", status: "normal" },
  { label: "杠杆倍数", value: 2.8, max: 5, unit: "x", status: "warning" },
  { label: "集中度风险", value: 28, max: 50, unit: "%", status: "normal" },
];

export function RealTimeRiskModule() {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "danger":
        return "text-[#EF4444]";
      case "warning":
        return "text-warning";
      default:
        return "text-[#22C55E]";
    }
  };

  const getProgressColor = (status: string) => {
    switch (status) {
      case "danger":
        return "bg-[#EF4444]";
      case "warning":
        return "bg-warning";
      default:
        return "bg-[#22C55E]";
    }
  };

  return (
    <div className="bg-card rounded-md p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-6 h-6 rounded-md bg-warning/10 flex items-center justify-center">
          <Shield className="w-3.5 h-3.5 text-warning" strokeWidth={1.5} />
        </div>
        <h3 className="text-[12px] font-medium text-foreground">实时风险指标</h3>
      </div>

      <div className="space-y-3">
        {riskMetrics.map((metric, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-muted-foreground">{metric.label}</span>
              <span className={cn("text-[11px] font-mono font-semibold", getStatusColor(metric.status))}>
                {metric.value}{metric.unit}
              </span>
            </div>
            <div className="h-1.5 bg-secondary/60 rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all", getProgressColor(metric.status))}
                style={{ width: `${(metric.value / metric.max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* 风险预警 */}
      <div className="mt-3 pt-3 border-t border-border/50">
        <div className="flex items-center gap-1.5 text-[10px] text-warning">
          <AlertTriangle className="w-3 h-3" />
          <span>杠杆倍数接近预警阈值</span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// 今日交易汇总模块
// ============================================
interface TradeSummary {
  label: string;
  value: number | string;
  change?: number;
  isPositive?: boolean;
}

const tradeSummaryData: TradeSummary[] = [
  { label: "交易笔数", value: 24, change: 8, isPositive: true },
  { label: "买入金额", value: "¥1,250,000", change: 15.2, isPositive: true },
  { label: "卖出金额", value: "¥980,000", change: -5.3, isPositive: false },
  { label: "手续费", value: "¥2,450" },
  { label: "已实现盈亏", value: "+¥47,500", change: 12.5, isPositive: true },
];

export function TodayTradingSummaryModule() {
  return (
    <div className="bg-card rounded-md p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center">
            <Activity className="w-3.5 h-3.5 text-primary" strokeWidth={1.5} />
          </div>
          <h3 className="text-[12px] font-medium text-foreground">今日交易汇总</h3>
        </div>
        <span className="text-[9px] text-muted-foreground/50 flex items-center gap-1">
          <Clock className="w-2.5 h-2.5" />
          实时更新
        </span>
      </div>

      <div className="space-y-2">
        {tradeSummaryData.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between py-1.5">
            <span className="text-[10px] text-muted-foreground">{item.label}</span>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-semibold text-foreground">
                {item.value}
              </span>
              {item.change !== undefined && (
                <span
                  className={cn(
                    "text-[9px] font-medium flex items-center",
                    item.isPositive ? "text-[#EF4444]" : "text-[#22C55E]"
                  )}
                >
                  {item.isPositive ? (
                    <ArrowUpRight className="w-2.5 h-2.5" />
                  ) : (
                    <ArrowDownRight className="w-2.5 h-2.5" />
                  )}
                  {Math.abs(item.change)}%
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================
// 数据源状态摘要模块
// ============================================
interface DataSource {
  name: string;
  count: string;
  status: "online" | "warning" | "offline";
  lastUpdate?: string;
}

const dataSources: DataSource[] = [
  { name: "新闻 API", count: "5/5 源", status: "online" },
  { name: "期货分钟K线", count: "14/14 品种", status: "online", lastUpdate: "2 分钟前" },
  { name: "期货日线K线", count: "14/14 品种", status: "online", lastUpdate: "昨日 23:10" },
  { name: "期货外盘K线", count: "21/30 品种", status: "warning", lastUpdate: "部分失败" },
  { name: "股票分钟K线", count: "14/14 品种", status: "online", lastUpdate: "2 分钟前" },
  { name: "股票日线K线", count: "14/14 品种", status: "online", lastUpdate: "昨日 23:10" },
];

interface DataSourceStatusModuleProps {
  onNavigate?: (view: string) => void;
}

export function DataSourceStatusModule({ onNavigate }: DataSourceStatusModuleProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "online":
        return <CheckCircle2 className="w-3.5 h-3.5 text-[#22C55E]" />;
      case "warning":
        return <AlertTriangle className="w-3.5 h-3.5 text-warning" />;
      case "offline":
        return <XCircle className="w-3.5 h-3.5 text-[#EF4444]" />;
      default:
        return null;
    }
  };

  const onlineCount = dataSources.filter((ds) => ds.status === "online").length;

  const handleClick = () => {
    if (onNavigate) {
      onNavigate("data-collection");
    }
  };

  return (
    <div className="bg-card rounded-md p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#22C55E]/10 flex items-center justify-center">
            <Database className="w-3.5 h-3.5 text-[#22C55E]" strokeWidth={1.5} />
          </div>
          <h3 className="text-[12px] font-medium text-foreground">数据源状态</h3>
        </div>
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#22C55E]/10 text-[#22C55E] font-medium">
          {onlineCount}/{dataSources.length} 正常
        </span>
      </div>

      <div className="space-y-1.5">
        {dataSources.map((source, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between py-2 px-2.5 bg-secondary/20 rounded hover:bg-secondary/40 transition-colors cursor-pointer"
            onClick={handleClick}
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <span className="text-[10px] font-medium text-foreground truncate">{source.name}</span>
              <span className="text-[9px] text-muted-foreground flex-shrink-0">{source.count}</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {source.lastUpdate && (
                <span className="text-[9px] text-muted-foreground/60">{source.lastUpdate}</span>
              )}
              {getStatusIcon(source.status)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================
// 待办事项模块
// ============================================
interface TodoItem {
  id: number;
  title: string;
  type: "alert" | "task" | "review" | "config";
  priority: "high" | "medium" | "low";
  time?: string;
  done: boolean;
}

const todoItems: TodoItem[] = [
  { id: 1, title: "确认 AU2412 买入信号", type: "alert", priority: "high", time: "10分钟前", done: false },
  { id: 2, title: "审核风控参数调整", type: "review", priority: "high", done: false },
  { id: 3, title: "检查 IF2403 止损设置", type: "config", priority: "medium", done: false },
  { id: 4, title: "更新策略权重配置", type: "task", priority: "medium", done: true },
  { id: 5, title: "导出周度交易报告", type: "task", priority: "low", done: false },
];

export function TodoModule() {
  const [items, setItems] = useState(todoItems);

  const toggleDone = (id: number) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, done: !item.done } : item))
    );
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "alert":
        return <Bell className="w-3 h-3 text-[#EF4444]" />;
      case "review":
        return <FileText className="w-3 h-3 text-warning" />;
      case "config":
        return <Settings className="w-3 h-3 text-primary" />;
      default:
        return <Calendar className="w-3 h-3 text-muted-foreground" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-[#EF4444]";
      case "medium":
        return "bg-warning";
      default:
        return "bg-muted-foreground/50";
    }
  };

  const pendingCount = items.filter((i) => !i.done).length;

  return (
    <div className="bg-card rounded-md p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#EF4444]/10 flex items-center justify-center">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#EF4444]" strokeWidth={1.5} />
          </div>
          <h3 className="text-[12px] font-medium text-foreground">待办事项</h3>
        </div>
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#EF4444]/10 text-[#EF4444] font-medium">
          {pendingCount} 待处理
        </span>
      </div>

      <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
        {items.map((item) => (
          <div
            key={item.id}
            className={cn(
              "flex items-center gap-2.5 py-2 px-2.5 rounded transition-colors cursor-pointer",
              item.done ? "bg-muted/30 opacity-60" : "bg-secondary/30 hover:bg-secondary/50"
            )}
            onClick={() => toggleDone(item.id)}
          >
            <div className={cn("w-1 h-1 rounded-full flex-shrink-0", getPriorityColor(item.priority))} />
            {getTypeIcon(item.type)}
            <span
              className={cn(
                "text-[10px] flex-1 truncate",
                item.done ? "line-through text-muted-foreground" : "text-foreground"
              )}
            >
              {item.title}
            </span>
            {item.time && !item.done && (
              <span className="text-[9px] text-muted-foreground/50">{item.time}</span>
            )}
            {item.done && <CheckCircle2 className="w-3 h-3 text-[#22C55E]" />}
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================
// 追踪股票模块
// ============================================
interface WatchlistStock {
  code: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  isWatching: boolean;
}

const watchlistStocks: WatchlistStock[] = [
  { code: "600519", name: "贵州茅台", price: 1680.50, change: 25.30, changePercent: 1.53, isWatching: true },
  { code: "000858", name: "五粮液", price: 142.80, change: -2.15, changePercent: -1.48, isWatching: true },
  { code: "601318", name: "中国平安", price: 48.65, change: 0.85, changePercent: 1.78, isWatching: true },
  { code: "000001", name: "平安银行", price: 12.35, change: -0.12, changePercent: -0.96, isWatching: false },
  { code: "600036", name: "招商银行", price: 35.20, change: 0.45, changePercent: 1.29, isWatching: true },
];

export function WatchlistModule() {
  const [stocks, setStocks] = useState(watchlistStocks);

  const toggleWatch = (code: string) => {
    setStocks((prev) =>
      prev.map((s) => (s.code === code ? { ...s, isWatching: !s.isWatching } : s))
    );
  };

  return (
    <div className="bg-card rounded-md p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center">
            <Star className="w-3.5 h-3.5 text-primary" strokeWidth={1.5} />
          </div>
          <h3 className="text-[12px] font-medium text-foreground">追踪股票</h3>
        </div>
        <Button variant="ghost" size="sm" className="h-6 text-[10px] text-muted-foreground">
          管理
        </Button>
      </div>

      <div className="space-y-1">
        {stocks.map((stock) => (
          <div
            key={stock.code}
            className="flex items-center justify-between py-2 px-2 hover:bg-secondary/30 rounded transition-colors"
          >
            <div className="flex items-center gap-2 min-w-0">
              <button
                onClick={() => toggleWatch(stock.code)}
                className="flex-shrink-0"
              >
                {stock.isWatching ? (
                  <Eye className="w-3.5 h-3.5 text-primary" />
                ) : (
                  <EyeOff className="w-3.5 h-3.5 text-muted-foreground/50" />
                )}
              </button>
              <div className="min-w-0">
                <p className="text-[10px] font-mono font-semibold text-foreground">{stock.code}</p>
                <p className="text-[9px] text-muted-foreground/60 truncate">{stock.name}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-[11px] font-mono font-semibold text-foreground">
                {stock.price.toFixed(2)}
              </p>
              <p
                className={cn(
                  "text-[9px] font-mono",
                  stock.change >= 0 ? "text-[#EF4444]" : "text-[#22C55E]"
                )}
              >
                {stock.change >= 0 ? "+" : ""}
                {stock.change.toFixed(2)} ({stock.changePercent >= 0 ? "+" : ""}
                {stock.changePercent.toFixed(2)}%)
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
