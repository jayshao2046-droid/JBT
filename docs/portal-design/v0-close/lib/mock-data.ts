import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Lock,
  Activity,
  PieChart,
  AlertTriangle,
  Target,
  Zap,
  BarChart3,
  Database,
  CheckSquare,
} from 'lucide-react'

// KPI 数据类型
export interface KPIData {
  id: string
  title: string
  value: string | number
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: React.ElementType
  description?: string
  progress?: number
  status?: 'success' | 'warning' | 'danger'
}

// 持仓数据类型
export interface PositionData {
  id: string
  symbol: string
  direction: 'long' | 'short'
  quantity: number
  costPrice: number
  currentPrice: number
  profitLoss: number
  profitLossPercent: number
}

// 策略信号类型
export interface StrategySignal {
  id: string
  symbol: string
  price: number
  strategyName: string
  confidence: number
  signalType: 'bullish' | 'bearish' | 'neutral'
  isDisabled: boolean
  timestamp: string
}

// 数据源状态类型
export interface DataSourceStatus {
  id: string
  name: string
  status: 'online' | 'warning' | 'offline'
  sourceCount: number
  lastUpdate: string
}

// 新闻数据类型
export interface NewsItem {
  id: string
  title: string
  source: string
  publishTime: string
  importance: 'high' | 'medium' | 'low'
  category?: string
}

// 收益数据类型
export interface ChurnData {
  metric: string
  value: number
  fullMark: number
}

// Mock KPI 数据
export const mockKPIData: KPIData[] = [
  {
    id: 'profit-today',
    title: '今日盈亏',
    value: 12345.67,
    change: '+8.5%',
    changeType: 'positive',
    icon: TrendingUp,
    description: '日收益 ¥',
  },
  {
    id: 'account-equity',
    title: '账户权益',
    value: 1234567.89,
    change: '+2.3%',
    changeType: 'positive',
    icon: Wallet,
    description: '总权益 ¥',
  },
  {
    id: 'margin-used',
    title: '持仓保证金',
    value: 456789.12,
    change: '37%',
    changeType: 'neutral',
    icon: Lock,
    description: '占总权益 %',
  },
  {
    id: 'float-profit',
    title: '浮动盈亏',
    value: 23456.78,
    change: '+1.9%',
    changeType: 'positive',
    icon: Activity,
    description: '未平仓 ¥',
  },
  {
    id: 'position-usage',
    title: '仓位使用率',
    value: 65,
    change: '',
    changeType: 'neutral',
    icon: PieChart,
    progress: 65,
    status: 'success',
  },
  {
    id: 'var-risk',
    title: 'VaR 风险值',
    value: 123456.78,
    change: '中',
    changeType: 'neutral',
    icon: AlertTriangle,
    description: '95% 置信度 ¥',
  },
  {
    id: 'win-rate',
    title: '胜率',
    value: 68,
    change: '68/100',
    changeType: 'positive',
    icon: Target,
    description: '盈利交易占比 %',
  },
  {
    id: 'profit-ratio',
    title: '盈亏比',
    value: 2.45,
    change: '优秀',
    changeType: 'positive',
    icon: TrendingUp,
    description: '平均盈利/亏损',
  },
  {
    id: 'signal-count',
    title: '策略信号数量',
    value: 12,
    change: '8待处理',
    changeType: 'neutral',
    icon: Zap,
    description: '活跃信号',
  },
  {
    id: 'trade-count-today',
    title: '今日交易笔数',
    value: 28,
    change: '+5笔',
    changeType: 'positive',
    icon: BarChart3,
    description: '开仓/平仓',
  },
  {
    id: 'datasource-status',
    title: '数据源状态',
    value: '8/10',
    change: '在线',
    changeType: 'positive',
    icon: Database,
    description: '在线数据源',
  },
  {
    id: 'todo-items',
    title: '待办事项',
    value: 5,
    change: '高优先级',
    changeType: 'neutral',
    icon: CheckSquare,
    description: '未完成任务',
  },
]

// Mock 持仓数据
export const mockPositions: PositionData[] = [
  {
    id: '1',
    symbol: 'IF2504',
    direction: 'long',
    quantity: 10,
    costPrice: 3850.5,
    currentPrice: 3920.0,
    profitLoss: 6950.0,
    profitLossPercent: 1.81,
  },
  {
    id: '2',
    symbol: 'IF2505',
    direction: 'short',
    quantity: 5,
    costPrice: 3900.0,
    currentPrice: 3850.0,
    profitLoss: 2500.0,
    profitLossPercent: 1.28,
  },
  {
    id: '3',
    symbol: 'IC2504',
    direction: 'long',
    quantity: 8,
    costPrice: 8450.25,
    currentPrice: 8520.75,
    profitLoss: 5640.0,
    profitLossPercent: 0.83,
  },
  {
    id: '4',
    symbol: 'IM2504',
    direction: 'long',
    quantity: 15,
    costPrice: 1200.5,
    currentPrice: 1185.25,
    profitLoss: -2268.75,
    profitLossPercent: -1.27,
  },
  {
    id: '5',
    symbol: 'T2506',
    direction: 'short',
    quantity: 20,
    costPrice: 99.5,
    currentPrice: 99.65,
    profitLoss: -3000.0,
    profitLossPercent: 0.15,
  },
]

// Mock 策略信号数据
export const mockSignals: StrategySignal[] = [
  {
    id: '1',
    symbol: 'IF2504',
    price: 3920.0,
    strategyName: '趋势跟踪',
    confidence: 85,
    signalType: 'bullish',
    isDisabled: false,
    timestamp: '2024-01-15T10:30:00Z',
  },
  {
    id: '2',
    symbol: 'IC2504',
    price: 8520.75,
    strategyName: '均值回归',
    confidence: 72,
    signalType: 'bearish',
    isDisabled: false,
    timestamp: '2024-01-15T10:28:00Z',
  },
  {
    id: '3',
    symbol: 'IM2504',
    price: 1185.25,
    strategyName: '动量策略',
    confidence: 68,
    signalType: 'neutral',
    isDisabled: false,
    timestamp: '2024-01-15T10:25:00Z',
  },
  {
    id: '4',
    symbol: 'T2506',
    price: 99.65,
    strategyName: '统计套利',
    confidence: 78,
    signalType: 'bullish',
    isDisabled: true,
    timestamp: '2024-01-15T10:20:00Z',
  },
  {
    id: '5',
    symbol: 'IF2505',
    price: 3850.0,
    strategyName: '波动率交易',
    confidence: 62,
    signalType: 'bearish',
    isDisabled: false,
    timestamp: '2024-01-15T10:18:00Z',
  },
  {
    id: '6',
    symbol: 'CIF2504',
    price: 245.5,
    strategyName: '机器学习',
    confidence: 81,
    signalType: 'bullish',
    isDisabled: false,
    timestamp: '2024-01-15T10:15:00Z',
  },
]

// Mock 收益数据
export const mockChurnData: ChurnData[] = [
  { metric: '日收益', value: 8.5, fullMark: 20 },
  { metric: '周收益', value: 12.3, fullMark: 30 },
  { metric: '月收益', value: 18.6, fullMark: 50 },
  { metric: '年收益', value: 35.8, fullMark: 100 },
  { metric: '夏普比率', value: 1.85, fullMark: 3 },
  { metric: '最大回撤', value: 8.2, fullMark: 20 },
]

// Mock 数据源状态
export const mockDataSources: DataSourceStatus[] = [
  {
    id: '1',
    name: '新闻 API',
    status: 'online',
    sourceCount: 5,
    lastUpdate: '2024-01-15T10:35:00Z',
  },
  {
    id: '2',
    name: '期货 K 线',
    status: 'online',
    sourceCount: 12,
    lastUpdate: '2024-01-15T10:35:00Z',
  },
  {
    id: '3',
    name: '股票 K 线',
    status: 'online',
    sourceCount: 8,
    lastUpdate: '2024-01-15T10:35:00Z',
  },
  {
    id: '4',
    name: '财经日历',
    status: 'warning',
    sourceCount: 3,
    lastUpdate: '2024-01-15T10:30:00Z',
  },
  {
    id: '5',
    name: '实时行情',
    status: 'online',
    sourceCount: 50,
    lastUpdate: '2024-01-15T10:35:00Z',
  },
  {
    id: '6',
    name: '基本面数据',
    status: 'offline',
    sourceCount: 6,
    lastUpdate: '2024-01-15T09:00:00Z',
  },
]

// Mock 新闻数据
export const mockNews: NewsItem[] = [
  {
    id: '1',
    title: '美联储宣布暂停加息，市场反应积极',
    source: '新华财经',
    publishTime: '2024-01-15T10:30:00Z',
    importance: 'high',
    category: '宏观经济',
  },
  {
    id: '2',
    title: '科技股继续上涨，AI概念再创新高',
    source: '中国证券报',
    publishTime: '2024-01-15T10:15:00Z',
    importance: 'high',
    category: '行业动态',
  },
  {
    id: '3',
    title: '期货市场成交量创历史新高',
    source: '期货日报',
    publishTime: '2024-01-15T09:45:00Z',
    importance: 'medium',
    category: '市场数据',
  },
  {
    id: '4',
    title: '央行宣布流动性管理新措施',
    source: '金融时报',
    publishTime: '2024-01-15T09:30:00Z',
    importance: 'high',
    category: '金融政策',
  },
  {
    id: '5',
    title: '国债收益率跌至年内新低',
    source: '第一财经',
    publishTime: '2024-01-15T09:00:00Z',
    importance: 'medium',
    category: '债券市场',
  },
  {
    id: '6',
    title: '能源板块异军突起，油价创新高',
    source: '证券时报',
    publishTime: '2024-01-15T08:30:00Z',
    importance: 'medium',
    category: '大宗商品',
  },
]

// 时间格式化函数
export function formatTimeAgo(timestamp: string): string {
  const now = new Date()
  const past = new Date(timestamp)
  const diffMs = now.getTime() - past.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  return `${diffDays}天前`
}
