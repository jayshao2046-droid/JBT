"use client";

import { useState } from "react";
import {
  AlertTriangle,
  TrendingUp,
  ShoppingCart,
  Newspaper,
  Globe,
  BarChart3,
  LineChart,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { SentinelMetrics } from "./sentinel-metrics";
import { ChurnRadarChart } from "./churn-radar-chart";
import { useOrbit } from "./orbit-provider";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  RealTimeRiskModule,
  TodayTradingSummaryModule,
  DataSourceStatusModule,
} from "./dashboard-modules";
import { SignalConfirmModal, type SignalData } from "./modals/signal-confirm-modal";
import { ClosePositionModal, type PositionData } from "./modals/close-position-modal";
import { BanSignalModal, type BanSignalData } from "./modals/ban-signal-modal";
import { ManualOpenPositionModal, type OpenPositionData } from "./modals/manual-open-position-modal";
import { useToast } from "@/hooks/use-toast";


// 策略信号数据 - 扩展为6条
const initialStrategySignals: (SignalData & { strategyName: string; isBanned?: boolean; banExpiry?: Date })[] = [
  { code: "RB2406", currentPrice: 3200, signal: "买入", confidence: 85, type: "buy", suggestedQuantity: 2, reason: "MACD金叉，成交量放大", strategyName: "趋势突破策略" },
  { code: "AU2412", currentPrice: 1400, signal: "买入", confidence: 78, type: "buy", suggestedQuantity: 1, reason: "突破关键阻力位", strategyName: "均线交叉策略" },
  { code: "IF2403", currentPrice: 3850, signal: "卖出", confidence: 72, type: "sell", reason: "KDJ超买，顶背离", strategyName: "震荡反转策略" },
  { code: "CU2405", currentPrice: 76500, signal: "观望", confidence: 55, type: "hold", reason: "震荡区间，等待突破", strategyName: "区间突破策略" },
  { code: "AG2406", currentPrice: 5820, signal: "买入", confidence: 82, type: "buy", suggestedQuantity: 3, reason: "均线多头排列", strategyName: "动量追踪策略" },
  { code: "I2405", currentPrice: 890, signal: "卖出", confidence: 68, type: "sell", reason: "库存数据利空", strategyName: "基本面策略" },
];

// 持仓数据
const positions: PositionData[] = [
  { code: "AU2412", direction: "long", quantity: 5, avgCost: 1380, currentPrice: 1400, pnl: 10000, pnlPercent: 1.45 },
  { code: "IF2403", direction: "short", quantity: 2, avgCost: 3900, currentPrice: 3850, pnl: 10000, pnlPercent: 1.28 },
  { code: "CU2405", direction: "long", quantity: 3, avgCost: 77000, currentPrice: 76500, pnl: -1500, pnlPercent: -0.65 },
  { code: "AG2406", direction: "long", quantity: 10, avgCost: 5750, currentPrice: 5820, pnl: 7000, pnlPercent: 1.22 },
];

// 重大新闻数据
const now = Date.now();
const DAY = 86400000;
const majorNews = [
  { id: 1,  title: "国务院发布扩大内需促消费若干措施", source: "新华社", ts: now - 1000 * 60 * 5 },
  { id: 2,  title: "A股三大指数集体收涨，沪指涨1.2%", source: "证券时报", ts: now - 1000 * 60 * 20 },
  { id: 3,  title: "央行下调存款准备金率0.5个百分点", source: "中国人民银行", ts: now - 1000 * 60 * 45 },
  { id: 4,  title: "期货市场波动率创近三个月新高", source: "期货日报", ts: now - 1000 * 60 * 70 },
  { id: 5,  title: "铜价突破关键阻力位，多头信号显现", source: "金属资讯", ts: now - 1000 * 60 * 100 },
  { id: 6,  title: "螺纹钢主力合约涨停，钢厂减产预期升温", source: "我的钢铁", ts: now - 1000 * 60 * 130 },
  { id: 7,  title: "豆粕期货受美豆出口数据提振大幅上涨", source: "农产品期货网", ts: now - 1000 * 60 * 180 },
  { id: 8,  title: "原油库存数据超预期，油价承压回落", source: "能源快报", ts: now - 1000 * 60 * 240 },
  { id: 9,  title: "黄金ETF持仓量连续三周增加，避险情绪升温", source: "贵金属报", ts: now - 1000 * 60 * 300 },
  { id: 10, title: "银行间市场利率走低，流动性持续宽松", source: "中国货币网", ts: now - DAY * 0.3 },
  { id: 11, title: "沪深300期指大幅升水，市场情绪乐观", source: "中金所", ts: now - DAY * 0.4 },
  { id: 12, title: "外资连续5日净买入A股，北向资金回流", source: "Wind", ts: now - DAY * 0.5 },
  { id: 13, title: "财政部宣布增发2万亿特别国债", source: "财政部", ts: now - DAY * 0.7 },
  { id: 14, title: "多家券商上调A股年度目标价", source: "证券日报", ts: now - DAY * 1 },
  { id: 15, title: "PMI数据超预期，制造业景气度回升", source: "国家统计局", ts: now - DAY * 1.2 },
  { id: 16, title: "新能源汽车销量创月度新高", source: "中汽协", ts: now - DAY * 1.5 },
  { id: 17, title: "LPR维持不变，房贷政策窗口期延长", source: "央行", ts: now - DAY * 2 },
  { id: 18, title: "大宗商品指数回升，有色金属领涨", source: "CRB", ts: now - DAY * 3 },
  { id: 19, title: "A股IPO节奏放缓，监管层强化退市制度", source: "证监会", ts: now - DAY * 4 },
  { id: 20, title: "养老金入市规模超2000亿，长期资金持续入场", source: "社保基金", ts: now - DAY * 5 },
].filter((n) => now - n.ts < DAY * 7);

const globalNews = [
  { id: 1,  title: "Fed signals rate cut path amid cooling inflation", source: "Reuters", ts: now - 1000 * 60 * 3 },
  { id: 2,  title: "ECB holds rates as Eurozone GDP beats forecast", source: "Bloomberg", ts: now - 1000 * 60 * 15 },
  { id: 3,  title: "BoJ surprises markets with YCC band adjustment", source: "Nikkei", ts: now - 1000 * 60 * 40 },
  { id: 4,  title: "UK CPI falls to 2.1%, lowest in three years", source: "FT", ts: now - 1000 * 60 * 65 },
  { id: 5,  title: "Middle East tensions escalate after Gaza ceasefire collapses", source: "AP News", ts: now - 1000 * 60 * 90 },
  { id: 6,  title: "OPEC+ extends 2.2m bpd voluntary cuts to Q3", source: "Oil Price", ts: now - 1000 * 60 * 120 },
  { id: 7,  title: "S&P 500 hits record high on tech earnings surge", source: "WSJ", ts: now - 1000 * 60 * 160 },
  { id: 8,  title: "Bitcoin crosses $80,000 as ETF inflows accelerate", source: "CoinDesk", ts: now - 1000 * 60 * 200 },
  { id: 9,  title: "US non-farm payrolls miss estimates at 148K", source: "Reuters", ts: now - 1000 * 60 * 250 },
  { id: 10, title: "China exports surge 8.7% YoY, trade surplus widens", source: "Bloomberg", ts: now - DAY * 0.4 },
  { id: 11, title: "Germany manufacturing PMI contracts for 20th month", source: "Markit", ts: now - DAY * 0.6 },
  { id: 12, title: "IMF upgrades global growth outlook to 3.2%", source: "IMF", ts: now - DAY * 0.8 },
  { id: 13, title: "Taiwan Strait tensions rise as military drills expand", source: "FT", ts: now - DAY * 1 },
  { id: 14, title: "Brent crude tumbles 3% on surprise US stockpile build", source: "Oil Price", ts: now - DAY * 1.3 },
  { id: 15, title: "Nvidia surpasses Apple as world's most valuable company", source: "WSJ", ts: now - DAY * 1.6 },
  { id: 16, title: "Argentina peso crisis deepens, IMF bailout talks stall", source: "Reuters", ts: now - DAY * 2 },
  { id: 17, title: "India overtakes Japan as world's 4th largest economy", source: "Bloomberg", ts: now - DAY * 2.5 },
  { id: 18, title: "EU carbon price falls 12% on weak industrial demand", source: "Energy Monitor", ts: now - DAY * 3 },
  { id: 19, title: "Russia-Ukraine ceasefire talks collapse in Geneva", source: "AP News", ts: now - DAY * 4 },
  { id: 20, title: "Fed balance sheet shrinks to pre-pandemic levels", source: "FT", ts: now - DAY * 5 },
];

interface PortfolioPulseProps {
  onViewChange?: (view: string) => void;
}

function formatNewsTime(ts: number): string {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins}分钟前`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}小时前`;
  const days = Math.floor(hrs / 24);
  return `${days}天前`;
}

export function PortfolioPulse({ onViewChange }: PortfolioPulseProps) {
  const { getPortfolioMetrics } = useOrbit();
  const metrics = getPortfolioMetrics();
  const { toast } = useToast();

  // 弹窗状态
  const [signalModalOpen, setSignalModalOpen] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState<SignalData | null>(null);
  const [closeModalOpen, setCloseModalOpen] = useState(false);
  const [closeModalMode, setCloseModalMode] = useState<"single" | "all">("single");
  const [selectedPosition, setSelectedPosition] = useState<PositionData | null>(null);
  
  // 禁止信号状态
  const [banModalOpen, setBanModalOpen] = useState(false);
  const [selectedBanSignal, setSelectedBanSignal] = useState<BanSignalData | null>(null);
  const [strategySignals, setStrategySignals] = useState(initialStrategySignals);

  // 手动开仓状态
  const [openPositionModalOpen, setOpenPositionModalOpen] = useState(false);

  // 处理信号确认
  const handleSignalClick = (signal: SignalData) => {
    if (signal.type === "hold") return;
    setSelectedSignal(signal);
    setSignalModalOpen(true);
  };

  // 处理禁止信号
  const handleBanSignal = (signal: typeof initialStrategySignals[0]) => {
    setSelectedBanSignal({
      code: signal.code,
      signal: signal.signal,
      confidence: signal.confidence,
      strategyName: signal.strategyName,
      type: signal.type,
    });
    setBanModalOpen(true);
  };

  // 确认禁止
  const handleBanConfirm = (banType: "temporary" | "permanent", hours?: number) => {
    if (!selectedBanSignal) return;
    setStrategySignals((prev) =>
      prev.map((s) =>
        s.code === selectedBanSignal.code
          ? {
              ...s,
              isBanned: true,
              banExpiry: banType === "temporary" && hours
                ? new Date(Date.now() + hours * 60 * 60 * 1000)
                : undefined,
            }
          : s
      )
    );
  };

  // 恢复信号
  const handleRestoreSignal = (code: string) => {
    setStrategySignals((prev) =>
      prev.map((s) =>
        s.code === code ? { ...s, isBanned: false, banExpiry: undefined } : s
      )
    );
  };

  const handleSignalConfirm = async (quantity: number, stopLoss: number, takeProfit: number) => {
    console.log("执行交易:", { signal: selectedSignal, quantity, stopLoss, takeProfit });
    // 实际交易逻辑
  };

  // 处理一键平仓
  const handleCloseAll = () => {
    setCloseModalMode("all");
    setCloseModalOpen(true);
  };

  // 处理单个平仓
  const handleClosePosition = (position: PositionData) => {
    setSelectedPosition(position);
    setCloseModalMode("single");
    setCloseModalOpen(true);
  };

  const handleCloseConfirm = async (quantity: number) => {
    console.log("执行平仓:", { mode: closeModalMode, position: selectedPosition, quantity });
    // 实际平仓逻辑
  };

  // 手动开仓确认
  const handleOpenPositionConfirm = (data: OpenPositionData) => {
    console.log("手动开仓:", data);
    toast({
      title: "手动开仓成功",
      description: `${data.code} ${data.direction === "long" ? "做多" : "做空"} ${data.quantity} 手`,
    });
    // 实际开仓逻辑：记录到交易日志、刷新持仓列表、发送通知等
  };

  return (
    <div className="p-5 space-y-5 max-w-[1600px]">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-lg font-semibold text-foreground tracking-tight">JBotQuant</h1>
          <p className="text-[11px] text-muted-foreground/70 mt-0.5">量化交易策略执行看板</p>
        </div>
        <Button
          variant="destructive"
          size="sm"
          className="h-8 text-[11px] font-medium px-4"
          onClick={handleCloseAll}
        >
          一键平仓
        </Button>
      </div>

      {/* KPI 卡片 - 8个 (2行x4列) */}
      <SentinelMetrics
        totalArr={metrics.totalArr}
        averageNrr={metrics.averageNrr}
        averageHealthScore={metrics.averageHealthScore}
        accountCount={metrics.accountCount}
        onCloseAll={handleCloseAll}
      />

      {/* 收益表 + 当前持仓 - 一行布局 (60% + 40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-4">
        {/* 收益表 - 60% */}
        <div className="lg:col-span-6 bg-card rounded-md p-4 h-[380px]">
          <ChurnRadarChart />
        </div>

        {/* 当前持仓 - 40% */}
        <div className="lg:col-span-4 bg-card rounded-md p-4 h-[380px] flex flex-col">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center">
                <BarChart3 className="w-3.5 h-3.5 text-primary" strokeWidth={1.5} />
              </div>
              <h3 className="text-[13px] font-medium text-foreground">当前持仓</h3>
            </div>
            <span className="text-[10px] text-muted-foreground/50">{positions.length} 个持仓</span>
          </div>

          {/* 持仓列表 - 可滚动 */}
          <div className="flex-1 overflow-y-auto space-y-1.5 min-h-0">
            {positions.map((pos, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between py-2 px-2.5 bg-secondary/30 rounded hover:bg-secondary/50 transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className="text-[12px] font-mono font-semibold text-foreground">{pos.code}</span>
                  <span
                    className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded flex-shrink-0",
                      pos.direction === "long" ? "bg-[#EF4444]/10 text-[#EF4444]" : "bg-[#22C55E]/10 text-[#22C55E]"
                    )}
                  >
                    {pos.direction === "long" ? "多" : "空"} {pos.quantity}手
                  </span>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-[11px] font-mono text-muted-foreground">
                    {pos.currentPrice.toLocaleString()}
                  </span>
                  <span
                    className={cn(
                      "text-[11px] font-mono font-semibold flex items-center",
                      pos.pnl >= 0 ? "text-[#EF4444]" : "text-[#22C55E]"
                    )}
                  >
                    {pos.pnl >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                    {pos.pnl >= 0 ? "+" : ""}{pos.pnl.toLocaleString()}
                  </span>
                  <Button
                    variant="destructive"
                    size="sm"
                    className="h-6 px-2 text-[10px]"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleClosePosition(pos);
                    }}
                  >
                    平仓
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* 底部汇总 */}
          <div className="mt-3 pt-3 border-t border-border/50 flex-shrink-0">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-muted-foreground/60">
                总持仓 {positions.reduce((sum, p) => sum + p.quantity, 0)} 手
              </span>
              <span className="text-muted-foreground/60">
                总浮盈{" "}
                <span className={cn("font-mono font-semibold", positions.reduce((sum, p) => sum + p.pnl, 0) >= 0 ? "text-[#EF4444]" : "text-[#22C55E]")}>
                  {positions.reduce((sum, p) => sum + p.pnl, 0) >= 0 ? "+" : ""}
                  {positions.reduce((sum, p) => sum + p.pnl, 0).toLocaleString()}
                </span>
              </span>
              <span className="text-muted-foreground/60">
                保证金占用 <span className="font-mono font-semibold text-foreground">125,000</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 今日交易汇总 + 策略信号 - 一行各50% */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 今日交易汇总 - 50% */}
        <TodayTradingSummaryModule />

        {/* 策略信号 - 50%，高度固定，超出滚动 */}
        <div className="bg-card rounded-md p-4 h-[320px] flex flex-col">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center">
                <TrendingUp className="w-3.5 h-3.5 text-primary" strokeWidth={1.5} />
              </div>
              <div>
                <h3 className="text-[13px] font-medium text-foreground">策略信号</h3>
                <p className="text-[10px] text-muted-foreground/60">实时交易信号推荐</p>
              </div>
            </div>
            <Button
              size="sm"
              className="h-8 w-14 text-[10px] bg-primary hover:bg-primary/90 text-white"
              onClick={() => setOpenPositionModalOpen(true)}
            >
              开仓
            </Button>
          </div>

          {/* 信号列表 - 可滚动，显示6条 */}
          <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
            {strategySignals.map((signal, index) => (
              <div
                key={index}
                className={cn(
                  "p-2.5 bg-secondary/30 rounded hover:bg-secondary/50 transition-colors",
                  signal.isBanned && "opacity-50"
                )}
              >
                <div className="flex items-stretch gap-3">
                  {/* 左侧信息区 */}
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => !signal.isBanned && handleSignalClick(signal)}
                  >
                    {/* 第一行：品种代码 + 价格（高亮） */}
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[12px] font-mono font-bold text-foreground">{signal.code}</span>
                      <span className="text-[11px] font-mono font-semibold text-primary">
                        {signal.currentPrice.toLocaleString()}
                      </span>
                    </div>
                    {/* 第二行：策略名称 + 置信度 */}
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground">{signal.strategyName}</span>
                      <span className="text-[10px] font-mono text-muted-foreground/70">{signal.confidence}%</span>
                    </div>
                  </div>

                  {/* 中间：看多/看空/观望 */}
                  <div className="flex items-center justify-center w-12 flex-shrink-0">
                    <span
                      className={cn(
                        "text-[11px] font-bold px-1.5 py-0.5 rounded",
                        signal.type === "buy" && "bg-[#EF4444]/10 text-[#EF4444]",
                        signal.type === "sell" && "bg-[#22C55E]/10 text-[#22C55E]",
                        signal.type === "hold" && "bg-muted text-muted-foreground"
                      )}
                    >
                      {signal.type === "buy" ? "看多" : signal.type === "sell" ? "看空" : "观望"}
                    </span>
                  </div>

                  {/* 右侧：禁止/恢复按钮 */}
                  <div className="flex items-center flex-shrink-0">
                    {signal.isBanned ? (
                      <Button
                        size="sm"
                        className="h-8 w-14 text-[10px] bg-[#22C55E] hover:bg-[#22C55E]/90 text-white"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRestoreSignal(signal.code);
                        }}
                      >
                        恢复
                      </Button>
                    ) : (
                      <Button
                        variant="destructive"
                        size="sm"
                        className="h-8 w-14 text-[10px]"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleBanSignal(signal);
                        }}
                      >
                        禁止
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 风险指标 + 数据源状态 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RealTimeRiskModule />
        <DataSourceStatusModule onNavigate={onViewChange} />
      </div>

      {/* 新闻区块 - 两列布局：重大新闻60% + 全球新闻40% */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-4">
        {/* 重大新闻 - 60% */}
        <div className="lg:col-span-6 bg-card rounded-md p-4 flex flex-col h-[440px]">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-[#EF4444]/10 flex items-center justify-center">
                <Newspaper className="w-3.5 h-3.5 text-[#EF4444]" strokeWidth={1.5} />
              </div>
              <h3 className="text-[13px] font-medium text-foreground">重大新闻</h3>
              <span className="text-[10px] text-muted-foreground/50">最新在顶部 · 7天自动清除</span>
            </div>
            <span className="text-[10px] text-muted-foreground/50">{majorNews.length} 条</span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-0.5 min-h-0">
            {majorNews.map((news) => (
              <div key={news.id} className="py-2 px-2.5 hover:bg-secondary/30 rounded transition-colors cursor-pointer">
                <h4 className="text-[11px] font-medium text-foreground hover:text-primary transition-colors leading-snug">
                  {news.title}
                </h4>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-muted-foreground/70 font-medium">{news.source}</span>
                  <span className="text-[10px] text-muted-foreground/40">{formatNewsTime(news.ts)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 全球新闻 - 40% */}
        <div className="lg:col-span-4 bg-card rounded-md p-4 flex flex-col h-[440px]">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-[#22C55E]/10 flex items-center justify-center">
                <Globe className="w-3.5 h-3.5 text-[#22C55E]" strokeWidth={1.5} />
              </div>
              <h3 className="text-[13px] font-medium text-foreground">全球新闻</h3>
              <span className="text-[10px] text-muted-foreground/50">实时刷新</span>
            </div>
            <span className="text-[10px] text-muted-foreground/50">{globalNews.length} 条</span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-0.5 min-h-0">
            {globalNews.map((news) => (
              <div key={news.id} className="py-2 px-2.5 hover:bg-secondary/30 rounded transition-colors cursor-pointer">
                <h4 className="text-[11px] font-medium text-foreground hover:text-primary transition-colors leading-snug">
                  {news.title}
                </h4>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-muted-foreground/70 font-medium">{news.source}</span>
                  <span className="text-[10px] text-muted-foreground/40">{formatNewsTime(news.ts)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 弹窗 */}
      <SignalConfirmModal
        isOpen={signalModalOpen}
        onClose={() => setSignalModalOpen(false)}
        onConfirm={handleSignalConfirm}
        signal={selectedSignal}
      />

      <ClosePositionModal
        isOpen={closeModalOpen}
        onClose={() => setCloseModalOpen(false)}
        onConfirm={handleCloseConfirm}
        position={selectedPosition}
        mode={closeModalMode}
        positions={positions}
      />

      <BanSignalModal
        open={banModalOpen}
        onOpenChange={setBanModalOpen}
        signal={selectedBanSignal}
        onConfirm={handleBanConfirm}
      />

      <ManualOpenPositionModal
        open={openPositionModalOpen}
        onOpenChange={setOpenPositionModalOpen}
        onConfirm={handleOpenPositionConfirm}
      />
    </div>
  );
}
