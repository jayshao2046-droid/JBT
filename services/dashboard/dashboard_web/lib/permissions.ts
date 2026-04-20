export interface PermissionItem {
  key: string
  label: string
  description: string
}

export interface PermissionGroup {
  id: string
  label: string
  permissions: PermissionItem[]
}

export const PERMISSION_GROUPS: PermissionGroup[] = [
  {
    id: 'dashboard',
    label: '总控台',
    permissions: [
      { key: 'dashboard.view', label: '查看总控台', description: '访问系统主看板总览页面' },
    ],
  },
  {
    id: 'sim_trading',
    label: '模拟交易',
    permissions: [
      { key: 'sim_trading.view', label: '模拟交易概览', description: '查看账户权益、持仓、成交汇总' },
      { key: 'sim_trading.risk', label: '风控监控', description: '查看风控事件和告警历史' },
      { key: 'sim_trading.orders', label: '交易管理', description: '查看订单列表和手动下单操作' },
      { key: 'sim_trading.market', label: '行情检视', description: '查看实时行情和深度数据' },
      { key: 'sim_trading.intelligence', label: '战情风控', description: '高级智能风控分析' },
      { key: 'sim_trading.ctp_config', label: 'CTP 配置', description: '配置 CTP 连接参数（敏感操作）' },
      { key: 'sim_trading.risk_presets', label: '风控预设', description: '管理风控参数预设' },
    ],
  },
  {
    id: 'decision',
    label: '策略决策',
    permissions: [
      { key: 'decision.view', label: '策略决策概览', description: '查看策略总览和信号统计' },
      { key: 'decision.signals', label: '信号管理', description: '查看交易信号列表' },
      { key: 'decision.signals.approve', label: '信号审批', description: '审批或拒绝交易信号（敏感操作）' },
      { key: 'decision.research', label: '研究报告', description: '查看研究员分析报告' },
      { key: 'decision.strategies', label: '策略仓库', description: '查看和管理策略版本' },
      { key: 'decision.models', label: '模型管理', description: '配置 AI / LLM 模型参数' },
      { key: 'decision.reports', label: '研报管理', description: '管理历史研报记录' },
    ],
  },
  {
    id: 'data',
    label: '数据采集',
    permissions: [
      { key: 'data.view', label: '数据采集概览', description: '查看采集器状态统计' },
      { key: 'data.collectors', label: '采集器管理', description: '查看和控制 21 个数据采集器' },
      { key: 'data.explorer', label: '数据浏览器', description: '查询和导出历史数据' },
    ],
  },
  {
    id: 'backtest',
    label: '回测系统',
    permissions: [
      { key: 'backtest.view', label: '回测概览', description: '查看回测任务统计' },
      { key: 'backtest.run', label: '提交回测', description: '提交新的回测任务' },
      { key: 'backtest.results', label: '回测结果', description: '查看回测报告和绩效分析' },
      { key: 'backtest.review', label: '策略审核', description: '人工审核和评分策略' },
      { key: 'backtest.optimizer', label: '参数优化', description: '运行 Optuna 参数搜索优化' },
    ],
  },
  {
    id: 'researcher',
    label: '研究员',
    permissions: [
      { key: 'researcher.view', label: '研究员看板', description: '访问研究员专属工作台' },
    ],
  },
  {
    id: 'settings',
    label: '系统设置',
    permissions: [
      { key: 'settings.view', label: '查看系统设置', description: '查看系统配置和服务状态' },
      { key: 'settings.users', label: '用户管理', description: '添加、删除和管理用户账户（敏感操作）' },
    ],
  },
  {
    id: 'billing',
    label: '计费管理',
    permissions: [
      { key: 'billing.view', label: '计费查看', description: '查看 API 用量和费用统计' },
    ],
  },
]

export const ALL_PERMISSIONS: string[] = PERMISSION_GROUPS.flatMap(g =>
  g.permissions.map(p => p.key)
)

/** 新普通用户的默认只读权限 */
export const DEFAULT_USER_PERMISSIONS: string[] = [
  'dashboard.view',
  'sim_trading.view',
  'decision.view',
  'data.view',
  'backtest.view',
]
