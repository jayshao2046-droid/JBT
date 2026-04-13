'use client'

import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, PanelLeftClose, PanelLeft } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useOrbit } from './orbit-provider'
import type { ViewType } from './command-dock'

// ─── 静态数据 ──────────────────────────────────────────────────────────────────

interface FuturesPosition {
  type: 'futures'
  code: string
  name: string
  direction: '多' | '空'
  lots: number
  entryPrice: number
  currentPrice: number
  pnl: number          // 正=盈利 负=亏损
  pnlPct: number
}

interface StockPosition {
  type: 'stock'
  code: string
  name: string
  direction: '多' | '空'
  lots: number
  entryPrice: number
  currentPrice: number
  pnl: number
  pnlPct: number
}

type Position = FuturesPosition | StockPosition

const futuresPositions: FuturesPosition[] = [
  { type: 'futures', code: 'rb2405', name: '螺纹钢', direction: '多', lots: 10, entryPrice: 3850, currentPrice: 3920, pnl: 7000, pnlPct: 1.82 },
  { type: 'futures', code: 'hc2405', name: '热卷', direction: '多', lots: 8, entryPrice: 3920, currentPrice: 3985, pnl: 5200, pnlPct: 1.66 },
  { type: 'futures', code: 'i2405', name: '铁矿石', direction: '空', lots: 5, entryPrice: 890, currentPrice: 912, pnl: -1100, pnlPct: -2.47 },
  { type: 'futures', code: 'm2405', name: '豆粕', direction: '多', lots: 12, entryPrice: 3150, currentPrice: 3210, pnl: 7200, pnlPct: 1.90 },
  { type: 'futures', code: 'y2405', name: '豆油', direction: '空', lots: 6, entryPrice: 7850, currentPrice: 7920, pnl: -2520, pnlPct: -0.89 },
]

const stockPositions: StockPosition[] = [
  { type: 'stock', code: '600519', name: '贵州茅台', direction: '多', lots: 100, entryPrice: 1680, currentPrice: 1752, pnl: 7200, pnlPct: 4.29 },
  { type: 'stock', code: '000858', name: '五粮液', direction: '多', lots: 200, entryPrice: 142, currentPrice: 148, pnl: 1200, pnlPct: 4.23 },
  { type: 'stock', code: '601318', name: '中国平安', direction: '空', lots: 500, entryPrice: 48, currentPrice: 49.8, pnl: -900, pnlPct: -3.75 },
  { type: 'stock', code: '600036', name: '招商银行', direction: '多', lots: 300, entryPrice: 36.5, currentPrice: 37.8, pnl: 3900, pnlPct: 3.56 },
  { type: 'stock', code: '000333', name: '美的集团', direction: '空', lots: 200, entryPrice: 62, currentPrice: 63.5, pnl: -3000, pnlPct: -2.42 },
  { type: 'stock', code: '601888', name: '中国中免', direction: '多', lots: 150, entryPrice: 68, currentPrice: 72, pnl: 6000, pnlPct: 5.88 },
  { type: 'stock', code: '600276', name: '恒瑞医药', direction: '空', lots: 400, entryPrice: 42, currentPrice: 43.2, pnl: -4800, pnlPct: -2.86 },
  { type: 'stock', code: '002415', name: '海康威视', direction: '多', lots: 300, entryPrice: 29.5, currentPrice: 31.2, pnl: 5100, pnlPct: 5.76 },
  { type: 'stock', code: '600900', name: '长江电力', direction: '空', lots: 500, entryPrice: 22.8, currentPrice: 23.5, pnl: -3500, pnlPct: -3.07 },
  { type: 'stock', code: '600585', name: '海螺水泥', direction: '多', lots: 200, entryPrice: 24.5, currentPrice: 25.8, pnl: 2600, pnlPct: 5.31 },
  { type: 'stock', code: '000651', name: '格力电器', direction: '空', lots: 300, entryPrice: 38, currentPrice: 39.1, pnl: -3300, pnlPct: -2.89 },
  { type: 'stock', code: '601166', name: '兴业银行', direction: '多', lots: 500, entryPrice: 18.2, currentPrice: 19.0, pnl: 4000, pnlPct: 4.40 },
  { type: 'stock', code: '600030', name: '中信证券', direction: '空', lots: 400, entryPrice: 21.5, currentPrice: 22.3, pnl: -3200, pnlPct: -3.72 },
  { type: 'stock', code: '000568', name: '泸州老窖', direction: '多', lots: 100, entryPrice: 145, currentPrice: 152, pnl: 7000, pnlPct: 4.83 },
  { type: 'stock', code: '600809', name: '山西汾酒', direction: '多', lots: 100, entryPrice: 195, currentPrice: 204, pnl: 9000, pnlPct: 4.62 },
]

type SortOption = 'pnl' | 'profit' | 'loss'

const sortLabels: Record<SortOption, string> = {
  pnl: '收益',
  profit: '盈利',
  loss: '亏损',
}

// ─── 单行持仓组件 ──────────────────────────────────────────────────────────────

function PositionRow({
  position,
  isSelected,
  onClick,
}: {
  position: Position
  isSelected: boolean
  onClick: () => void
}) {
  const isProfitable = position.pnl > 0
  const profitColor = isProfitable ? '#FF3B30' : '#3FB950'

  return (
    <motion.button
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -8 }}
      transition={{ duration: 0.1 }}
      onClick={onClick}
      className={cn(
        'w-full px-4 py-2.5 text-left transition-all duration-100 relative group',
        isSelected ? 'bg-primary/5' : 'hover:bg-secondary/30'
      )}
    >
      {isSelected && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-8 bg-primary rounded-r-full" />
      )}

      <div className="flex items-start gap-2.5">
        {/* 状态圆点 */}
        <div className="mt-[5px] shrink-0">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: profitColor }}
          />
        </div>

        {/* 持仓信息 */}
        <div className="flex-1 min-w-0">
          {/* 第一行：代码+名称 / 盈亏金额+标签 */}
          <div className="flex items-center justify-between gap-2">
            <span className="text-[12px] font-medium text-foreground">
              {position.code}{' '}
              <span className="text-muted-foreground/70" suppressHydrationWarning>{position.name}</span>
            </span>
            <div className="flex items-center gap-1.5 shrink-0">
              <span
                className="text-[11px] font-mono font-medium"
                style={{ color: profitColor }}
              >
                {isProfitable ? '+' : ''}
                {position.pnl >= 0
                  ? `¥${position.pnl.toLocaleString()}`
                  : `-¥${Math.abs(position.pnl).toLocaleString()}`}
              </span>
              <span
                className="px-1.5 py-0.5 text-[9px] font-medium rounded"
                style={{
                  color: profitColor,
                  backgroundColor: `${profitColor}18`,
                }}
              >
                {isProfitable ? '盈利' : '亏损'}
              </span>
            </div>
          </div>

          {/* 第二行：方向(仅期货)+手数+开仓价+当前价 */}
          <div className="mt-0.5 text-[10px] text-muted-foreground/55 flex items-center gap-2">
            {position.type === 'futures' && (
              <span
                className={cn(
                  'font-medium',
                  position.direction === '多' ? 'text-[#FF3B30]' : 'text-[#3FB950]'
                )}
              >
                {position.direction}
              </span>
            )}
            <span>{position.lots} 手</span>
            <span>开仓@{position.entryPrice}</span>
            <span>当前@{position.currentPrice}</span>
          </div>
        </div>
      </div>
    </motion.button>
  )
}

// ─── 主组件 ───────────────────────────────────────────────────────────────────

interface AccountListProps {
  selectedAccountId: string | null
  onSelectAccount: (account: { id: string; name: string }) => void
  onNewAccount: () => void
  onViewChange?: (view: ViewType) => void
}

export function AccountList({
  selectedAccountId,
  onSelectAccount,
  onNewAccount,
  onViewChange,
}: AccountListProps) {
  const { sidebarCollapsed, setSidebarCollapsed } = useOrbit()
  const [sortBy, setSortBy] = useState<SortOption>('pnl')
  const [showSortMenu, setShowSortMenu] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const sortedFutures = useMemo(() => {
    const list = [...futuresPositions]
    if (sortBy === 'profit') return list.filter((p) => p.pnl > 0).sort((a, b) => b.pnl - a.pnl)
    if (sortBy === 'loss') return list.filter((p) => p.pnl < 0).sort((a, b) => a.pnl - b.pnl)
    return list.sort((a, b) => b.pnl - a.pnl)
  }, [sortBy])

  const sortedStocks = useMemo(() => {
    const list = [...stockPositions]
    if (sortBy === 'profit') return list.filter((p) => p.pnl > 0).sort((a, b) => b.pnl - a.pnl)
    if (sortBy === 'loss') return list.filter((p) => p.pnl < 0).sort((a, b) => a.pnl - b.pnl)
    return list.sort((a, b) => b.pnl - a.pnl)
  }, [sortBy])

  const futuresPnlTotal = futuresPositions.reduce((sum, p) => sum + p.pnl, 0)
  const stocksPnlTotal = stockPositions.reduce((sum, p) => sum + p.pnl, 0)

  const handlePositionClick = (position: Position) => {
    const id = `${position.type}-${position.code}`
    setSelectedId(id)
    onSelectAccount({ id, name: `${position.code} ${position.name}` })
    if (onViewChange) {
      if (position.type === 'futures') {
        onViewChange('futures-detail')
      } else {
        onViewChange('stock-detail')
      }
    }
  }

  // ── 折叠态 ─────────────────────────────────────────────────────────────────
  if (sidebarCollapsed) {
    return (
      <motion.div
        initial={{ width: 280 }}
        animate={{ width: 96 }}
        transition={{ duration: 0.15, ease: 'easeOut' }}
        className="h-full flex flex-col bg-card/50"
      >
        <div className="p-2.5 flex justify-center">
          <button
            onClick={() => setSidebarCollapsed(false)}
            className="w-9 h-9 flex items-center justify-center rounded-md hover:bg-secondary/60 transition-colors"
            title="展开侧边栏"
          >
            <PanelLeft className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-1 space-y-0.5 px-1.5">
          {[...futuresPositions, ...stockPositions].map((p) => (
            <button
              key={`${p.type}-${p.code}`}
              onClick={() => handlePositionClick(p)}
              className="w-full flex items-center gap-1.5 px-1.5 py-1 rounded hover:bg-secondary/40 transition-colors"
              title={`${p.code} ${p.name}`}
            >
              <div
                className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: p.pnl > 0 ? '#FF3B30' : '#3FB950' }}
              />
              <span
                className="text-[13px] text-muted-foreground/70 whitespace-nowrap"
                suppressHydrationWarning
              >
                {p.name}
              </span>
            </button>
          ))}
        </div>
      </motion.div>
    )
  }

  // ── 展开态 ─────────────────────────────────────────────────────────────────
  return (
    <motion.div
      initial={{ width: 56 }}
      animate={{ width: 280 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      className="h-full flex flex-col bg-card/50"
    >
      {/* Header */}
      <div className="px-4 pt-4 pb-2 space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-[13px] font-semibold text-foreground tracking-tight" suppressHydrationWarning>
            持仓列表
          </h2>
          <button
            onClick={() => setSidebarCollapsed(true)}
            className="p-1 rounded-md hover:bg-secondary/60 transition-colors"
            title="收起侧边栏"
          >
            <PanelLeftClose className="w-4 h-4 text-muted-foreground/70" />
          </button>
        </div>

        {/* 排序 */}
        <div className="flex items-center">
          <div className="relative">
            <button
              onClick={() => setShowSortMenu(!showSortMenu)}
              className="flex items-center gap-1 text-[11px] text-muted-foreground/70 hover:text-muted-foreground transition-colors"
            >
              <span suppressHydrationWarning>排序：</span>
              <span className="text-foreground/80 font-medium" suppressHydrationWarning>
                {sortLabels[sortBy]}
              </span>
              <ChevronDown className="w-3 h-3" />
            </button>

            <AnimatePresence>
              {showSortMenu && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowSortMenu(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.1 }}
                    className="absolute top-full left-0 mt-1 py-1 bg-popover border border-border/50 rounded-md shadow-lg z-20 min-w-[80px]"
                  >
                    {(Object.keys(sortLabels) as SortOption[]).map((option) => (
                      <button
                        key={option}
                        onClick={() => {
                          setSortBy(option)
                          setShowSortMenu(false)
                        }}
                        className={cn(
                          'w-full px-3 py-1.5 text-left text-[11px] transition-colors',
                          sortBy === option
                            ? 'bg-primary/8 text-primary'
                            : 'text-foreground hover:bg-secondary/50'
                        )}
                        suppressHydrationWarning
                      >
                        {sortLabels[option]}
                      </button>
                    ))}
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* List — scrollable */}
      <div className="flex-1 overflow-y-auto [&::-webkit-scrollbar]:w-[3px] [&::-webkit-scrollbar-track]:transparent [&::-webkit-scrollbar-thumb]:bg-border/50 [&::-webkit-scrollbar-thumb]:rounded-full">
        <AnimatePresence mode="popLayout">
          {/* 期货持仓 */}
          {sortedFutures.map((p) => (
            <PositionRow
              key={`futures-${p.code}`}
              position={p}
              isSelected={selectedId === `futures-${p.code}`}
              onClick={() => handlePositionClick(p)}
            />
          ))}
        </AnimatePresence>

        {/* 分割线 */}
        <div className="mx-4 my-1.5 border-t border-border/40 flex items-center gap-2">
          <span className="text-[9px] text-muted-foreground/40 whitespace-nowrap py-0.5" suppressHydrationWarning>
            股票追踪
          </span>
        </div>

        <AnimatePresence mode="popLayout">
          {/* 股票持仓 */}
          {sortedStocks.map((p) => (
            <PositionRow
              key={`stock-${p.code}`}
              position={p}
              isSelected={selectedId === `stock-${p.code}`}
              onClick={() => handlePositionClick(p)}
            />
          ))}
        </AnimatePresence>

        {sortedFutures.length === 0 && sortedStocks.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-muted-foreground/60 text-[12px]" suppressHydrationWarning>
              没有符合条件的持仓
            </p>
          </div>
        )}
      </div>

      {/* Footer stats */}
      <div className="px-4 py-2.5 border-t border-border/40 space-y-1.5">
        {/* 期货持仓行 */}
        <div className="flex items-center justify-between text-[11px]">
          <span className="font-bold text-foreground/80" suppressHydrationWarning>
            持仓数量：{sortedFutures.length}
          </span>
          <span
            className="font-mono font-bold"
            style={{ color: futuresPnlTotal >= 0 ? '#FF3B30' : '#3FB950' }}
          >
            {futuresPnlTotal >= 0 ? '+' : ''}
            {futuresPnlTotal >= 0
              ? `¥${futuresPnlTotal.toLocaleString()}`
              : `-¥${Math.abs(futuresPnlTotal).toLocaleString()}`}
          </span>
        </div>
        {/* 股票追踪行 */}
        <div className="flex items-center justify-between text-[11px]">
          <span className="font-bold text-foreground/80" suppressHydrationWarning>
            股票追踪：{sortedStocks.length}
          </span>
          <span
            className="font-mono font-bold"
            style={{ color: stocksPnlTotal >= 0 ? '#FF3B30' : '#3FB950' }}
          >
            {stocksPnlTotal >= 0 ? '+' : ''}
            {stocksPnlTotal >= 0
              ? `¥${stocksPnlTotal.toLocaleString()}`
              : `-¥${Math.abs(stocksPnlTotal).toLocaleString()}`}
          </span>
        </div>
      </div>
    </motion.div>
  )
}
