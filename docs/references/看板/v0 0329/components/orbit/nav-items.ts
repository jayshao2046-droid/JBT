import {
  Home,
  TrendingUp,
  LineChart as LineChartIcon,
  Monitor,
  Shield,
  Server,
  Settings,
  Wheat,
  BarChart3,
  Globe,
  DollarSign,
  PiggyBank,
  Target,
  Building2,
  Flag,
  Database,
  Gauge,
  HardDrive,
  Bell,
  FileText,
  Activity,
  Cpu,
  ScrollText,
  Sliders,
  ShieldCheck,
  Download,
  BellRing,
} from 'lucide-react'
import type { ViewType } from './command-dock'

export interface NavItem {
  id: string
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>
  label: string
  viewType?: ViewType
  children?: NavItem[]
}

export interface SystemStatusItem {
  id: string
  label: string
  status: 'online' | 'offline' | 'warning'
}

export const navItems: NavItem[] = [
  { id: 'dashboard', icon: Home, label: '首页', viewType: 'dashboard' },
  {
    id: 'trade',
    icon: TrendingUp,
    label: '交易',
    children: [
      { id: 'china-futures', label: '中国期货', icon: Wheat, viewType: 'china-futures' },
      { id: 'china-a-stock', label: '中国A股', icon: BarChart3, viewType: 'china-a-stock' },
      { id: 'foreign-exchange', label: '外盘交易', icon: Globe, viewType: 'china-futures' },
      { id: 'basic-exchange', label: '基金交易', icon: PiggyBank, viewType: 'china-futures' },
      { id: 'options', label: '期权交易', icon: Target, viewType: 'china-futures' },
      { id: 'hk-stocks', label: '香港股市', icon: Building2, viewType: 'china-a-stock' },
      { id: 'us-stocks', label: '美国股市', icon: Flag, viewType: 'china-a-stock' },
    ],
  },
  {
    id: 'strategy',
    icon: LineChartIcon,
    label: '策略',
    children: [
      { id: 'strategy-china-futures', label: '中国期货', icon: Wheat, viewType: 'strategy-china-futures' },
      { id: 'strategy-china-a-stock', label: '中国A股', icon: BarChart3, viewType: 'strategy-china-a-stock' },
    ],
  },
  {
    id: 'monitor',
    icon: Monitor,
    label: '监控',
    children: [
      { id: 'risk-monitor', label: '风险监控', icon: Shield, viewType: 'risk-monitor' },
      { id: 'alert-records', label: '告警记录', icon: Bell, viewType: 'alert-records' },
      { id: 'compliance-report', label: '合规报告', icon: FileText, viewType: 'compliance-report' },
    ],
  },
  {
    id: 'risk',
    icon: Shield,
    label: '风控',
    children: [
      { id: 'data-collection', label: '数据采集', icon: Database, viewType: 'data-collection' },
      { id: 'api-quota', label: 'API配额', icon: Gauge, viewType: 'api-quota' },
      { id: 'storage', label: '存储管理', icon: HardDrive, viewType: 'storage' },
    ],
  },
  {
    id: 'ops',
    icon: Server,
    label: '运维',
    children: [
      { id: 'device-heartbeat', label: '设备心跳', icon: Activity, viewType: 'device-heartbeat' },
      { id: 'process-monitor', label: '进程监控', icon: Cpu, viewType: 'process-monitor' },
      { id: 'log-records', label: '日志记录', icon: ScrollText, viewType: 'log-records' },
    ],
  },
  {
    id: 'settings',
    icon: Settings,
    label: '设置',
    viewType: 'settings',
    children: [
      { id: 'strategy-params', label: '策略参数', icon: Sliders, viewType: 'strategy-params' },
      { id: 'risk-params', label: '风控参数', icon: ShieldCheck, viewType: 'risk-params' },
      { id: 'collection-params', label: '采集参数', icon: Download, viewType: 'collection-params' },
      { id: 'notification-config', label: '通知配置', icon: BellRing, viewType: 'notification-config' },
    ],
  },
]

export const systemStatus: SystemStatusItem[] = [
  { id: 'data', label: '数据端', status: 'online' },
  { id: 'decision', label: '决策端', status: 'online' },
  { id: 'trading', label: '交易端', status: 'online' },
]
