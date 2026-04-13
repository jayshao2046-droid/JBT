# Dashboard 完整升级提示词 - 参考 v0 0329 版本

## 总体要求

请参考 `参考文件/v0 0329/` 中的完整实现，对当前的 Dashboard 首页进行全面升级。保持现有的布局框架（MainLayout + AppSidebar + AppHeader），重点升级首页内容。

**核心原则：**
- 所有数据使用模拟数据（mock data）
- 保持橙色主题（orange-500/600）和深色背景（neutral-900/800）
- 使用 shadcn/ui 组件库 + Tailwind CSS
- 使用 lucide-react 图标库
- 使用 recharts 进行数据可视化
- TypeScript 类型定义完整
- 响应式布局，支持移动端

---

## 第一部分：核心 KPI 指标区（顶部）

### 布局
- 3 行 × 4 列网格布局
- 每个 KPI 卡片高度 120px
- 使用 `grid grid-cols-4 gap-4` 布局

### 12 个核心 KPI

**第一行：**
1. **今日盈亏**
   - 显示金额（带正负号和颜色）
   - 显示涨跌幅百分比
   - 使用 TrendingUp/TrendingDown 图标
   - CountUp 动画效果

2. **账户权益**
   - 显示总权益金额
   - 显示较昨日变化
   - 使用 Wallet 图标

3. **持仓保证金**
   - 显示占用保证金金额
   - 显示占总权益百分比
   - 使用 Lock 图标

4. **浮动盈亏**
   - 显示未平仓盈亏
   - 显示盈亏比例
   - 使用 Activity 图标

**第二行：**
5. **仓位使用率**
   - 显示百分比（带进度条）
   - 根据使用率显示颜色（绿/黄/红）
   - 使用 PieChart 图标

6. **VaR 风险值**
   - 显示 95% 置信度下的最大损失
   - 显示风险等级（低/中/高）
   - 使用 AlertTriangle 图标

7. **胜率**
   - 显示盈利交易占比
   - 显示盈利/亏损笔数
   - 使用 Target 图标

8. **盈亏比**
   - 显示平均盈利/平均亏损比值
   - 显示评级（优秀/良好/一般）
   - 使用 TrendingUp 图标

**第三行：**
9. **策略信号数量**
   - 显示当前活跃信号数
   - 显示待处理/已处理数量
   - 使用 Zap 图标

10. **今日交易笔数**
    - 显示开仓/平仓笔数
    - 显示较昨日变化
    - 使用 BarChart3 图标

11. **数据源状态**
    - 显示在线/离线数据源数量
    - 显示健康度百分比
    - 使用 Database 图标

12. **待办事项**
    - 显示未完成任务数量
    - 显示优先级分布
    - 使用 CheckSquare 图标

### 数据结构示例

```typescript
interface KPIData {
  id: string;
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: LucideIcon;
  description?: string;
  progress?: number; // 0-100
  status?: 'success' | 'warning' | 'danger';
}
```

### 组件实现要点
- 使用 CountUp 组件实现数字滚动动画
- 根据 changeType 动态显示颜色（绿色/红色/灰色）
- 进度条使用 shadcn/ui 的 Progress 组件
- 卡片悬停效果（hover:bg-neutral-800）

---

## 第二部分：收益表 + 当前持仓（60% + 40% 布局）

### 左侧：收益表（60%）
- 使用 recharts 绘制雷达图或折线图
- 显示多维度收益指标（日收益、周收益、月收益、年收益、夏普比率、最大回撤）
- 高度 380px
- 支持切换图表类型（雷达图/折线图/柱状图）

**数据结构：**
```typescript
interface ChurnData {
  metric: string;
  value: number;
  fullMark: number;
}
```

### 右侧：当前持仓（40%）
- 显示持仓列表（品种代码、方向、数量、成本价、当前价、盈亏、操作）
- 每行显示一个持仓
- 多头显示绿色标签，空头显示红色标签
- 盈亏金额根据正负显示颜色
- 每行右侧有"平仓"按钮
- 底部显示汇总（总持仓、总浮盈、保证金占用）

**数据结构：**
```typescript
interface PositionData {
  id: string;
  symbol: string;
  direction: 'long' | 'short';
  quantity: number;
  costPrice: number;
  currentPrice: number;
  profitLoss: number;
  profitLossPercent: number;
}
```

---

## 第三部分：今日交易汇总 + 策略信号（50% + 50% 布局）

### 左侧：今日交易汇总（50%）
- 显示 4 个关键指标：
  1. 交易笔数（开仓/平仓）
  2. 买入金额
  3. 卖出金额
  4. 手续费
  5. 已实现盈亏
- 使用卡片网格布局（2×2）
- 高度 320px

### 右侧：策略信号推荐（50%）
- 显示 6 条实时策略信号
- 每条信号包含：
  - 品种代码（如 IF2504）
  - 当前价格
  - 策略名称
  - 置信度（百分比）
  - 信号类型（看多/看空/观望）
  - 操作按钮（禁止/恢复）
- 看多显示绿色标签，看空显示红色标签，观望显示灰色标签
- 禁止的信号显示为半透明
- 底部有"手动开仓"按钮

**数据结构：**
```typescript
interface StrategySignal {
  id: string;
  symbol: string;
  price: number;
  strategyName: string;
  confidence: number;
  signalType: 'bullish' | 'bearish' | 'neutral';
  isDisabled: boolean;
  timestamp: string;
}
```

---

## 第四部分：实时风险指标 + 数据源状态（50% + 50% 布局）

### 左侧：实时风险指标（50%）
- 显示 4 个风险指标：
  1. **保证金使用率**：显示百分比和进度条
  2. **当日回撤**：显示回撤金额和百分比
  3. **杠杆倍数**：显示当前杠杆和风险等级
  4. **集中度风险**：显示最大持仓占比
- 每个指标根据风险水平显示不同颜色：
  - 正常：绿色
  - 警告：黄色
  - 危险：红色
- 使用进度条可视化风险水平

### 右侧：数据源状态监控（50%）
- 显示 6 个数据源的状态：
  1. 新闻 API
  2. 期货 K 线数据
  3. 股票 K 线数据
  4. 财经日历
  5. 实时行情
  6. 基本面数据
- 每个数据源显示：
  - 名称
  - 状态（在线/警告/离线）
  - 数据源数量
  - 最后更新时间
- 在线显示绿色圆点，警告显示黄色圆点，离线显示红色圆点
- 底部有"查看详情"按钮（跳转到数据采集页面）

**数据结构：**
```typescript
interface DataSourceStatus {
  id: string;
  name: string;
  status: 'online' | 'warning' | 'offline';
  sourceCount: number;
  lastUpdate: string;
}
```

---

## 第五部分：新闻模块（60% + 40% 布局）

### 左侧：重大新闻（60%）
- 显示 20 条重大新闻
- 每条新闻包含：
  - 标题
  - 来源
  - 发布时间（格式化为"刚刚"/"X分钟前"/"X小时前"/"X天前"）
  - 重要性标签（高/中/低）
- 高度 440px，可滚动
- 新闻超过 7 天自动清除

### 右侧：全球新闻（40%）
- 显示全球市场新闻
- 布局与重大新闻类似
- 高度 440px，可滚动

**数据结构：**
```typescript
interface NewsItem {
  id: string;
  title: string;
  source: string;
  publishTime: string;
  importance: 'high' | 'medium' | 'low';
  category?: string;
}
```

**时间格式化函数：**
```typescript
function formatTimeAgo(timestamp: string): string {
  const now = new Date();
  const past = new Date(timestamp);
  const diffMs = now.getTime() - past.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  return `${diffDays}天前`;
}
```

---

## 第六部分：交互弹窗

### 1. 信号确认弹窗
- 点击策略信号的"开仓"按钮时弹出
- 显示信号详情（品种、价格、方向、数量、止损、止盈）
- 用户可以修改数量、止损、止盈
- 确认/取消按钮

### 2. 平仓确认弹窗
- 点击持仓的"平仓"按钮时弹出
- 显示持仓详情（品种、方向、数量、成本价、当前价、盈亏）
- 用户可以选择平仓数量（部分平仓/全部平仓）
- 确认/取消按钮

### 3. 禁止信号弹窗
- 点击策略信号的"禁止"按钮时弹出
- 显示禁止原因选择（策略失效/市场环境变化/手动干预/其他）
- 用户可以输入备注
- 确认/取消按钮

### 4. 手动开仓弹窗
- 点击"手动开仓"按钮时弹出
- 用户输入品种代码、方向、数量、价格、止损、止盈
- 确认/取消按钮

**使用 shadcn/ui 的 Dialog 组件实现**

---

## 第七部分：CountUp 动画

所有数字类 KPI 指标使用 CountUp 动画效果，提升视觉体验。

**安装依赖：**
```bash
npm install react-countup
```

**使用示例：**
```typescript
import CountUp from 'react-countup';

<CountUp
  start={0}
  end={12345.67}
  duration={2}
  decimals={2}
  separator=","
  prefix="¥"
/>
```

---

## 第八部分：布局调整

### 整体布局
```
┌─────────────────────────────────────────────────────────┐
│  核心 KPI 指标区（3行×4列）                              │
├─────────────────────────────────────────────────────────┤
│  收益表（60%）          │  当前持仓（40%）               │
├─────────────────────────────────────────────────────────┤
│  今日交易汇总（50%）    │  策略信号（50%）               │
├─────────────────────────────────────────────────────────┤
│  实时风险指标（50%）    │  数据源状态（50%）             │
├─────────────────────────────────────────────────────────┤
│  重大新闻（60%）        │  全球新闻（40%）               │
└─────────────────────────────────────────────────────────┘
```

### 间距规范
- 各部分之间间距：`mb-6`（24px）
- 卡片内边距：`p-6`（24px）
- 网格间距：`gap-4`（16px）

### 响应式断点
- 桌面端（≥1024px）：按上述布局显示
- 平板端（768px-1023px）：部分区域改为单列
- 移动端（<768px）：全部改为单列，KPI 改为 2×6 布局

---

## 第九部分：模拟数据示例

### KPI 数据
```typescript
const mockKPIData: KPIData[] = [
  {
    id: 'profit-today',
    title: '今日盈亏',
    value: 12345.67,
    change: '+8.5%',
    changeType: 'positive',
    icon: TrendingUp,
  },
  {
    id: 'account-equity',
    title: '账户权益',
    value: 1234567.89,
    change: '+2.3%',
    changeType: 'positive',
    icon: Wallet,
  },
  // ... 其他 10 个 KPI
];
```

### 持仓数据
```typescript
const mockPositions: PositionData[] = [
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
  // ... 其他持仓
];
```

### 策略信号数据
```typescript
const mockSignals: StrategySignal[] = [
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
  // ... 其他信号
];
```

---

## 第十部分：技术栈和依赖

### 核心依赖
```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "lucide-react": "latest",
    "recharts": "^2.10.0",
    "react-countup": "^6.5.0",
    "@radix-ui/react-dialog": "latest",
    "@radix-ui/react-progress": "latest",
    "class-variance-authority": "latest",
    "clsx": "latest",
    "tailwind-merge": "latest"
  }
}
```

### 文件结构
```
app/
  page.tsx                          # 首页（总控台）
components/
  dashboard/
    kpi-card.tsx                    # KPI 卡片组件
    churn-radar-chart.tsx           # 收益表雷达图
    current-positions.tsx           # 当前持仓列表
    today-trading-summary.tsx       # 今日交易汇总
    strategy-signals.tsx            # 策略信号推荐
    real-time-risk.tsx              # 实时风险指标
    data-source-status.tsx          # 数据源状态监控
    major-news.tsx                  # 重大新闻列表
    global-news.tsx                 # 全球新闻列表
    signal-confirm-dialog.tsx       # 信号确认弹窗
    close-position-dialog.tsx       # 平仓确认弹窗
    disable-signal-dialog.tsx       # 禁止信号弹窗
    manual-open-dialog.tsx          # 手动开仓弹窗
  layout/
    main-layout.tsx                 # 主布局
    app-sidebar.tsx                 # 侧边栏
    app-header.tsx                  # 顶栏
  ui/
    button.tsx                      # 按钮组件
    card.tsx                        # 卡片组件
    dialog.tsx                      # 弹窗组件
    progress.tsx                    # 进度条组件
    badge.tsx                       # 标签组件
lib/
  utils.ts                          # 工具函数（cn, formatTimeAgo 等）
  mock-data.ts                      # 模拟数据
```

---

## 实现步骤建议

1. **第一步**：实现 12 个核心 KPI 指标区
2. **第二步**：实现收益表 + 当前持仓
3. **第三步**：实现今日交易汇总 + 策略信号
4. **第四步**：实现实时风险指标 + 数据源状态
5. **第五步**：实现新闻模块
6. **第六步**：实现交互弹窗
7. **第七步**：添加 CountUp 动画
8. **第八步**：响应式适配和细节优化

---

## 注意事项

1. **所有数据都是模拟数据**，不需要连接真实 API
2. **保持橙色主题**（orange-500/600）和深色背景（neutral-900/800）
3. **使用 TypeScript**，所有数据结构都要有类型定义
4. **使用 shadcn/ui 组件**，不要自己从零实现基础组件
5. **使用 lucide-react 图标**，保持图标风格统一
6. **实现响应式布局**，支持桌面端、平板端、移动端
7. **添加悬停效果**，提升交互体验
8. **使用 CountUp 动画**，让数字变化更生动
9. **实现完整的交互弹窗**，让用户可以进行操作（虽然是模拟的）
10. **参考 v0 0329 版本的代码**，保持风格一致

---

## 参考文件路径

- v0 0329 版本代码：`参考文件/v0 0329/`
- 当前实现代码：`services/dashboard/dashboard_web/`
- 任务文档：`docs/tasks/TASK-0096-dashboard-统一看板-P0P1阶段.md`

---

## 最终效果

完成后，首页应该是一个功能完整、信息丰富、交互流畅的量化交易总控台，包含：
- 12 个核心 KPI 指标，一目了然
- 收益表可视化，直观展示多维度收益
- 当前持仓列表，实时监控持仓状态
- 今日交易汇总，掌握交易全貌
- 策略信号推荐，辅助决策
- 实时风险指标，防范风险
- 数据源状态监控，保障数据质量
- 新闻模块，及时获取市场信息
- 交互弹窗，支持模拟操作
- CountUp 动画，提升视觉体验

让用户一打开页面，就能快速了解系统的整体状态，做出明智的交易决策。
