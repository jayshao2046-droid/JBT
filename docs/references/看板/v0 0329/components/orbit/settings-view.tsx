"use client";
// uses useToastActions from toast-provider (no addToast)
import React, { useState, useMemo } from "react";
import {
  Settings,
  Power,
  Users,
  Globe,
  Shield,
  Brain,
  Monitor,
  Save,
  Download,
  Upload,
  RotateCcw,
  Plus,
  Pencil,
  Trash2,
  TestTube,
  Sun,
  Moon,
  Clock,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Wifi,
  WifiOff,
  Smartphone,
  Laptop,
  Server,
  LogOut,
  RefreshCw,
  Eye,
  Terminal,
  Play,
  Pause,
  X,
  ChevronDown,
  Info,
  Cpu,
  HardDrive,
  Activity,
  Zap,
  Lock,
  Unlock,
  Network,
  Router,
  CloudDownload,
  Check,
  Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useToastActions } from "@/components/orbit/toast-provider";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

// ==================== Types ====================
interface TradingPeriod {
  id: string;
  name: string;
  startTime: string;
  endTime: string;
  enabled: boolean;
}

interface SpecialDate {
  date: Date;
  name: string;
  noTrade: boolean;
}

interface TradingAccount {
  id: string;
  name: string;
  type: "live" | "sim";
  status: "normal" | "paused" | "disabled";
  assetTypes: string[];
  futuresConfig?: {
    broker: string;
    brokerId: string;
    userId: string;
    password: string;
  };
  stockConfig?: {
    broker: string;
    accountNo: string;
    password: string;
  };
}

interface NetworkConfig {
  mode: "tailscale" | "pgyer" | "direct" | "hybrid";
  tailscale: {
    tailnet: string;
    status: "connected" | "disconnected";
    magicDns: boolean;
  };
  pgyer: {
    networkId: string;
    status: "connected" | "disconnected";
    deviceIp: string;
  };
  hybrid: {
    priority: string[];
    autoFailover: boolean;
  };
}

interface WhitelistIP {
  id: string;
  ip: string;
  description: string;
}

interface RegisteredDevice {
  id: string;
  name: string;
  type: "laptop" | "phone" | "tablet" | "server";
  ip: string;
  mac: string;
  status: "online" | "offline";
  autoLogin: boolean;
}

interface LoginSession {
  id: string;
  deviceName: string;
  ip: string;
  loginTime: string;
  lastActivity: string;
  status: "online" | "idle";
}

interface AIModel {
  id: string;
  name: string;
  fileName: string;
  size: string;
  memoryRequired: string;
  status: "downloaded" | "downloading" | "not_downloaded";
  progress?: number;
}

interface SystemDevice {
  id: string;
  name: string;
  role: "trading" | "decision" | "data" | "dashboard";
  internalIp: string;
  tailscaleIp: string;
  pgyerIp: string;
  mac: string;
  status: "online" | "offline";
  registered: boolean;
}

interface ConfigHistory {
  id: string;
  time: string;
  changes: string[];
  version: string;
}

// ==================== Mock Data ====================
const defaultTradingPeriods: TradingPeriod[] = [
  { id: "morning", name: "早盘", startTime: "09:00", endTime: "11:30", enabled: true },
  { id: "afternoon", name: "午盘", startTime: "13:00", endTime: "15:00", enabled: true },
  { id: "night", name: "夜盘", startTime: "21:00", endTime: "23:00", enabled: true },
];

const defaultSpecialDates: SpecialDate[] = [
  { date: new Date(2026, 3, 4), name: "清明节", noTrade: true },
  { date: new Date(2026, 4, 1), name: "劳动节", noTrade: true },
  { date: new Date(2026, 5, 14), name: "端午节", noTrade: true },
];

const defaultAccounts: TradingAccount[] = [
  {
    id: "1",
    name: "主账户",
    type: "live",
    status: "normal",
    assetTypes: ["futures", "stock", "forex"],
    futuresConfig: { broker: "CTP", brokerId: "9999", userId: "123456", password: "******" },
    stockConfig: { broker: "中信", accountNo: "88888888", password: "******" },
  },
  {
    id: "2",
    name: "模拟账户",
    type: "sim",
    status: "normal",
    assetTypes: ["futures"],
    futuresConfig: { broker: "SimNow", brokerId: "9999", userId: "test001", password: "******" },
  },
  {
    id: "3",
    name: "测试账户",
    type: "sim",
    status: "paused",
    assetTypes: ["futures", "stock"],
    futuresConfig: { broker: "CTP", brokerId: "9999", userId: "test002", password: "******" },
  },
];

const defaultWhitelistIPs: WhitelistIP[] = [
  { id: "1", ip: "192.168.1.0/24", description: "内网" },
  { id: "2", ip: "100.82.139.52", description: "Studio Tailscale" },
  { id: "3", ip: "172.16.0.49", description: "Mini 蒲公英" },
  { id: "4", ip: "192.168.0.100", description: "iPhone" },
  { id: "5", ip: "192.168.0.101", description: "iPad" },
];

const defaultRegisteredDevices: RegisteredDevice[] = [
  { id: "1", name: "MacBook Pro", type: "laptop", ip: "192.168.1.101", mac: "aa:bb:cc:dd:ee:ff", status: "online", autoLogin: true },
  { id: "2", name: "iPhone 15", type: "phone", ip: "192.168.0.100", mac: "11:22:33:44:55:66", status: "online", autoLogin: true },
  { id: "3", name: "iPad Pro", type: "tablet", ip: "192.168.0.101", mac: "77:88:99:aa:bb:cc", status: "offline", autoLogin: true },
];

const defaultLoginSessions: LoginSession[] = [
  { id: "1", deviceName: "MacBook Pro", ip: "192.168.1.101", loginTime: "2026-03-21 09:00", lastActivity: "2026-03-21 17:08", status: "online" },
  { id: "2", deviceName: "iPhone 15", ip: "192.168.0.100", loginTime: "2026-03-21 10:30", lastActivity: "2026-03-21 16:45", status: "idle" },
];

const defaultAIModels: AIModel[] = [
  { id: "1", name: "DeepSeek 14B", fileName: "DeepSeek-14B-Q4_K_M.gguf", size: "8.2 GB", memoryRequired: "8GB", status: "downloaded" },
  { id: "2", name: "DeepSeek 32B", fileName: "DeepSeek-32B-Q4_K_M.gguf", size: "16.5 GB", memoryRequired: "16GB", status: "downloading", progress: 67 },
  { id: "3", name: "DeepSeek 70B", fileName: "DeepSeek-70B-Q4_K_M.gguf", size: "35.2 GB", memoryRequired: "35GB", status: "not_downloaded" },
  { id: "4", name: "Qwen Max", fileName: "云端模型", size: "-", memoryRequired: "-", status: "downloaded" },
];

const defaultSystemDevices: SystemDevice[] = [
  { id: "1", name: "Mac Studio", role: "trading", internalIp: "192.168.1.102", tailscaleIp: "100.82.139.52", pgyerIp: "172.16.1.130", mac: "11:22:33:44:55:66", status: "online", registered: true },
  { id: "2", name: "Mac Mini M1", role: "decision", internalIp: "192.168.1.103", tailscaleIp: "100.78.156.89", pgyerIp: "172.16.0.50", mac: "77:88:99:aa:bb:cc", status: "online", registered: true },
  { id: "3", name: "Mac Mini M4", role: "data", internalIp: "192.168.1.104", tailscaleIp: "100.65.123.45", pgyerIp: "172.16.0.51", mac: "dd:ee:ff:00:11:22", status: "online", registered: true },
  { id: "4", name: "MacBook Pro", role: "dashboard", internalIp: "192.168.1.101", tailscaleIp: "100.82.139.62", pgyerIp: "172.16.1.131", mac: "aa:bb:cc:dd:ee:ff", status: "online", registered: true },
];

const defaultConfigHistory: ConfigHistory[] = [
  { id: "1", time: "2026-03-21 17:08:32", changes: ["自动交易开关：关闭 → 开启", "添加 IP 白名单：iPad"], version: "v2.3" },
  { id: "2", time: "2026-03-20 14:22:15", changes: ["组网方式：Tailscale → 混合模式", "启用故障转移"], version: "v2.2" },
  { id: "3", time: "2026-03-19 09:45:00", changes: ["AI 模型切换：14B → 32B", "并发数：1 → 2"], version: "v2.1" },
];

// ==================== Component ====================
export function SettingsView() {
  const toast = useToastActions();

  // Auto Trading Control
  const [tradingEnabled, setTradingEnabled] = useState(true);
  const [tradingPeriods, setTradingPeriods] = useState<TradingPeriod[]>(defaultTradingPeriods);
  const [specialDates, setSpecialDates] = useState<SpecialDate[]>(defaultSpecialDates);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [newSpecialDateName, setNewSpecialDateName] = useState("");
  const [tradingPaused, setTradingPaused] = useState(false);

  // Account Management
  const [accounts, setAccounts] = useState<TradingAccount[]>(defaultAccounts);
  const [selectedAccount, setSelectedAccount] = useState<TradingAccount | null>(null);
  const [accountTab, setAccountTab] = useState("list");
  const [showAccountDialog, setShowAccountDialog] = useState(false);
  const [editingAccount, setEditingAccount] = useState<TradingAccount | null>(null);

  // Network Config
  const [networkConfig, setNetworkConfig] = useState<NetworkConfig>({
    mode: "tailscale",
    tailscale: { tailnet: "tailbb3441.ts.net", status: "connected", magicDns: true },
    pgyer: { networkId: "orkj775970wqa57f", status: "connected", deviceIp: "172.16.0.49" },
    hybrid: { priority: ["direct", "tailscale", "pgyer"], autoFailover: true },
  });

  // Security Settings
  const [accessMode, setAccessMode] = useState<"whitelist" | "password" | "hybrid">("hybrid");
  const [ipWhitelistEnabled, setIpWhitelistEnabled] = useState(true);
  const [whitelistIPs, setWhitelistIPs] = useState<WhitelistIP[]>(defaultWhitelistIPs);
  const [registeredDevices, setRegisteredDevices] = useState<RegisteredDevice[]>(defaultRegisteredDevices);
  const [loginSessions, setLoginSessions] = useState<LoginSession[]>(defaultLoginSessions);
  const [showAddIPDialog, setShowAddIPDialog] = useState(false);
  const [showRegisterDeviceDialog, setShowRegisterDeviceDialog] = useState(false);
  const [newIP, setNewIP] = useState({ ip: "", description: "" });
  const [newDevice, setNewDevice] = useState({ name: "", type: "laptop" as const, ip: "", mac: "" });

  // AI Model Config
  const [selectedModel, setSelectedModel] = useState("1");
  const [maxConcurrency, setMaxConcurrency] = useState(2);
  const [memoryLimit, setMemoryLimit] = useState(24);
  const [gpuEnabled, setGpuEnabled] = useState(true);
  const [aiModels, setAIModels] = useState<AIModel[]>(defaultAIModels);

  // Device Management
  const [systemDevices, setSystemDevices] = useState<SystemDevice[]>(defaultSystemDevices);
  const [showAddDeviceDialog, setShowAddDeviceDialog] = useState(false);

  // Config Management
  const [configHistory] = useState<ConfigHistory[]>(defaultConfigHistory);

  // 保存配置确认弹窗
  const [showSaveConfirm, setShowSaveConfirm] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [changedItems, setChangedItems] = useState<string[]>([
    "因子权重：动量类 35% → 40%",
    "开仓阈值：70% → 75%",
    "风险级别：中等 → 高"
  ]);

  const handleSaveConfig = async () => {
    setIsSaving(true);
    await new Promise(r => setTimeout(r, 1200));
    setIsSaving(false);
    setShowSaveConfirm(false);
    toast.success("配置已保存并生效");
  };
  const [showSaveConfirmDialog, setShowSaveConfirmDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [pendingChanges, setPendingChanges] = useState<string[]>([]);
  const [lastSaveTime] = useState("2026-03-21 17:08:32");
  const [configVersion] = useState("v2.3");

  // Track changes for save confirmation
  const [originalState] = useState({
    tradingEnabled: true,
    networkMode: "tailscale",
    accessMode: "hybrid",
    selectedModel: "1",
  });

  // Calculate pending changes
  const calculateChanges = () => {
    const changes: string[] = [];
    if (tradingEnabled !== originalState.tradingEnabled) {
      changes.push(`自动交易开关：${originalState.tradingEnabled ? "开启" : "关闭"} → ${tradingEnabled ? "开启" : "关闭"}`);
    }
    if (networkConfig.mode !== originalState.networkMode) {
      const modeNames: Record<string, string> = { tailscale: "Tailscale", pgyer: "蒲公英", direct: "内网直连", hybrid: "混合模式" };
      changes.push(`组网方式：${modeNames[originalState.networkMode]} → ${modeNames[networkConfig.mode]}`);
    }
    if (accessMode !== originalState.accessMode) {
      const accessNames: Record<string, string> = { whitelist: "白名单模式", password: "密码模式", hybrid: "混合模式" };
      changes.push(`访问控制：${accessNames[originalState.accessMode]} → ${accessNames[accessMode]}`);
    }
    if (selectedModel !== originalState.selectedModel) {
      const model = aiModels.find((m) => m.id === selectedModel);
      const origModel = aiModels.find((m) => m.id === originalState.selectedModel);
      changes.push(`AI 模型：${origModel?.name} → ${model?.name}`);
    }
    return changes;
  };

  // Handlers
  const handleSave = () => {
    const changes = calculateChanges();
    setPendingChanges(changes);
    setShowSaveConfirmDialog(true);
  };

  const confirmSave = () => {
    setShowSaveConfirmDialog(false);
    toast.success("保存成功：系统配置已保存");
  };

  const handleExport = () => {
    const config = {
      tradingEnabled,
      tradingPeriods,
      specialDates: specialDates.map((d) => ({ ...d, date: d.date.toISOString() })),
      accounts,
      networkConfig,
      accessMode,
      ipWhitelistEnabled,
      whitelistIPs,
      registeredDevices,
      selectedModel,
      maxConcurrency,
      memoryLimit,
      gpuEnabled,
      systemDevices,
      exportTime: new Date().toISOString(),
      version: configVersion,
    };
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `system-settings-${format(new Date(), "yyyy-MM-dd-HHmmss")}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("导出成功：配置文件已下载");
  };

  const handleImport = () => {
    setShowImportDialog(true);
  };

  const confirmImport = () => {
    setShowImportDialog(false);
    toast.success("导入成功：配置已覆盖，请检查各项设置");
  };

  const handleResetDefaults = () => {
    setTradingEnabled(true);
    setTradingPeriods(defaultTradingPeriods);
    setNetworkConfig((prev) => ({ ...prev, mode: "tailscale" }));
    setAccessMode("hybrid");
    setSelectedModel("1");
    setMaxConcurrency(2);
    setMemoryLimit(24);
    toast.info("已恢复默认：所有配置已重置为默认值");
  };

  const handlePauseTrade = () => {
    setTradingPaused(true);
    toast.warning("交易已暂停：所有自动交易已紧急暂停");
  };

  const handleResumeTrade = () => {
    setTradingPaused(false);
    toast.success("交易已恢复：自动交易已恢复执行");
  };

  const handleTestConnection = (type: string) => {
    toast.info(`测试连接中：正在测试 ${type} 连接...`);
    setTimeout(() => {
      toast.success(`连接成功：${type} 连接正常`);
    }, 1500);
  };

  const handleAddSpecialDate = () => {
    if (selectedDate && newSpecialDateName) {
      setSpecialDates([...specialDates, { date: selectedDate, name: newSpecialDateName, noTrade: true }]);
      setSelectedDate(undefined);
      setNewSpecialDateName("");
      toast.success(`添加成功：已添加特殊日期 ${newSpecialDateName}`);
    }
  };

  const handleDeleteSpecialDate = (date: Date) => {
    setSpecialDates(specialDates.filter((d) => d.date.getTime() !== date.getTime()));
    toast.success("删除成功：特殊日期已删除");
  };

  const handleAddIP = () => {
    if (newIP.ip && newIP.description) {
      setWhitelistIPs([...whitelistIPs, { id: Date.now().toString(), ...newIP }]);
      setNewIP({ ip: "", description: "" });
      setShowAddIPDialog(false);
      toast.success(`添加成功：IP ${newIP.ip} 已加入白名单`);
    }
  };

  const handleDeleteIP = (id: string) => {
    setWhitelistIPs(whitelistIPs.filter((ip) => ip.id !== id));
    toast.success("删除成功：IP 已从白名单移除");
  };

  const handleRegisterDevice = () => {
    if (newDevice.name && newDevice.ip && newDevice.mac) {
      setRegisteredDevices([...registeredDevices, { id: Date.now().toString(), ...newDevice, status: "offline", autoLogin: true }]);
      setNewDevice({ name: "", type: "laptop", ip: "", mac: "" });
      setShowRegisterDeviceDialog(false);
      toast.success(`注册成功：设备 ${newDevice.name} 已注册`);
    }
  };

  const handleDeleteDevice = (id: string) => {
    setRegisteredDevices(registeredDevices.filter((d) => d.id !== id));
    toast.success("删除成功：设备已注销");
  };

  const handleForceLogout = (sessionId: string) => {
    setLoginSessions(loginSessions.filter((s) => s.id !== sessionId));
    toast.success("登出成功：会话已强制结束");
  };

  const handleEndAllSessions = () => {
    setLoginSessions([]);
    toast.success("全部登出：所有会话已结束");
  };

  const handleDownloadModel = (modelId: string) => {
    setAIModels(aiModels.map((m) => (m.id === modelId ? { ...m, status: "downloading", progress: 0 } : m)));
    toast.info("开始下载：模型下载已开始");
  };

  const handleCancelDownload = (modelId: string) => {
    setAIModels(aiModels.map((m) => (m.id === modelId ? { ...m, status: "not_downloaded", progress: undefined } : m)));
    toast.info("下载取消：模型下载已取消");
  };

  const handleDeleteModel = (modelId: string) => {
    setAIModels(aiModels.map((m) => (m.id === modelId ? { ...m, status: "not_downloaded", progress: undefined } : m)));
    toast.success("删除成功：模型文件已删除");
  };

  const handleRemoteAction = (deviceId: string, action: string) => {
    const device = systemDevices.find((d) => d.id === deviceId);
    const actionName = action === "connect" ? "连接" : action === "restart" ? "重启" : action === "logs" ? "查看日志" : "强制登出";
    if (action === "restart") {
      toast.warning(`${actionName}：正在对 ${device?.name} 执行操作...`);
    } else {
      toast.info(`${actionName}：正在对 ${device?.name} 执行操作...`);
    }
  };

  // Special dates for calendar highlighting
  const specialDateSet = useMemo(() => new Set(specialDates.map((d) => d.date.toDateString())), [specialDates]);

  const getRoleName = (role: SystemDevice["role"]) => {
    const names: Record<SystemDevice["role"], string> = {
      trading: "交易端",
      decision: "决策端",
      data: "数据端",
      dashboard: "看板端",
    };
    return names[role];
  };

  const getDeviceIcon = (type: RegisteredDevice["type"]) => {
    switch (type) {
      case "laptop":
        return <Laptop className="h-4 w-4" />;
      case "phone":
        return <Smartphone className="h-4 w-4" />;
      case "tablet":
        return <Smartphone className="h-4 w-4" />;
      case "server":
        return <Server className="h-4 w-4" />;
    }
  };

  return (
    <TooltipProvider>
      <div className="h-full overflow-auto">
        <div className="min-w-[1000px] space-y-6 p-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
                <Settings className="h-6 w-6 text-primary" />
                系统设置
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">配置自动交易、账户管理、网络连接、安全设置和 AI 模型</p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleResetDefaults}>
                <RotateCcw className="mr-1.5 h-4 w-4" />
                恢复默认
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="mr-1.5 h-4 w-4" />
                导出配置
              </Button>
              <Button variant="outline" size="sm" onClick={handleImport}>
                <Upload className="mr-1.5 h-4 w-4" />
                导入配置
              </Button>
        <Button size="sm" onClick={() => setShowSaveConfirm(true)}>
          <Save className="w-4 h-4 mr-1" />
          保存配置
        </Button>
            </div>
          </div>

          {/* Module 1: Auto Trading Control */}
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Power className="h-5 w-5 text-primary" />
                自动交易控制
              </CardTitle>
              <CardDescription>控制系统级自动交易执行</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-3 gap-6">
                {/* System Switch */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">系统交易开关</Label>
                  <div className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/30 p-4">
                    <div className="space-y-1">
                      <div className="text-sm font-medium">全局自动交易</div>
                      <div className="text-xs text-muted-foreground">控制是否执行自动交易</div>
                    </div>
                    <Switch checked={tradingEnabled} onCheckedChange={setTradingEnabled} disabled={tradingPaused} />
                  </div>
                  {tradingPaused && (
                    <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-2 text-xs text-destructive">
                      <AlertTriangle className="h-4 w-4" />
                      交易已紧急暂停
                    </div>
                  )}
                </div>

                {/* Trading Periods */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">交易时段控制</Label>
                  <div className="space-y-2 rounded-lg border border-border/50 bg-muted/30 p-4">
                    {tradingPeriods.map((period) => (
                      <div key={period.id} className="flex items-center gap-3">
                        <Checkbox
                          id={period.id}
                          checked={period.enabled}
                          onCheckedChange={(checked) =>
                            setTradingPeriods(tradingPeriods.map((p) => (p.id === period.id ? { ...p, enabled: !!checked } : p)))
                          }
                        />
                        <Label htmlFor={period.id} className="flex-1 cursor-pointer text-sm">
                          {period.name} ({period.startTime}-{period.endTime})
                        </Label>
                        {period.enabled ? (
                          <Badge variant="outline" className="border-green-500/50 bg-green-500/10 text-green-400">
                            启用
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-muted-foreground">
                            禁用
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Emergency Pause */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">紧急暂停</Label>
                  <div className="space-y-3 rounded-lg border border-border/50 bg-muted/30 p-4">
                    <div className="text-xs text-muted-foreground">手动紧急暂停所有交易</div>
                    <div className="flex gap-2">
                      <Button
                        variant={tradingPaused ? "outline" : "destructive"}
                        size="sm"
                        onClick={handlePauseTrade}
                        disabled={tradingPaused}
                        className="flex-1"
                      >
                        <Pause className="mr-1.5 h-4 w-4" />
                        立即暂停
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleResumeTrade} disabled={!tradingPaused} className="flex-1">
                        <Play className="mr-1.5 h-4 w-4" />
                        恢复交易
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Special Dates and Calendar */}
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-3">
                  <Label className="text-sm font-medium">特殊日期设置</Label>
                  <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                    <div className="mb-3 flex gap-2">
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="outline" size="sm" className="w-[160px] justify-start">
                            <Calendar className="mr-2 h-4 w-4" />
                            {selectedDate ? format(selectedDate, "yyyy-MM-dd") : "选择日期"}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <CalendarComponent mode="single" selected={selectedDate} onSelect={setSelectedDate} locale={zhCN} />
                        </PopoverContent>
                      </Popover>
                      <Input placeholder="备注名称" value={newSpecialDateName} onChange={(e) => setNewSpecialDateName(e.target.value)} className="flex-1" />
                      <Button size="sm" onClick={handleAddSpecialDate} disabled={!selectedDate || !newSpecialDateName}>
                        <Plus className="mr-1.5 h-4 w-4" />
                        添加
                      </Button>
                    </div>
                    <ScrollArea className="h-[120px]">
                      <div className="space-y-2">
                        {specialDates.map((sd) => (
                          <div key={sd.date.toISOString()} className="flex items-center justify-between rounded-md bg-background/50 px-3 py-2">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="border-red-500/50 bg-red-500/10 text-red-400">
                                不交易
                              </Badge>
                              <span className="text-sm">{format(sd.date, "yyyy-MM-dd")}</span>
                              <span className="text-xs text-muted-foreground">{sd.name}</span>
                            </div>
                            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleDeleteSpecialDate(sd.date)}>
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label className="text-sm font-medium">交易日历</Label>
                  <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                    <CalendarComponent
                      mode="single"
                      locale={zhCN}
                      className="mx-auto"
                      modifiers={{ special: (date) => specialDateSet.has(date.toDateString()) }}
                      modifiersClassNames={{ special: "bg-red-500/20 text-red-400 font-medium" }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Module 2: Account Management */}
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Users className="h-5 w-5 text-primary" />
                账户管理
              </CardTitle>
              <CardDescription>多账户配置和切换</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs value={accountTab} onValueChange={setAccountTab}>
                <TabsList className="mb-4">
                  <TabsTrigger value="list">账户列表</TabsTrigger>
                  <TabsTrigger value="details">账户详情</TabsTrigger>
                </TabsList>

                <TabsContent value="list">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>账户名称</TableHead>
                        <TableHead>类型</TableHead>
                        <TableHead>状态</TableHead>
                        <TableHead>资产类别</TableHead>
                        <TableHead className="text-right">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {accounts.map((account) => (
                        <TableRow key={account.id}>
                          <TableCell className="font-medium">{account.name}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{account.type === "live" ? "实盘" : "模拟"}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={
                                account.status === "normal"
                                  ? "border-green-500/50 bg-green-500/10 text-green-400"
                                  : account.status === "paused"
                                    ? "border-yellow-500/50 bg-yellow-500/10 text-yellow-400"
                                    : "border-red-500/50 bg-red-500/10 text-red-400"
                              }
                            >
                              {account.status === "normal" ? "正常" : account.status === "paused" ? "暂停" : "禁用"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              {account.assetTypes.includes("futures") && (
                                <Badge variant="secondary" className="text-xs">
                                  期货
                                </Badge>
                              )}
                              {account.assetTypes.includes("stock") && (
                                <Badge variant="secondary" className="text-xs">
                                  股票
                                </Badge>
                              )}
                              {account.assetTypes.includes("forex") && (
                                <Badge variant="secondary" className="text-xs">
                                  外汇
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setSelectedAccount(account);
                                  setAccountTab("details");
                                }}
                              >
                                <Pencil className="mr-1 h-3 w-3" />
                                编辑
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => setAccounts(accounts.filter((a) => a.id !== account.id))}>
                                <Trash2 className="mr-1 h-3 w-3" />
                                删除
                              </Button>
                              <Button variant="outline" size="sm">
                                切换
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <div className="mt-4">
                    <Button variant="outline" size="sm" onClick={() => setShowAccountDialog(true)}>
                      <Plus className="mr-1.5 h-4 w-4" />
                      添加账户
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="details">
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-6">
                      {/* Basic Info */}
                      <div className="space-y-4 rounded-lg border border-border/50 bg-muted/30 p-4">
                        <h4 className="text-sm font-medium">账户基本信息</h4>
                        <div className="grid gap-4">
                          <div className="grid gap-2">
                            <Label>账户名称</Label>
                            <Input defaultValue={selectedAccount?.name || "主账户"} />
                          </div>
                          <div className="grid gap-2">
                            <Label>账户类型</Label>
                            <Select defaultValue={selectedAccount?.type || "live"}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="live">实盘</SelectItem>
                                <SelectItem value="sim">模拟</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="grid gap-2">
                            <Label>交易品种</Label>
                            <div className="flex flex-wrap gap-3">
                              {["futures", "stock", "forex", "fund", "option"].map((type) => (
                                <div key={type} className="flex items-center gap-2">
                                  <Checkbox
                                    id={`asset-${type}`}
                                    defaultChecked={selectedAccount?.assetTypes?.includes(type) || type === "futures"}
                                  />
                                  <Label htmlFor={`asset-${type}`} className="cursor-pointer text-sm">
                                    {type === "futures"
                                      ? "期货"
                                      : type === "stock"
                                        ? "股票"
                                        : type === "forex"
                                          ? "外汇"
                                          : type === "fund"
                                            ? "基金"
                                            : "期权"}
                                  </Label>
                                </div>
                              ))}
                            </div>
                          </div>
                          <div className="grid gap-2">
                            <Label>账户状态</Label>
                            <Select defaultValue={selectedAccount?.status || "normal"}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="normal">正常</SelectItem>
                                <SelectItem value="paused">暂停</SelectItem>
                                <SelectItem value="disabled">禁用</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </div>

                      {/* Futures Config */}
                      <div className="space-y-4 rounded-lg border border-border/50 bg-muted/30 p-4">
                        <h4 className="text-sm font-medium">期货账户配置</h4>
                        <div className="grid gap-4">
                          <div className="grid gap-2">
                            <Label>期货公司</Label>
                            <Select defaultValue={selectedAccount?.futuresConfig?.broker || "CTP"}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="CTP">CTP</SelectItem>
                                <SelectItem value="SimNow">SimNow</SelectItem>
                                <SelectItem value="飞马">飞马</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="grid gap-2">
                            <Label>经纪商 ID</Label>
                            <Input defaultValue={selectedAccount?.futuresConfig?.brokerId || ""} placeholder="经纪商 ID" />
                          </div>
                          <div className="grid gap-2">
                            <Label>用户 ID</Label>
                            <Input defaultValue={selectedAccount?.futuresConfig?.userId || ""} placeholder="用户 ID" />
                          </div>
                          <div className="grid gap-2">
                            <Label>密码</Label>
                            <Input type="password" defaultValue={selectedAccount?.futuresConfig?.password || ""} placeholder="********" />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Stock Config */}
                    <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-4 rounded-lg border border-border/50 bg-muted/30 p-4">
                        <h4 className="text-sm font-medium">股票账户配置</h4>
                        <div className="grid gap-4">
                          <div className="grid gap-2">
                            <Label>券商</Label>
                            <Select defaultValue={selectedAccount?.stockConfig?.broker || "中信"}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="中信">中信证券</SelectItem>
                                <SelectItem value="华泰">华泰证券</SelectItem>
                                <SelectItem value="国泰君安">国泰君安</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="grid gap-2">
                            <Label>账户号</Label>
                            <Input defaultValue={selectedAccount?.stockConfig?.accountNo || ""} placeholder="账户号" />
                          </div>
                          <div className="grid gap-2">
                            <Label>交易密码</Label>
                            <Input type="password" defaultValue={selectedAccount?.stockConfig?.password || ""} placeholder="********" />
                          </div>
                        </div>
                      </div>

                      <div className="flex items-end gap-2 pb-4">
                        <Button onClick={() => toast.success("保存成功：账户配置已保存")}>
                          <Save className="mr-1.5 h-4 w-4" />
                          保存账户
                        </Button>
                        <Button variant="outline" onClick={() => handleTestConnection("账户")}>
                          <TestTube className="mr-1.5 h-4 w-4" />
                          测试连接
                        </Button>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Module 3: Network Configuration */}
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Globe className="h-5 w-5 text-primary" />
                网络配置
              </CardTitle>
              <CardDescription>配置网络连接和组网方式</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-3 gap-6">
                {/* Network Mode Selection */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">组网方式选择</Label>
                  <RadioGroup
                    value={networkConfig.mode}
                    onValueChange={(value: NetworkConfig["mode"]) => setNetworkConfig({ ...networkConfig, mode: value })}
                    className="space-y-2"
                  >
                    <div className="flex items-center space-x-2 rounded-md border border-border/50 bg-muted/30 p-3">
                      <RadioGroupItem value="tailscale" id="tailscale" />
                      <Label htmlFor="tailscale" className="flex cursor-pointer items-center gap-2">
                        <Network className="h-4 w-4 text-blue-400" />
                        Tailscale
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2 rounded-md border border-border/50 bg-muted/30 p-3">
                      <RadioGroupItem value="pgyer" id="pgyer" />
                      <Label htmlFor="pgyer" className="flex cursor-pointer items-center gap-2">
                        <Router className="h-4 w-4 text-green-400" />
                        蒲公英
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2 rounded-md border border-border/50 bg-muted/30 p-3">
                      <RadioGroupItem value="direct" id="direct" />
                      <Label htmlFor="direct" className="flex cursor-pointer items-center gap-2">
                        <Wifi className="h-4 w-4 text-yellow-400" />
                        内网直连
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2 rounded-md border border-border/50 bg-muted/30 p-3">
                      <RadioGroupItem value="hybrid" id="hybrid" />
                      <Label htmlFor="hybrid" className="flex cursor-pointer items-center gap-2">
                        <Zap className="h-4 w-4 text-purple-400" />
                        混合模式
                      </Label>
                    </div>
                  </RadioGroup>
                </div>

                {/* Conditional Config Display */}
                {networkConfig.mode === "tailscale" && (
                  <div className="col-span-2 space-y-3">
                    <Label className="text-sm font-medium">Tailscale 配置</Label>
                    <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                      <div className="grid gap-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Tailnet</span>
                          <span className="font-mono text-sm">{networkConfig.tailscale.tailnet}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">状态</span>
                          <Badge
                            variant="outline"
                            className={
                              networkConfig.tailscale.status === "connected"
                                ? "border-green-500/50 bg-green-500/10 text-green-400"
                                : "border-red-500/50 bg-red-500/10 text-red-400"
                            }
                          >
                            {networkConfig.tailscale.status === "connected" ? "已连接" : "断开"}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">MagicDNS</span>
                          <Switch
                            checked={networkConfig.tailscale.magicDns}
                            onCheckedChange={(checked) =>
                              setNetworkConfig({ ...networkConfig, tailscale: { ...networkConfig.tailscale, magicDns: checked } })
                            }
                          />
                        </div>
                        <div className="flex gap-2 pt-2">
                          <Button variant="outline" size="sm" onClick={() => handleTestConnection("Tailscale")}>
                            <RefreshCw className="mr-1.5 h-4 w-4" />
                            重新认证
                          </Button>
                          <Button variant="outline" size="sm">
                            <Eye className="mr-1.5 h-4 w-4" />
                            查看设备
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {networkConfig.mode === "pgyer" && (
                  <div className="col-span-2 space-y-3">
                    <Label className="text-sm font-medium">蒲公英配置</Label>
                    <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                      <div className="grid gap-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">网络 ID</span>
                          <span className="font-mono text-sm">{networkConfig.pgyer.networkId}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">状态</span>
                          <Badge
                            variant="outline"
                            className={
                              networkConfig.pgyer.status === "connected"
                                ? "border-green-500/50 bg-green-500/10 text-green-400"
                                : "border-red-500/50 bg-red-500/10 text-red-400"
                            }
                          >
                            {networkConfig.pgyer.status === "connected" ? "已连接" : "断开"}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">设备 IP</span>
                          <span className="font-mono text-sm">{networkConfig.pgyer.deviceIp}</span>
                        </div>
                        <div className="flex gap-2 pt-2">
                          <Button variant="outline" size="sm" onClick={() => handleTestConnection("蒲公英")}>
                            <RefreshCw className="mr-1.5 h-4 w-4" />
                            重新连接
                          </Button>
                          <Button variant="outline" size="sm">
                            <Eye className="mr-1.5 h-4 w-4" />
                            查看设备
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {networkConfig.mode === "direct" && (
                  <div className="col-span-2 space-y-3">
                    <Label className="text-sm font-medium">内网直连配置</Label>
                    <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                      <div className="grid gap-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">网络状态</span>
                          <Badge variant="outline" className="border-green-500/50 bg-green-500/10 text-green-400">
                            已连接
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">网段</span>
                          <span className="font-mono text-sm">192.168.1.0/24</span>
                        </div>
                        <div className="flex gap-2 pt-2">
                          <Button variant="outline" size="sm" onClick={() => handleTestConnection("内网")}>
                            <TestTube className="mr-1.5 h-4 w-4" />
                            测试连接
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {networkConfig.mode === "hybrid" && (
                  <div className="col-span-2 space-y-3">
                    <Label className="text-sm font-medium">混合模式配置</Label>
                    <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                      <div className="grid gap-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">优先级</span>
                          <span className="text-sm">内网直连 {">"} Tailscale {">"} 蒲公英</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">故障转移</span>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={networkConfig.hybrid.autoFailover}
                              onCheckedChange={(checked) =>
                                setNetworkConfig({ ...networkConfig, hybrid: { ...networkConfig.hybrid, autoFailover: checked } })
                              }
                            />
                            <span className="text-xs text-muted-foreground">启用自动切换</span>
                          </div>
                        </div>
                        <div className="flex gap-2 pt-2">
                          <Button variant="outline" size="sm" onClick={() => handleTestConnection("混合网络")}>
                            <TestTube className="mr-1.5 h-4 w-4" />
                            测试连接
                          </Button>
                          <Button variant="outline" size="sm">
                            <Eye className="mr-1.5 h-4 w-4" />
                            查看路由表
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Module 4: Security Settings */}
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="h-5 w-5 text-primary" />
                安全设置
              </CardTitle>
              <CardDescription>系统安全和访问控制</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-3 gap-6">
                {/* Access Control Mode */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">访问控制</Label>
                  <RadioGroup value={accessMode} onValueChange={(value: typeof accessMode) => setAccessMode(value)} className="space-y-2">
                    <div className="flex items-center space-x-2 rounded-md border border-border/50 bg-muted/30 p-3">
                      <RadioGroupItem value="whitelist" id="whitelist-mode" />
                      <Label htmlFor="whitelist-mode" className="flex cursor-pointer items-center gap-2">
                        <Lock className="h-4 w-4 text-green-400" />
                        白名单模式
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2 rounded-md border border-border/50 bg-muted/30 p-3">
                      <RadioGroupItem value="password" id="password-mode" />
                      <Label htmlFor="password-mode" className="flex cursor-pointer items-center gap-2">
                        <Lock className="h-4 w-4 text-blue-400" />
                        密码模式
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2 rounded-md border border-border/50 bg-muted/30 p-3">
                      <RadioGroupItem value="hybrid" id="hybrid-mode" />
                      <Label htmlFor="hybrid-mode" className="flex cursor-pointer items-center gap-2">
                        <Shield className="h-4 w-4 text-purple-400" />
                        混合模式
                      </Label>
                    </div>
                  </RadioGroup>
                  <p className="text-xs text-muted-foreground">
                    {accessMode === "whitelist"
                      ? "白名单设备自动免登录"
                      : accessMode === "password"
                        ? "所有设备需密码验证"
                        : "白名单免登录，非白名单需密码"}
                  </p>
                </div>

                {/* IP Whitelist */}
                {(accessMode === "whitelist" || accessMode === "hybrid") && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-medium">IP 白名单</Label>
                      <Switch checked={ipWhitelistEnabled} onCheckedChange={setIpWhitelistEnabled} />
                    </div>
                    <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                      <ScrollArea className="h-[180px]">
                        <div className="space-y-2">
                          {whitelistIPs.map((ip) => (
                            <div key={ip.id} className="flex items-center justify-between rounded-md bg-background/50 px-3 py-2">
                              <div>
                                <span className="font-mono text-sm">{ip.ip}</span>
                                <span className="ml-2 text-xs text-muted-foreground">({ip.description})</span>
                              </div>
                              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleDeleteIP(ip.id)}>
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                      <Button variant="outline" size="sm" className="mt-3 w-full" onClick={() => setShowAddIPDialog(true)}>
                        <Plus className="mr-1.5 h-4 w-4" />
                        添加 IP
                      </Button>
                    </div>
                  </div>
                )}

                {/* Device Registration */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">设备注册</Label>
                  <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                    <ScrollArea className="h-[180px]">
                      <div className="space-y-2">
                        {registeredDevices.map((device) => (
                          <div key={device.id} className="flex items-center justify-between rounded-md bg-background/50 px-3 py-2">
                            <div className="flex items-center gap-2">
                              {getDeviceIcon(device.type)}
                              <div>
                                <div className="text-sm font-medium">{device.name}</div>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                  <span>{device.ip}</span>
                                  {device.autoLogin && (
                                    <Badge variant="outline" className="h-4 border-green-500/50 bg-green-500/10 px-1 text-[10px] text-green-400">
                                      免登录
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              <Badge
                                variant="outline"
                                className={
                                  device.status === "online"
                                    ? "border-green-500/50 bg-green-500/10 text-green-400"
                                    : "border-muted-foreground/50 text-muted-foreground"
                                }
                              >
                                {device.status === "online" ? "在线" : "离线"}
                              </Badge>
                              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleDeleteDevice(device.id)}>
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                    <Button variant="outline" size="sm" className="mt-3 w-full" onClick={() => setShowRegisterDeviceDialog(true)}>
                      <Plus className="mr-1.5 h-4 w-4" />
                      注册新设备
                    </Button>
                  </div>
                </div>
              </div>

              {/* Login Sessions */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">登录会话管理</Label>
                  <Button variant="outline" size="sm" onClick={handleEndAllSessions}>
                    <LogOut className="mr-1.5 h-4 w-4" />
                    结束所有会话
                  </Button>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>设备名称</TableHead>
                      <TableHead>IP 地址</TableHead>
                      <TableHead>登录时间</TableHead>
                      <TableHead>最后活动</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead className="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loginSessions.map((session) => (
                      <TableRow key={session.id}>
                        <TableCell className="font-medium">{session.deviceName}</TableCell>
                        <TableCell className="font-mono text-sm">{session.ip}</TableCell>
                        <TableCell>{session.loginTime}</TableCell>
                        <TableCell>{session.lastActivity}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={
                              session.status === "online"
                                ? "border-green-500/50 bg-green-500/10 text-green-400"
                                : "border-yellow-500/50 bg-yellow-500/10 text-yellow-400"
                            }
                          >
                            {session.status === "online" ? "在线" : "空闲"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" onClick={() => handleForceLogout(session.id)}>
                            <LogOut className="mr-1 h-3 w-3" />
                            强制登出
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Module 5: AI Model Configuration */}
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Brain className="h-5 w-5 text-primary" />
                AI 模型配置
              </CardTitle>
              <CardDescription>本地大模型管理和并发设置</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-3 gap-6">
                {/* Model Selection */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">模型选择</Label>
                  <RadioGroup value={selectedModel} onValueChange={setSelectedModel} className="space-y-2">
                    {aiModels.map((model) => (
                      <div
                        key={model.id}
                        className={`flex items-center space-x-2 rounded-md border p-3 ${
                          model.status === "downloaded" ? "border-border/50 bg-muted/30" : "border-border/30 bg-muted/10 opacity-60"
                        }`}
                      >
                        <RadioGroupItem value={model.id} id={`model-${model.id}`} disabled={model.status !== "downloaded"} />
                        <Label htmlFor={`model-${model.id}`} className="flex flex-1 cursor-pointer items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Cpu className="h-4 w-4 text-primary" />
                            <span>{model.name}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">({model.memoryRequired})</span>
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                {/* Concurrency Settings */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">并发设置</Label>
                  <div className="space-y-4 rounded-lg border border-border/50 bg-muted/30 p-4">
                    <div className="grid gap-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">最大并发数</Label>
                        <span className="text-sm font-medium">{maxConcurrency}</span>
                      </div>
                      <Input
                        type="number"
                        min={1}
                        max={4}
                        value={maxConcurrency}
                        onChange={(e) => setMaxConcurrency(Number(e.target.value))}
                        className="h-8"
                      />
                      <p className="text-xs text-muted-foreground">范围: 1-4</p>
                    </div>
                    <div className="grid gap-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">内存限制</Label>
                        <span className="text-sm font-medium">{memoryLimit} GB</span>
                      </div>
                      <Input
                        type="number"
                        min={8}
                        max={32}
                        value={memoryLimit}
                        onChange={(e) => setMemoryLimit(Number(e.target.value))}
                        className="h-8"
                      />
                      <p className="text-xs text-muted-foreground">范围: 8-32 GB</p>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label className="text-sm">GPU 加速</Label>
                        <p className="text-xs text-muted-foreground">使用 MPS 加速</p>
                      </div>
                      <Switch checked={gpuEnabled} onCheckedChange={setGpuEnabled} />
                    </div>
                  </div>
                </div>

                {/* Performance Monitor */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">模型性能监控</Label>
                  <div className="space-y-3 rounded-lg border border-border/50 bg-muted/30 p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">当前模型</span>
                      <span className="text-sm font-medium">{aiModels.find((m) => m.id === selectedModel)?.name}</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">内存占用</span>
                        <span>7.2 GB / {memoryLimit} GB</span>
                      </div>
                      <Progress value={(7.2 / memoryLimit) * 100} className="h-2" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">响应时间</span>
                      <span className="text-sm">1.25s</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">并发数</span>
                      <span className="text-sm">1/{maxConcurrency}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">状态</span>
                      <Badge variant="outline" className="border-green-500/50 bg-green-500/10 text-green-400">
                        正常
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>

              {/* Model Download Management */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">模型下载管理</Label>
                  <Button variant="outline" size="sm">
                    <RefreshCw className="mr-1.5 h-4 w-4" />
                    刷新模型列表
                  </Button>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>模型名称</TableHead>
                      <TableHead>文件名</TableHead>
                      <TableHead>大小</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead className="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {aiModels.map((model) => (
                      <TableRow key={model.id}>
                        <TableCell className="font-medium">{model.name}</TableCell>
                        <TableCell className="font-mono text-sm">{model.fileName}</TableCell>
                        <TableCell>{model.size}</TableCell>
                        <TableCell>
                          {model.status === "downloaded" ? (
                            <Badge variant="outline" className="border-green-500/50 bg-green-500/10 text-green-400">
                              已下载
                            </Badge>
                          ) : model.status === "downloading" ? (
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="border-yellow-500/50 bg-yellow-500/10 text-yellow-400">
                                下载中
                              </Badge>
                              <Progress value={model.progress} className="h-2 w-16" />
                              <span className="text-xs">{model.progress}%</span>
                            </div>
                          ) : (
                            <Badge variant="outline" className="text-muted-foreground">
                              未下载
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          {model.status === "downloaded" ? (
                            <Button variant="ghost" size="sm" onClick={() => handleDeleteModel(model.id)}>
                              <Trash2 className="mr-1 h-3 w-3" />
                              删除
                            </Button>
                          ) : model.status === "downloading" ? (
                            <Button variant="ghost" size="sm" onClick={() => handleCancelDownload(model.id)}>
                              <X className="mr-1 h-3 w-3" />
                              取消
                            </Button>
                          ) : (
                            <Button variant="outline" size="sm" onClick={() => handleDownloadModel(model.id)}>
                              <CloudDownload className="mr-1 h-3 w-3" />
                              下载
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Module 6: Device Management */}
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Monitor className="h-5 w-5 text-primary" />
                设备管理
              </CardTitle>
              <CardDescription>管理系统各设备配置和状态</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {systemDevices.map((device) => (
                  <Card key={device.id} className="border-border/50 bg-muted/30">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2 text-sm font-medium">
                          <Server className="h-4 w-4 text-primary" />
                          {getRoleName(device.role)}
                        </CardTitle>
                        <Badge
                          variant="outline"
                          className={
                            device.status === "online"
                              ? "border-green-500/50 bg-green-500/10 text-green-400"
                              : "border-red-500/50 bg-red-500/10 text-red-400"
                          }
                        >
                          {device.status === "online" ? "在线" : "离线"}
                        </Badge>
                      </div>
                      <CardDescription>{device.name}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3 pt-0">
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">内网 IP</span>
                          <span className="font-mono">{device.internalIp}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">外网 IP</span>
                          <div className="text-right">
                            <span className="font-mono text-xs">{device.tailscaleIp}</span>
                            <span className="mx-1 text-muted-foreground">/</span>
                            <span className="font-mono text-xs">{device.pgyerIp}</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">MAC 地址</span>
                          <span className="font-mono text-xs">{device.mac}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">注册状态</span>
                          <Badge
                            variant="outline"
                            className={device.registered ? "border-green-500/50 bg-green-500/10 text-green-400" : "text-muted-foreground"}
                          >
                            {device.registered ? "已注册" : "未注册"}
                          </Badge>
                        </div>
                      </div>
                      <Separator />
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleRemoteAction(device.id, "connect")}>
                          <Terminal className="mr-1 h-3 w-3" />
                          远程连接
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleRemoteAction(device.id, "restart")}>
                          <RefreshCw className="mr-1 h-3 w-3" />
                          重启
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleRemoteAction(device.id, "logs")}>
                          <Eye className="mr-1 h-3 w-3" />
                          查看日志
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleRemoteAction(device.id, "logout")}>
                          <LogOut className="mr-1 h-3 w-3" />
                          强制登出
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="mt-4">
                <Button variant="outline" size="sm" onClick={() => setShowAddDeviceDialog(true)}>
                  <Plus className="mr-1.5 h-4 w-4" />
                  添加设备
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Config Operations Section */}
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Settings className="h-5 w-5 text-primary" />
                配置操作
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Button onClick={handleSave}>
                  <Save className="mr-1.5 h-4 w-4" />
                  保存配置
                </Button>
                <Button variant="outline" onClick={handleResetDefaults}>
                  <RotateCcw className="mr-1.5 h-4 w-4" />
                  恢复默认
                </Button>
                <Button variant="outline" onClick={handleExport}>
                  <Download className="mr-1.5 h-4 w-4" />
                  导出配置 JSON
                </Button>
                <Button variant="outline" onClick={handleImport}>
                  <Upload className="mr-1.5 h-4 w-4" />
                  导入配置
                </Button>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">配置信息</h4>
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      最后保存时间：{lastSaveTime}
                    </div>
                    <div className="flex items-center gap-2">
                      <Info className="h-4 w-4" />
                      配置版本：{configVersion}
                    </div>
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      修改记录：{configHistory.length} 次
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-medium">最近修改记录</h4>
                  <ScrollArea className="h-[100px]">
                    <div className="space-y-2">
                      {configHistory.slice(0, 5).map((history) => (
                        <div key={history.id} className="rounded-md bg-muted/30 p-2 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{history.version}</span>
                            <span className="text-muted-foreground">{history.time}</span>
                          </div>
                          <div className="mt-1 text-muted-foreground">
                            {history.changes.slice(0, 2).map((change, idx) => (
                              <div key={idx}>• {change}</div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Save Config Confirmation Dialog */}
      <Dialog open={showSaveConfirm} onOpenChange={setShowSaveConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              确认保存配置？
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4 max-h-[400px] overflow-y-auto">
            <div className="space-y-2">
              <p className="text-sm font-medium text-foreground">修改项：{changedItems.length} 项</p>
              {changedItems.map((item, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <span className="text-primary mt-1">•</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
            <div className="rounded-md bg-amber-500/10 border border-amber-500/20 p-3 flex gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="text-xs text-amber-700 dark:text-amber-300">
                <p className="font-medium">⚠️ 注意：保存后将立即生效，影响后续交易决策</p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveConfirm(false)} disabled={isSaving}>
              取消
            </Button>
            <Button onClick={handleSaveConfig} disabled={isSaving} className="flex items-center gap-2">
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  处理中...
                </>
              ) : (
                '确认保存'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Confirmation Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>导入配置</DialogTitle>
            <DialogDescription>导入配置将覆盖当前所有设置，确定要继续吗？</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="rounded-md border border-dashed border-border/50 p-8 text-center">
              <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm text-muted-foreground">点击或拖拽 JSON 配置文件到此处</p>
              <Input type="file" accept=".json" className="mt-4" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowImportDialog(false)}>
              取消
            </Button>
            <Button onClick={confirmImport}>确认导入</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add IP Dialog */}
      <Dialog open={showAddIPDialog} onOpenChange={setShowAddIPDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加 IP 白名单</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>IP 地址</Label>
              <Input placeholder="例如: 192.168.1.100 或 192.168.1.0/24" value={newIP.ip} onChange={(e) => setNewIP({ ...newIP, ip: e.target.value })} />
            </div>
            <div className="grid gap-2">
              <Label>备注说明</Label>
              <Input placeholder="例如: 办公室电脑" value={newIP.description} onChange={(e) => setNewIP({ ...newIP, description: e.target.value })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddIPDialog(false)}>
              取消
            </Button>
            <Button onClick={handleAddIP}>添加</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Register Device Dialog */}
      <Dialog open={showRegisterDeviceDialog} onOpenChange={setShowRegisterDeviceDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>注册新设备</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>设备名称</Label>
              <Input placeholder="例如: MacBook Pro" value={newDevice.name} onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })} />
            </div>
            <div className="grid gap-2">
              <Label>设备类型</Label>
              <Select value={newDevice.type} onValueChange={(value: RegisteredDevice["type"]) => setNewDevice({ ...newDevice, type: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="laptop">笔记本</SelectItem>
                  <SelectItem value="phone">手机</SelectItem>
                  <SelectItem value="tablet">平板</SelectItem>
                  <SelectItem value="server">服务器</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>IP 地址</Label>
              <Input placeholder="例如: 192.168.1.100" value={newDevice.ip} onChange={(e) => setNewDevice({ ...newDevice, ip: e.target.value })} />
            </div>
            <div className="grid gap-2">
              <Label>MAC 地址</Label>
              <Input placeholder="例如: aa:bb:cc:dd:ee:ff" value={newDevice.mac} onChange={(e) => setNewDevice({ ...newDevice, mac: e.target.value })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRegisterDeviceDialog(false)}>
              取消
            </Button>
            <Button onClick={handleRegisterDevice}>注册</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add System Device Dialog */}
      <Dialog open={showAddDeviceDialog} onOpenChange={setShowAddDeviceDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加系统设备</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>设备名称</Label>
              <Input placeholder="例如: Mac Studio" />
            </div>
            <div className="grid gap-2">
              <Label>设备角色</Label>
              <Select defaultValue="trading">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="trading">交易端</SelectItem>
                  <SelectItem value="decision">决策端</SelectItem>
                  <SelectItem value="data">数据端</SelectItem>
                  <SelectItem value="dashboard">看板端</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>内网 IP</Label>
              <Input placeholder="例如: 192.168.1.102" />
            </div>
            <div className="grid gap-2">
              <Label>Tailscale IP</Label>
              <Input placeholder="例如: 100.82.139.52" />
            </div>
            <div className="grid gap-2">
              <Label>蒲公英 IP</Label>
              <Input placeholder="例如: 172.16.1.130" />
            </div>
            <div className="grid gap-2">
              <Label>MAC 地址</Label>
              <Input placeholder="例如: 11:22:33:44:55:66" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDeviceDialog(false)}>
              取消
            </Button>
            <Button
              onClick={() => {
                setShowAddDeviceDialog(false);
                toast.success("添加成功：设备已添加");
              }}
            >
              添加
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
}
