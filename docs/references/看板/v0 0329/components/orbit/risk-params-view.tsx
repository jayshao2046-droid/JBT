"use client";

import React, { useState, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { useToastActions } from "./toast-provider";
import {
  TrendingUp,
  AlertTriangle,
  Activity,
  Zap,
  Flame,
  Scale,
  Ban,
  Save,
  RotateCcw,
  Download,
  Upload,
  History,
  Clock,
  FileJson,
  Check,
  X,
  Plus,
  Trash2,
  Edit2,
  MessageSquare,
  Phone,
  Bell,
  Mail,
  ShieldCheck,
  Search,
  FileCheck,
  Sparkles,
} from "lucide-react";
import { motion } from "framer-motion";

// ─────────────────────────────────────────────
// Shared sub-components
// ─────────────────────────────────────────────

function SectionHeader({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof TrendingUp;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex items-start gap-3 mb-5">
      <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shrink-0">
        <Icon className="w-4 h-4 text-primary" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {description && (
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
        )}
      </div>
    </div>
  );
}

function ParamCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-muted/30 rounded-lg p-4 border border-border/40 space-y-1">
      {children}
    </div>
  );
}

function ParamLabel({
  label,
  description,
}: {
  label: string;
  description?: string;
}) {
  return (
    <div className="mb-2">
      <p className="text-xs font-medium text-foreground whitespace-nowrap">{label}</p>
      {description && (
        <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">{description}</p>
      )}
    </div>
  );
}

function NumberInput({
  value,
  onChange,
  min,
  max,
  step = 1,
  unit,
  error,
}: {
  value: string;
  onChange: (v: string) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  error?: string;
}) {
  const numVal = parseFloat(value);
  const hasError =
    error ||
    (min !== undefined && numVal < min) ||
    (max !== undefined && numVal > max);

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <Input
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          min={min}
          max={max}
          step={step}
          className={cn(
            "h-8 text-xs w-24",
            hasError && "border-destructive focus-visible:ring-destructive"
          )}
        />
        {unit && (
          <span className="text-xs text-muted-foreground whitespace-nowrap">{unit}</span>
        )}
        {!hasError && value !== "" && (
          <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
        )}
        {hasError && <X className="w-3.5 h-3.5 text-destructive shrink-0" />}
      </div>
      {hasError && (
        <p className="text-[10px] text-destructive">
          {error || `范围 ${min}–${max}`}
        </p>
      )}
    </div>
  );
}

function NotifyCheckboxGroup({
  value,
  onChange,
}: {
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const options = [
    { id: "sms", label: "短信", icon: MessageSquare },
    { id: "phone", label: "电话", icon: Phone },
    { id: "feishu", label: "飞书", icon: Bell },
    { id: "email", label: "邮件", icon: Mail },
  ];
  return (
    <div className="flex flex-wrap gap-3 mt-1">
      {options.map(({ id, label, icon: Icon }) => (
        <label key={id} className="flex items-center gap-1.5 cursor-pointer">
          <Checkbox
            checked={value.includes(id)}
            onCheckedChange={(checked) => {
              if (checked) onChange([...value, id]);
              else onChange(value.filter((v) => v !== id));
            }}
          />
          <Icon className="w-3 h-3 text-muted-foreground" />
          <span className="text-xs text-foreground whitespace-nowrap">{label}</span>
        </label>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────
// Preset configurations
// ─────────────────────────────────────────────

const PRESETS = {
  conservative: {
    name: "保守型",
    description: "低风险，适合稳健投资",
    totalPositionLimit: "50",
    singleSymbolLimit: "10",
    singleSectorLimit: "25",
    cashReserveRatio: "50",
    dailyVar: "3",
    weeklyVar: "6",
    monthlyVar: "10",
    dailyLossBreaker: "3",
    consecutiveLossBreaker: "2",
  },
  balanced: {
    name: "平衡型",
    description: "中等风险，风险收益平衡",
    totalPositionLimit: "70",
    singleSymbolLimit: "15",
    singleSectorLimit: "35",
    cashReserveRatio: "30",
    dailyVar: "5",
    weeklyVar: "10",
    monthlyVar: "15",
    dailyLossBreaker: "5",
    consecutiveLossBreaker: "3",
  },
  aggressive: {
    name: "激进型",
    description: "高风险高收益",
    totalPositionLimit: "90",
    singleSymbolLimit: "25",
    singleSectorLimit: "50",
    cashReserveRatio: "10",
    dailyVar: "8",
    weeklyVar: "15",
    monthlyVar: "25",
    dailyLossBreaker: "8",
    consecutiveLossBreaker: "5",
  },
};

// ─────────────────────────────────────────────
// Default config
// ─────────────────────────────────────────────

const DEFAULT_CONFIG = {
  // 仓位限制
  totalPositionLimit: "80",
  singleSymbolLimit: "20",
  singleSectorLimit: "40",
  cashReserveRatio: "20",
  dynamicPosition: true,
  volatilityCoeff: "1.5",
  // 强平规则
  liquidationTrigger: "80",
  liquidationOrder: "max-loss",
  liquidationRatio: "20",
  liquidationWarningOffset: "5",
  liquidationNotify: ["sms", "phone", "feishu", "email"],
  warningNotify: ["feishu", "email"],
  // VaR限制
  dailyVar: "5",
  weeklyVar: "10",
  monthlyVar: "15",
  varMethod: "historical",
  varConfidence: "95",
  varBreachAction: "reduce",
  varBreachNotify: ["feishu", "email"],
  // 异常检测
  slippageThreshold: "3",
  fillFailureRate: "5",
  dataDelayThreshold: "5",
  liquidityThreshold: "0.5",
  abnormalVolatility: "8",
  alertLevel: "P1",
  // 风控熔断
  dailyLossBreaker: "5",
  consecutiveLossBreaker: "3",
  breakerAction: "pause-1h",
  breakerNotify: ["feishu", "email"],
  breakerRecovery: "auto",
  // 交易限制
  maxHoldingSymbols: "8",
  maxDailyTrades: "50",
  minHoldingDays: "1",
  noOvernightPosition: true,
  daySessionCloseTime: "14:55",
  nightSessionCloseTime: "22:55",
};

type Config = typeof DEFAULT_CONFIG;

// ─────────────────────────────────────────────
// Blacklist types
// ─────────────────────────────────────────────

interface BlacklistSymbol {
  id: string;
  code: string;
  name: string;
  addedAt: string;
  reason: string;
  remark?: string;
}

interface BlacklistStrategy {
  id: string;
  name: string;
  strategyId: string;
  addedAt: string;
  reason: string;
  remark?: string;
}

interface BlacklistPeriod {
  id: string;
  description: string;
  startTime: string;
  endTime: string;
  repeat: string;
  remark?: string;
}

const INIT_SYMBOLS: BlacklistSymbol[] = [
  { id: "1", code: "IF2403", name: "沪深300指数期货", addedAt: "2026-03-10", reason: "流动性不足", remark: "日均成交量低于阈值" },
  { id: "2", code: "rb2405", name: "螺纹钢期货", addedAt: "2026-03-15", reason: "异常波动", remark: "近期波动率超标" },
  { id: "3", code: "IC2406", name: "中证500期货", addedAt: "2026-03-18", reason: "交割月临近", remark: "距交割不足10日" },
];

const INIT_STRATEGIES: BlacklistStrategy[] = [
  { id: "1", name: "高频动量策略", strategyId: "HFM-001", addedAt: "2026-03-12", reason: "回撤超限", remark: "连续3日最大回撤超5%" },
  { id: "2", name: "套利策略A", strategyId: "ARB-002", addedAt: "2026-03-14", reason: "策略失效", remark: "套利空间消失" },
];

const INIT_PERIODS: BlacklistPeriod[] = [
  { id: "1", description: "重大节假日前后", startTime: "09:25", endTime: "09:35", repeat: "每日", remark: "开盘10分钟波动大" },
  { id: "2", description: "午间休市", startTime: "11:30", endTime: "13:00", repeat: "每日", remark: "避免隔午风险" },
  { id: "3", description: "尾盘15分钟", startTime: "14:45", endTime: "15:00", repeat: "每日", remark: "收盘前波动大" },
];

// ─────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────

export function RiskParamsView() {
  const toast = useToastActions();
  const [config, setConfig] = useState<Config>({ ...DEFAULT_CONFIG });
  const [savedConfig, setSavedConfig] = useState<Config>({ ...DEFAULT_CONFIG });
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showPresetDialog, setShowPresetDialog] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState("2026-03-21 17:08:32");
  const [version, setVersion] = useState("v2.3");
  const [changeCount, setChangeCount] = useState(3);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importPreview, setImportPreview] = useState<Config | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  // Blacklist state
  const [symbols, setSymbols] = useState<BlacklistSymbol[]>(INIT_SYMBOLS);
  const [strategies, setStrategies] = useState<BlacklistStrategy[]>(INIT_STRATEGIES);
  const [periods, setPeriods] = useState<BlacklistPeriod[]>(INIT_PERIODS);
  const [blacklistSearch, setBlacklistSearch] = useState("");
  const [selectedSymbols, setSelectedSymbols] = useState<Set<string>>(new Set());
  const [selectedStrategies, setSelectedStrategies] = useState<Set<string>>(new Set());
  const [selectedPeriods, setSelectedPeriods] = useState<Set<string>>(new Set());

  // Add/Edit dialog states
  const [showAddSymbolDialog, setShowAddSymbolDialog] = useState(false);
  const [showAddStrategyDialog, setShowAddStrategyDialog] = useState(false);
  const [showAddPeriodDialog, setShowAddPeriodDialog] = useState(false);
  const [editingSymbol, setEditingSymbol] = useState<BlacklistSymbol | null>(null);
  const [editingStrategy, setEditingStrategy] = useState<BlacklistStrategy | null>(null);
  const [editingPeriod, setEditingPeriod] = useState<BlacklistPeriod | null>(null);

  // Form states for add/edit dialogs
  const [symbolForm, setSymbolForm] = useState({ code: "", name: "", reason: "", remark: "" });
  const [strategyForm, setStrategyForm] = useState({ name: "", strategyId: "", reason: "", remark: "" });
  const [periodForm, setPeriodForm] = useState({ description: "", startTime: "", endTime: "", repeat: "每日", remark: "" });

  const set = useCallback(
    (key: keyof Config, value: Config[keyof Config]) => {
      setConfig((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  // Validation helpers
  const totalCheck =
    parseFloat(config.totalPositionLimit) + parseFloat(config.cashReserveRatio) <= 100;
  const singleCheck =
    parseFloat(config.singleSymbolLimit) <= parseFloat(config.totalPositionLimit);
  const sectorCheck =
    parseFloat(config.singleSectorLimit) <= parseFloat(config.totalPositionLimit);

  // Filtered blacklists
  const filteredSymbols = symbols.filter(s => 
    !blacklistSearch || 
    s.code.toLowerCase().includes(blacklistSearch.toLowerCase()) ||
    s.name.toLowerCase().includes(blacklistSearch.toLowerCase())
  );
  const filteredStrategies = strategies.filter(s => 
    !blacklistSearch || 
    s.name.toLowerCase().includes(blacklistSearch.toLowerCase()) ||
    s.strategyId.toLowerCase().includes(blacklistSearch.toLowerCase())
  );
  const filteredPeriods = periods.filter(p => 
    !blacklistSearch || 
    p.description.toLowerCase().includes(blacklistSearch.toLowerCase())
  );

  // Check if config has changes compared to saved
  const hasChanges = JSON.stringify(config) !== JSON.stringify(savedConfig);

  const handleSave = async () => {
    setSaving(true);
    await new Promise((r) => setTimeout(r, 800));
    setSaving(false);
    setShowSaveDialog(false);
    const now = new Date().toLocaleString("zh-CN");
    setLastSaved(now);
    setSavedConfig({ ...config });
    setChangeCount((c) => c + 1);
    const vParts = version.replace("v", "").split(".");
    setVersion(`v${vParts[0]}.${parseInt(vParts[1]) + 1}`);
    toast.success("风控参数已保存");
  };

  const handleReset = () => {
    setConfig({ ...DEFAULT_CONFIG });
    setShowResetDialog(false);
    toast.success("已恢复默认配置");
  };

  const handleExport = () => {
    const exportData = {
      version: version,
      exportTime: new Date().toISOString(),
      config: config,
      blacklists: {
        symbols,
        strategies,
        periods,
      }
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `risk-params-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("配置已导出");
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target?.result as string);
        
        // Validate required fields
        if (!data.version) {
          setImportError("配置文件缺少 version 字段");
          setImportPreview(null);
          return;
        }
        if (!data.config) {
          setImportError("配置文件缺少 config 字段");
          setImportPreview(null);
          return;
        }
        
        // Validate config structure
        const requiredKeys = ["totalPositionLimit", "singleSymbolLimit", "dailyVar", "liquidationTrigger"];
        for (const key of requiredKeys) {
          if (!(key in data.config)) {
            setImportError(`配置文件缺少必要字段: ${key}`);
            setImportPreview(null);
            return;
          }
        }

        // Validate numeric ranges
        const numericValidations = [
          { key: "totalPositionLimit", min: 0, max: 100 },
          { key: "singleSymbolLimit", min: 0, max: 100 },
          { key: "dailyVar", min: 0, max: 50 },
        ];
        for (const { key, min, max } of numericValidations) {
          const val = parseFloat(data.config[key]);
          if (isNaN(val) || val < min || val > max) {
            setImportError(`字段 ${key} 的值无效 (范围: ${min}-${max})`);
            setImportPreview(null);
            return;
          }
        }

        setImportError(null);
        setImportPreview(data.config);
      } catch {
        setImportError("JSON 解析失败，请检查文件格式");
        setImportPreview(null);
      }
    };
    reader.readAsText(file);
  };

  const handleImport = () => {
    if (!importPreview) return;
    setConfig({ ...DEFAULT_CONFIG, ...importPreview });
    setShowImportDialog(false);
    setImportPreview(null);
    setImportError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    toast.success("配置导入成功");
  };

  const applyPreset = (presetKey: keyof typeof PRESETS) => {
    const preset = PRESETS[presetKey];
    setConfig(prev => ({
      ...prev,
      totalPositionLimit: preset.totalPositionLimit,
      singleSymbolLimit: preset.singleSymbolLimit,
      singleSectorLimit: preset.singleSectorLimit,
      cashReserveRatio: preset.cashReserveRatio,
      dailyVar: preset.dailyVar,
      weeklyVar: preset.weeklyVar,
      monthlyVar: preset.monthlyVar,
      dailyLossBreaker: preset.dailyLossBreaker,
      consecutiveLossBreaker: preset.consecutiveLossBreaker,
    }));
    setShowPresetDialog(false);
    toast.success(`已应用${preset.name}方案`);
  };

  // Blacklist CRUD handlers
  const handleAddSymbol = () => {
    if (!symbolForm.code || !symbolForm.name || !symbolForm.reason) {
      toast.error("请填写必填字段");
      return;
    }
    const newSymbol: BlacklistSymbol = {
      id: Date.now().toString(),
      code: symbolForm.code,
      name: symbolForm.name,
      reason: symbolForm.reason,
      remark: symbolForm.remark,
      addedAt: new Date().toISOString().slice(0, 10),
    };
    setSymbols(prev => [...prev, newSymbol]);
    setSymbolForm({ code: "", name: "", reason: "", remark: "" });
    setShowAddSymbolDialog(false);
    toast.success("品种已添加到黑名单");
  };

  const handleEditSymbol = () => {
    if (!editingSymbol || !symbolForm.code || !symbolForm.name || !symbolForm.reason) {
      toast.error("请填写必填字段");
      return;
    }
    setSymbols(prev => prev.map(s => s.id === editingSymbol.id ? {
      ...s,
      code: symbolForm.code,
      name: symbolForm.name,
      reason: symbolForm.reason,
      remark: symbolForm.remark,
    } : s));
    setEditingSymbol(null);
    setSymbolForm({ code: "", name: "", reason: "", remark: "" });
    toast.success("品种信息已更新");
  };

  const handleAddStrategy = () => {
    if (!strategyForm.name || !strategyForm.strategyId || !strategyForm.reason) {
      toast.error("请填写必填字段");
      return;
    }
    const newStrategy: BlacklistStrategy = {
      id: Date.now().toString(),
      name: strategyForm.name,
      strategyId: strategyForm.strategyId,
      reason: strategyForm.reason,
      remark: strategyForm.remark,
      addedAt: new Date().toISOString().slice(0, 10),
    };
    setStrategies(prev => [...prev, newStrategy]);
    setStrategyForm({ name: "", strategyId: "", reason: "", remark: "" });
    setShowAddStrategyDialog(false);
    toast.success("策略已添加到黑名单");
  };

  const handleEditStrategy = () => {
    if (!editingStrategy || !strategyForm.name || !strategyForm.strategyId || !strategyForm.reason) {
      toast.error("请填写必填字段");
      return;
    }
    setStrategies(prev => prev.map(s => s.id === editingStrategy.id ? {
      ...s,
      name: strategyForm.name,
      strategyId: strategyForm.strategyId,
      reason: strategyForm.reason,
      remark: strategyForm.remark,
    } : s));
    setEditingStrategy(null);
    setStrategyForm({ name: "", strategyId: "", reason: "", remark: "" });
    toast.success("策略信息已更新");
  };

  const handleAddPeriod = () => {
    if (!periodForm.description || !periodForm.startTime || !periodForm.endTime) {
      toast.error("请填写必填字段");
      return;
    }
    const newPeriod: BlacklistPeriod = {
      id: Date.now().toString(),
      description: periodForm.description,
      startTime: periodForm.startTime,
      endTime: periodForm.endTime,
      repeat: periodForm.repeat,
      remark: periodForm.remark,
    };
    setPeriods(prev => [...prev, newPeriod]);
    setPeriodForm({ description: "", startTime: "", endTime: "", repeat: "每日", remark: "" });
    setShowAddPeriodDialog(false);
    toast.success("时段已添加到黑名单");
  };

  const handleEditPeriod = () => {
    if (!editingPeriod || !periodForm.description || !periodForm.startTime || !periodForm.endTime) {
      toast.error("请填写必填字段");
      return;
    }
    setPeriods(prev => prev.map(p => p.id === editingPeriod.id ? {
      ...p,
      description: periodForm.description,
      startTime: periodForm.startTime,
      endTime: periodForm.endTime,
      repeat: periodForm.repeat,
      remark: periodForm.remark,
    } : p));
    setEditingPeriod(null);
    setPeriodForm({ description: "", startTime: "", endTime: "", repeat: "每日", remark: "" });
    toast.success("时段信息已更新");
  };

  // Batch delete handlers
  const handleBatchDeleteSymbols = () => {
    if (selectedSymbols.size === 0) return;
    setSymbols(prev => prev.filter(s => !selectedSymbols.has(s.id)));
    setSelectedSymbols(new Set());
    toast.success(`已删除 ${selectedSymbols.size} 个品种`);
  };

  const handleBatchDeleteStrategies = () => {
    if (selectedStrategies.size === 0) return;
    setStrategies(prev => prev.filter(s => !selectedStrategies.has(s.id)));
    setSelectedStrategies(new Set());
    toast.success(`已删除 ${selectedStrategies.size} 个策略`);
  };

  const handleBatchDeletePeriods = () => {
    if (selectedPeriods.size === 0) return;
    setPeriods(prev => prev.filter(p => !selectedPeriods.has(p.id)));
    setSelectedPeriods(new Set());
    toast.success(`已删除 ${selectedPeriods.size} 个时段`);
  };

  return (
    <div className="min-w-[900px] p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center">
            <ShieldCheck className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground">风控参数配置</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              配置仓位限制、强平规则、VaR 限制、异常检测和风控熔断
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={() => setShowPresetDialog(true)}>
            <Sparkles className="w-3.5 h-3.5" />
            预设方案
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={() => setShowResetDialog(true)}>
            <RotateCcw className="w-3.5 h-3.5" />
            恢复默认
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={handleExport}>
            <Download className="w-3.5 h-3.5" />
            导出配置
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={() => setShowImportDialog(true)}>
            <Upload className="w-3.5 h-3.5" />
            导入配置
          </Button>
          <Button size="sm" className="gap-1.5 text-xs" onClick={() => setShowSaveDialog(true)} disabled={!hasChanges}>
            <Save className="w-3.5 h-3.5" />
            保存配置
          </Button>
        </div>
      </div>

      {/* Changes indicator */}
      {hasChanges && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-center gap-2 text-xs text-amber-600">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>您有未保存的更改，请记得保存配置。</span>
        </div>
      )}

      {/* Module 1: 仓位限制 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={TrendingUp} title="仓位限制" description="控制总体风险暴露" />

        {/* Validation banner */}
        {(!totalCheck || !singleCheck || !sectorCheck) && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 text-xs text-destructive">
            <X className="w-4 h-4 shrink-0" />
            <span>
              {!totalCheck && "总仓位 + 现金保留不得超过 100%。"}
              {!singleCheck && "单品种仓位不得超过总仓位上限。"}
              {!sectorCheck && "单一板块仓位不得超过总仓位上限。"}
            </span>
          </div>
        )}

        <div className="grid grid-cols-3 gap-4">
          <ParamCard>
            <ParamLabel label="总仓位上限" description="占用保证金占总权益比例上限" />
            <NumberInput
              value={config.totalPositionLimit}
              onChange={(v) => set("totalPositionLimit", v)}
              min={0}
              max={100}
              unit="%"
              error={!totalCheck ? "总仓位 + 现金保留 > 100%" : undefined}
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="单品种仓位上限" description="单个品种占总资金比例上限" />
            <NumberInput
              value={config.singleSymbolLimit}
              onChange={(v) => set("singleSymbolLimit", v)}
              min={0}
              max={100}
              unit="%"
              error={!singleCheck ? "不得超过总仓位上限" : undefined}
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="单一板块仓位上限" description="同一板块占总资金比例上限" />
            <NumberInput
              value={config.singleSectorLimit}
              onChange={(v) => set("singleSectorLimit", v)}
              min={0}
              max={100}
              unit="%"
              error={!sectorCheck ? "不得超过总仓位上限" : undefined}
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="现金保留比例" description="始终保持的现金比例" />
            <NumberInput
              value={config.cashReserveRatio}
              onChange={(v) => set("cashReserveRatio", v)}
              min={0}
              max={100}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="动态仓位调整" description="根据波动率自动调整仓位" />
            <Switch
              checked={config.dynamicPosition}
              onCheckedChange={(v) => set("dynamicPosition", v)}
            />
          </ParamCard>

          {config.dynamicPosition && (
            <ParamCard>
              <ParamLabel label="波动率系数" description="波动率越高，仓位越低" />
              <NumberInput
                value={config.volatilityCoeff}
                onChange={(v) => set("volatilityCoeff", v)}
                min={0.5}
                max={3.0}
                step={0.1}
                unit="倍"
              />
            </ParamCard>
          )}
        </div>
      </motion.div>

      {/* Module 2: 强平规则 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={AlertTriangle} title="强平规则" description="触发强平时的处理逻辑" />
        <div className="grid grid-cols-3 gap-4">
          <ParamCard>
            <ParamLabel label="强平触发线" description="低于此比例触发强平" />
            <NumberInput
              value={config.liquidationTrigger}
              onChange={(v) => set("liquidationTrigger", v)}
              min={0}
              max={100}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="平仓顺序" description="先平哪些仓位" />
            <Select
              value={config.liquidationOrder}
              onValueChange={(v) => set("liquidationOrder", v)}
            >
              <SelectTrigger className="h-8 text-xs w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="max-loss">最大亏损优先</SelectItem>
                <SelectItem value="max-position">最大仓位优先</SelectItem>
                <SelectItem value="lifo">后进先出</SelectItem>
                <SelectItem value="fifo">先进先出</SelectItem>
              </SelectContent>
            </Select>
          </ParamCard>

          <ParamCard>
            <ParamLabel label="单次平仓比例" description="每次平仓的比例" />
            <NumberInput
              value={config.liquidationRatio}
              onChange={(v) => set("liquidationRatio", v)}
              min={5}
              max={100}
              step={5}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="预警提前量" description="预警线 = 强平线 + 此值" />
            <NumberInput
              value={config.liquidationWarningOffset}
              onChange={(v) => set("liquidationWarningOffset", v)}
              min={0}
              max={20}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="强平通知方式" description="触发强平时通知方式" />
            <NotifyCheckboxGroup
              value={config.liquidationNotify}
              onChange={(v) => set("liquidationNotify", v)}
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="预警通知方式" description="触发预警时通知方式" />
            <NotifyCheckboxGroup
              value={config.warningNotify}
              onChange={(v) => set("warningNotify", v)}
            />
          </ParamCard>
        </div>
      </motion.div>

      {/* Module 3: VaR 限制 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Activity} title="VaR 限制" description="Value at Risk 风险敞口限制" />
        <div className="grid grid-cols-3 gap-4">
          <ParamCard>
            <ParamLabel label="日 VaR 限制" description="单日最大预期损失" />
            <NumberInput
              value={config.dailyVar}
              onChange={(v) => set("dailyVar", v)}
              min={0}
              max={20}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="周 VaR 限制" description="单周最大预期损失" />
            <NumberInput
              value={config.weeklyVar}
              onChange={(v) => set("weeklyVar", v)}
              min={0}
              max={30}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="月 VaR 限制" description="单月最大预期损失" />
            <NumberInput
              value={config.monthlyVar}
              onChange={(v) => set("monthlyVar", v)}
              min={0}
              max={50}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="VaR 计算方法" description="风险价值计算方式" />
            <Select
              value={config.varMethod}
              onValueChange={(v) => set("varMethod", v)}
            >
              <SelectTrigger className="h-8 text-xs w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="historical">历史模拟法</SelectItem>
                <SelectItem value="parametric">参数法</SelectItem>
                <SelectItem value="monte-carlo">蒙特卡洛</SelectItem>
              </SelectContent>
            </Select>
          </ParamCard>

          <ParamCard>
            <ParamLabel label="置信度" description="VaR 置信水平" />
            <Select
              value={config.varConfidence}
              onValueChange={(v) => set("varConfidence", v)}
            >
              <SelectTrigger className="h-8 text-xs w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="90">90%</SelectItem>
                <SelectItem value="95">95%</SelectItem>
                <SelectItem value="99">99%</SelectItem>
              </SelectContent>
            </Select>
          </ParamCard>

          <ParamCard>
            <ParamLabel label="超限处理" description="超过 VaR 限制时的操作" />
            <Select
              value={config.varBreachAction}
              onValueChange={(v) => set("varBreachAction", v)}
            >
              <SelectTrigger className="h-8 text-xs w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="warn">仅告警</SelectItem>
                <SelectItem value="reduce">自动减仓</SelectItem>
                <SelectItem value="pause">暂停交易</SelectItem>
              </SelectContent>
            </Select>
          </ParamCard>
        </div>
      </motion.div>

      {/* Module 4: 异常检测 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Zap} title="异常检测" description="实时监控交易异常" />
        <div className="grid grid-cols-3 gap-4">
          <ParamCard>
            <ParamLabel label="滑点阈值" description="超过此滑点触发告警" />
            <NumberInput
              value={config.slippageThreshold}
              onChange={(v) => set("slippageThreshold", v)}
              min={0}
              max={10}
              step={0.5}
              unit="跳"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="委托失败率阈值" description="失败率超过此值告警" />
            <NumberInput
              value={config.fillFailureRate}
              onChange={(v) => set("fillFailureRate", v)}
              min={0}
              max={50}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="数据延迟阈值" description="数据延迟超过此值告警" />
            <NumberInput
              value={config.dataDelayThreshold}
              onChange={(v) => set("dataDelayThreshold", v)}
              min={0}
              max={60}
              unit="秒"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="流动性阈值" description="盘口深度低于此值告警" />
            <NumberInput
              value={config.liquidityThreshold}
              onChange={(v) => set("liquidityThreshold", v)}
              min={0}
              max={10}
              step={0.1}
              unit="万手"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="异常波动阈值" description="超过此波动率告警" />
            <NumberInput
              value={config.abnormalVolatility}
              onChange={(v) => set("abnormalVolatility", v)}
              min={0}
              max={30}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="告警级别" description="异常检测告警级别" />
            <Select
              value={config.alertLevel}
              onValueChange={(v) => set("alertLevel", v)}
            >
              <SelectTrigger className="h-8 text-xs w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="P0">P0 紧急</SelectItem>
                <SelectItem value="P1">P1 重要</SelectItem>
                <SelectItem value="P2">P2 一般</SelectItem>
              </SelectContent>
            </Select>
          </ParamCard>
        </div>
      </motion.div>

      {/* Module 5: 风控熔断 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Flame} title="风控熔断" description="极端情况下的保护机制" />
        <div className="grid grid-cols-3 gap-4">
          <ParamCard>
            <ParamLabel label="日亏损熔断" description="单日亏损超过此值熔断" />
            <NumberInput
              value={config.dailyLossBreaker}
              onChange={(v) => set("dailyLossBreaker", v)}
              min={0}
              max={20}
              unit="%"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="连续亏损熔断" description="连续亏损次数达到此值熔断" />
            <NumberInput
              value={config.consecutiveLossBreaker}
              onChange={(v) => set("consecutiveLossBreaker", v)}
              min={1}
              max={10}
              unit="次"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="熔断处理" description="触发熔断后的操作" />
            <Select
              value={config.breakerAction}
              onValueChange={(v) => set("breakerAction", v)}
            >
              <SelectTrigger className="h-8 text-xs w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pause-1h">暂停 1 小时</SelectItem>
                <SelectItem value="pause-day">暂停当日</SelectItem>
                <SelectItem value="close-all">平仓后暂停</SelectItem>
              </SelectContent>
            </Select>
          </ParamCard>

          <ParamCard>
            <ParamLabel label="熔断通知方式" description="触发熔断时通知方式" />
            <NotifyCheckboxGroup
              value={config.breakerNotify}
              onChange={(v) => set("breakerNotify", v)}
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="恢复方式" description="熔断后如何恢复交易" />
            <Select
              value={config.breakerRecovery}
              onValueChange={(v) => set("breakerRecovery", v)}
            >
              <SelectTrigger className="h-8 text-xs w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">自动恢复</SelectItem>
                <SelectItem value="manual">手动确认</SelectItem>
              </SelectContent>
            </Select>
          </ParamCard>
        </div>
      </motion.div>

      {/* Module 6: 交易限制 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Scale} title="交易限制" description="交易行为约束" />
        <div className="grid grid-cols-3 gap-4">
          <ParamCard>
            <ParamLabel label="最大持仓品种数" description="同时持仓的品种数量上限" />
            <NumberInput
              value={config.maxHoldingSymbols}
              onChange={(v) => set("maxHoldingSymbols", v)}
              min={1}
              max={20}
              unit="个"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="日内最大交易次数" description="单日交易次数上限" />
            <NumberInput
              value={config.maxDailyTrades}
              onChange={(v) => set("maxDailyTrades", v)}
              min={1}
              max={500}
              unit="笔"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="最小持仓周期" description="开仓后至少持有此周期" />
            <NumberInput
              value={config.minHoldingDays}
              onChange={(v) => set("minHoldingDays", v)}
              min={0}
              max={30}
              unit="天"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="禁止持仓过夜" description="是否允许持仓过夜" />
            <Switch
              checked={config.noOvernightPosition}
              onCheckedChange={(v) => set("noOvernightPosition", v)}
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="强制平仓时间（日盘）" description="日盘强制平仓时间" />
            <Input
              type="time"
              value={config.daySessionCloseTime}
              onChange={(e) => set("daySessionCloseTime", e.target.value)}
              className="h-8 text-xs w-32"
            />
          </ParamCard>

          <ParamCard>
            <ParamLabel label="强制平仓时间（夜盘）" description="夜盘强制平仓时间" />
            <Input
              type="time"
              value={config.nightSessionCloseTime}
              onChange={(e) => set("nightSessionCloseTime", e.target.value)}
              className="h-8 text-xs w-32"
            />
          </ParamCard>
        </div>
      </motion.div>

      {/* Module 7: 黑名单管理 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={Ban} title="黑名单管理" description="禁止交易的品种 / 策略 / 时段" />
        
        {/* Search bar */}
        <div className="mb-4 flex items-center gap-2">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <Input
              placeholder="搜索品种、策略、时段..."
              value={blacklistSearch}
              onChange={(e) => setBlacklistSearch(e.target.value)}
              className="h-8 text-xs pl-8"
            />
          </div>
          {blacklistSearch && (
            <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => setBlacklistSearch("")}>
              <X className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>

        <Tabs defaultValue="symbols">
          <TabsList className="mb-4">
            <TabsTrigger value="symbols" className="text-xs">品种黑名单 ({filteredSymbols.length})</TabsTrigger>
            <TabsTrigger value="strategies" className="text-xs">策略黑名单 ({filteredStrategies.length})</TabsTrigger>
            <TabsTrigger value="periods" className="text-xs">时段黑名单 ({filteredPeriods.length})</TabsTrigger>
          </TabsList>

          {/* 品种黑名单 */}
          <TabsContent value="symbols">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  {selectedSymbols.size > 0 && (
                    <Button size="sm" variant="destructive" className="gap-1 text-xs h-7" onClick={handleBatchDeleteSymbols}>
                      <Trash2 className="w-3 h-3" />
                      批量删除 ({selectedSymbols.size})
                    </Button>
                  )}
                </div>
                <Button size="sm" variant="outline" className="gap-1 text-xs h-7"
                  onClick={() => {
                    setSymbolForm({ code: "", name: "", reason: "", remark: "" });
                    setShowAddSymbolDialog(true);
                  }}>
                  <Plus className="w-3 h-3" />
                  添加品种
                </Button>
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left py-2 px-2 w-8">
                      <Checkbox
                        checked={selectedSymbols.size === filteredSymbols.length && filteredSymbols.length > 0}
                        onCheckedChange={(checked) => {
                          if (checked) setSelectedSymbols(new Set(filteredSymbols.map(s => s.id)));
                          else setSelectedSymbols(new Set());
                        }}
                      />
                    </th>
                    {["品种代码", "品种名称", "添加时间", "添加原因", "备注", "操作"].map((h) => (
                      <th key={h} className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredSymbols.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-muted-foreground">
                        暂无数据
                      </td>
                    </tr>
                  ) : filteredSymbols.map((s) => (
                    <tr key={s.id} className="border-b border-border/30 hover:bg-muted/30">
                      <td className="py-2 px-2">
                        <Checkbox
                          checked={selectedSymbols.has(s.id)}
                          onCheckedChange={(checked) => {
                            const newSet = new Set(selectedSymbols);
                            if (checked) newSet.add(s.id);
                            else newSet.delete(s.id);
                            setSelectedSymbols(newSet);
                          }}
                        />
                      </td>
                      <td className="py-2 px-2 font-mono text-foreground whitespace-nowrap">{s.code}</td>
                      <td className="py-2 px-2 text-foreground whitespace-nowrap">{s.name}</td>
                      <td className="py-2 px-2 text-muted-foreground whitespace-nowrap">{s.addedAt}</td>
                      <td className="py-2 px-2 text-muted-foreground">{s.reason}</td>
                      <td className="py-2 px-2 text-muted-foreground max-w-[150px] truncate" title={s.remark}>{s.remark || "-"}</td>
                      <td className="py-2 px-2 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px] gap-1"
                            onClick={() => {
                              setEditingSymbol(s);
                              setSymbolForm({ code: s.code, name: s.name, reason: s.reason, remark: s.remark || "" });
                            }}>
                            <Edit2 className="w-3 h-3" />编辑
                          </Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px] gap-1 text-destructive hover:text-destructive"
                            onClick={() => {
                              setSymbols((prev) => prev.filter((x) => x.id !== s.id));
                              toast.success("已移除");
                            }}>
                            <Trash2 className="w-3 h-3" />移除
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TabsContent>

          {/* 策略黑名单 */}
          <TabsContent value="strategies">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  {selectedStrategies.size > 0 && (
                    <Button size="sm" variant="destructive" className="gap-1 text-xs h-7" onClick={handleBatchDeleteStrategies}>
                      <Trash2 className="w-3 h-3" />
                      批量删除 ({selectedStrategies.size})
                    </Button>
                  )}
                </div>
                <Button size="sm" variant="outline" className="gap-1 text-xs h-7"
                  onClick={() => {
                    setStrategyForm({ name: "", strategyId: "", reason: "", remark: "" });
                    setShowAddStrategyDialog(true);
                  }}>
                  <Plus className="w-3 h-3" />
                  添加策略
                </Button>
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left py-2 px-2 w-8">
                      <Checkbox
                        checked={selectedStrategies.size === filteredStrategies.length && filteredStrategies.length > 0}
                        onCheckedChange={(checked) => {
                          if (checked) setSelectedStrategies(new Set(filteredStrategies.map(s => s.id)));
                          else setSelectedStrategies(new Set());
                        }}
                      />
                    </th>
                    {["策略名称", "策略 ID", "添加时间", "添加原因", "备注", "操作"].map((h) => (
                      <th key={h} className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredStrategies.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-muted-foreground">
                        暂无数据
                      </td>
                    </tr>
                  ) : filteredStrategies.map((s) => (
                    <tr key={s.id} className="border-b border-border/30 hover:bg-muted/30">
                      <td className="py-2 px-2">
                        <Checkbox
                          checked={selectedStrategies.has(s.id)}
                          onCheckedChange={(checked) => {
                            const newSet = new Set(selectedStrategies);
                            if (checked) newSet.add(s.id);
                            else newSet.delete(s.id);
                            setSelectedStrategies(newSet);
                          }}
                        />
                      </td>
                      <td className="py-2 px-2 text-foreground whitespace-nowrap">{s.name}</td>
                      <td className="py-2 px-2 font-mono text-foreground whitespace-nowrap">{s.strategyId}</td>
                      <td className="py-2 px-2 text-muted-foreground whitespace-nowrap">{s.addedAt}</td>
                      <td className="py-2 px-2 text-muted-foreground">{s.reason}</td>
                      <td className="py-2 px-2 text-muted-foreground max-w-[150px] truncate" title={s.remark}>{s.remark || "-"}</td>
                      <td className="py-2 px-2 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px] gap-1"
                            onClick={() => {
                              setEditingStrategy(s);
                              setStrategyForm({ name: s.name, strategyId: s.strategyId, reason: s.reason, remark: s.remark || "" });
                            }}>
                            <Edit2 className="w-3 h-3" />编辑
                          </Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px] gap-1 text-destructive hover:text-destructive"
                            onClick={() => {
                              setStrategies((prev) => prev.filter((x) => x.id !== s.id));
                              toast.success("已移除");
                            }}>
                            <Trash2 className="w-3 h-3" />移除
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TabsContent>

          {/* 时段黑名单 */}
          <TabsContent value="periods">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  {selectedPeriods.size > 0 && (
                    <Button size="sm" variant="destructive" className="gap-1 text-xs h-7" onClick={handleBatchDeletePeriods}>
                      <Trash2 className="w-3 h-3" />
                      批量删除 ({selectedPeriods.size})
                    </Button>
                  )}
                </div>
                <Button size="sm" variant="outline" className="gap-1 text-xs h-7"
                  onClick={() => {
                    setPeriodForm({ description: "", startTime: "", endTime: "", repeat: "每日", remark: "" });
                    setShowAddPeriodDialog(true);
                  }}>
                  <Plus className="w-3 h-3" />
                  添加时段
                </Button>
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left py-2 px-2 w-8">
                      <Checkbox
                        checked={selectedPeriods.size === filteredPeriods.length && filteredPeriods.length > 0}
                        onCheckedChange={(checked) => {
                          if (checked) setSelectedPeriods(new Set(filteredPeriods.map(p => p.id)));
                          else setSelectedPeriods(new Set());
                        }}
                      />
                    </th>
                    {["时段描述", "开始时间", "结束时间", "重复规则", "备注", "操作"].map((h) => (
                      <th key={h} className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredPeriods.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-muted-foreground">
                        暂无数据
                      </td>
                    </tr>
                  ) : filteredPeriods.map((p) => (
                    <tr key={p.id} className="border-b border-border/30 hover:bg-muted/30">
                      <td className="py-2 px-2">
                        <Checkbox
                          checked={selectedPeriods.has(p.id)}
                          onCheckedChange={(checked) => {
                            const newSet = new Set(selectedPeriods);
                            if (checked) newSet.add(p.id);
                            else newSet.delete(p.id);
                            setSelectedPeriods(newSet);
                          }}
                        />
                      </td>
                      <td className="py-2 px-2 text-foreground whitespace-nowrap">{p.description}</td>
                      <td className="py-2 px-2 font-mono text-foreground whitespace-nowrap">{p.startTime}</td>
                      <td className="py-2 px-2 font-mono text-foreground whitespace-nowrap">{p.endTime}</td>
                      <td className="py-2 px-2 text-muted-foreground whitespace-nowrap">{p.repeat}</td>
                      <td className="py-2 px-2 text-muted-foreground max-w-[150px] truncate" title={p.remark}>{p.remark || "-"}</td>
                      <td className="py-2 px-2 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px] gap-1"
                            onClick={() => {
                              setEditingPeriod(p);
                              setPeriodForm({ description: p.description, startTime: p.startTime, endTime: p.endTime, repeat: p.repeat, remark: p.remark || "" });
                            }}>
                            <Edit2 className="w-3 h-3" />编辑
                          </Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px] gap-1 text-destructive hover:text-destructive"
                            onClick={() => {
                              setPeriods((prev) => prev.filter((x) => x.id !== p.id));
                              toast.success("已移除");
                            }}>
                            <Trash2 className="w-3 h-3" />移除
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TabsContent>
        </Tabs>
      </motion.div>

      {/* 配置操作区 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card-surface p-5"
      >
        <SectionHeader icon={FileJson} title="配置信息" />
        <div className="flex items-center gap-6 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>最后保存：{lastSaved}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileJson className="w-3.5 h-3.5" />
            <span>配置版本：{version}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <History className="w-3.5 h-3.5" />
            <span>修改记录：{changeCount} 次</span>
          </div>
        </div>
      </motion.div>

      {/* Save Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>确认保存配置</DialogTitle>
            <DialogDescription>
              即将保存风控参数配置，此操作将立即生效并影响交易系统风控行为，请确认无误后继续。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowSaveDialog(false)}>
              取消
            </Button>
<Button size="sm" onClick={handleSave} disabled={saving}>
{saving ? <><Spinner className="w-4 h-4 mr-1" />保存中...</> : "确认保存"}
</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset Dialog */}
      <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>恢复默认配置</DialogTitle>
            <DialogDescription>
              此操作将清除所有自定义配置，恢复系统默认风控参数，确认继续？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowResetDialog(false)}>
              取消
            </Button>
            <Button variant="destructive" size="sm" onClick={handleReset}>
              确认恢复
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preset Dialog */}
      <Dialog open={showPresetDialog} onOpenChange={setShowPresetDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>选择预设方案</DialogTitle>
            <DialogDescription>
              选择预设方案将覆盖仓位限制、VaR 限制和熔断参数，其他参数保持不变。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            {(Object.keys(PRESETS) as Array<keyof typeof PRESETS>).map((key) => {
              const preset = PRESETS[key];
              return (
                <div
                  key={key}
                  className="p-3 border border-border/50 rounded-lg hover:bg-muted/30 cursor-pointer transition-colors"
                  onClick={() => applyPreset(key)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-foreground">{preset.name}</span>
                    <span className="text-[10px] text-muted-foreground">{preset.description}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-[10px] text-muted-foreground">
                    <span>总仓位: {preset.totalPositionLimit}%</span>
                    <span>单品种: {preset.singleSymbolLimit}%</span>
                    <span>日VaR: {preset.dailyVar}%</span>
                  </div>
                </div>
              );
            })}
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowPresetDialog(false)}>
              取消
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={showImportDialog} onOpenChange={(open) => {
        setShowImportDialog(open);
        if (!open) {
          setImportPreview(null);
          setImportError(null);
          if (fileInputRef.current) fileInputRef.current.value = "";
        }
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>导入配置</DialogTitle>
            <DialogDescription>
              导入将覆盖当前所有风控参数配置，请确认您已备份现有配置后继续。
            </DialogDescription>
          </DialogHeader>
          <div className="py-3 space-y-3">
            <Input 
              ref={fileInputRef}
              type="file" 
              accept=".json" 
              className="text-xs" 
              onChange={handleFileSelect}
            />
            
            {importError && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 text-xs text-destructive">
                <X className="w-4 h-4 shrink-0" />
                <span>{importError}</span>
              </div>
            )}
            
            {importPreview && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg space-y-2">
                <div className="flex items-center gap-2 text-xs text-emerald-600">
                  <FileCheck className="w-4 h-4" />
                  <span>配置验证通过</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[10px] text-muted-foreground">
                  <span>总仓位: {importPreview.totalPositionLimit}%</span>
                  <span>单品种: {importPreview.singleSymbolLimit}%</span>
                  <span>日VaR: {importPreview.dailyVar}%</span>
                  <span>强平线: {importPreview.liquidationTrigger}%</span>
                </div>
              </div>
            )}
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowImportDialog(false)}>
              取消
            </Button>
            <Button size="sm" onClick={handleImport} disabled={!importPreview}>
              确认导入
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Symbol Dialog */}
      <Dialog open={showAddSymbolDialog} onOpenChange={setShowAddSymbolDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>添加品种黑名单</DialogTitle>
            <DialogDescription>
              添加后该品种将被禁止交易。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">品种代码 *</label>
              <Input
                placeholder="如 rb2405"
                value={symbolForm.code}
                onChange={(e) => setSymbolForm(f => ({ ...f, code: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">品种名称 *</label>
              <Input
                placeholder="如 螺纹钢"
                value={symbolForm.name}
                onChange={(e) => setSymbolForm(f => ({ ...f, name: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">添加原因 *</label>
              <Input
                placeholder="如 流动性不足/波动过大"
                value={symbolForm.reason}
                onChange={(e) => setSymbolForm(f => ({ ...f, reason: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">备注</label>
              <Input
                placeholder="可选备注信息"
                value={symbolForm.remark}
                onChange={(e) => setSymbolForm(f => ({ ...f, remark: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowAddSymbolDialog(false)}>
              取消
            </Button>
            <Button size="sm" onClick={handleAddSymbol}>
              确认添加
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Symbol Dialog */}
      <Dialog open={!!editingSymbol} onOpenChange={(open) => !open && setEditingSymbol(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>编辑品种黑名单</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">品种代码 *</label>
              <Input
                placeholder="如 rb2405"
                value={symbolForm.code}
                onChange={(e) => setSymbolForm(f => ({ ...f, code: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">品种名称 *</label>
              <Input
                placeholder="如 螺纹钢"
                value={symbolForm.name}
                onChange={(e) => setSymbolForm(f => ({ ...f, name: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">添加原因 *</label>
              <Input
                placeholder="如 流动性不足/波动过大"
                value={symbolForm.reason}
                onChange={(e) => setSymbolForm(f => ({ ...f, reason: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">备注</label>
              <Input
                placeholder="可选备注信息"
                value={symbolForm.remark}
                onChange={(e) => setSymbolForm(f => ({ ...f, remark: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setEditingSymbol(null)}>
              取消
            </Button>
            <Button size="sm" onClick={handleEditSymbol}>
              保存修改
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Strategy Dialog */}
      <Dialog open={showAddStrategyDialog} onOpenChange={setShowAddStrategyDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>添加策略黑名单</DialogTitle>
            <DialogDescription>
              添加后该策略将被禁止运行。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">策略名称 *</label>
              <Input
                placeholder="如 高频动量策略"
                value={strategyForm.name}
                onChange={(e) => setStrategyForm(f => ({ ...f, name: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">策略 ID *</label>
              <Input
                placeholder="如 HFM-001"
                value={strategyForm.strategyId}
                onChange={(e) => setStrategyForm(f => ({ ...f, strategyId: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">添加原因 *</label>
              <Input
                placeholder="如 回撤超限/失效"
                value={strategyForm.reason}
                onChange={(e) => setStrategyForm(f => ({ ...f, reason: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">备注</label>
              <Input
                placeholder="可选备注信息"
                value={strategyForm.remark}
                onChange={(e) => setStrategyForm(f => ({ ...f, remark: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowAddStrategyDialog(false)}>
              取消
            </Button>
            <Button size="sm" onClick={handleAddStrategy}>
              确认添加
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Strategy Dialog */}
      <Dialog open={!!editingStrategy} onOpenChange={(open) => !open && setEditingStrategy(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>编辑策略黑名单</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">策略名称 *</label>
              <Input
                placeholder="如 高频动量策略"
                value={strategyForm.name}
                onChange={(e) => setStrategyForm(f => ({ ...f, name: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">策略 ID *</label>
              <Input
                placeholder="如 HFM-001"
                value={strategyForm.strategyId}
                onChange={(e) => setStrategyForm(f => ({ ...f, strategyId: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">添加原因 *</label>
              <Input
                placeholder="如 回撤超限/失效"
                value={strategyForm.reason}
                onChange={(e) => setStrategyForm(f => ({ ...f, reason: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">备注</label>
              <Input
                placeholder="可选备注信息"
                value={strategyForm.remark}
                onChange={(e) => setStrategyForm(f => ({ ...f, remark: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setEditingStrategy(null)}>
              取消
            </Button>
            <Button size="sm" onClick={handleEditStrategy}>
              保存修改
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Period Dialog */}
      <Dialog open={showAddPeriodDialog} onOpenChange={setShowAddPeriodDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>添加时段黑名单</DialogTitle>
            <DialogDescription>
              添加后该时段将禁止交易。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">时段描述 *</label>
              <Input
                placeholder="如 重大节假日前后"
                value={periodForm.description}
                onChange={(e) => setPeriodForm(f => ({ ...f, description: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground">开始时间 *</label>
                <Input
                  type="time"
                  value={periodForm.startTime}
                  onChange={(e) => setPeriodForm(f => ({ ...f, startTime: e.target.value }))}
                  className="h-8 text-xs"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground">结束时间 *</label>
                <Input
                  type="time"
                  value={periodForm.endTime}
                  onChange={(e) => setPeriodForm(f => ({ ...f, endTime: e.target.value }))}
                  className="h-8 text-xs"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">重复规则 *</label>
              <Select
                value={periodForm.repeat}
                onValueChange={(v) => setPeriodForm(f => ({ ...f, repeat: v }))}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="每日">每日</SelectItem>
                  <SelectItem value="每周">每周</SelectItem>
                  <SelectItem value="每月">每月</SelectItem>
                  <SelectItem value="自定义">自定义</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">备注</label>
              <Input
                placeholder="可选备注信息"
                value={periodForm.remark}
                onChange={(e) => setPeriodForm(f => ({ ...f, remark: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowAddPeriodDialog(false)}>
              取消
            </Button>
            <Button size="sm" onClick={handleAddPeriod}>
              确认添加
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Period Dialog */}
      <Dialog open={!!editingPeriod} onOpenChange={(open) => !open && setEditingPeriod(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>编辑时段黑名单</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">时段描述 *</label>
              <Input
                placeholder="如 重大节假日前后"
                value={periodForm.description}
                onChange={(e) => setPeriodForm(f => ({ ...f, description: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground">开始时间 *</label>
                <Input
                  type="time"
                  value={periodForm.startTime}
                  onChange={(e) => setPeriodForm(f => ({ ...f, startTime: e.target.value }))}
                  className="h-8 text-xs"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground">结束时间 *</label>
                <Input
                  type="time"
                  value={periodForm.endTime}
                  onChange={(e) => setPeriodForm(f => ({ ...f, endTime: e.target.value }))}
                  className="h-8 text-xs"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">重复规则 *</label>
              <Select
                value={periodForm.repeat}
                onValueChange={(v) => setPeriodForm(f => ({ ...f, repeat: v }))}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="每日">每日</SelectItem>
                  <SelectItem value="每周">每周</SelectItem>
                  <SelectItem value="每月">每月</SelectItem>
                  <SelectItem value="自定义">自定义</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">备注</label>
              <Input
                placeholder="可选备注信息"
                value={periodForm.remark}
                onChange={(e) => setPeriodForm(f => ({ ...f, remark: e.target.value }))}
                className="h-8 text-xs"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" onClick={() => setEditingPeriod(null)}>
              取消
            </Button>
            <Button size="sm" onClick={handleEditPeriod}>
              保存修改
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
