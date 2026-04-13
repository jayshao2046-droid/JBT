"use client";
// uses useToastActions from toast-provider (no addToast)
import React, { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
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
  MessageSquare,
  AlertTriangle,
  Clock,
  Moon,
  FileText,
  History,
  Save,
  Download,
  Upload,
  RotateCcw,
  X,
  CheckCircle2,
  Loader2,
  Mail,
  Phone,
  MessageCircle,
  Bell,
  Send,
  Eye,
  EyeOff,
  RefreshCw,
  Search,
  ChevronDown,
  Copy,
  Trash2,
  AlertCircle,
  Info,
  Calendar,
  Zap,
  Shield,
} from "lucide-react";

// ─── Types ─────────────────────────────────────────────────────────────────

interface ChannelConfig {
  enabled: boolean;
  webhookUrl?: string;
  botName?: string;
  groupId?: string;
  strongReminder?: boolean;
  smtpServer?: string;
  port?: number;
  ssl?: boolean;
  from?: string;
  password?: string;
  recipients?: string[];
  provider?: string;
  accessKeyId?: string;
  accessKeySecret?: string;
  signName?: string;
  callCode?: string;
  status: "normal" | "error" | "unknown";
  todaySent: number;
  successRate: number;
  lastTest?: string;
  lastTestResult?: string;
}

interface AlertLevelConfig {
  name: string;
  color: string;
  conditions: Record<string, { enabled: boolean; threshold?: number }>;
  channels: Record<string, { enabled: boolean; strongReminder?: boolean; htmlFormat?: boolean }>;
  frequency: string;
  escalation: { enabled: boolean; timeout?: number; targetLevel?: string };
  responseTime: number;
}

interface ScheduledTask {
  enabled: boolean;
  time?: string;
  sessions?: { time: string; name: string; content: string[]; enabled: boolean }[];
  content?: string[];
  format?: Record<string, boolean>;
  channels: Record<string, boolean | { enabled: boolean; attachment?: boolean }>;
  lastSent?: string;
  lastStatus?: string;
  nextScheduled?: string;
}

interface TimeSettings {
  doNotDisturb: {
    enabled: boolean;
    start: string;
    end: string;
    p0p1Normal: boolean;
    p2p3Pause: boolean;
    allPause: boolean;
  };
  weekendHoliday: {
    weekend: "enabled" | "emergency_only" | "disabled";
    holiday: "enabled" | "emergency_only" | "disabled";
    autoSyncHolidays: boolean;
  };
  tradingHoursPriority: {
    enabled: boolean;
    daySession: { start: string; end: string };
    nightSession: { start: string; end: string };
    nonTradingDelay: number;
  };
}

interface HistoryRecord {
  id: string;
  time: string;
  level: string;
  channel: string;
  title: string;
  recipient: string;
  status: "success" | "failed" | "retrying";
  duration: number;
}

interface NotificationTemplate {
  feishu: string;
  email: { subject: string; body: string };
}

// ─── Mock Data ──────────────────────────────────────────────────────────────

const defaultChannels: Record<string, ChannelConfig> = {
  feishu: {
    enabled: true,
    webhookUrl: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx",
    botName: "BotQuant 监控助手",
    groupId: "oc_a1b2c3d4e5f6",
    strongReminder: true,
    status: "normal",
    todaySent: 125,
    successRate: 99.2,
    lastTest: "2026-03-21 17:08:32",
    lastTestResult: "连接成功！延迟 125ms，消息已发送到 [量化交易监控群]",
  },
  email: {
    enabled: true,
    smtpServer: "smtp.qq.com",
    port: 587,
    ssl: true,
    from: "botquant@xxx.com",
    password: "**************",
    recipients: ["jayshao@quant.com", "backup@quant.com"],
    status: "normal",
    todaySent: 85,
    successRate: 98.8,
    lastTest: "2026-03-21 17:08:32",
    lastTestResult: "发送成功！邮件已发送到 jayshao@quant.com",
  },
  sms: {
    enabled: true,
    provider: "aliyun",
    accessKeyId: "LTAI5t***********",
    accessKeySecret: "**************",
    signName: "BotQuant",
    recipients: ["138****1234"],
    status: "normal",
    todaySent: 12,
    successRate: 99.5,
  },
  phone: {
    enabled: true,
    provider: "aliyun",
    accessKeyId: "LTAI5t***********",
    accessKeySecret: "**************",
    callCode: "P0_ALERT",
    recipients: ["138****1234"],
    status: "normal",
    todaySent: 2,
    successRate: 100,
  },
};

const defaultAlertLevels: Record<string, AlertLevelConfig> = {
  P0: {
    name: "紧急告警",
    color: "red",
    conditions: {
      varExceed: { enabled: true, threshold: 10 },
      drawdownExceed: { enabled: true, threshold: -10 },
      leverageExceed: { enabled: true, threshold: 2.5 },
      dataInterrupt: { enabled: true, threshold: 30 },
      dailyLoss: { enabled: true, threshold: 4 },
    },
    channels: {
      feishu: { enabled: true, strongReminder: true },
      email: { enabled: true, htmlFormat: true },
      sms: { enabled: true },
      phone: { enabled: true },
    },
    frequency: "immediate",
    escalation: { enabled: true, timeout: 15, targetLevel: "P0" },
    responseTime: 5,
  },
  P1: {
    name: "重要告警",
    color: "amber",
    conditions: {
      varExceed: { enabled: true, threshold: 7 },
      drawdownExceed: { enabled: true, threshold: -7 },
      leverageExceed: { enabled: true, threshold: 2.0 },
      dataInterrupt: { enabled: true, threshold: 10 },
      singleSourceFail: { enabled: true },
    },
    channels: {
      feishu: { enabled: true, strongReminder: false },
      email: { enabled: true, htmlFormat: false },
      sms: { enabled: false },
      phone: { enabled: false },
    },
    frequency: "hourly",
    escalation: { enabled: true, timeout: 60, targetLevel: "P0" },
    responseTime: 15,
  },
  P2: {
    name: "一般告警",
    color: "blue",
    conditions: {
      varExceed: { enabled: true, threshold: 5 },
      drawdownExceed: { enabled: true, threshold: -5 },
      dataQualityDrop: { enabled: true },
      singleVarietyLoss: { enabled: true, threshold: 1 },
    },
    channels: {
      feishu: { enabled: true },
      email: { enabled: true },
      sms: { enabled: false },
      phone: { enabled: false },
    },
    frequency: "daily",
    escalation: { enabled: true, timeout: 1440, targetLevel: "P1" },
    responseTime: 60,
  },
  P3: {
    name: "提示告警",
    color: "gray",
    conditions: {
      normalSwitch: { enabled: true },
      backfillComplete: { enabled: true },
      dailyReport: { enabled: true },
    },
    channels: {
      feishu: { enabled: true },
      email: { enabled: true },
      sms: { enabled: false },
      phone: { enabled: false },
    },
    frequency: "daily",
    escalation: { enabled: false },
    responseTime: 1440,
  },
};

const defaultScheduledTasks: Record<string, ScheduledTask> = {
  premarketReminder: {
    enabled: true,
    sessions: [
      { time: "08:30", name: "日盘盘前", content: ["overnight", "news", "sentiment", "position"], enabled: true },
      { time: "13:00", name: "午盘盘前", content: ["morning_summary", "news", "position_change", "afternoon_outlook"], enabled: true },
      { time: "20:00", name: "夜盘盘前", content: ["daily_summary", "news", "overnight_preview", "risk_warning"], enabled: true },
    ],
    channels: { feishu: true, email: true },
  },
  dailyNewsBriefing: {
    enabled: true,
    time: "08:15",
    content: ["global_headlines", "major_events", "economic_data", "policy_updates"],
    format: { clearTitle: true, summary: true, impactAnalysis: true, sourceLinks: true },
    channels: { feishu: true, email: { enabled: true, attachment: true } },
    lastSent: "2026-03-21 08:15",
    lastStatus: "success",
    nextScheduled: "2026-03-22 08:15",
  },
  dailySummary: {
    enabled: false,
    time: "23:00",
    content: ["daily_pnl", "trade_stats", "alert_summary", "system_status"],
    channels: { feishu: true, email: true },
  },
};

const defaultTimeSettings: TimeSettings = {
  doNotDisturb: {
    enabled: true,
    start: "22:00",
    end: "08:00",
    p0p1Normal: true,
    p2p3Pause: true,
    allPause: false,
  },
  weekendHoliday: {
    weekend: "emergency_only",
    holiday: "emergency_only",
    autoSyncHolidays: true,
  },
  tradingHoursPriority: {
    enabled: true,
    daySession: { start: "09:00", end: "15:30" },
    nightSession: { start: "21:00", end: "23:00" },
    nonTradingDelay: 5,
  },
};

const defaultTemplates: Record<string, NotificationTemplate> = {
  P0: {
    feishu: `【紧急告警】{告警类型} 超阈值

⚠️ 当前值：{当前值}
📊 阈值：{阈值}
🎯 影响品种：{品种}
💰 潜在损失：{损失}

[立即处理] {处理链接}`,
    email: {
      subject: "[P0 紧急] {告警类型} - BotQuant 监控系统",
      body: "HTML 格式模板，包含详细图表和数据...",
    },
  },
  P1: {
    feishu: `【重要告警】{告警类型} 接近阈值

📈 当前值：{当前值}
📊 阈值：{阈值}
💡 建议操作：{建议操作}

[查看详情] {详情链接}`,
    email: {
      subject: "[P1 重要] {告警类型} - BotQuant 监控系统",
      body: "HTML 格式模板...",
    },
  },
  P2: {
    feishu: `【提示告警】{告警类型} 预警

当前值：{当前值}
阈值：{阈值}
无需立即处理`,
    email: {
      subject: "[P2 提示] {告警类型} - BotQuant 监控系统",
      body: "HTML 格式模板...",
    },
  },
  P3: {
    feishu: `【信息通知】{告警类型}

{内容}

仅供参考`,
    email: {
      subject: "[P3 信息] {告警类型} - BotQuant 监控系统",
      body: "HTML 格式模板...",
    },
  },
};

const templateVariables = [
  "告警类型", "当前值", "阈值", "品种", "损失", "处理链接", "时间",
  "建议操作", "影响账户", "影响品种", "潜在损失", "告警级别",
  "通知渠道", "响应时间", "负责人", "备注", "内容", "详情链接",
];

const defaultHistoryRecords: HistoryRecord[] = [
  { id: "1", time: "03-21 08:15", level: "P2", channel: "飞书 + 邮件", title: "全球新闻简报", recipient: "jay@...", status: "success", duration: 1.2 },
  { id: "2", time: "03-21 08:30", level: "P2", channel: "飞书 + 邮件", title: "盘前提醒", recipient: "jay@...", status: "success", duration: 0.8 },
  { id: "3", time: "03-21 10:15", level: "P1", channel: "飞书 + 邮件", title: "VaR 超标", recipient: "jay@...", status: "success", duration: 1.5 },
  { id: "4", time: "03-20 14:30", level: "P0", channel: "飞书 + 邮件 + 短信", title: "数据中断", recipient: "jay@...", status: "success", duration: 2.1 },
  { id: "5", time: "03-20 10:00", level: "P1", channel: "飞书 + 邮件", title: "回撤预警", recipient: "jay@...", status: "failed", duration: 0 },
  { id: "6", time: "03-19 23:00", level: "P3", channel: "飞书 + 邮件", title: "每日汇总", recipient: "jay@...", status: "success", duration: 1.8 },
];

const historyStats = {
  today: { sent: 210, success: 208, failed: 2, rate: 99.0 },
  week: { sent: 1458, success: 1445, failed: 13, rate: 99.1 },
  month: { sent: 6250, success: 6198, failed: 52, rate: 99.2 },
  byChannel: {
    feishu: { sent: 6200, rate: 99.2 },
    email: { sent: 6180, rate: 98.9 },
    sms: { sent: 125, rate: 99.5 },
    phone: { sent: 12, rate: 100 },
  },
};

// ─── Sub-components ──────────────────────────────────────────────────────────

function SectionHeader({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: typeof MessageSquare;
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
    <label className="block text-xs font-medium text-muted-foreground mb-1.5 whitespace-nowrap">
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
  disabled,
}: {
  value: string | number;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  className?: string;
  error?: string;
  disabled?: boolean;
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
        disabled={disabled}
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

function ChannelStatusBadge({ status }: { status: "normal" | "error" | "unknown" }) {
  const map = {
    normal: { color: "bg-emerald-500", text: "text-#3FB950", bg: "bg-emerald-500/10", label: "正常" },
    error: { color: "bg-red-500", text: "text-#FF3B30", bg: "bg-red-500/10", label: "异常" },
    unknown: { color: "bg-gray-500", text: "text-gray-600", bg: "bg-gray-500/10", label: "未知" },
  };
  const s = map[status];
  return (
    <div className={cn("flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium", s.bg, s.text)}>
      <span className={cn("w-1.5 h-1.5 rounded-full", s.color)} />
      {s.label}
    </div>
  );
}

function AlertLevelBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    P0: "bg-red-500/15 text-red-500 border-red-500/30",
    P1: "bg-amber-500/15 text-amber-500 border-amber-500/30",
    P2: "bg-blue-500/15 text-blue-500 border-blue-500/30",
    P3: "bg-gray-500/15 text-gray-400 border-gray-500/30",
  };
  return (
    <span className={cn("px-2 py-0.5 rounded text-[11px] font-medium border", colors[level] || colors.P3)}>
      {level}
    </span>
  );
}

function StatusBadge({ status }: { status: "success" | "failed" | "retrying" }) {
  const map = {
    success: { icon: CheckCircle2, color: "text-emerald-500", label: "成功" },
    failed: { icon: AlertCircle, color: "text-red-500", label: "失败" },
    retrying: { icon: RefreshCw, color: "text-amber-500", label: "重试中" },
  };
  const s = map[status];
  return (
    <div className={cn("flex items-center gap-1 text-xs", s.color)}>
      <s.icon className="w-3.5 h-3.5" />
      {s.label}
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
              <p className="text-[11px] text-amber-600">注意：部分配置需要重启通知服务后生效</p>
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

// ─── Template Preview Modal ───────────────────────────────────────────────────

function TemplatePreviewModal({
  open,
  onClose,
  level,
  template,
}: {
  open: boolean;
  onClose: () => void;
  level: string;
  template: NotificationTemplate;
}) {
  const previewContent = template.feishu
    .replace("{告警类型}", "VaR 超标")
    .replace("{当前值}", "12.5%")
    .replace("{阈值}", "10%")
    .replace("{品种}", "IF2403, IC2403")
    .replace("{损失}", "¥125,000")
    .replace("{处理链接}", "https://botquant.com/alert/123")
    .replace("{建议操作}", "建议减仓 20%")
    .replace("{详情链接}", "https://botquant.com/detail/123")
    .replace("{内容}", "系统运行正常");

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
            className="relative z-10 w-[520px] bg-card border border-border rounded-xl shadow-2xl"
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Eye className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">{level} 模板预览</h3>
                  <p className="text-xs text-muted-foreground">变量已替换为示例值</p>
                </div>
              </div>
              <button onClick={onClose} className="w-7 h-7 rounded-md hover:bg-muted flex items-center justify-center">
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">飞书消息预览</p>
                <div className="p-4 bg-muted/30 rounded-lg border border-border">
                  <pre className="text-xs text-foreground whitespace-pre-wrap font-sans">{previewContent}</pre>
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">邮件预览</p>
                <div className="p-4 bg-muted/30 rounded-lg border border-border space-y-2">
                  <p className="text-xs text-foreground">
                    <span className="text-muted-foreground">主题：</span>
                    {template.email.subject
                      .replace("{告警类型}", "VaR 超标")}
                  </p>
                  <p className="text-xs text-muted-foreground">{template.email.body}</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export function NotificationConfigView() {
  const toast = useToastActions();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State
  const [channels, setChannels] = useState(defaultChannels);
  const [alertLevels, setAlertLevels] = useState(defaultAlertLevels);
  const [scheduledTasks, setScheduledTasks] = useState(defaultScheduledTasks);
  const [timeSettings, setTimeSettings] = useState(defaultTimeSettings);
  const [templates, setTemplates] = useState(defaultTemplates);
  const [retryConfig, setRetryConfig] = useState({ enabled: true, maxRetries: 3, interval: 5, notifyOnFail: true });
  const [historyRecords] = useState(defaultHistoryRecords);
  
  // UI State
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [previewModal, setPreviewModal] = useState<{ open: boolean; level: string } | null>(null);
  const [testingChannel, setTestingChannel] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState<Record<string, boolean>>({});
  const [historyFilter, setHistoryFilter] = useState({ timeRange: "7days", level: "all", channel: "all", status: "all", search: "" });
  const [editingTemplate, setEditingTemplate] = useState<string | null>(null);
  const [showTemplatePreview, setShowTemplatePreview] = useState(false);
  const [previewTemplateLevel, setPreviewTemplateLevel] = useState("P0");
  const [previewVariables, setPreviewVariables] = useState({
    title: "强平风险预警",
    content: "账户强平风险等级已升至最高",
    time: new Date().toLocaleString("zh-CN"),
    level: "P0"
  });

  // Changes tracking
  const [changes, setChanges] = useState<string[]>([]);

  const addChange = useCallback((change: string) => {
    setChanges((prev) => {
      if (prev.includes(change)) return prev;
      return [...prev, change];
    });
  }, []);

  // Handlers
  const handleTestChannel = async (channelKey: string) => {
    setTestingChannel(channelKey);
    await new Promise((r) => setTimeout(r, 1500));
    
    // 模拟90%成功率
    const isSuccess = Math.random() > 0.1;
    setTestingChannel(null);
    
    if (isSuccess) {
      const responseTime = Math.floor(Math.random() * 100 + 50);
      setChannels((prev) => ({
        ...prev,
        [channelKey]: {
          ...prev[channelKey],
          lastTest: new Date().toLocaleString("zh-CN"),
          lastTestResult: `✅ 连接成功！延迟 ${responseTime}ms，消息已发送`,
          status: "normal",
        },
      }));
      toast.success(`✅ ${channelKey === "feishu" ? "飞书" : channelKey === "email" ? "邮箱" : channelKey}机器人连接成功`);
    } else {
      setChannels((prev) => ({
        ...prev,
        [channelKey]: {
          ...prev[channelKey],
          lastTest: new Date().toLocaleString("zh-CN"),
          lastTestResult: "❌ 连接失败，请检查配置",
          status: "error",
        },
      }));
      toast.error(`❌ 连接失败，请检查配置`);
    }
    
    const channelName = channelKey === "feishu" ? "飞书" : channelKey === "email" ? "邮件" : channelKey === "sms" ? "短信" : "电话";
    toast.success(`测试成功：${channelName}通道连接正常`);
  };

  const handleSave = () => {
    if (changes.length === 0) {
      toast.info("无需保存：配置未发生变化");
      return;
    }
    setShowConfirmModal(true);
  };

  const confirmSave = () => {
    setShowConfirmModal(false);
    toast.success(`保存成功：已保存 ${changes.length} 项配置修改`);
    setChanges([]);
  };

  const handleExport = () => {
    const config = {
      version: "v2.3",
      exportTime: new Date().toISOString(),
      channels,
      alertLevels,
      scheduledTasks,
      timeSettings,
      templates,
      retryConfig,
    };
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `notification-config-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("导出成功：配置文件已下载");
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const config = JSON.parse(ev.target?.result as string);
        if (config.channels) setChannels(config.channels);
        if (config.alertLevels) setAlertLevels(config.alertLevels);
        if (config.scheduledTasks) setScheduledTasks(config.scheduledTasks);
        if (config.timeSettings) setTimeSettings(config.timeSettings);
        if (config.templates) setTemplates(config.templates);
        if (config.retryConfig) setRetryConfig(config.retryConfig);
        toast.success("导入成功：配置已加载");
        addChange("导入外部配置文件");
      } catch {
        toast.error("导入失败：配置文件格式错误");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleResetDefault = () => {
    setChannels(defaultChannels);
    setAlertLevels(defaultAlertLevels);
    setScheduledTasks(defaultScheduledTasks);
    setTimeSettings(defaultTimeSettings);
    setTemplates(defaultTemplates);
    setRetryConfig({ enabled: true, maxRetries: 3, interval: 5, notifyOnFail: true });
    setChanges([]);
    toast.info("已恢复默认：所有配置已重置为默认值");
  };

  const handleResend = (record: HistoryRecord) => {
    toast.success(`重发成功：已重新发送 "${record.title}" 通知`);
  };

  // Filtered history
  const filteredHistory = historyRecords.filter((r) => {
    if (historyFilter.level !== "all" && r.level !== historyFilter.level) return false;
    if (historyFilter.status !== "all" && r.status !== historyFilter.status) return false;
    if (historyFilter.search && !r.title.includes(historyFilter.search)) return false;
    return true;
  });

  const conditionLabels: Record<string, string> = {
    varExceed: "VaR 超阈值",
    drawdownExceed: "回撤超阈值",
    leverageExceed: "杠杆超阈值",
    dataInterrupt: "数据中断",
    dailyLoss: "日亏损超阈值",
    singleSourceFail: "单源失败",
    dataQualityDrop: "数据质量下降",
    singleVarietyLoss: "单品种亏损",
    normalSwitch: "正常切换",
    backfillComplete: "补录完成",
    dailyReport: "日常报告",
  };

  const frequencyOptions = [
    { value: "immediate", label: "立即" },
    { value: "every_5min", label: "每 5 分钟" },
    { value: "every_15min", label: "每 15 分钟" },
    { value: "every_30min", label: "每 30 分钟" },
    { value: "hourly", label: "每小时汇总" },
    { value: "every_6h", label: "每 6 小时" },
    { value: "daily", label: "每日汇总" },
    { value: "weekly", label: "每周汇总" },
  ];

  const contentLabels: Record<string, string> = {
    overnight: "隔夜外盘涨跌",
    news: "早盘新闻",
    sentiment: "情绪指标",
    position: "持仓建议",
    morning_summary: "上午总结",
    position_change: "持仓变化",
    afternoon_outlook: "下午展望",
    daily_summary: "全天总结",
    overnight_preview: "外盘预告",
    risk_warning: "风险提示",
    global_headlines: "全球头条",
    major_events: "重大事件",
    economic_data: "经济数据",
    policy_updates: "政策动态",
    daily_pnl: "今日盈亏",
    trade_stats: "交易统计",
    alert_summary: "告警汇总",
    system_status: "系统状态",
  };

  return (
    <div className="min-w-[900px] h-full overflow-auto">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-foreground">通知配置</h1>
            <p className="text-xs text-muted-foreground mt-1">配置通知渠道、告警级别、定时任务和通知模板</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={handleResetDefault}>
              <RotateCcw className="w-3.5 h-3.5" />
              恢复默认
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={handleExport}>
              <Download className="w-3.5 h-3.5" />
              导出配置
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={() => fileInputRef.current?.click()}>
              <Upload className="w-3.5 h-3.5" />
              导入配置
            </Button>
            <input ref={fileInputRef} type="file" accept=".json" className="hidden" onChange={handleImport} />
            <Button size="sm" className="gap-1.5 text-xs bg-primary text-primary-foreground" onClick={handleSave}>
              <Save className="w-3.5 h-3.5" />
              保存配置
              {changes.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-primary-foreground/20 text-[10px]">
                  {changes.length}
                </span>
              )}
            </Button>
          </div>
        </div>

        {/* Module 1: Channel Config */}
        <div className="p-5 rounded-xl border border-border bg-card/50">
          <SectionHeader
            icon={MessageSquare}
            title="通知渠道配置"
            description="配置通知发送渠道，支持多渠道并行"
          />

          <div className="space-y-5">
            {/* Feishu */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <MessageCircle className="w-5 h-5 text-blue-500" />
                  <span className="text-sm font-medium text-foreground">飞书机器人配置</span>
                  <ChannelStatusBadge status={channels.feishu.status} />
                </div>
                <Switch
                  checked={channels.feishu.enabled}
                  onCheckedChange={(v) => {
                    setChannels((p) => ({ ...p, feishu: { ...p.feishu, enabled: v } }));
                    addChange(`飞书机器人 ${v ? "启用" : "禁用"}`);
                  }}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <FormLabel required>Webhook URL</FormLabel>
                  <ConfigInput
                    value={channels.feishu.webhookUrl || ""}
                    onChange={(v) => {
                      setChannels((p) => ({ ...p, feishu: { ...p.feishu, webhookUrl: v } }));
                      addChange("飞书 Webhook URL 更新");
                    }}
                    placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
                  />
                </div>
                <div>
                  <FormLabel>机器人名称</FormLabel>
                  <ConfigInput
                    value={channels.feishu.botName || ""}
                    onChange={(v) => {
                      setChannels((p) => ({ ...p, feishu: { ...p.feishu, botName: v } }));
                      addChange("飞书机器人名称更新");
                    }}
                    placeholder="BotQuant 监控助手"
                  />
                </div>
                <div>
                  <FormLabel>群聊 ID</FormLabel>
                  <ConfigInput
                    value={channels.feishu.groupId || ""}
                    onChange={(v) => {
                      setChannels((p) => ({ ...p, feishu: { ...p.feishu, groupId: v } }));
                      addChange("飞书群聊 ID 更新");
                    }}
                    placeholder="oc_a1b2c3d4e5f6"
                  />
                </div>
                <div className="col-span-2 flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="feishu-strong"
                      checked={channels.feishu.strongReminder}
                      onCheckedChange={(v) => {
                        setChannels((p) => ({ ...p, feishu: { ...p.feishu, strongReminder: !!v } }));
                        addChange(`飞书强提醒模式 ${v ? "开启" : "关闭"}`);
                      }}
                    />
                    <label htmlFor="feishu-strong" className="text-xs text-foreground cursor-pointer">
                      开启强提醒模式 (@全员)
                    </label>
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-border/60">
                <div className="flex items-center justify-between">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-xs"
                    onClick={() => handleTestChannel("feishu")}
                    disabled={testingChannel === "feishu"}
                  >
                    {testingChannel === "feishu" ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Send className="w-3.5 h-3.5" />
                    )}
                    测试连接
                  </Button>
                  <div className="text-xs text-muted-foreground">
                    今日发送：<span className="text-foreground">{channels.feishu.todaySent}</span> 条 | 
                    成功率：<span className="text-emerald-500">{channels.feishu.successRate}%</span>
                  </div>
                </div>
                {channels.feishu.lastTest && (
                  <div className="mt-3 p-3 rounded-lg bg-emerald-500/8 border border-emerald-500/20">
                    <div className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="text-xs text-#3FB950">{channels.feishu.lastTestResult}</p>
                        <p className="text-[10px] text-muted-foreground mt-1">最后测试时间：{channels.feishu.lastTest}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Email */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-amber-500" />
                  <span className="text-sm font-medium text-foreground">邮件 SMTP 配置</span>
                  <ChannelStatusBadge status={channels.email.status} />
                </div>
                <Switch
                  checked={channels.email.enabled}
                  onCheckedChange={(v) => {
                    setChannels((p) => ({ ...p, email: { ...p.email, enabled: v } }));
                    addChange(`邮件服务 ${v ? "启用" : "禁用"}`);
                  }}
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <FormLabel required>SMTP 服务器</FormLabel>
                  <ConfigInput
                    value={channels.email.smtpServer || ""}
                    onChange={(v) => {
                      setChannels((p) => ({ ...p, email: { ...p.email, smtpServer: v } }));
                      addChange("SMTP 服务器更新");
                    }}
                    placeholder="smtp.qq.com"
                  />
                </div>
                <div>
                  <FormLabel required>端口</FormLabel>
                  <ConfigInput
                    type="number"
                    value={channels.email.port || 587}
                    onChange={(v) => {
                      setChannels((p) => ({ ...p, email: { ...p.email, port: parseInt(v) || 587 } }));
                      addChange("SMTP 端口更新");
                    }}
                    placeholder="587"
                  />
                </div>
                <div className="flex items-end pb-0.5">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="email-ssl"
                      checked={channels.email.ssl}
                      onCheckedChange={(v) => {
                        setChannels((p) => ({ ...p, email: { ...p.email, ssl: !!v } }));
                        addChange(`SSL/TLS ${v ? "开启" : "关闭"}`);
                      }}
                    />
                    <label htmlFor="email-ssl" className="text-xs text-foreground cursor-pointer">SSL/TLS</label>
                  </div>
                </div>
                <div>
                  <FormLabel required>发件人邮箱</FormLabel>
                  <ConfigInput
                    value={channels.email.from || ""}
                    onChange={(v) => {
                      setChannels((p) => ({ ...p, email: { ...p.email, from: v } }));
                      addChange("发件人邮箱更新");
                    }}
                    placeholder="botquant@xxx.com"
                  />
                </div>
                <div className="col-span-2">
                  <FormLabel required>授权码/密码</FormLabel>
                  <div className="relative">
                    <Input
                      type={showPassword.email ? "text" : "password"}
                      value={channels.email.password || ""}
                      onChange={(e) => {
                        setChannels((p) => ({ ...p, email: { ...p.email, password: e.target.value } }));
                        addChange("邮箱授权码更新");
                      }}
                      className="h-8 text-xs bg-muted/30 border-border/60 pr-9"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((p) => ({ ...p, email: !p.email }))}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword.email ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div className="col-span-3">
                  <FormLabel required>收件人列表</FormLabel>
                  <ConfigInput
                    value={channels.email.recipients?.join(", ") || ""}
                    onChange={(v) => {
                      setChannels((p) => ({ ...p, email: { ...p.email, recipients: v.split(",").map((s) => s.trim()).filter(Boolean) } }));
                      addChange("收件人列表更新");
                    }}
                    placeholder="jayshao@quant.com, backup@quant.com"
                  />
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-border/60">
                <div className="flex items-center justify-between">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-xs"
                    onClick={() => handleTestChannel("email")}
                    disabled={testingChannel === "email"}
                  >
                    {testingChannel === "email" ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Send className="w-3.5 h-3.5" />
                    )}
                    测试发送
                  </Button>
                  <div className="text-xs text-muted-foreground">
                    今日发送：<span className="text-foreground">{channels.email.todaySent}</span> 条 | 
                    成功率：<span className="text-emerald-500">{channels.email.successRate}%</span>
                  </div>
                </div>
                {channels.email.lastTest && (
                  <div className="mt-3 p-3 rounded-lg bg-emerald-500/8 border border-emerald-500/20">
                    <div className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="text-xs text-#3FB950">{channels.email.lastTestResult}</p>
                        <p className="text-[10px] text-muted-foreground mt-1">最后测试时间：{channels.email.lastTest}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Channel Status Monitor */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <p className="text-xs font-medium text-foreground mb-3">渠道状态监控</p>
              <div className="space-y-2">
                {[
                  { key: "feishu", icon: MessageCircle, name: "飞书机器人", color: "text-blue-500" },
                  { key: "email", icon: Mail, name: "邮件服务", color: "text-amber-500" },
                  { key: "sms", icon: MessageSquare, name: "短信服务", color: "text-green-500" },
                  { key: "phone", icon: Phone, name: "电话服务", color: "text-purple-500" },
                ].map((ch) => {
                  const c = channels[ch.key as keyof typeof channels];
                  return (
                    <div key={ch.key} className="flex items-center justify-between py-2 px-3 rounded-lg bg-background/50">
                      <div className="flex items-center gap-3">
                        <ch.icon className={cn("w-4 h-4", ch.color)} />
                        <span className="text-xs text-foreground">{ch.name}</span>
                        <ChannelStatusBadge status={c.status} />
                      </div>
                      <div className="text-xs text-muted-foreground">
                        今日发送：<span className="text-foreground">{c.todaySent}</span> 条 | 
                        成功率：<span className={cn(c.successRate >= 99 ? "text-emerald-500" : c.successRate >= 95 ? "text-amber-500" : "text-red-500")}>{c.successRate}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="text-[10px] text-muted-foreground mt-3">最后同步时间：{new Date().toLocaleString("zh-CN")}</p>
            </div>
          </div>
        </div>

        {/* Module 2: Alert Level Config */}
        <div className="p-5 rounded-xl border border-border bg-card/50">
          <SectionHeader
            icon={AlertTriangle}
            title="告警级别配置"
            description="配置各级别告警的触发条件、通知渠道和升级机制"
          />

          <div className="space-y-4">
            {Object.entries(alertLevels).map(([level, config]) => {
              const colorMap: Record<string, { bg: string; border: string; dot: string }> = {
                red: { bg: "bg-red-500/5", border: "border-red-500/20", dot: "bg-red-500" },
                amber: { bg: "bg-amber-500/5", border: "border-amber-500/20", dot: "bg-amber-500" },
                blue: { bg: "bg-blue-500/5", border: "border-blue-500/20", dot: "bg-blue-500" },
                gray: { bg: "bg-gray-500/5", border: "border-gray-500/20", dot: "bg-gray-500" },
              };
              const c = colorMap[config.color] || colorMap.gray;

              return (
                <div key={level} className={cn("p-4 rounded-lg border", c.bg, c.border)}>
                  <div className="flex items-center gap-3 mb-4">
                    <span className={cn("w-3 h-3 rounded-full", c.dot)} />
                    <span className="text-sm font-medium text-foreground">{level} {config.name}</span>
                  </div>

                  {/* Conditions */}
                  <div className="mb-4">
                    <p className="text-xs font-medium text-muted-foreground mb-2">触发条件</p>
                    <div className="flex flex-wrap gap-3">
                      {Object.entries(config.conditions).map(([key, cond]) => (
                        <div key={key} className="flex items-center gap-2">
                          <Checkbox
                            id={`${level}-${key}`}
                            checked={cond.enabled}
                            onCheckedChange={(v) => {
                              setAlertLevels((p) => ({
                                ...p,
                                [level]: {
                                  ...p[level],
                                  conditions: {
                                    ...p[level].conditions,
                                    [key]: { ...p[level].conditions[key], enabled: !!v },
                                  },
                                },
                              }));
                              addChange(`${level} ${conditionLabels[key] || key} ${v ? "启用" : "禁用"}`);
                            }}
                          />
                          <label htmlFor={`${level}-${key}`} className="text-xs text-foreground cursor-pointer whitespace-nowrap">
                            {conditionLabels[key] || key}
                            {cond.threshold !== undefined && (
                              <span className="text-muted-foreground ml-1">
                                {">"} {cond.threshold}{key.includes("Loss") || key.includes("drawdown") ? "%" : key.includes("Interrupt") ? "分钟" : key.includes("leverage") ? "倍" : "%"}
                              </span>
                            )}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Channels */}
                  <div className="mb-4">
                    <p className="text-xs font-medium text-muted-foreground mb-2">通知渠道</p>
                    <div className="flex flex-wrap gap-4">
                      {[
                        { key: "feishu", label: "飞书", extra: config.channels.feishu?.strongReminder ? " (强提醒@全员)" : "" },
                        { key: "email", label: "邮件", extra: config.channels.email?.htmlFormat ? " (HTML 格式)" : "" },
                        { key: "sms", label: "短信" },
                        { key: "phone", label: "电话" },
                      ].map((ch) => (
                        <div key={ch.key} className="flex items-center gap-2">
                          <Checkbox
                            id={`${level}-ch-${ch.key}`}
                            checked={config.channels[ch.key]?.enabled}
                            onCheckedChange={(v) => {
                              setAlertLevels((p) => ({
                                ...p,
                                [level]: {
                                  ...p[level],
                                  channels: {
                                    ...p[level].channels,
                                    [ch.key]: { ...p[level].channels[ch.key], enabled: !!v },
                                  },
                                },
                              }));
                              addChange(`${level} ${ch.label}通知 ${v ? "启用" : "禁用"}`);
                            }}
                          />
                          <label htmlFor={`${level}-ch-${ch.key}`} className="text-xs text-foreground cursor-pointer whitespace-nowrap">
                            {ch.label}{ch.extra}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Frequency & Escalation */}
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <FormLabel>通知频率</FormLabel>
                      <Select
                        value={config.frequency}
                        onValueChange={(v) => {
                          setAlertLevels((p) => ({
                            ...p,
                            [level]: { ...p[level], frequency: v },
                          }));
                          addChange(`${level} 通知频率更新为 ${frequencyOptions.find((o) => o.value === v)?.label}`);
                        }}
                      >
                        <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {frequencyOptions.map((o) => (
                            <SelectItem key={o.value} value={o.value} className="text-xs">{o.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <FormLabel>升级机制</FormLabel>
                      <div className="flex items-center gap-2 h-8">
                        <Checkbox
                          id={`${level}-escalation`}
                          checked={config.escalation.enabled}
                          onCheckedChange={(v) => {
                            setAlertLevels((p) => ({
                              ...p,
                              [level]: {
                                ...p[level],
                                escalation: { ...p[level].escalation, enabled: !!v },
                              },
                            }));
                            addChange(`${level} 升级机制 ${v ? "启用" : "禁用"}`);
                          }}
                        />
                        <label htmlFor={`${level}-escalation`} className="text-xs text-foreground cursor-pointer">
                          {config.escalation.enabled && config.escalation.timeout
                            ? `${config.escalation.timeout} 分钟未处理升级为 ${config.escalation.targetLevel}`
                            : "无升级"}
                        </label>
                      </div>
                    </div>
                    <div>
                      <FormLabel>响应时间要求</FormLabel>
                      <div className="h-8 flex items-center text-xs text-foreground">
                        {"<"} {config.responseTime >= 60 ? `${config.responseTime / 60} 小时` : `${config.responseTime} 分钟`}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Module 3: Scheduled Tasks */}
        <div className="p-5 rounded-xl border border-border bg-card/50">
          <SectionHeader
            icon={Clock}
            title="定时通知配置"
            description="配置每日定时发送的通知任务"
          />

          <div className="space-y-5">
            {/* Pre-market Reminder */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Bell className="w-5 h-5 text-blue-500" />
                  <span className="text-sm font-medium text-foreground">盘前交易提醒</span>
                  <span className="text-xs text-muted-foreground">(每日 3 次)</span>
                </div>
                <Switch
                  checked={scheduledTasks.premarketReminder.enabled}
                  onCheckedChange={(v) => {
                    setScheduledTasks((p) => ({ ...p, premarketReminder: { ...p.premarketReminder, enabled: v } }));
                    addChange(`盘前提醒 ${v ? "启用" : "禁用"}`);
                  }}
                />
              </div>
              <div className="space-y-3">
                {scheduledTasks.premarketReminder.sessions?.map((session, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-background/50 border border-border/40">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-medium text-foreground">{session.name}</span>
                        <Input
                          type="time"
                          value={session.time}
                          onChange={(e) => {
                            const newSessions = [...(scheduledTasks.premarketReminder.sessions || [])];
                            newSessions[idx] = { ...newSessions[idx], time: e.target.value };
                            setScheduledTasks((p) => ({
                              ...p,
                              premarketReminder: { ...p.premarketReminder, sessions: newSessions },
                            }));
                            addChange(`${session.name}时间更新为 ${e.target.value}`);
                          }}
                          className="w-24 h-7 text-xs bg-muted/30 border-border/60"
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          "w-2 h-2 rounded-full",
                          session.enabled ? "bg-emerald-500" : "bg-gray-500"
                        )} />
                        <span className="text-xs text-muted-foreground">{session.enabled ? "已启用" : "已禁用"}</span>
                        <Switch
                          checked={session.enabled}
                          onCheckedChange={(v) => {
                            const newSessions = [...(scheduledTasks.premarketReminder.sessions || [])];
                            newSessions[idx] = { ...newSessions[idx], enabled: v };
                            setScheduledTasks((p) => ({
                              ...p,
                              premarketReminder: { ...p.premarketReminder, sessions: newSessions },
                            }));
                            addChange(`${session.name} ${v ? "启用" : "禁用"}`);
                          }}
                        />
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {session.content.map((c) => (
                        <span key={c} className="px-2 py-0.5 rounded bg-primary/10 text-[11px] text-primary">
                          {contentLabels[c] || c}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-4">
                <span className="text-xs text-muted-foreground">通知渠道：</span>
                {[{ key: "feishu", label: "飞书" }, { key: "email", label: "邮件" }].map((ch) => (
                  <div key={ch.key} className="flex items-center gap-2">
                    <Checkbox
                      id={`premarket-${ch.key}`}
                      checked={!!scheduledTasks.premarketReminder.channels[ch.key]}
                      onCheckedChange={(v) => {
                        setScheduledTasks((p) => ({
                          ...p,
                          premarketReminder: {
                            ...p.premarketReminder,
                            channels: { ...p.premarketReminder.channels, [ch.key]: !!v },
                          },
                        }));
                        addChange(`盘前提醒 ${ch.label} ${v ? "启用" : "禁用"}`);
                      }}
                    />
                    <label htmlFor={`premarket-${ch.key}`} className="text-xs text-foreground cursor-pointer">{ch.label}</label>
                  </div>
                ))}
              </div>
            </div>

            {/* Daily News Briefing */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-amber-500" />
                  <span className="text-sm font-medium text-foreground">全球新闻简报</span>
                  <span className="text-xs text-muted-foreground">(每日 1 次)</span>
                </div>
                <Switch
                  checked={scheduledTasks.dailyNewsBriefing.enabled}
                  onCheckedChange={(v) => {
                    setScheduledTasks((p) => ({ ...p, dailyNewsBriefing: { ...p.dailyNewsBriefing, enabled: v } }));
                    addChange(`新闻简报 ${v ? "启用" : "禁用"}`);
                  }}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FormLabel>发送时间</FormLabel>
                  <Input
                    type="time"
                    value={scheduledTasks.dailyNewsBriefing.time}
                    onChange={(e) => {
                      setScheduledTasks((p) => ({
                        ...p,
                        dailyNewsBriefing: { ...p.dailyNewsBriefing, time: e.target.value },
                      }));
                      addChange(`新闻简报发送时间更新为 ${e.target.value}`);
                    }}
                    className="h-8 text-xs bg-muted/30 border-border/60"
                  />
                </div>
                <div>
                  <FormLabel>内容范围</FormLabel>
                  <div className="flex flex-wrap gap-2">
                    {scheduledTasks.dailyNewsBriefing.content?.map((c) => (
                      <span key={c} className="px-2 py-0.5 rounded bg-amber-500/10 text-[11px] text-amber-600">
                        {contentLabels[c] || c}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="mt-3 p-3 rounded-lg bg-background/50">
                <p className="text-xs text-muted-foreground mb-2">简报格式</p>
                <div className="flex flex-wrap gap-3">
                  {[
                    { key: "clearTitle", label: "标题清晰" },
                    { key: "summary", label: "内容归纳" },
                    { key: "impactAnalysis", label: "影响分析" },
                    { key: "sourceLinks", label: "新闻源链接" },
                  ].map((f) => (
                    <div key={f.key} className="flex items-center gap-2">
                      <Checkbox
                        id={`briefing-${f.key}`}
                        checked={scheduledTasks.dailyNewsBriefing.format?.[f.key]}
                        onCheckedChange={(v) => {
                          setScheduledTasks((p) => ({
                            ...p,
                            dailyNewsBriefing: {
                              ...p.dailyNewsBriefing,
                              format: { ...p.dailyNewsBriefing.format, [f.key]: !!v },
                            },
                          }));
                          addChange(`新闻简报格式 ${f.label} ${v ? "启用" : "禁用"}`);
                        }}
                      />
                      <label htmlFor={`briefing-${f.key}`} className="text-xs text-foreground cursor-pointer">{f.label}</label>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                <div>
                  最近发送：<span className="text-foreground">{scheduledTasks.dailyNewsBriefing.lastSent}</span>
                  <span className="ml-2 text-emerald-500">({scheduledTasks.dailyNewsBriefing.lastStatus === "success" ? "成功" : "失败"})</span>
                </div>
                <div>
                  明日计划：<span className="text-foreground">{scheduledTasks.dailyNewsBriefing.nextScheduled}</span>
                </div>
              </div>
            </div>

            {/* Daily Summary */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-purple-500" />
                  <span className="text-sm font-medium text-foreground">每日汇总报告</span>
                  <span className="text-xs text-muted-foreground">(可选)</span>
                </div>
                <Switch
                  checked={scheduledTasks.dailySummary.enabled}
                  onCheckedChange={(v) => {
                    setScheduledTasks((p) => ({ ...p, dailySummary: { ...p.dailySummary, enabled: v } }));
                    addChange(`每日汇总 ${v ? "启用" : "禁用"}`);
                  }}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FormLabel>发送时间</FormLabel>
                  <Input
                    type="time"
                    value={scheduledTasks.dailySummary.time}
                    onChange={(e) => {
                      setScheduledTasks((p) => ({
                        ...p,
                        dailySummary: { ...p.dailySummary, time: e.target.value },
                      }));
                      addChange(`每日汇总发送时间更新为 ${e.target.value}`);
                    }}
                    className="h-8 text-xs bg-muted/30 border-border/60"
                  />
                </div>
                <div>
                  <FormLabel>内容</FormLabel>
                  <div className="flex flex-wrap gap-2">
                    {scheduledTasks.dailySummary.content?.map((c) => (
                      <span key={c} className="px-2 py-0.5 rounded bg-purple-500/10 text-[11px] text-purple-600">
                        {contentLabels[c] || c}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Module 4: Time Settings */}
        <div className="p-5 rounded-xl border border-border bg-card/50">
          <SectionHeader
            icon={Moon}
            title="通知时段设置"
            description="配置通知发送的时间段限制"
          />

          <div className="space-y-5">
            {/* Do Not Disturb */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-foreground">免打扰时段</span>
                <Switch
                  checked={timeSettings.doNotDisturb.enabled}
                  onCheckedChange={(v) => {
                    setTimeSettings((p) => ({ ...p, doNotDisturb: { ...p.doNotDisturb, enabled: v } }));
                    addChange(`免打扰时段 ${v ? "启用" : "禁用"}`);
                  }}
                />
              </div>
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <FormLabel>开始时间</FormLabel>
                  <Input
                    type="time"
                    value={timeSettings.doNotDisturb.start}
                    onChange={(e) => {
                      setTimeSettings((p) => ({ ...p, doNotDisturb: { ...p.doNotDisturb, start: e.target.value } }));
                      addChange(`免打扰开始时间更新为 ${e.target.value}`);
                    }}
                    className="h-8 text-xs bg-muted/30 border-border/60"
                  />
                </div>
                <div>
                  <FormLabel>结束时间</FormLabel>
                  <Input
                    type="time"
                    value={timeSettings.doNotDisturb.end}
                    onChange={(e) => {
                      setTimeSettings((p) => ({ ...p, doNotDisturb: { ...p.doNotDisturb, end: e.target.value } }));
                      addChange(`免打扰结束时间更新为 ${e.target.value}`);
                    }}
                    className="h-8 text-xs bg-muted/30 border-border/60"
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mb-2">此时间段内：</p>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="dnd-p0p1"
                    checked={timeSettings.doNotDisturb.p0p1Normal}
                    onCheckedChange={(v) => {
                      setTimeSettings((p) => ({ ...p, doNotDisturb: { ...p.doNotDisturb, p0p1Normal: !!v } }));
                      addChange(`免打扰时段 P0/P1 正常发送 ${v ? "启用" : "禁用"}`);
                    }}
                  />
                  <label htmlFor="dnd-p0p1" className="text-xs text-foreground cursor-pointer">P0/P1 级别正常发送</label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="dnd-p2p3"
                    checked={timeSettings.doNotDisturb.p2p3Pause}
                    onCheckedChange={(v) => {
                      setTimeSettings((p) => ({ ...p, doNotDisturb: { ...p.doNotDisturb, p2p3Pause: !!v } }));
                      addChange(`免打扰时段 P2/P3 暂停 ${v ? "启用" : "禁用"}`);
                    }}
                  />
                  <label htmlFor="dnd-p2p3" className="text-xs text-foreground cursor-pointer">不发送 P2/P3 级别通知</label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="dnd-all"
                    checked={timeSettings.doNotDisturb.allPause}
                    onCheckedChange={(v) => {
                      setTimeSettings((p) => ({ ...p, doNotDisturb: { ...p.doNotDisturb, allPause: !!v } }));
                      addChange(`免打扰时段全部暂停 ${v ? "启用" : "禁用"}`);
                    }}
                  />
                  <label htmlFor="dnd-all" className="text-xs text-foreground cursor-pointer">全部暂停 (不推荐)</label>
                </div>
              </div>
            </div>

            {/* Weekend/Holiday */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <span className="text-sm font-medium text-foreground block mb-4">周末/节假日通知</span>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FormLabel>周末通知</FormLabel>
                  <Select
                    value={timeSettings.weekendHoliday.weekend}
                    onValueChange={(v: TimeSettings["weekendHoliday"]["weekend"]) => {
                      setTimeSettings((p) => ({ ...p, weekendHoliday: { ...p.weekendHoliday, weekend: v } }));
                      addChange(`周末通知模式更新`);
                    }}
                  >
                    <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="enabled" className="text-xs">开启</SelectItem>
                      <SelectItem value="emergency_only" className="text-xs">仅紧急通知 (P0/P1)</SelectItem>
                      <SelectItem value="disabled" className="text-xs">完全关闭</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <FormLabel>节假日通知</FormLabel>
                  <Select
                    value={timeSettings.weekendHoliday.holiday}
                    onValueChange={(v: TimeSettings["weekendHoliday"]["holiday"]) => {
                      setTimeSettings((p) => ({ ...p, weekendHoliday: { ...p.weekendHoliday, holiday: v } }));
                      addChange(`节假日通知模式更新`);
                    }}
                  >
                    <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="enabled" className="text-xs">开启</SelectItem>
                      <SelectItem value="emergency_only" className="text-xs">仅紧急通知 (P0/P1)</SelectItem>
                      <SelectItem value="disabled" className="text-xs">完全关闭</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <Checkbox
                  id="auto-sync-holidays"
                  checked={timeSettings.weekendHoliday.autoSyncHolidays}
                  onCheckedChange={(v) => {
                    setTimeSettings((p) => ({ ...p, weekendHoliday: { ...p.weekendHoliday, autoSyncHolidays: !!v } }));
                    addChange(`自动同步节假日 ${v ? "启用" : "禁用"}`);
                  }}
                />
                <label htmlFor="auto-sync-holidays" className="text-xs text-foreground cursor-pointer">自动同步法定节假日列表</label>
              </div>
            </div>

            {/* Trading Hours Priority */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-foreground">交易时段优先</span>
                <Switch
                  checked={timeSettings.tradingHoursPriority.enabled}
                  onCheckedChange={(v) => {
                    setTimeSettings((p) => ({ ...p, tradingHoursPriority: { ...p.tradingHoursPriority, enabled: v } }));
                    addChange(`交易时段优先 ${v ? "启用" : "禁用"}`);
                  }}
                />
              </div>
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <FormLabel>日盘时段</FormLabel>
                  <div className="flex items-center gap-2">
                    <Input
                      type="time"
                      value={timeSettings.tradingHoursPriority.daySession.start}
                      onChange={(e) => {
                        setTimeSettings((p) => ({
                          ...p,
                          tradingHoursPriority: {
                            ...p.tradingHoursPriority,
                            daySession: { ...p.tradingHoursPriority.daySession, start: e.target.value },
                          },
                        }));
                        addChange(`日盘开始时间更新`);
                      }}
                      className="h-8 text-xs bg-muted/30 border-border/60 w-24"
                    />
                    <span className="text-xs text-muted-foreground">-</span>
                    <Input
                      type="time"
                      value={timeSettings.tradingHoursPriority.daySession.end}
                      onChange={(e) => {
                        setTimeSettings((p) => ({
                          ...p,
                          tradingHoursPriority: {
                            ...p.tradingHoursPriority,
                            daySession: { ...p.tradingHoursPriority.daySession, end: e.target.value },
                          },
                        }));
                        addChange(`日盘结束时间更新`);
                      }}
                      className="h-8 text-xs bg-muted/30 border-border/60 w-24"
                    />
                  </div>
                </div>
                <div>
                  <FormLabel>夜盘时段</FormLabel>
                  <div className="flex items-center gap-2">
                    <Input
                      type="time"
                      value={timeSettings.tradingHoursPriority.nightSession.start}
                      onChange={(e) => {
                        setTimeSettings((p) => ({
                          ...p,
                          tradingHoursPriority: {
                            ...p.tradingHoursPriority,
                            nightSession: { ...p.tradingHoursPriority.nightSession, start: e.target.value },
                          },
                        }));
                        addChange(`夜盘开始时间更新`);
                      }}
                      className="h-8 text-xs bg-muted/30 border-border/60 w-24"
                    />
                    <span className="text-xs text-muted-foreground">-</span>
                    <Input
                      type="time"
                      value={timeSettings.tradingHoursPriority.nightSession.end}
                      onChange={(e) => {
                        setTimeSettings((p) => ({
                          ...p,
                          tradingHoursPriority: {
                            ...p.tradingHoursPriority,
                            nightSession: { ...p.tradingHoursPriority.nightSession, end: e.target.value },
                          },
                        }));
                        addChange(`夜盘结束时间更新`);
                      }}
                      className="h-8 text-xs bg-muted/30 border-border/60 w-24"
                    />
                  </div>
                </div>
              </div>
              <div>
                <FormLabel>非交易时段通知延迟</FormLabel>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={timeSettings.tradingHoursPriority.nonTradingDelay}
                    onChange={(e) => {
                      setTimeSettings((p) => ({
                        ...p,
                        tradingHoursPriority: {
                          ...p.tradingHoursPriority,
                          nonTradingDelay: parseInt(e.target.value) || 0,
                        },
                      }));
                      addChange(`非交易时段延迟更新为 ${e.target.value} 分钟`);
                    }}
                    min={0}
                    max={30}
                    className="h-8 text-xs bg-muted/30 border-border/60 w-20"
                  />
                  <span className="text-xs text-muted-foreground">分钟 (0-30)</span>
                </div>
              </div>
              <p className="text-[11px] text-muted-foreground mt-3">
                说明：非交易时段的通知延迟到下一个交易时段开始时发送
              </p>
            </div>
          </div>
        </div>

        {/* Module 5: Templates */}
        <div className="p-5 rounded-xl border border-border bg-card/50">
          <SectionHeader
            icon={FileText}
            title="通知模板编辑"
            description="编辑各级别通知的消息模板"
          />

          <div className="space-y-4">
            {Object.entries(templates).map(([level, template]) => {
              const colorMap: Record<string, string> = {
                P0: "border-red-500/30",
                P1: "border-amber-500/30",
                P2: "border-blue-500/30",
                P3: "border-gray-500/30",
              };

              return (
                <div key={level} className={cn("p-4 rounded-lg bg-muted/20 border", colorMap[level] || "border-border/60")}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <AlertLevelBadge level={level} />
                      <span className="text-sm font-medium text-foreground">{alertLevels[level]?.name || level} 模板</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5 text-xs h-7"
                        onClick={() => setPreviewModal({ open: true, level })}
                      >
                        <Eye className="w-3.5 h-3.5" />
                        预览
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5 text-xs h-7"
                        onClick={() => {
                          setTemplates((p) => ({ ...p, [level]: defaultTemplates[level] }));
                          addChange(`${level} 模板重置为默认`);
                        }}
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        重置
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <FormLabel>飞书模板</FormLabel>
                      <Textarea
                        value={template.feishu}
                        onChange={(e) => {
                          setTemplates((p) => ({ ...p, [level]: { ...p[level], feishu: e.target.value } }));
                          addChange(`${level} 飞书模板更新`);
                        }}
                        className="min-h-[120px] text-xs bg-muted/30 border-border/60 font-mono"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <FormLabel>邮件主题</FormLabel>
                        <ConfigInput
                          value={template.email.subject}
                          onChange={(v) => {
                            setTemplates((p) => ({
                              ...p,
                              [level]: { ...p[level], email: { ...p[level].email, subject: v } },
                            }));
                            addChange(`${level} 邮件主题更新`);
                          }}
                        />
                      </div>
                      <div>
                        <FormLabel>邮件正文格式</FormLabel>
                        <div className="h-8 flex items-center text-xs text-muted-foreground">
                          HTML 格式，带图表和详细数据
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Variables List */}
            <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
              <p className="text-xs font-medium text-foreground mb-3">可用变量列表</p>
              <div className="flex flex-wrap gap-2">
                {templateVariables.map((v) => (
                  <button
                    key={v}
                    onClick={() => {
                      navigator.clipboard.writeText(`{${v}}`);
                      toast.info(`已复制：变量 {${v}} 已复制到剪贴板`);
                    }}
                    className="px-2 py-1 rounded bg-primary/10 text-[11px] text-primary hover:bg-primary/20 transition-colors cursor-pointer"
                  >
                    {`{${v}}`}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground mt-2">点击变量可复制</p>
            </div>
          </div>
        </div>

        {/* Module 6: History */}
        <div className="p-5 rounded-xl border border-border bg-card/50">
          <SectionHeader
            icon={History}
            title="通知历史记录"
            description="查看通知发送记录和统计"
          />

          {/* Filters */}
          <div className="p-4 rounded-lg bg-muted/20 border border-border/60 mb-4">
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <FormLabel>时间范围</FormLabel>
                <Select value={historyFilter.timeRange} onValueChange={(v) => setHistoryFilter((p) => ({ ...p, timeRange: v }))}>
                  <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60 w-28">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7days" className="text-xs">近 7 天</SelectItem>
                    <SelectItem value="30days" className="text-xs">近 30 天</SelectItem>
                    <SelectItem value="custom" className="text-xs">自定义</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <FormLabel>通知级别</FormLabel>
                <Select value={historyFilter.level} onValueChange={(v) => setHistoryFilter((p) => ({ ...p, level: v }))}>
                  <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60 w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all" className="text-xs">全部</SelectItem>
                    <SelectItem value="P0" className="text-xs">P0</SelectItem>
                    <SelectItem value="P1" className="text-xs">P1</SelectItem>
                    <SelectItem value="P2" className="text-xs">P2</SelectItem>
                    <SelectItem value="P3" className="text-xs">P3</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <FormLabel>通知渠道</FormLabel>
                <Select value={historyFilter.channel} onValueChange={(v) => setHistoryFilter((p) => ({ ...p, channel: v }))}>
                  <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60 w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all" className="text-xs">全部</SelectItem>
                    <SelectItem value="feishu" className="text-xs">飞书</SelectItem>
                    <SelectItem value="email" className="text-xs">邮件</SelectItem>
                    <SelectItem value="sms" className="text-xs">短信</SelectItem>
                    <SelectItem value="phone" className="text-xs">电话</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <FormLabel>发送状态</FormLabel>
                <Select value={historyFilter.status} onValueChange={(v) => setHistoryFilter((p) => ({ ...p, status: v }))}>
                  <SelectTrigger className="h-8 text-xs bg-muted/30 border-border/60 w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all" className="text-xs">全部</SelectItem>
                    <SelectItem value="success" className="text-xs">成功</SelectItem>
                    <SelectItem value="failed" className="text-xs">失败</SelectItem>
                    <SelectItem value="retrying" className="text-xs">重试中</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <FormLabel>搜索</FormLabel>
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                  <Input
                    value={historyFilter.search}
                    onChange={(e) => setHistoryFilter((p) => ({ ...p, search: e.target.value }))}
                    placeholder="输入关键词搜索..."
                    className="h-8 text-xs bg-muted/30 border-border/60 pl-8"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Records Table */}
          <div className="rounded-lg border border-border overflow-hidden mb-4">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-muted/30 border-b border-border">
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 whitespace-nowrap">时间</th>
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 whitespace-nowrap">级别</th>
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 whitespace-nowrap">渠道</th>
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 whitespace-nowrap">标题</th>
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 whitespace-nowrap">接收人</th>
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 whitespace-nowrap">状态</th>
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 whitespace-nowrap">耗时</th>
                  <th className="text-left font-medium text-muted-foreground px-4 py-3 whitespace-nowrap">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredHistory.map((record) => (
                  <tr key={record.id} className="border-b border-border/60 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3 text-foreground whitespace-nowrap">{record.time}</td>
                    <td className="px-4 py-3 whitespace-nowrap"><AlertLevelBadge level={record.level} /></td>
                    <td className="px-4 py-3 text-foreground whitespace-nowrap">{record.channel}</td>
                    <td className="px-4 py-3 text-foreground whitespace-nowrap">{record.title}</td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{record.recipient}</td>
                    <td className="px-4 py-3 whitespace-nowrap"><StatusBadge status={record.status} /></td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{record.duration > 0 ? `${record.duration}s` : "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <button className="text-primary hover:underline">查看</button>
                        <button className="text-primary hover:underline" onClick={() => handleResend(record)}>重发</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Statistics */}
          <div className="p-4 rounded-lg bg-muted/20 border border-border/60 mb-4">
            <p className="text-xs font-medium text-foreground mb-3">发送统计</p>
            <div className="space-y-2 mb-4">
              {[
                { label: "今日发送", ...historyStats.today },
                { label: "本周发送", ...historyStats.week },
                { label: "本月发送", ...historyStats.month },
              ].map((s) => (
                <div key={s.label} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{s.label}：</span>
                  <span className="text-foreground">
                    {s.sent.toLocaleString()} 条 | 成功：{s.success.toLocaleString()} 条 | 失败：{s.failed} 条 | 
                    成功率：<span className={cn(s.rate >= 99 ? "text-emerald-500" : s.rate >= 95 ? "text-amber-500" : "text-red-500")}>{s.rate}%</span>
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs font-medium text-foreground mb-2">按渠道统计</p>
            <div className="grid grid-cols-4 gap-3">
              {[
                { key: "feishu", label: "飞书", icon: MessageCircle, color: "text-blue-500" },
                { key: "email", label: "邮件", icon: Mail, color: "text-amber-500" },
                { key: "sms", label: "短信", icon: MessageSquare, color: "text-green-500" },
                { key: "phone", label: "电话", icon: Phone, color: "text-purple-500" },
              ].map((ch) => {
                const s = historyStats.byChannel[ch.key as keyof typeof historyStats.byChannel];
                return (
                  <div key={ch.key} className="p-3 rounded-lg bg-background/50">
                    <div className="flex items-center gap-2 mb-1">
                      <ch.icon className={cn("w-4 h-4", ch.color)} />
                      <span className="text-xs text-foreground">{ch.label}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {s.sent.toLocaleString()} 条 (<span className="text-emerald-500">{s.rate}%</span>)
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Retry Config */}
          <div className="p-4 rounded-lg bg-muted/20 border border-border/60">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium text-foreground">失败重试配置</span>
              <Switch
                checked={retryConfig.enabled}
                onCheckedChange={(v) => {
                  setRetryConfig((p) => ({ ...p, enabled: v }));
                  addChange(`失败重试 ${v ? "启用" : "禁用"}`);
                }}
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <FormLabel>重试次数</FormLabel>
                <Input
                  type="number"
                  value={retryConfig.maxRetries}
                  onChange={(e) => {
                    setRetryConfig((p) => ({ ...p, maxRetries: parseInt(e.target.value) || 3 }));
                    addChange(`重试次数更新为 ${e.target.value}`);
                  }}
                  min={1}
                  max={10}
                  className="h-8 text-xs bg-muted/30 border-border/60"
                />
              </div>
              <div>
                <FormLabel>重试间隔</FormLabel>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={retryConfig.interval}
                    onChange={(e) => {
                      setRetryConfig((p) => ({ ...p, interval: parseInt(e.target.value) || 5 }));
                      addChange(`重试间隔更新为 ${e.target.value} 分钟`);
                    }}
                    min={1}
                    max={60}
                    className="h-8 text-xs bg-muted/30 border-border/60"
                  />
                  <span className="text-xs text-muted-foreground whitespace-nowrap">分钟</span>
                </div>
              </div>
              <div className="flex items-end pb-0.5">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="retry-notify"
                    checked={retryConfig.notifyOnFail}
                    onCheckedChange={(v) => {
                      setRetryConfig((p) => ({ ...p, notifyOnFail: !!v }));
                      addChange(`重试失败通知 ${v ? "启用" : "禁用"}`);
                    }}
                  />
                  <label htmlFor="retry-notify" className="text-xs text-foreground cursor-pointer whitespace-nowrap">
                    重试失败后通知管理员
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Config Info */}
        <div className="p-4 rounded-lg border border-border bg-card/50">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span>最后保存时间：<span className="text-foreground">2026-03-21 17:08:32</span></span>
              <span>配置版本：<span className="text-foreground">v2.3</span></span>
              <span>修改记录：<span className="text-foreground">3 次</span></span>
            </div>
            {changes.length > 0 && (
              <span className="text-amber-500">有 {changes.length} 项未保存的修改</span>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <ConfirmSaveModal
        open={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onConfirm={confirmSave}
        changes={changes}
      />

      {previewModal && (
        <TemplatePreviewModal
          open={previewModal.open}
          onClose={() => setPreviewModal(null)}
          level={previewModal.level}
          template={templates[previewModal.level]}
        />
      )}
    </div>
  );
}
