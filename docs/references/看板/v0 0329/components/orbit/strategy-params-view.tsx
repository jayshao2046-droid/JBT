"use client";

import React from "react";
import { useState, useMemo, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { useToastActions } from "./toast-provider";
import { 
  Sliders, 
  Target, 
  Scale, 
  Settings2, 
  Save, 
  RotateCcw, 
  Download, 
  Upload, 
  ChevronDown, 
  ChevronRight,
  TrendingUp,
  Activity,
  BarChart3,
  Zap,
  Waves,
  AlertTriangle,
  Check,
  X,
  Clock,
  FileJson,
  History
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Section Header Component
interface SectionHeaderProps {
  icon: typeof Sliders;
  title: string;
  description?: string;
  badge?: React.ReactNode;
}

function SectionHeader({ icon: Icon, title, description, badge }: SectionHeaderProps) {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shrink-0">
        <Icon className="w-4 h-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {badge}
        </div>
        {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
      </div>
    </div>
  );
}

// Factor Category Interface
interface Factor {
  id: string;
  name: string;
  weight: number;
}

interface FactorCategory {
  id: string;
  name: string;
  icon: typeof TrendingUp;
  factors: Factor[];
}

// Initial factor data
const initialFactorCategories: FactorCategory[] = [
  {
    id: "momentum",
    name: "动量类",
    icon: TrendingUp,
    factors: [
      { id: "price_momentum", name: "价格动量", weight: 12.5 },
      { id: "relative_strength", name: "相对强弱", weight: 10.8 },
      { id: "trend_strength", name: "趋势强度", weight: 7.8 },
      { id: "momentum_breakout", name: "动量突破", weight: 6.2 },
      { id: "macd", name: "MACD", weight: 5.5 },
      { id: "rsi", name: "RSI", weight: 4.8 },
      { id: "kdj", name: "KDJ", weight: 3.9 },
      { id: "cci", name: "CCI", weight: 3.5 },
    ],
  },
  {
    id: "mean_reversion",
    name: "均值回归类",
    icon: Activity,
    factors: [
      { id: "bollinger", name: "布林带", weight: 9.2 },
      { id: "mean_revert", name: "均值回复", weight: 7.2 },
      { id: "bias", name: "乖离率", weight: 4.5 },
      { id: "zscore", name: "Z-Score", weight: 3.8 },
      { id: "percentile", name: "百分位", weight: 2.8 },
      { id: "stddev", name: "标准差", weight: 2.5 },
    ],
  },
  {
    id: "volume",
    name: "成交量类",
    icon: BarChart3,
    factors: [
      { id: "volume_up", name: "放量", weight: 8.5 },
      { id: "volume_down", name: "缩量", weight: 6.1 },
      { id: "price_volume_div", name: "量价背离", weight: 3.8 },
      { id: "obv", name: "OBV", weight: 2.9 },
      { id: "vwap", name: "VWAP", weight: 2.2 },
      { id: "volume_ratio", name: "量比", weight: 1.5 },
    ],
  },
  {
    id: "breakout",
    name: "突破类",
    icon: Zap,
    factors: [
      { id: "channel_breakout", name: "通道突破", weight: 6.5 },
      { id: "high_low_breakout", name: "高低点突破", weight: 4.2 },
      { id: "donchian", name: "唐奇安通道", weight: 3.5 },
      { id: "atr_breakout", name: "ATR 突破", weight: 2.8 },
      { id: "range_breakout", name: "区间突破", weight: 2.0 },
    ],
  },
  {
    id: "volatility",
    name: "波动率类",
    icon: Waves,
    factors: [
      { id: "atr", name: "ATR", weight: 3.2 },
      { id: "hist_vol", name: "历史波动率", weight: 2.5 },
      { id: "impl_vol", name: "隐含波动率", weight: 2.0 },
      { id: "amplitude", name: "振幅", weight: 1.8 },
      { id: "vix", name: "VIX", weight: 1.2 },
      { id: "parkinson", name: "Parkinson", weight: 0.8 },
    ],
  },
];

// Signal threshold settings
interface SignalThresholds {
  openConfidence: number;
  closeConfidence: number;
  stopLoss: number;
  takeProfit: number;
  minHoldPeriod: number;
}

// Trading rules
interface TradingRules {
  maxPositions: number;
  maxSinglePosition: number;
  maxSectorPosition: number;
  cashReserve: number;
  maxDailyTrades: number;
  minHoldPeriod: number;
}

// Advanced factor params
interface AdvancedParams {
  momentum: { lookback: number; entryThreshold: number; exitThreshold: number };
  meanReversion: { period: number; stdMultiplier: number };
  breakout: { channelPeriod: number; filterPeriod: number };
  volume: { multiplier: number; confirmPeriod: number };
  volatility: { atrPeriod: number; implVolThreshold: number };
}

// Get weight color indicator
function getWeightColor(weight: number): string {
  if (weight >= 8) return "text-red-500";
  if (weight >= 5) return "text-amber-500";
  return "text-emerald-500";
}

function getWeightDot(weight: number): string {
  if (weight >= 8) return "bg-red-500";
  if (weight >= 5) return "bg-amber-500";
  return "bg-emerald-500";
}

export function StrategyParamsView() {
  const toast = useToastActions();
  
  // Factor weights state
  const [factorCategories, setFactorCategories] = useState<FactorCategory[]>(initialFactorCategories);
  const [expandedCategories, setExpandedCategories] = useState<string[]>(["momentum"]);
  const [preset, setPreset] = useState<string>("manual");
  
  // Signal thresholds state
  const [thresholds, setThresholds] = useState<SignalThresholds>({
    openConfidence: 70,
    closeConfidence: 50,
    stopLoss: -5,
    takeProfit: 10,
    minHoldPeriod: 1,
  });
  
  // Trading rules state
  const [rules, setRules] = useState<TradingRules>({
    maxPositions: 8,
    maxSinglePosition: 15,
    maxSectorPosition: 40,
    cashReserve: 20,
    maxDailyTrades: 50,
    minHoldPeriod: 1,
  });
  
  // Advanced params state
  const [advancedParams, setAdvancedParams] = useState<AdvancedParams>({
    momentum: { lookback: 20, entryThreshold: 0.5, exitThreshold: 0.3 },
    meanReversion: { period: 30, stdMultiplier: 2.0 },
    breakout: { channelPeriod: 55, filterPeriod: 20 },
    volume: { multiplier: 1.5, confirmPeriod: 3 },
    volatility: { atrPeriod: 14, implVolThreshold: 30 },
  });
  
  // UI state
  const [saving, setSaving] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importJson, setImportJson] = useState("");
  
  // Config metadata
  const [lastSaved, setLastSaved] = useState("2026-03-21 17:08:32");
  const [configVersion] = useState("v2.3");
  const [modifyCount, setModifyCount] = useState(3);
  
  // Calculate total weight
  const totalWeight = useMemo(() => {
    return factorCategories.reduce((sum, cat) => 
      sum + cat.factors.reduce((catSum, f) => catSum + f.weight, 0), 0
    );
  }, [factorCategories]);
  
  // Calculate category subtotals
  const categorySubtotals = useMemo(() => {
    return factorCategories.reduce((acc, cat) => {
      acc[cat.id] = cat.factors.reduce((sum, f) => sum + f.weight, 0);
      return acc;
    }, {} as Record<string, number>);
  }, [factorCategories]);
  
  // Weight validation status
  const weightStatus = useMemo(() => {
    if (Math.abs(totalWeight - 100) < 0.1) return "valid";
    if (totalWeight > 100) return "over";
    return "under";
  }, [totalWeight]);
  
  // Toggle category expansion
  const toggleCategory = (catId: string) => {
    setExpandedCategories(prev => 
      prev.includes(catId) ? prev.filter(id => id !== catId) : [...prev, catId]
    );
  };
  
  // Update factor weight
  const updateFactorWeight = useCallback((categoryId: string, factorId: string, newWeight: number) => {
    setFactorCategories(prev => prev.map(cat => 
      cat.id === categoryId 
        ? { ...cat, factors: cat.factors.map(f => f.id === factorId ? { ...f, weight: newWeight } : f) }
        : cat
    ));
  }, []);
  
  // Apply preset
  const applyPreset = (presetType: string) => {
    setPreset(presetType);
    if (presetType === "equal") {
      // Equal weight: distribute equally among all factors
      const totalFactors = factorCategories.reduce((sum, cat) => sum + cat.factors.length, 0);
      const equalWeight = parseFloat((100 / totalFactors).toFixed(1));
      setFactorCategories(prev => prev.map(cat => ({
        ...cat,
        factors: cat.factors.map(f => ({ ...f, weight: equalWeight }))
      })));
      toast.success("已应用等权方案");
    } else if (presetType === "ic") {
      // IC weighted: use predefined IC-based weights
      setFactorCategories(initialFactorCategories);
      toast.success("已应用 IC 加权方案");
    }
  };
  
  // Save configuration
  const handleSave = async () => {
    if (weightStatus !== "valid") {
      toast.error("总权重必须等于 100%");
      return;
    }
    
    setSaving(true);
    await new Promise(resolve => setTimeout(resolve, 800));
    setSaving(false);
    setShowSaveDialog(false);
    setLastSaved(new Date().toLocaleString("zh-CN"));
    setModifyCount(prev => prev + 1);
    toast.success("配置保存成功");
  };
  
  // Reset to defaults
  const handleReset = () => {
    setFactorCategories(initialFactorCategories);
    setThresholds({
      openConfidence: 70,
      closeConfidence: 50,
      stopLoss: -5,
      takeProfit: 10,
      minHoldPeriod: 1,
    });
    setRules({
      maxPositions: 8,
      maxSinglePosition: 15,
      maxSectorPosition: 40,
      cashReserve: 20,
      maxDailyTrades: 50,
      minHoldPeriod: 1,
    });
    setAdvancedParams({
      momentum: { lookback: 20, entryThreshold: 0.5, exitThreshold: 0.3 },
      meanReversion: { period: 30, stdMultiplier: 2.0 },
      breakout: { channelPeriod: 55, filterPeriod: 20 },
      volume: { multiplier: 1.5, confirmPeriod: 3 },
      volatility: { atrPeriod: 14, implVolThreshold: 30 },
    });
    setPreset("manual");
    toast.success("已恢复默认配置");
  };
  
  // Export configuration
  const handleExport = () => {
    const config = {
      version: configVersion,
      exportTime: new Date().toISOString(),
      factorWeights: factorCategories,
      signalThresholds: thresholds,
      tradingRules: rules,
      advancedParams: advancedParams,
    };
    
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `strategy-config-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("配置已导出");
  };
  
  // Import configuration
  const handleImport = () => {
    try {
      const config = JSON.parse(importJson);
      if (config.factorWeights) setFactorCategories(config.factorWeights);
      if (config.signalThresholds) setThresholds(config.signalThresholds);
      if (config.tradingRules) setRules(config.tradingRules);
      if (config.advancedParams) setAdvancedParams(config.advancedParams);
      setShowImportDialog(false);
      setImportJson("");
      toast.success("配置导入成功");
    } catch {
      toast.error("配置格式错误，请检查 JSON 格式");
    }
  };

  return (
    <div className="p-6 space-y-6 overflow-x-auto">
      {/* Header */}
      <div className="flex items-center justify-between min-w-[800px]">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">策略参数配置</h1>
          <p className="text-sm text-muted-foreground mt-1">配置因子权重、信号阈值和交易规则</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-1.5" onClick={handleReset}>
            <RotateCcw className="w-4 h-4" />
            恢复默认
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5" onClick={handleExport}>
            <Download className="w-4 h-4" />
            导出配置
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5" onClick={() => setShowImportDialog(true)}>
            <Upload className="w-4 h-4" />
            导入配置
          </Button>
          <Button 
            size="sm" 
            className="gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={() => setShowSaveDialog(true)}
            disabled={saving}
          >
            {saving ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                保存配置
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Factor Weight Configuration */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }} 
        animate={{ opacity: 1, y: 0 }} 
        className="card-surface p-5 min-w-[800px]"
      >
        <SectionHeader 
          icon={Scale} 
          title="因子权重配置" 
          description="总权重必须等于 100%"
          badge={
            <span className={cn(
              "px-2 py-0.5 rounded text-xs font-medium",
              weightStatus === "valid" ? "bg-emerald-500/10 text-emerald-600" :
              weightStatus === "over" ? "bg-red-500/10 text-red-600" :
              "bg-amber-500/10 text-amber-600"
            )}>
              当前: {totalWeight.toFixed(1)}%
            </span>
          }
        />
        
        {/* Preset Selection */}
        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border/50">
          <span className="text-xs text-muted-foreground">预设方案:</span>
          <div className="flex gap-2">
            <Button 
              variant={preset === "equal" ? "default" : "outline"} 
              size="sm" 
              className="h-7 text-xs"
              onClick={() => applyPreset("equal")}
            >
              等权
            </Button>
            <Button 
              variant={preset === "ic" ? "default" : "outline"} 
              size="sm" 
              className="h-7 text-xs"
              onClick={() => applyPreset("ic")}
            >
              IC 加权
            </Button>
            <Button 
              variant={preset === "manual" ? "default" : "outline"} 
              size="sm" 
              className="h-7 text-xs"
              onClick={() => setPreset("manual")}
            >
              手动配置
            </Button>
          </div>
        </div>
        
        {/* Weight Validation */}
        <div className={cn(
          "flex items-center gap-2 p-2 rounded-lg mb-4 text-xs",
          weightStatus === "valid" ? "bg-emerald-500/10" :
          weightStatus === "over" ? "bg-red-500/10" :
          "bg-amber-500/10"
        )}>
          {weightStatus === "valid" ? (
            <>
              <Check className="w-4 h-4 text-emerald-600" />
              <span className="text-emerald-600">总权重: {totalWeight.toFixed(1)}% (有效)</span>
            </>
          ) : weightStatus === "over" ? (
            <>
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <span className="text-red-600">总权重: {totalWeight.toFixed(1)}% (超过 100%，请调整)</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span className="text-amber-600">总权重: {totalWeight.toFixed(1)}% (不足 100%，请调整)</span>
            </>
          )}
        </div>
        
        {/* Factor Categories */}
        <div className="space-y-3">
          {factorCategories.map(category => (
            <div key={category.id} className="border border-border/50 rounded-lg overflow-hidden">
              {/* Category Header */}
              <button
                className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                onClick={() => toggleCategory(category.id)}
              >
                <div className="flex items-center gap-2">
                  {expandedCategories.includes(category.id) ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  )}
                  <category.icon className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium text-foreground">{category.name}</span>
                  <span className="text-xs text-muted-foreground">({category.factors.length} 个因子)</span>
                </div>
                <span className="text-xs font-medium text-primary">
                  小计: {categorySubtotals[category.id]?.toFixed(1)}%
                </span>
              </button>
              
              {/* Category Factors */}
              <AnimatePresence>
                {expandedCategories.includes(category.id) && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="p-3 space-y-3 bg-background">
                      {category.factors.map(factor => (
                        <div key={factor.id} className="flex items-center gap-4">
                          <div className="flex items-center gap-2 w-28 shrink-0">
                            <div className={cn("w-2 h-2 rounded-full", getWeightDot(factor.weight))} />
                            <span className="text-xs text-foreground whitespace-nowrap">{factor.name}</span>
                          </div>
                          <div className="flex-1">
                            <Slider
                              value={[factor.weight]}
                              min={0}
                              max={20}
                              step={0.1}
                              onValueChange={([value]) => updateFactorWeight(category.id, factor.id, value)}
                              className="w-full"
                            />
                          </div>
                          <span className={cn("text-xs font-mono w-14 text-right", getWeightColor(factor.weight))}>
                            {factor.weight.toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Signal Threshold Settings */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ delay: 0.1 }}
        className="card-surface p-5 min-w-[800px]"
      >
        <SectionHeader icon={Target} title="信号阈值设置" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label className="text-xs">开仓置信度阈值</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={thresholds.openConfidence}
                onChange={e => setThresholds(prev => ({ ...prev, openConfidence: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">%</span>
            </div>
            <p className="text-[10px] text-muted-foreground">低于此值不生成信号</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">平仓置信度阈值</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={thresholds.closeConfidence}
                onChange={e => setThresholds(prev => ({ ...prev, closeConfidence: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">%</span>
            </div>
            <p className="text-[10px] text-muted-foreground">低于此值触发平仓</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">止损触发阈值</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={thresholds.stopLoss}
                onChange={e => setThresholds(prev => ({ ...prev, stopLoss: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">%</span>
            </div>
            <p className="text-[10px] text-muted-foreground">亏损超过此值触发止损</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">止盈触发阈值</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={thresholds.takeProfit}
                onChange={e => setThresholds(prev => ({ ...prev, takeProfit: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">%</span>
            </div>
            <p className="text-[10px] text-muted-foreground">盈利超过此值触发止盈</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">信号过滤周期</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={thresholds.minHoldPeriod}
                onChange={e => setThresholds(prev => ({ ...prev, minHoldPeriod: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">天</span>
            </div>
            <p className="text-[10px] text-muted-foreground">新信号需等待此周期后才可开仓</p>
          </div>
        </div>
      </motion.div>

      {/* Trading Rules */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ delay: 0.2 }}
        className="card-surface p-5 min-w-[800px]"
      >
        <SectionHeader icon={Settings2} title="交易规则" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label className="text-xs">最大持仓品种数</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={rules.maxPositions}
                onChange={e => setRules(prev => ({ ...prev, maxPositions: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">个</span>
            </div>
            <p className="text-[10px] text-muted-foreground">同时持仓的品种数量上限</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">单品种最大仓位</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={rules.maxSinglePosition}
                onChange={e => setRules(prev => ({ ...prev, maxSinglePosition: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">%</span>
            </div>
            <p className="text-[10px] text-muted-foreground">单个品种占总资金比例上限</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">单一板块最大仓位</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={rules.maxSectorPosition}
                onChange={e => setRules(prev => ({ ...prev, maxSectorPosition: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">%</span>
            </div>
            <p className="text-[10px] text-muted-foreground">同一板块占总资金比例上限</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">现金保留比例</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={rules.cashReserve}
                onChange={e => setRules(prev => ({ ...prev, cashReserve: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">%</span>
            </div>
            <p className="text-[10px] text-muted-foreground">始终保持的现金比例</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">日内最大交易次数</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={rules.maxDailyTrades}
                onChange={e => setRules(prev => ({ ...prev, maxDailyTrades: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">笔</span>
            </div>
            <p className="text-[10px] text-muted-foreground">单日交易次数上限</p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">最小持仓周期</Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={rules.minHoldPeriod}
                onChange={e => setRules(prev => ({ ...prev, minHoldPeriod: Number(e.target.value) }))}
                className="h-8 text-xs"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">天</span>
            </div>
            <p className="text-[10px] text-muted-foreground">开仓后至少持有此周期</p>
          </div>
        </div>
      </motion.div>

      {/* Advanced Factor Parameters */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ delay: 0.3 }}
        className="card-surface p-5 min-w-[800px]"
      >
        <SectionHeader icon={Sliders} title="因子参数微调" description="高级用户设置" />
        <div className="space-y-6">
          {/* Momentum Parameters */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              <span className="text-xs font-medium text-foreground">动量因子参数</span>
            </div>
            <div className="grid grid-cols-3 gap-4 pl-6">
              <div className="space-y-1">
                <Label className="text-[10px]">回看周期</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={advancedParams.momentum.lookback}
                    onChange={e => setAdvancedParams(prev => ({ 
                      ...prev, 
                      momentum: { ...prev.momentum, lookback: Number(e.target.value) }
                    }))}
                    className="h-7 text-xs"
                  />
                  <span className="text-[10px] text-muted-foreground">天</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">入场阈值</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={advancedParams.momentum.entryThreshold}
                  onChange={e => setAdvancedParams(prev => ({ 
                    ...prev, 
                    momentum: { ...prev.momentum, entryThreshold: Number(e.target.value) }
                  }))}
                  className="h-7 text-xs"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">出场阈值</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={advancedParams.momentum.exitThreshold}
                  onChange={e => setAdvancedParams(prev => ({ 
                    ...prev, 
                    momentum: { ...prev.momentum, exitThreshold: Number(e.target.value) }
                  }))}
                  className="h-7 text-xs"
                />
              </div>
            </div>
          </div>
          
          {/* Mean Reversion Parameters */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary" />
              <span className="text-xs font-medium text-foreground">均值回归因子参数</span>
            </div>
            <div className="grid grid-cols-3 gap-4 pl-6">
              <div className="space-y-1">
                <Label className="text-[10px]">均值周期</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={advancedParams.meanReversion.period}
                    onChange={e => setAdvancedParams(prev => ({ 
                      ...prev, 
                      meanReversion: { ...prev.meanReversion, period: Number(e.target.value) }
                    }))}
                    className="h-7 text-xs"
                  />
                  <span className="text-[10px] text-muted-foreground">天</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">标准差倍数</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={advancedParams.meanReversion.stdMultiplier}
                  onChange={e => setAdvancedParams(prev => ({ 
                    ...prev, 
                    meanReversion: { ...prev.meanReversion, stdMultiplier: Number(e.target.value) }
                  }))}
                  className="h-7 text-xs"
                />
              </div>
            </div>
          </div>
          
          {/* Breakout Parameters */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-primary" />
              <span className="text-xs font-medium text-foreground">突破因子参数</span>
            </div>
            <div className="grid grid-cols-3 gap-4 pl-6">
              <div className="space-y-1">
                <Label className="text-[10px]">通道周期</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={advancedParams.breakout.channelPeriod}
                    onChange={e => setAdvancedParams(prev => ({ 
                      ...prev, 
                      breakout: { ...prev.breakout, channelPeriod: Number(e.target.value) }
                    }))}
                    className="h-7 text-xs"
                  />
                  <span className="text-[10px] text-muted-foreground">天</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">过滤周期</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={advancedParams.breakout.filterPeriod}
                    onChange={e => setAdvancedParams(prev => ({ 
                      ...prev, 
                      breakout: { ...prev.breakout, filterPeriod: Number(e.target.value) }
                    }))}
                    className="h-7 text-xs"
                  />
                  <span className="text-[10px] text-muted-foreground">天</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Volume Parameters */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              <span className="text-xs font-medium text-foreground">成交量因子参数</span>
            </div>
            <div className="grid grid-cols-3 gap-4 pl-6">
              <div className="space-y-1">
                <Label className="text-[10px]">放量倍数</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={advancedParams.volume.multiplier}
                  onChange={e => setAdvancedParams(prev => ({ 
                    ...prev, 
                    volume: { ...prev.volume, multiplier: Number(e.target.value) }
                  }))}
                  className="h-7 text-xs"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">确认周期</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={advancedParams.volume.confirmPeriod}
                    onChange={e => setAdvancedParams(prev => ({ 
                      ...prev, 
                      volume: { ...prev.volume, confirmPeriod: Number(e.target.value) }
                    }))}
                    className="h-7 text-xs"
                  />
                  <span className="text-[10px] text-muted-foreground">天</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Volatility Parameters */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Waves className="w-4 h-4 text-primary" />
              <span className="text-xs font-medium text-foreground">波动率因子参数</span>
            </div>
            <div className="grid grid-cols-3 gap-4 pl-6">
              <div className="space-y-1">
                <Label className="text-[10px]">ATR 周期</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={advancedParams.volatility.atrPeriod}
                    onChange={e => setAdvancedParams(prev => ({ 
                      ...prev, 
                      volatility: { ...prev.volatility, atrPeriod: Number(e.target.value) }
                    }))}
                    className="h-7 text-xs"
                  />
                  <span className="text-[10px] text-muted-foreground">天</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">隐含波动率阈值</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={advancedParams.volatility.implVolThreshold}
                    onChange={e => setAdvancedParams(prev => ({ 
                      ...prev, 
                      volatility: { ...prev.volatility, implVolThreshold: Number(e.target.value) }
                    }))}
                    className="h-7 text-xs"
                  />
                  <span className="text-[10px] text-muted-foreground">%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Configuration Operations */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ delay: 0.4 }}
        className="card-surface p-5 min-w-[800px]"
      >
        <SectionHeader icon={FileJson} title="配置操作" />
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              <span>最后保存: {lastSaved}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <FileJson className="w-3.5 h-3.5" />
              <span>配置版本: {configVersion}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" />
              <span>修改记录: {modifyCount} 次</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-1.5" onClick={handleReset}>
              <RotateCcw className="w-4 h-4" />
              恢复默认
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={handleExport}>
              <Download className="w-4 h-4" />
              导出 JSON
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => setShowImportDialog(true)}>
              <Upload className="w-4 h-4" />
              导入配置
            </Button>
            <Button 
              size="sm" 
              className="gap-1.5"
              onClick={() => setShowSaveDialog(true)}
            >
              <Save className="w-4 h-4" />
              保存配置
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Save Confirmation Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>确认保存配置</DialogTitle>
            <DialogDescription>
              确定要保存当前的策略参数配置吗？此操作将覆盖之前的配置。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">总权重</span>
              <span className={cn(
                "font-medium",
                weightStatus === "valid" ? "text-emerald-600" : "text-red-600"
              )}>
                {totalWeight.toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">配置版本</span>
              <span className="font-medium">{configVersion}</span>
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSave} disabled={saving || weightStatus !== "valid"}>
              {saving ? "保存中..." : "确认保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>导入配置</DialogTitle>
            <DialogDescription>
              请粘贴 JSON 格式的配置文件内容，导入后将覆盖当前配置。
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <textarea
              className="w-full h-48 p-3 text-xs font-mono bg-muted/50 border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder='{"version": "v2.3", "factorWeights": [...], ...}'
              value={importJson}
              onChange={e => setImportJson(e.target.value)}
            />
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setShowImportDialog(false); setImportJson(""); }}>
              取消
            </Button>
            <Button onClick={handleImport} disabled={!importJson.trim()}>
              确认导入
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
