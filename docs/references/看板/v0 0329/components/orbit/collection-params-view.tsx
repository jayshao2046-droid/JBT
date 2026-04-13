"use client";
// uses useToastActions from toast-provider (no addToast)
import React, { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useToastActions } from "./toast-provider";
import {
  Database,
  Clock,
  Repeat,
  RotateCcw,
  HardDrive,
  PlusCircle,
  Save,
  Download,
  Upload,
  X,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Wifi,
  WifiOff,
  Edit3,
  Trash2,
  TestTube,
  ChevronRight,
  ArrowRight,
  Info,
  FolderOpen,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

// ─── Types ─────────────────────────────────────────────────────────────────

interface DataSourceToggle {
  id: string;
  name: string;
  enabled: boolean;
}

type DataSourceCategory = "market" | "fundamental" | "macro" | "alternative" | "exchange";

interface RedundancyConfig {
  primary: string;
  secondary: string;
  tertiary?: string;
  switchStrategy: "auto" | "manual";
  failCount: number;
  delayThreshold?: number;
  qualityThreshold?: number;
  missingDataThreshold?: number;
  switchBackStrategy: "immediate" | "stable";
  switchBackWait: number;
  currentSource: string;
  lastSwitchTime: string;
  switchCountToday: number;
}

interface SwitchLog {
  time: string;
  type: string;
  from: string;
  to: string;
  reason: string;
  status: "成功" | "失败";
}

interface CustomSource {
  id: string;
  name: string;
  type: string;
  provider: string;
  apiUrl: string;
  authType: "apiKey" | "oauth2" | "basic" | "none";
  apiKey?: string;
  frequency: string;
  timeout: number;
  maxRetries: number;
  dataFormat: string;
  role: "primary" | "secondary" | "tertiary";
  priority: number;
  status: "normal" | "delayed" | "failed";
  lastCollection: string;
  successRate: number;
}

// ─── Mock Data ──────────────────────────────────────────────────────────────

const defaultDataSources: Record<DataSourceCategory, DataSourceToggle[]> = {
  market: [
    { id: "tushare", name: "Tushare Pro", enabled: true },
    { id: "akshare", name: "AkShare", enabled: true },
    { id: "wind", name: "Wind", enabled: true },
    { id: "choice", name: "Choice", enabled: false },
    { id: "joinquant", name: "聚宽", enabled: false },
    { id: "uqer", name: "优矿", enabled: false },
    { id: "ricequant", name: "Ricequant", enabled: false },
    { id: "ticker", name: "Ticker", enabled: false },
    { id: "yahoo", name: "Yahoo Finance", enabled: false },
    { id: "alpha", name: "Alpha Vantage", enabled: false },
    { id: "bloomberg", name: "Bloomberg", enabled: false },
    { id: "reuters", name: "Reuters", enabled: false },
    { id: "ice", name: "ICE", enabled: false },
    { id: "cme", name: "CME", enabled: false },
    { id: "shfe", name: "SHFE", enabled: false },
  ],
  fundamental: [
    { id: "financial_report", name: "财报数据", enabled: true },
    { id: "announcement", name: "公告数据", enabled: true },
    { id: "research_report", name: "研报数据", enabled: true },
    { id: "institution", name: "机构调研", enabled: false },
    { id: "shareholder", name: "股东数据", enabled: false },
    { id: "dragon_tiger", name: "龙虎榜", enabled: false },
    { id: "margin", name: "融资融券", enabled: false },
    { id: "block_trade", name: "大宗交易", enabled: false },
    { id: "pledge", name: "股权质押", enabled: false },
    { id: "lock_up", name: "限售解禁", enabled: false },
    { id: "dividend", name: "分红送转", enabled: false },
    { id: "forecast", name: "业绩预告", enabled: false },
  ],
  macro: [
    { id: "gdp", name: "GDP", enabled: true },
    { id: "cpi", name: "CPI", enabled: true },
    { id: "ppi", name: "PPI", enabled: true },
    { id: "pmi", name: "PMI", enabled: true },
    { id: "interest_rate", name: "利率", enabled: false },
    { id: "exchange_rate", name: "汇率", enabled: false },
    { id: "central_bank", name: "央行数据", enabled: false },
    { id: "fiscal", name: "财政数据", enabled: false },
  ],
  alternative: [
    { id: "sentiment", name: "舆情数据", enabled: true },
    { id: "satellite", name: "卫星数据", enabled: true },
    { id: "supply_chain", name: "供应链数据", enabled: false },
    { id: "ecommerce", name: "电商数据", enabled: false },
    { id: "social_media", name: "社交媒体", enabled: false },
    { id: "search_index", name: "搜索指数", enabled: false },
    { id: "weather", name: "天气数据", enabled: false },
  ],
  exchange: [
    { id: "shfe_ex", name: "上期所", enabled: true },
    { id: "dce", name: "大商所", enabled: true },
    { id: "czce", name: "郑商所", enabled: true },
    { id: "cffex", name: "中金所", enabled: true },
    { id: "sse", name: "上交所", enabled: true },
  ],
};

const defaultRedundancy: Record<string, RedundancyConfig> = {
  market: {
    primary: "Tushare",
    secondary: "AkShare",
    tertiary: "Wind",
    switchStrategy: "auto",
    failCount: 3,
    delayThreshold: 5,
    qualityThreshold: 80,
    switchBackStrategy: "stable",
    switchBackWait: 30,
    currentSource: "Tushare",
    lastSwitchTime: "2026-03-21 14:30:25",
    switchCountToday: 2,
  },
  macro: {
    primary: "Wind",
    secondary: "Choice",
    tertiary: "Tushare",
    switchStrategy: "auto",
    failCount: 2,
    delayThreshold: 10,
    missingDataThreshold: 10,
    switchBackStrategy: "stable",
    switchBackWait: 60,
    currentSource: "Choice",
    lastSwitchTime: "2026-03-21 10:15:00",
    switchCountToday: 1,
  },
  fundamental: {
    primary: "Tushare",
    secondary: "Choice",
    switchStrategy: "auto",
    failCount: 3,
    qualityThreshold: 85,
    switchBackStrategy: "stable",
    switchBackWait: 120,
    currentSource: "Tushare",
    lastSwitchTime: "2026-03-20 09:00:00",
    switchCountToday: 0,
  },
};

const switchLogs: SwitchLog[] = [
  { time: "03-21 10:15", type: "宏观数据", from: "Wind", to: "Choice", reason: "主源失败", status: "成功" },
  { time: "03-21 08:30", type: "行情数据", from: "Tushare", to: "AkShare", reason: "延迟过高", status: "成功" },
  { time: "03-20 14:00", type: "基本面", from: "Tushare", to: "Choice", reason: "数据质量低", status: "成功" },
];

const defaultCustomSources: CustomSource[] = [
  {
    id: "custom_001", name: "新华财经", type: "宏观", provider: "新华网",
    apiUrl: "https://api.xinhuanet.com/finance/v1", authType: "apiKey",
    apiKey: "xh_***********", frequency: "每小时", timeout: 10, maxRetries: 3,
    dataFormat: "JSON", role: "secondary", priority: 50,
    status: "normal", lastCollection: "08:00", successRate: 98.5,
  },
  {
    id: "custom_002", name: "物流指闻", type: "另类", provider: "物流56",
    apiUrl: "https://www.logistic56.com/api", authType: "none",
    frequency: "每小时", timeout: 10, maxRetries: 3,
    dataFormat: "HTML", role: "secondary", priority: 45,
    status: "normal", lastCollection: "09:00", successRate: 95.2,
  },
  {
    id: "custom_003", name: "FreightWaves", type: "另类", provider: "FW",
    apiUrl: "https://api.freightwaves.com/v1", authType: "apiKey",
    apiKey: "fw_***********", frequency: "每小时", timeout: 15, maxRetries: 3,
    dataFormat: "JSON", role: "tertiary", priority: 40,
    status: "delayed", lastCollection: "07:30", successRate: 82.1,
  },
];

// ─── Sub-components ──────────────────────────────────────────────────────────

function SectionHeader({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: typeof Database;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between mb-5">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-primary" />
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

function FormLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return (
    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
      {children}
      {required && <span className="text-destructive ml-0.5">*</span>}
    </label>
  );
}

function ConfigInput({
  value,
  onChange,
  type = "text",
  placeholder,
  min,
  max,
  className,
  error,
}: {
  value: string | number;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  className?: string;
  error?: string;
}) {
  return (
    <div className="relative">
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        className={cn(
          "h-8 text-xs bg-muted/30 border-border/60",
          error && "border-destructive/60 focus-visible:ring-destructive/30",
          className
        )}
      />
      {error && (
        <p className="text-[10px] text-destructive mt-1 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}
    </div>
  );
}

function SourceStatusBadge({ status, source, isPrimary }: { status: string; source: string; isPrimary: boolean }) {
  const isNormal = isPrimary;
  return (
    <div className={cn(
      "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium",
      isNormal
        ? "bg-emerald-500/10 text-emerald-600"
        : "bg-amber-500/10 text-amber-600"
    )}>
      <span className={cn("w-1.5 h-1.5 rounded-full", isNormal ? "bg-emerald-500" : "bg-amber-500")} />
      {source}（{isPrimary ? "主源" : "副源"}）
      {!isPrimary && <AlertTriangle className="w-3 h-3" />}
    </div>
  );
}

function CustomSourceStatusDot({ status }: { status: CustomSource["status"] }) {
  const map = {
    normal: { color: "bg-emerald-500", label: "正常" },
    delayed: { color: "bg-amber-500", label: "延迟" },
    failed: { color: "bg-red-500", label: "失败" },
  };
  const s = map[status];
  return (
    <div className="flex items-center gap-1.5">
      <span className={cn("w-2 h-2 rounded-full", s.color)} />
      <span className="text-xs text-muted-foreground">{s.label}</span>
    </div>
  );
}

// ─── Confirm Modal ────────────────────────────────────────────────────────────

function ConfirmSaveModal({
  open,
  onClose,
  onConfirm,
  changes,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  changes: string[];
}) {
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            className="relative z-10 w-[480px] bg-card border border-border rounded-xl shadow-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
                <Save className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">确认保存配置？</h3>
                <p className="text-xs text-muted-foreground mt-0.5">以下配置将被修改</p>
              </div>
            </div>
            <div className="space-y-1.5 mb-5 max-h-48 overflow-y-auto">
              {changes.map((c, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-foreground">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                  {c}
                </div>
              ))}
            </div>
            <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/8 border border-amber-500/20 mb-5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />
              <p className="text-[11px] text-amber-600">注意：部分配置需要重启采集服务后生效</p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={onClose}>取消</Button>
              <Button size="sm" className="gap-1.5 bg-primary text-primary-foreground" onClick={onConfirm}>
                <Save className="w-3.5 h-3.5" />
                确认保存
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

// ─── Add Source Modal ─────────────────────────────────────────────────────────

function AddSourceModal({
  open,
  onClose,
  onAdd,
}: {
  open: boolean;
  onClose: () => void;
  onAdd: (source: CustomSource) => void;
}) {
  const [name, setName] = useState("");
  const [type, setType] = useState("宏观");
  const [provider, setProvider] = useState("");
  const [description, setDescription] = useState("");
  const [apiUrl, setApiUrl] = useState("");
  const [authType, setAuthType] = useState<"apiKey" | "oauth2" | "basic" | "none">("apiKey");
  const [apiKey, setApiKey] = useState("");
  const [frequency, setFrequency] = useState("每小时");
  const [timeout, setTimeout2] = useState("10");
  const [maxRetries, setMaxRetries] = useState("3");
  const [dataFormat, setDataFormat] = useState("JSON");
  const [role, setRole] = useState<"primary" | "secondary" | "tertiary">("secondary");
  const [priority, setPriority] = useState("50");
  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "failed">("idle");
  const [testLatency, setTestLatency] = useState(0);

  const errors: Record<string, string> = {};
  if (name && name.trim().length < 2) errors.name = "名称至少2个字符";
  if (apiUrl && !apiUrl.startsWith("http")) errors.apiUrl = "���输入有效的 URL（以 http/https 开头）";
  const timeoutNum = parseInt(timeout);
  if (timeout && (isNaN(timeoutNum) || timeoutNum < 1 || timeoutNum > 60)) errors.timeout = "超时时间 1-60 秒";
  const priorityNum = parseInt(priority);
  if (priority && (isNaN(priorityNum) || priorityNum < 1 || priorityNum > 100)) errors.priority = "优先级 1-100";

  const handleTest = () => {
    if (!apiUrl) return;
    setTestStatus("testing");
    setTimeout(() => {
      const latency = Math.floor(Math.random() * 200) + 50;
      setTestLatency(latency);
      setTestStatus(latency < 300 ? "success" : "failed");
    }, 1800);
  };

  const handleAdd = () => {
    if (!name || !apiUrl) return;
    onAdd({
      id: `custom_${Date.now()}`,
      name, type, provider, apiUrl, authType, apiKey,
      frequency, timeout: parseInt(timeout) || 10,
      maxRetries: parseInt(maxRetries) || 3,
      dataFormat, role, priority: parseInt(priority) || 50,
      status: "normal", lastCollection: "-", successRate: 0,
    });
    onClose();
  };

  const isValid = name.trim().length >= 2 && apiUrl.startsWith("http") && Object.keys(errors).length === 0;

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            className="relative z-10 w-[580px] max-h-[90vh] overflow-y-auto bg-card border border-border rounded-xl shadow-2xl"
          >
            {/* Header */}
            <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <PlusCircle className="w-4 h-4 text-primary" />
                </div>
                <h3 className="text-sm font-semibold text-foreground">添加新数据源</h3>
              </div>
              <button onClick={onClose} className="w-7 h-7 rounded-md hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div>
                <p className="text-xs font-semibold text-foreground mb-3 flex items-center gap-2">
                  <Info className="w-3.5 h-3.5 text-muted-foreground" />
                  基本信息
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <FormLabel required>数据源名称</FormLabel>
                    <ConfigInput value={name} onChange={setName} placeholder="如 新华财经" error={errors.name} />
                  </div>
                  <div>
                    <FormLabel required>数据类型</FormLabel>
                    <Select value={type} onValueChange={setType}>
                      <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {["行情数据", "基本面", "宏观", "另类", "交易所"].map((t) => (
                          <SelectItem key={t} value={t} className="text-xs">{t}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <FormLabel>供应商</FormLabel>
                    <ConfigInput value={provider} onChange={setProvider} placeholder="如 新华网" />
                  </div>
                  <div>
                    <FormLabel>描述</FormLabel>
                    <ConfigInput value={description} onChange={setDescription} placeholder="可选" />
                  </div>
                </div>
              </div>

              {/* Connection */}
              <div>
                <p className="text-xs font-semibold text-foreground mb-3 flex items-center gap-2">
                  <Wifi className="w-3.5 h-3.5 text-muted-foreground" />
                  连接配置
                </p>
                <div className="space-y-3">
                  <div>
                    <FormLabel required>API 地址</FormLabel>
                    <ConfigInput value={apiUrl} onChange={setApiUrl} placeholder="https://api.example.com/v1" error={errors.apiUrl} />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <FormLabel>认证方式</FormLabel>
                      <Select value={authType} onValueChange={(v) => setAuthType(v as typeof authType)}>
                        <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="apiKey" className="text-xs">API Key</SelectItem>
                          <SelectItem value="oauth2" className="text-xs">OAuth2</SelectItem>
                          <SelectItem value="basic" className="text-xs">用户名密码</SelectItem>
                          <SelectItem value="none" className="text-xs">无认证</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    {authType !== "none" && (
                      <div>
                        <FormLabel>API Key / Token</FormLabel>
                        <ConfigInput value={apiKey} onChange={setApiKey} placeholder="••••••••" type="password" />
                      </div>
                    )}
                  </div>
                  {/* Test Connection */}
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleTest}
                      disabled={!apiUrl || testStatus === "testing"}
                      className="gap-1.5 text-xs"
                    >
                      {testStatus === "testing" ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <TestTube className="w-3.5 h-3.5" />
                      )}
                      测试连接
                    </Button>
                    <AnimatePresence mode="wait">
                      {testStatus === "testing" && (
                        <motion.span key="testing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-xs text-muted-foreground">
                          正在连接...
                        </motion.span>
                      )}
                      {testStatus === "success" && (
                        <motion.span key="success" initial={{ opacity: 0, x: -5 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="flex items-center gap-1.5 text-xs text-emerald-600">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          连接成功！延迟 {testLatency}ms
                        </motion.span>
                      )}
                      {testStatus === "failed" && (
                        <motion.span key="failed" initial={{ opacity: 0, x: -5 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="flex items-center gap-1.5 text-xs text-red-600">
                          <WifiOff className="w-3.5 h-3.5" />
                          连接失败，请检查 API 地址
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </div>

              {/* Collection Params */}
              <div>
                <p className="text-xs font-semibold text-foreground mb-3 flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                  采集参数
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <FormLabel>采集频率</FormLabel>
                    <Select value={frequency} onValueChange={setFrequency}>
                      <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {["实时", "每分钟", "每15分钟", "每小时", "每日"].map((f) => (
                          <SelectItem key={f} value={f} className="text-xs">{f}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <FormLabel>数据格式</FormLabel>
                    <Select value={dataFormat} onValueChange={setDataFormat}>
                      <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {["JSON", "XML", "CSV", "HTML"].map((f) => (
                          <SelectItem key={f} value={f} className="text-xs">{f}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <FormLabel>超时时间（秒）</FormLabel>
                    <ConfigInput value={timeout} onChange={setTimeout2} type="number" min={1} max={60} error={errors.timeout} />
                  </div>
                  <div>
                    <FormLabel>重试次数</FormLabel>
                    <ConfigInput value={maxRetries} onChange={setMaxRetries} type="number" min={0} max={10} />
                  </div>
                </div>
              </div>

              {/* Redundancy */}
              <div>
                <p className="text-xs font-semibold text-foreground mb-3 flex items-center gap-2">
                  <Repeat className="w-3.5 h-3.5 text-muted-foreground" />
                  冗余配置
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <FormLabel>作为</FormLabel>
                    <Select value={role} onValueChange={(v) => setRole(v as typeof role)}>
                      <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="primary" className="text-xs">主源</SelectItem>
                        <SelectItem value="secondary" className="text-xs">副源</SelectItem>
                        <SelectItem value="tertiary" className="text-xs">第三源</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <FormLabel>优先级 (1-100)</FormLabel>
                    <ConfigInput value={priority} onChange={setPriority} type="number" min={1} max={100} error={errors.priority} />
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 bg-card border-t border-border px-6 py-4 flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={onClose}>取消</Button>
              <Button
                size="sm"
                disabled={!isValid}
                className="gap-1.5 bg-primary text-primary-foreground"
                onClick={handleAdd}
              >
                <PlusCircle className="w-3.5 h-3.5" />
                确认添加
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function CollectionParamsView() {
  const toast = useToastActions();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State: data sources
  const [dataSources, setDataSources] = useState(defaultDataSources);
  const [activeTab, setActiveTab] = useState<DataSourceCategory>("market");

  // State: collection frequency
  const [marketInterval, setMarketInterval] = useState("1");
  const [marketUnit, setMarketUnit] = useState("秒");
  const [fundamentalTime, setFundamentalTime] = useState("09:00");
  const [fundamentalFreq, setFundamentalFreq] = useState("每日");
  const [macroTime, setMacroTime] = useState("08:00");
  const [macroFreq, setMacroFreq] = useState("每周");
  const [altInterval, setAltInterval] = useState("1");
  const [altUnit, setAltUnit] = useState("小时");
  const [exchangeMode, setExchangeMode] = useState("实时");
  const [tradingDaysOnly, setTradingDaysOnly] = useState(true);
  const [includeWeekend, setIncludeWeekend] = useState(false);
  const [includeHoliday, setIncludeHoliday] = useState(false);
  const [daySessionStart, setDaySessionStart] = useState("09:00");
  const [daySessionEnd, setDaySessionEnd] = useState("15:30");
  const [nightSessionStart, setNightSessionStart] = useState("21:00");
  const [nightSessionEnd, setNightSessionEnd] = useState("23:00");

  // State: redundancy
  const [redundancy, setRedundancy] = useState(defaultRedundancy);

  // State: retry
  const [maxRetries, setMaxRetries] = useState("3");
  const [retryInterval, setRetryInterval] = useState("30");
  const [timeout, setTimeoutSec] = useState("10");
  const [retryStrategy, setRetryStrategy] = useState("exponential");
  const [expInitial, setExpInitial] = useState("1");
  const [expMax, setExpMax] = useState("60");
  const [expMultiplier, setExpMultiplier] = useState("2");
  const [retryOnTimeout, setRetryOnTimeout] = useState(true);
  const [retryOnServer, setRetryOnServer] = useState(true);
  const [retryOnFormat, setRetryOnFormat] = useState(true);
  const [retryOnAuth, setRetryOnAuth] = useState(false);
  const [retryOnRateLimit, setRetryOnRateLimit] = useState(false);

  // State: storage
  const [storagePath, setStoragePath] = useState("/data/quant/");
  const [fileFormat, setFileFormat] = useState("Parquet");
  const [compression, setCompression] = useState("Snappy");
  const [retentionDays, setRetentionDays] = useState("365");
  const [dirByDate, setDirByDate] = useState(true);
  const [dirByVariety, setDirByVariety] = useState(true);
  const [dirByType, setDirByType] = useState(false);
  const [backupDaily, setBackupDaily] = useState(true);
  const [backupWeekly, setBackupWeekly] = useState(true);
  const [backupMonthly, setBackupMonthly] = useState(false);
  const [backupRetention, setBackupRetention] = useState("30");
  const [backupPath, setBackupPath] = useState("/backup/quant/");

  // State: custom sources
  const [customSources, setCustomSources] = useState<CustomSource[]>(defaultCustomSources);
  const [showAddModal, setShowAddModal] = useState(false);
  const [testingSourceId, setTestingSourceId] = useState<string | null>(null);

  // State: save confirm
  const [showConfirm, setShowConfirm] = useState(false);
  const [saving, setSaving] = useState(false);

  // State: config meta
  const [configVersion] = useState("v2.3");
  const [lastSaved, setLastSaved] = useState("2026-03-21 17:08:32");
  const [modifyCount, setModifyCount] = useState(3);

  // Validation errors
  const retryErrors: Record<string, string> = {};
  const maxR = parseInt(maxRetries);
  if (maxRetries && (isNaN(maxR) || maxR < 0 || maxR > 10)) retryErrors.maxRetries = "0-10 次";
  const retryI = parseInt(retryInterval);
  if (retryInterval && (isNaN(retryI) || retryI < 5 || retryI > 300)) retryErrors.retryInterval = "5-300 秒";
  const timeoutN = parseInt(timeout);
  if (timeout && (isNaN(timeoutN) || timeoutN < 1 || timeoutN > 60)) retryErrors.timeout = "1-60 秒";

  const storageErrors: Record<string, string> = {};
  if (!storagePath.startsWith("/")) storageErrors.storagePath = "路径必须以 / 开头";
  const retDays = parseInt(retentionDays);
  if (retentionDays && (isNaN(retDays) || retDays < 0)) storageErrors.retentionDays = "请输入 ≥ 0 的整数";

  // Handlers
  const toggleSource = (category: DataSourceCategory, id: string) => {
    setDataSources((prev) => ({
      ...prev,
      [category]: prev[category].map((s) => s.id === id ? { ...s, enabled: !s.enabled } : s),
    }));
  };

  const updateRedundancy = (key: string, field: string, value: unknown) => {
    setRedundancy((prev) => ({
      ...prev,
      [key]: { ...prev[key], [field]: value },
    }));
  };

  const handleSave = () => {
    const changes = [
      `行情数据采集频率：${marketInterval} ${marketUnit}`,
      `宏观数据主源：${redundancy.macro.primary}`,
      `重试次数：${maxRetries} 次`,
      `存储格式：${fileFormat}`,
      `备份策略：${[backupDaily && "每日", backupWeekly && "每周", backupMonthly && "每月"].filter(Boolean).join("、")}`,
    ];
    setShowConfirm(true);
    return changes;
  };

  const confirmSave = async () => {
    setShowConfirm(false);
    setSaving(true);
    await new Promise((r) => setTimeout(r, 1000));
    setSaving(false);
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    setLastSaved(`${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`);
    setModifyCount((n) => n + 1);
    toast.success("配置保存成功，部分配置需重启采集服务后生效");
  };

  const handleResetDefault = () => {
    setDataSources(defaultDataSources);
    setMarketInterval("1"); setMarketUnit("秒");
    setFundamentalTime("09:00"); setFundamentalFreq("每日");
    setMacroTime("08:00"); setMacroFreq("每周");
    setAltInterval("1"); setAltUnit("小时");
    setExchangeMode("实时");
    setMaxRetries("3"); setRetryInterval("30"); setTimeoutSec("10");
    setRetryStrategy("exponential");
    setStoragePath("/data/quant/"); setFileFormat("Parquet"); setCompression("Snappy");
    setRetentionDays("365");
    setRedundancy(defaultRedundancy);
    toast.info("已恢复默认配置");
  };

  const handleExport = () => {
    const config = {
      version: configVersion,
      exportTime: new Date().toISOString(),
      dataSources,
      collectionFrequency: {
        market: { interval: marketInterval, unit: marketUnit },
        fundamental: { time: fundamentalTime, frequency: fundamentalFreq },
        macro: { time: macroTime, frequency: macroFreq },
        alternative: { interval: altInterval, unit: altUnit },
        exchange: { mode: exchangeMode },
        timeWindow: { tradingDaysOnly, includeWeekend, includeHoliday },
      },
      redundancyConfig: redundancy,
      retryMechanism: {
        maxRetries: parseInt(maxRetries),
        retryInterval: parseInt(retryInterval),
        timeout: parseInt(timeout),
        strategy: retryStrategy,
        exponentialParams: { initialInterval: parseInt(expInitial), maxInterval: parseInt(expMax), multiplier: parseInt(expMultiplier) },
        retryConditions: { networkTimeout: retryOnTimeout, serverError: retryOnServer, dataFormatError: retryOnFormat, authFailure: retryOnAuth, rateLimit: retryOnRateLimit },
      },
      storageConfig: {
        path: storagePath, format: fileFormat, compression, retentionDays: parseInt(retentionDays),
        directoryStructure: { byDate: dirByDate, byVariety: dirByVariety, byDataType: dirByType },
        backup: { daily: backupDaily, weekly: backupWeekly, monthly: backupMonthly, retentionDays: parseInt(backupRetention), path: backupPath },
      },
      customSources,
    };
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `collection-config-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("配置文件导出成功");
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const config = JSON.parse(ev.target?.result as string);
        if (config.dataSources) setDataSources(config.dataSources);
        if (config.retryMechanism) {
          setMaxRetries(String(config.retryMechanism.maxRetries ?? 3));
          setRetryInterval(String(config.retryMechanism.retryInterval ?? 30));
          setTimeoutSec(String(config.retryMechanism.timeout ?? 10));
        }
        toast.success("配置导入成功");
      } catch {
        toast.error("导入失败：文件格式不正确");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleTestCustomSource = (id: string) => {
    setTestingSourceId(id);
    setTimeout(() => {
      setTestingSourceId(null);
      toast.success("连接测试成功");
    }, 1800);
  };

  const handleDeleteCustomSource = (id: string) => {
    setCustomSources((prev) => prev.filter((s) => s.id !== id));
    toast.info("数据源已删除");
  };

  const tabs: { key: DataSourceCategory; label: string; count: number }[] = [
    { key: "market", label: "行情数据", count: 15 },
    { key: "fundamental", label: "基本面数据", count: 12 },
    { key: "macro", label: "宏观数据", count: 8 },
    { key: "alternative", label: "另类数据", count: 7 },
    { key: "exchange", label: "交易所数据", count: 5 },
  ];

  const redundancyLabels: { key: string; label: string; hasTertiary: boolean }[] = [
    { key: "market", label: "行情数据冗余配置", hasTertiary: true },
    { key: "macro", label: "宏观数据冗余配置", hasTertiary: true },
    { key: "fundamental", label: "基本面数据冗余配置", hasTertiary: false },
  ];

  const sourceOptions = ["Tushare", "AkShare", "Wind", "Choice", "聚宽", "优矿", "东方财富", "Bloomberg"];

  const saveChanges = [
    `行情数据采集频率：1 秒 → ${marketInterval} ${marketUnit}`,
    `宏观数据主源：Wind → ${redundancy.macro.primary}`,
    `重试次数：3 → ${maxRetries}`,
    `存储格式：Parquet → ${fileFormat}`,
  ];

  return (
    <div className="p-6 space-y-6 min-w-[900px]">
      {/* Hidden file input */}
      <input ref={fileInputRef} type="file" accept=".json" className="hidden" onChange={handleImport} />

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">采集参数配置</h1>
          <p className="text-sm text-muted-foreground mt-1">配置数据源开关、采集频率、双源冗余、重试机制和数据存储</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" className="gap-1.5 text-xs whitespace-nowrap" onClick={handleResetDefault}>
            <RotateCcw className="w-3.5 h-3.5" />
            恢复默认
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs whitespace-nowrap" onClick={handleExport}>
            <Download className="w-3.5 h-3.5" />
            导出配置
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs whitespace-nowrap" onClick={() => fileInputRef.current?.click()}>
            <Upload className="w-3.5 h-3.5" />
            导入配置
          </Button>
          <Button
            size="sm"
            className="gap-1.5 text-xs whitespace-nowrap bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            {saving ? "保存中..." : "保存配置"}
          </Button>
        </div>
      </div>

      {/* ── Module 1: Data Source Toggles ─────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="card-surface p-5">
        <SectionHeader
          icon={Database}
          title="数据源开关"
          description="启用/禁用各数据源采集（共 47 个数据源）"
          action={
            <span className="text-xs text-muted-foreground">
              已启用：{Object.values(dataSources).flat().filter((s) => s.enabled).length} / 47
            </span>
          }
        />
        {/* Tab bar */}
        <div className="flex items-center gap-1 mb-4 border-b border-border">
          {tabs.map((tab) => {
            const enabledCount = dataSources[tab.key].filter((s) => s.enabled).length;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  "px-3 py-2 text-xs font-medium whitespace-nowrap transition-colors relative",
                  activeTab === tab.key
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {tab.label}
                <span className={cn(
                  "ml-1.5 text-[10px] px-1.5 py-0.5 rounded-full font-medium",
                  activeTab === tab.key ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                )}>
                  {enabledCount}/{tab.count}
                </span>
                {activeTab === tab.key && (
                  <motion.div
                    layoutId="tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-[2px] bg-primary rounded-t-full"
                  />
                )}
              </button>
            );
          })}
        </div>
        {/* Source grid */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.15 }}
            className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2"
          >
            {dataSources[activeTab].map((source) => (
              <button
                key={source.id}
                onClick={() => toggleSource(activeTab, source.id)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all",
                  source.enabled
                    ? "bg-emerald-500/8 border-emerald-500/30 text-emerald-700"
                    : "bg-muted/30 border-border/60 text-muted-foreground hover:border-border hover:text-foreground"
                )}
              >
                <span className={cn("w-2 h-2 rounded-full shrink-0", source.enabled ? "bg-emerald-500" : "bg-muted-foreground/30")} />
                <span className="truncate">{source.name}</span>
              </button>
            ))}
          </motion.div>
        </AnimatePresence>
      </motion.div>

      {/* ── Module 2: Collection Frequency ────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }} className="card-surface p-5">
        <SectionHeader icon={Clock} title="采集频率" description="各类型数据采集时间间隔" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Market */}
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-xs font-medium text-foreground mb-2">行情数据采集频率</p>
            <div className="flex gap-2">
              <div className="flex-1">
                <ConfigInput value={marketInterval} onChange={setMarketInterval} type="number" min={1} max={300} placeholder="1" />
              </div>
              <Select value={marketUnit} onValueChange={setMarketUnit}>
                <SelectTrigger className="w-24 h-8 text-xs bg-muted/30 border-border/60">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["秒", "分钟", "小时"].map((u) => (
                    <SelectItem key={u} value={u} className="text-xs">{u}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <p className="text-[10px] text-muted-foreground mt-1.5">Tick 级数据采集间隔</p>
          </div>

          {/* Fundamental */}
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-xs font-medium text-foreground mb-2">基本面数据采集频率</p>
            <div className="flex gap-2">
              <Input type="time" value={fundamentalTime} onChange={(e) => setFundamentalTime(e.target.value)} className="flex-1 h-8 text-xs bg-muted/30 border-border/60" />
              <Select value={fundamentalFreq} onValueChange={setFundamentalFreq}>
                <SelectTrigger className="w-24 h-8 text-xs bg-muted/30 border-border/60">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["每日", "每周", "每月"].map((f) => (
                    <SelectItem key={f} value={f} className="text-xs">{f}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <p className="text-[10px] text-muted-foreground mt-1.5">开盘前采集财报/公告等数据</p>
          </div>

          {/* Macro */}
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-xs font-medium text-foreground mb-2">宏观数据采集频率</p>
            <div className="flex gap-2">
              <Input type="time" value={macroTime} onChange={(e) => setMacroTime(e.target.value)} className="flex-1 h-8 text-xs bg-muted/30 border-border/60" />
              <Select value={macroFreq} onValueChange={setMacroFreq}>
                <SelectTrigger className="w-24 h-8 text-xs bg-muted/30 border-border/60">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["每周", "每月", "每季度"].map((f) => (
                    <SelectItem key={f} value={f} className="text-xs">{f}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <p className="text-[10px] text-muted-foreground mt-1.5">周初采集宏观经济数据</p>
          </div>

          {/* Alternative */}
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-xs font-medium text-foreground mb-2">另类数据采集频率</p>
            <div className="flex gap-2">
              <div className="flex-1">
                <ConfigInput value={altInterval} onChange={setAltInterval} type="number" min={1} placeholder="1" />
              </div>
              <Select value={altUnit} onValueChange={setAltUnit}>
                <SelectTrigger className="w-28 h-8 text-xs bg-muted/30 border-border/60">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["15分钟", "30分钟", "小时", "6小时"].map((u) => (
                    <SelectItem key={u} value={u} className="text-xs">每{u}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <p className="text-[10px] text-muted-foreground mt-1.5">舆情/新闻等高频数据</p>
          </div>

          {/* Exchange */}
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-xs font-medium text-foreground mb-2">交易所数据采集频率</p>
            <Select value={exchangeMode} onValueChange={setExchangeMode}>
              <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["实时", "每5分钟", "每15分钟"].map((m) => (
                  <SelectItem key={m} value={m} className="text-xs">{m}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-[10px] text-muted-foreground mt-1.5">交易所官方推送数据</p>
          </div>

          {/* Time window */}
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-xs font-medium text-foreground mb-2">采集时间窗口</p>
            <div className="space-y-1.5 mb-2">
              {[
                { label: "仅交易日", checked: tradingDaysOnly, onChange: setTradingDaysOnly },
                { label: "包含周末", checked: includeWeekend, onChange: setIncludeWeekend },
                { label: "包含节假日", checked: includeHoliday, onChange: setIncludeHoliday },
              ].map((item) => (
                <label key={item.label} className="flex items-center gap-2 cursor-pointer">
                  <Checkbox checked={item.checked} onCheckedChange={(v) => item.onChange(Boolean(v))} className="w-3.5 h-3.5" />
                  <span className="text-xs text-foreground">{item.label}</span>
                </label>
              ))}
            </div>
            <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
              <Input type="time" value={daySessionStart} onChange={(e) => setDaySessionStart(e.target.value)} className="h-6 text-[10px] px-1 bg-muted/30 border-border/60 w-16" />
              <span>-</span>
              <Input type="time" value={daySessionEnd} onChange={(e) => setDaySessionEnd(e.target.value)} className="h-6 text-[10px] px-1 bg-muted/30 border-border/60 w-16" />
              <span className="ml-1">/</span>
              <Input type="time" value={nightSessionStart} onChange={(e) => setNightSessionStart(e.target.value)} className="h-6 text-[10px] px-1 bg-muted/30 border-border/60 w-16" />
              <span>-</span>
              <Input type="time" value={nightSessionEnd} onChange={(e) => setNightSessionEnd(e.target.value)} className="h-6 text-[10px] px-1 bg-muted/30 border-border/60 w-16" />
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── Module 3: Redundancy Config ───────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-surface p-5">
        <SectionHeader
          icon={Repeat}
          title="双源/三源冗余配置"
          description="主源失败自动切换副源，确保数据不中断"
        />
        <div className="space-y-4">
          {redundancyLabels.map(({ key, label, hasTertiary }) => {
            const r = redundancy[key];
            const isPrimary = r.currentSource === r.primary;
            return (
              <div key={key} className="p-4 rounded-lg border border-border/60 bg-muted/10">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-semibold text-foreground">{label}</p>
                  <SourceStatusBadge status={r.currentSource} source={r.currentSource} isPrimary={isPrimary} />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
                  <div>
                    <FormLabel>主源</FormLabel>
                    <Select value={r.primary} onValueChange={(v) => updateRedundancy(key, "primary", v)}>
                      <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {sourceOptions.map((s) => <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <FormLabel>副源</FormLabel>
                    <Select value={r.secondary} onValueChange={(v) => updateRedundancy(key, "secondary", v)}>
                      <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {sourceOptions.map((s) => <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  {hasTertiary && (
                    <div>
                      <FormLabel>第三源</FormLabel>
                      <Select value={r.tertiary ?? ""} onValueChange={(v) => updateRedundancy(key, "tertiary", v)}>
                        <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {sourceOptions.map((s) => <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                  <div>
                    <FormLabel>切换策略</FormLabel>
                    <Select value={r.switchStrategy} onValueChange={(v) => updateRedundancy(key, "switchStrategy", v)}>
                      <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="auto" className="text-xs">自动切换</SelectItem>
                        <SelectItem value="manual" className="text-xs">手动切换</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <FormLabel>回切策略</FormLabel>
                    <Select value={r.switchBackStrategy} onValueChange={(v) => updateRedundancy(key, "switchBackStrategy", v)}>
                      <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="immediate" className="text-xs">立即回切</SelectItem>
                        <SelectItem value="stable" className="text-xs">稳定后回切</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <FormLabel>失败次数阈值</FormLabel>
                    <Input
                      type="number"
                      value={r.failCount}
                      onChange={(e) => updateRedundancy(key, "failCount", parseInt(e.target.value) || 3)}
                      min={1}
                      max={10}
                      className="h-8 text-xs bg-muted/30 border-border/60"
                    />
                  </div>
                  <div>
                    <FormLabel>回切等待（分钟）</FormLabel>
                    <Input
                      type="number"
                      value={r.switchBackWait}
                      onChange={(e) => updateRedundancy(key, "switchBackWait", parseInt(e.target.value) || 30)}
                      min={1}
                      className="h-8 text-xs bg-muted/30 border-border/60"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-4 text-[11px] text-muted-foreground pt-2 border-t border-border/40">
                  <span>最后切换：<span className="text-foreground font-mono">{r.lastSwitchTime}</span></span>
                  <span>今日切换：<span className="text-foreground font-mono">{r.switchCountToday} 次</span></span>
                </div>
              </div>
            );
          })}

          {/* Switch log */}
          <div>
            <p className="text-xs font-semibold text-foreground mb-2 flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 text-muted-foreground" />
              切换日志
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs min-w-[600px]">
                <thead>
                  <tr className="border-b border-border">
                    {["时间", "数据类型", "切换路径", "原因", "状态"].map((h) => (
                      <th key={h} className="py-2 px-3 text-left font-medium text-muted-foreground whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {switchLogs.map((log, i) => (
                    <tr key={i} className="border-b border-border/40 hover:bg-muted/20 transition-colors">
                      <td className="py-2 px-3 font-mono text-muted-foreground whitespace-nowrap">{log.time}</td>
                      <td className="py-2 px-3 whitespace-nowrap">{log.type}</td>
                      <td className="py-2 px-3 whitespace-nowrap">
                        <span className="flex items-center gap-1">
                          {log.from}
                          <ArrowRight className="w-3 h-3 text-muted-foreground" />
                          {log.to}
                        </span>
                      </td>
                      <td className="py-2 px-3 whitespace-nowrap text-muted-foreground">{log.reason}</td>
                      <td className="py-2 px-3 whitespace-nowrap">
                        <span className={cn(
                          "px-2 py-0.5 rounded-full text-[10px] font-medium",
                          log.status === "成功" ? "bg-emerald-500/10 text-emerald-600" : "bg-red-500/10 text-red-600"
                        )}>
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── Module 4: Retry Mechanism ─────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }} className="card-surface p-5">
        <SectionHeader icon={RotateCcw} title="重试机制" description="采集失败后的自动重试策略" />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <FormLabel>失败重试次数（0-10）</FormLabel>
            <ConfigInput value={maxRetries} onChange={setMaxRetries} type="number" min={0} max={10} error={retryErrors.maxRetries} />
            <p className="text-[10px] text-muted-foreground mt-1">采集失败后重试次数</p>
          </div>
          <div>
            <FormLabel>重试间隔（5-300 秒）</FormLabel>
            <ConfigInput value={retryInterval} onChange={setRetryInterval} type="number" min={5} max={300} error={retryErrors.retryInterval} />
            <p className="text-[10px] text-muted-foreground mt-1">每次重试间隔时间</p>
          </div>
          <div>
            <FormLabel>超时时间（1-60 秒）</FormLabel>
            <ConfigInput value={timeout} onChange={setTimeoutSec} type="number" min={1} max={60} error={retryErrors.timeout} />
            <p className="text-[10px] text-muted-foreground mt-1">单次请求超时时间</p>
          </div>
          <div>
            <FormLabel>重试策略</FormLabel>
            <Select value={retryStrategy} onValueChange={setRetryStrategy}>
              <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="exponential" className="text-xs">指数退避</SelectItem>
                <SelectItem value="fixed" className="text-xs">固定间隔</SelectItem>
                <SelectItem value="random" className="text-xs">随机间隔</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-[10px] text-muted-foreground mt-1">重试时间递增策略</p>
          </div>

          {/* Exponential params */}
          {retryStrategy === "exponential" && (
            <>
              <div>
                <FormLabel>初始间隔（秒）</FormLabel>
                <ConfigInput value={expInitial} onChange={setExpInitial} type="number" min={1} />
                <p className="text-[10px] text-muted-foreground mt-1">1s→2s→4s→8s→16s…</p>
              </div>
              <div>
                <FormLabel>最大间隔（秒）</FormLabel>
                <ConfigInput value={expMax} onChange={setExpMax} type="number" min={1} />
              </div>
              <div>
                <FormLabel>倍数</FormLabel>
                <ConfigInput value={expMultiplier} onChange={setExpMultiplier} type="number" min={1} max={10} />
              </div>
            </>
          )}

          {/* Retry conditions */}
          <div className="md:col-span-3">
            <FormLabel>重试条件</FormLabel>
            <div className="flex flex-wrap gap-4 mt-1">
              {[
                { label: "网络超时", checked: retryOnTimeout, onChange: setRetryOnTimeout },
                { label: "服务器错误", checked: retryOnServer, onChange: setRetryOnServer },
                { label: "数据格式错误", checked: retryOnFormat, onChange: setRetryOnFormat },
                { label: "认证失败", checked: retryOnAuth, onChange: setRetryOnAuth },
                { label: "限流错误", checked: retryOnRateLimit, onChange: setRetryOnRateLimit },
              ].map((item) => (
                <label key={item.label} className="flex items-center gap-2 cursor-pointer">
                  <Checkbox checked={item.checked} onCheckedChange={(v) => item.onChange(Boolean(v))} className="w-3.5 h-3.5" />
                  <span className="text-xs text-foreground">{item.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── Module 5: Storage Config ──────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.14 }} className="card-surface p-5">
        <SectionHeader icon={HardDrive} title="数据存储" description="采集数据的存储路径和格式" />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <FormLabel>存储路径</FormLabel>
            <div className="flex gap-2">
              <ConfigInput value={storagePath} onChange={setStoragePath} placeholder="/data/quant/" error={storageErrors.storagePath} className="flex-1" />
              <Button variant="outline" size="sm" className="gap-1 text-xs shrink-0 h-8">
                <FolderOpen className="w-3.5 h-3.5" />
                浏览
              </Button>
            </div>
            {!storageErrors.storagePath && (
              <p className="text-[10px] text-muted-foreground mt-1">数据存储根目录</p>
            )}
          </div>
          <div>
            <FormLabel>文件格式</FormLabel>
            <Select value={fileFormat} onValueChange={setFileFormat}>
              <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["Parquet", "CSV", "HDF5", "JSON"].map((f) => (
                  <SelectItem key={f} value={f} className="text-xs">{f}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-[10px] text-muted-foreground mt-1">数据存储文件格式</p>
          </div>
          <div>
            <FormLabel>压缩方式</FormLabel>
            <Select value={compression} onValueChange={setCompression}>
              <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["Snappy", "Gzip", "Zstd", "无压缩"].map((c) => (
                  <SelectItem key={c} value={c} className="text-xs">{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-[10px] text-muted-foreground mt-1">文件压缩算法</p>
          </div>
          <div>
            <FormLabel>保留天数（0=永久）</FormLabel>
            <ConfigInput value={retentionDays} onChange={setRetentionDays} type="number" min={0} max={9999} error={storageErrors.retentionDays} />
            <p className="text-[10px] text-muted-foreground mt-1">历史数据保留天数</p>
          </div>
          <div>
            <FormLabel>目录结构</FormLabel>
            <div className="space-y-1.5 mt-1">
              {[
                { label: "按日期分目录", checked: dirByDate, onChange: setDirByDate },
                { label: "按品种分目录", checked: dirByVariety, onChange: setDirByVariety },
                { label: "按数据类型分目录", checked: dirByType, onChange: setDirByType },
              ].map((item) => (
                <label key={item.label} className="flex items-center gap-2 cursor-pointer">
                  <Checkbox checked={item.checked} onCheckedChange={(v) => item.onChange(Boolean(v))} className="w-3.5 h-3.5" />
                  <span className="text-xs text-foreground">{item.label}</span>
                </label>
              ))}
            </div>
          </div>
          {/* Backup */}
          <div className="md:col-span-3">
            <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
              <p className="text-xs font-medium text-foreground mb-2">备份策略</p>
              <div className="flex flex-wrap items-center gap-4 mb-3">
                {[
                  { label: "每日备份", checked: backupDaily, onChange: setBackupDaily },
                  { label: "每周备份", checked: backupWeekly, onChange: setBackupWeekly },
                  { label: "每月备份", checked: backupMonthly, onChange: setBackupMonthly },
                ].map((item) => (
                  <label key={item.label} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox checked={item.checked} onCheckedChange={(v) => item.onChange(Boolean(v))} className="w-3.5 h-3.5" />
                    <span className="text-xs text-foreground">{item.label}</span>
                  </label>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <FormLabel>备份保留天数</FormLabel>
                  <ConfigInput value={backupRetention} onChange={setBackupRetention} type="number" min={1} placeholder="30" />
                </div>
                <div>
                  <FormLabel>备份路径</FormLabel>
                  <ConfigInput value={backupPath} onChange={setBackupPath} placeholder="/backup/quant/" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Directory example */}
        <div className="mt-3 px-3 py-2 rounded-lg bg-muted/30 border border-border/40">
          <p className="text-[10px] text-muted-foreground mb-1">目录示例：</p>
          <code className="text-[10px] text-foreground font-mono">
            {storagePath || "/data/quant/"}
            {dirByDate ? "2026/03/21/" : ""}
            {dirByVariety ? "rb2405" : "data"}
            .{fileFormat.toLowerCase()}
          </code>
        </div>
      </motion.div>

      {/* ── Module 6: Custom Sources ──────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.16 }} className="card-surface p-5">
        <SectionHeader
          icon={PlusCircle}
          title="新增采集源"
          description="添加新的数据源以应对采集失败或扩展数据覆盖"
          action={
            <Button size="sm" className="gap-1.5 text-xs bg-primary text-primary-foreground" onClick={() => setShowAddModal(true)}>
              <PlusCircle className="w-3.5 h-3.5" />
              添加数据源
            </Button>
          }
        />
        {customSources.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <div className="w-12 h-12 rounded-full bg-muted/40 flex items-center justify-center mb-3">
              <Database className="w-5 h-5 text-muted-foreground/50" />
            </div>
            <p className="text-sm font-medium text-foreground">暂无自定义数据源</p>
            <p className="text-xs text-muted-foreground mt-1">点击右上角按钮添加新的数据源</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs min-w-[760px]">
              <thead>
                <tr className="border-b border-border">
                  {["名称", "类型", "供应商", "角色", "状态", "最后采集", "成功率", "操作"].map((h) => (
                    <th key={h} className="py-2.5 px-3 text-left font-medium text-muted-foreground whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {customSources.map((source) => (
                  <tr key={source.id} className="border-b border-border/40 hover:bg-muted/20 transition-colors">
                    <td className="py-2.5 px-3 font-medium whitespace-nowrap">{source.name}</td>
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 bg-primary/8 text-primary rounded-full text-[10px] font-medium">{source.type}</span>
                    </td>
                    <td className="py-2.5 px-3 text-muted-foreground whitespace-nowrap">{source.provider}</td>
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <span className={cn(
                        "px-2 py-0.5 rounded-full text-[10px] font-medium",
                        source.role === "primary" ? "bg-blue-500/10 text-blue-600" :
                        source.role === "secondary" ? "bg-emerald-500/10 text-emerald-600" : "bg-muted text-muted-foreground"
                      )}>
                        {source.role === "primary" ? "主源" : source.role === "secondary" ? "副源" : "第三源"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <CustomSourceStatusDot status={source.status} />
                    </td>
                    <td className="py-2.5 px-3 font-mono text-muted-foreground whitespace-nowrap">{source.lastCollection}</td>
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <span className={cn(
                        "font-mono",
                        source.successRate >= 95 ? "text-emerald-600" :
                        source.successRate >= 85 ? "text-amber-600" : "text-red-600"
                      )}>
                        {source.successRate > 0 ? `${source.successRate}%` : "-"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => handleTestCustomSource(source.id)}
                          disabled={testingSourceId === source.id}
                          title="测试连接"
                        >
                          {testingSourceId === source.id
                            ? <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                            : <TestTube className="w-3.5 h-3.5" />
                          }
                        </Button>
                        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" title="编辑">
                          <Edit3 className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                          onClick={() => handleDeleteCustomSource(source.id)}
                          title="删除"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* ── Config Operations Footer ──────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18 }} className="card-surface p-5">
        <SectionHeader icon={Save} title="配置操作" />
        <div className="flex flex-wrap items-center gap-3 mb-5">
          <Button
            size="sm"
            className="gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            {saving ? "保存中..." : "保存配置"}
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5" onClick={handleResetDefault}>
            <RotateCcw className="w-3.5 h-3.5" />
            恢复默认
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5" onClick={handleExport}>
            <Download className="w-3.5 h-3.5" />
            导出配置 JSON
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5" onClick={() => fileInputRef.current?.click()}>
            <Upload className="w-3.5 h-3.5" />
            导入配置
          </Button>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-[10px] text-muted-foreground mb-1">最后保存时间</p>
            <p className="text-xs font-mono font-medium text-foreground">{lastSaved}</p>
          </div>
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-[10px] text-muted-foreground mb-1">配置版本</p>
            <p className="text-xs font-mono font-medium text-foreground">{configVersion}</p>
          </div>
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40">
            <p className="text-[10px] text-muted-foreground mb-1">累计修改次数</p>
            <p className="text-xs font-mono font-medium text-foreground">{modifyCount} 次</p>
          </div>
        </div>
      </motion.div>

      {/* Modals */}
      <ConfirmSaveModal
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={confirmSave}
        changes={saveChanges}
      />
      <AddSourceModal
        open={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={(src) => {
          setCustomSources((prev) => [...prev, src]);
          toast.success(`数据源「${src.name}」已添加`);
        }}
      />
    </div>
  );
}
