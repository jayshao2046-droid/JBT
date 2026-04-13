"use client";

import {
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  Eye,
  Wallet,
  LineChart,
  Target,
  Activity,
  Percent,
  PiggyBank,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CountUp } from "./count-up";

interface MetricCardProps {
  label: string;
  value: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  icon: typeof DollarSign;
  accentColor?: "primary" | "success" | "warning" | "critical" | "profit" | "loss";
  isProfit?: boolean;
  onClick?: () => void;
}

function MetricCard({
  label,
  value,
  prefix = "",
  suffix = "",
  decimals = 0,
  trend,
  trendValue,
  icon: Icon,
  accentColor = "primary",
  isProfit,
  onClick,
}: MetricCardProps) {
  const TrendIcon =
    trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;

  const iconColors = {
    primary: "text-primary",
    success: "text-[#22C55E]",
    warning: "text-warning",
    critical: "text-critical",
    profit: "text-[#EF4444]",
    loss: "text-[#22C55E]",
  };

  return (
    <div 
      className={cn(
        "p-3.5 bg-card rounded-md group flex flex-col items-center justify-center text-center",
        onClick && "cursor-pointer hover:bg-card/80 transition-colors"
      )}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center gap-1.5 mb-1.5">
        <Icon className={cn("w-3.5 h-3.5", iconColors[accentColor])} strokeWidth={1.5} />
        <span className="text-[10px] font-medium text-muted-foreground/70">
          {label}
        </span>
      </div>

      {/* Value */}
      <div className="mb-1">
        <CountUp
          end={value}
          prefix={prefix}
          suffix={suffix}
          decimals={decimals}
          className={cn(
            "text-sm font-semibold font-mono tracking-tight whitespace-nowrap",
            isProfit === true && "text-[#EF4444]",
            isProfit === false && "text-[#22C55E]",
            isProfit === undefined && "text-foreground"
          )}
        />
      </div>

      {/* Trend - minimal */}
      {trend && trendValue && (
        <div className="flex items-center justify-center gap-1">
          <span
            className={cn(
              "flex items-center gap-0.5 text-[10px] font-medium",
              trend === "up" && "text-[#EF4444]",
              trend === "down" && "text-[#22C55E]",
              trend === "neutral" && "text-muted-foreground"
            )}
          >
            <TrendIcon className="w-2.5 h-2.5" />
            {trendValue}
          </span>
        </div>
      )}
    </div>
  );
}

interface SentinelMetricsProps {
  totalArr: number;
  averageNrr: number;
  averageHealthScore: number;
  accountCount: number;
  onCloseAll?: () => void;
}

export function SentinelMetrics({
  totalArr,
  averageNrr,
  averageHealthScore,
  accountCount,
  onCloseAll,
}: SentinelMetricsProps) {
  // 固定模拟数据 - 12个KPI卡片（3行x4列）
  // 第1行
  const todayPnL = 47500;
  const totalAssets = 2065000;
  const holdingCost = 1755300;
  const floatingPnL = 309800;
  
  // 第2行
  const positionUsage = 78; // 仓位使用率
  const varRisk = 25000; // VaR风险
  const winRate = 68.5; // 胜率
  const pnlRatio = 2.15; // 盈亏比
  
  // 第3行
  const signalCount = 31; // 信号数量
  const tradeCount = 24; // 交易笔数
  const dataSourceStatus = 45; // 数据源在线数
  const todoCount = 4; // 待办事项数

  return (
    <div className="space-y-3">
      {/* 第1行 - 4个KPI */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-4 gap-2.5">
        <MetricCard
          label="今日盈亏"
          value={todayPnL}
          prefix=""
          suffix=""
          decimals={0}
          trend="up"
          trendValue="+2.3%"
          icon={DollarSign}
          accentColor="profit"
          isProfit={true}
        />
        <MetricCard
          label="账户权益"
          value={totalAssets}
          prefix=""
          suffix=""
          decimals={0}
          trend="up"
          trendValue="+8.2%"
          icon={Eye}
          accentColor="primary"
        />
        <MetricCard
          label="持仓保证金"
          value={holdingCost}
          prefix=""
          suffix=""
          decimals={0}
          icon={Wallet}
          accentColor="primary"
        />
        <MetricCard
          label="浮动盈亏"
          value={floatingPnL}
          prefix=""
          suffix=""
          decimals={0}
          trend="up"
          trendValue="+15.0%"
          icon={LineChart}
          accentColor="profit"
          isProfit={true}
        />
      </div>

      {/* 第2行 - 4个KPI */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-4 gap-2.5">
        <MetricCard
          label="仓位使用率"
          value={positionUsage}
          prefix=""
          suffix="%"
          decimals={0}
          icon={Percent}
          accentColor={positionUsage <= 70 ? "success" : positionUsage <= 80 ? "warning" : "critical"}
        />
        <MetricCard
          label="VaR风险"
          value={varRisk}
          prefix=""
          suffix=""
          decimals={0}
          icon={Activity}
          accentColor="critical"
        />
        <MetricCard
          label="胜率"
          value={winRate}
          prefix=""
          suffix="%"
          decimals={1}
          trend="up"
          trendValue="+3.2%"
          icon={PiggyBank}
          accentColor="success"
        />
        <MetricCard
          label="盈亏比"
          value={pnlRatio}
          prefix=""
          suffix=""
          decimals={2}
          trend="up"
          trendValue="+0.12"
          icon={Target}
          accentColor="profit"
          isProfit={true}
        />
      </div>

      {/* 第3行 - 4个KPI */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-4 gap-2.5">
        <MetricCard
          label="信号数量"
          value={signalCount}
          prefix=""
          suffix=""
          decimals={0}
          icon={DollarSign}
          accentColor="primary"
        />
        <MetricCard
          label="交易笔数"
          value={tradeCount}
          prefix=""
          suffix=""
          decimals={0}
          icon={LineChart}
          accentColor="primary"
        />
        <MetricCard
          label="数据源状态"
          value={dataSourceStatus}
          prefix=""
          suffix="/47"
          decimals={0}
          icon={Eye}
          accentColor="success"
          onClick={() => console.log("Navigate to data source status")}
        />
        <MetricCard
          label="待办事项"
          value={todoCount}
          prefix=""
          suffix=""
          decimals={0}
          icon={Activity}
          accentColor="warning"
        />
      </div>
    </div>
  );
}
