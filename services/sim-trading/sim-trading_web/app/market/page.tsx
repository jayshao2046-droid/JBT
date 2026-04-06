"use client"

import { useState, useEffect, useRef, useMemo, useCallback } from "react"
import { RefreshCw, TrendingUp, TrendingDown, Wifi, WifiOff } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { ALL_CONTRACTS, WATCHLISTS, FuturesContract, fmtPrice } from "@/lib/contracts"

// ─── 数据类型 ────────────────────────────────────────────────────────────────

interface TickData {
  symbol: string
  last: number
  open: number
  high: number
  low: number
  bid: number
  ask: number
  change: number      // 涨跌绝对值
  changePct: number   // 涨幅%
  volume: number      // 累计成交量（万手）
  curVol: number      // 现量（手/tick）
  turnover: number    // 成交额（亿元）
  velocity: number    // 涨速（%/s）
  prevLast: number    // 上一 tick，用于闪烁
}

// ─── 初始化模拟行情 ───────────────────────────────────────────────────────────

function buildInitialTicks(): Record<string, TickData> {
  const map: Record<string, TickData> = {}
  for (const c of ALL_CONTRACTS) {
    // 开盘价在基准价 ±0.3% 随机浮动
    const open = c.basePrice * (1 + (Math.random() - 0.5) * 0.006)
    const last = open
    const volBase = Math.random() * 50 + 10
    map[c.symbol] = {
      symbol: c.symbol,
      last,
      open: c.basePrice,
      high: last * (1 + Math.random() * 0.003),
      low: last * (1 - Math.random() * 0.003),
      bid: last - c.tick,
      ask: last + c.tick,
      change: last - c.basePrice,
      changePct: ((last - c.basePrice) / c.basePrice) * 100,
      volume: volBase,
      curVol: Math.floor(Math.random() * 200 + 5),
      turnover: (volBase * c.basePrice * 10) / 100_000_000,
      velocity: 0,
      prevLast: last,
    }
  }
  return map
}

// ─── 行情模拟引擎（每秒更新）────────────────────────────────────────────────

function simulateTick(
  prev: Record<string, TickData>,
  contracts: FuturesContract[],
): Record<string, TickData> {
  const next = { ...prev }
  for (const c of contracts) {
    const t = prev[c.symbol]
    if (!t) continue

    // 随机游走：偏向均值回归
    const revert = (c.basePrice - t.last) / c.basePrice   // 均值回归力
    const rand = (Math.random() - 0.49 + revert * 0.3) * c.tick * 3
    const newLast = Math.max(
      t.last + rand,
      c.basePrice * 0.85, // 最低不跌过基准 15%
    )
    const snapped = Math.round(newLast / c.tick) * c.tick
    const curVol = Math.floor(Math.random() * 600 + 1)
    next[c.symbol] = {
      ...t,
      last: snapped,
      prevLast: t.last,
      high: Math.max(t.high, snapped),
      low: Math.min(t.low, snapped),
      bid: snapped - c.tick,
      ask: snapped + c.tick,
      change: snapped - t.open,
      changePct: ((snapped - t.open) / t.open) * 100,
      curVol,
      volume: t.volume + curVol / 10_000,
      turnover: t.turnover + (curVol * snapped) / 100_000_000,
      velocity: ((snapped - t.last) / t.last) * 100,
    }
  }
  return next
}

// ─── 工具 ────────────────────────────────────────────────────────────────────

const contractMap = Object.fromEntries(ALL_CONTRACTS.map(c => [c.symbol, c]))

function pct(v: number) {
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`
}
function fmtVol(v: number) {
  if (v >= 10000) return `${(v / 10000).toFixed(1)}亿手`
  if (v >= 1) return `${v.toFixed(1)}万手`
  return `${(v * 10000).toFixed(0)}手`
}
function fmtTurnover(v: number) {
  if (v >= 10000) return `${(v / 10000).toFixed(1)}万亿`
  if (v >= 1) return `${v.toFixed(1)}亿`
  return `${(v * 10000).toFixed(0)}万`
}

// ─── 主组件 ──────────────────────────────────────────────────────────────────

export default function MarketPage() {
  const [ticks, setTicks] = useState<Record<string, TickData>>(() => buildInitialTicks())
  const [activeTab, setActiveTab] = useState(0)
  const [now, setNow] = useState(() => new Date())
  const [paused, setPaused] = useState(false)
  const pausedRef = useRef(paused)
  pausedRef.current = paused

  // 秒级更新行情
  useEffect(() => {
    const id = setInterval(() => {
      if (!pausedRef.current) {
        setTicks(prev => simulateTick(prev, ALL_CONTRACTS))
      }
      setNow(new Date())
    }, 1000)
    return () => clearInterval(id)
  }, [])

  const watchlist = WATCHLISTS[activeTab]
  const contracts = useMemo(
    () => ALL_CONTRACTS.filter(c => watchlist.symbols.includes(c.symbol)),
    [watchlist],
  )

  // 统计区：涨/跌/平
  const stats = useMemo(() => {
    let up = 0, dn = 0, flat = 0
    for (const c of contracts) {
      const pctVal = ticks[c.symbol]?.changePct ?? 0
      if (pctVal > 0.005) up++
      else if (pctVal < -0.005) dn++
      else flat++
    }
    return { up, dn, flat }
  }, [contracts, ticks])

  return (
    <div className="flex flex-col h-full bg-neutral-950 select-none">

      {/* ── 自选标签栏 ── */}
      <div className="flex items-center gap-1 px-4 py-2.5 border-b border-neutral-700 bg-neutral-900 shrink-0">
        {WATCHLISTS.map((wl, idx) => (
          <button
            key={wl.id}
            onClick={() => setActiveTab(idx)}
            className={`px-3.5 py-1 text-xs rounded font-medium transition-colors ${
              activeTab === idx
                ? "bg-orange-500 text-white"
                : "text-neutral-400 hover:text-white hover:bg-neutral-700"
            }`}
          >
            自选{idx + 1} · {wl.name}
            <span className="ml-1 opacity-60">({wl.symbols.length})</span>
          </button>
        ))}

        {/* 右侧状态 */}
        <div className="ml-auto flex items-center gap-3 text-xs text-neutral-500">
          {/* 涨跌统计 */}
          <span>
            <span className="text-red-400 font-mono">{stats.up}↑</span>
            <span className="mx-1 text-neutral-600">/</span>
            <span className="text-neutral-400 font-mono">{stats.flat}→</span>
            <span className="mx-1 text-neutral-600">/</span>
            <span className="text-green-400 font-mono">{stats.dn}↓</span>
          </span>
          {/* 骨架阶段标记 */}
          <Badge className="bg-amber-900/30 text-amber-400 border border-amber-700/40 text-xs">
            骨架 · 模拟行情
          </Badge>
          {/* 暂停/恢复 */}
          <button
            onClick={() => setPaused(p => !p)}
            className="flex items-center gap-1 text-neutral-500 hover:text-white transition-colors"
          >
            {paused ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {paused ? "恢复" : "暂停"}
          </button>
          {/* 时间 */}
          <span className="font-mono text-neutral-600 tabular-nums">
            {now.toLocaleTimeString("zh-CN")}
          </span>
        </div>
      </div>

      {/* ── 表格 ── */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-xs border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="bg-neutral-800 text-neutral-500 border-b border-neutral-700">
              <th className="px-2 py-2 text-left font-normal w-8">序</th>
              <th className="px-2 py-2 text-left font-normal w-20">代码</th>
              <th className="px-2 py-2 text-left font-normal min-w-[120px]">名称</th>
              <th className="px-2 py-2 text-right font-normal w-20">最新</th>
              <th className="px-2 py-2 text-right font-normal w-16">涨幅</th>
              <th className="px-2 py-2 text-right font-normal w-16">涨跌</th>
              <th className="px-2 py-2 text-right font-normal w-20">成交量</th>
              <th className="px-2 py-2 text-right font-normal w-16">现量</th>
              <th className="px-2 py-2 text-right font-normal w-20">买一价</th>
              <th className="px-2 py-2 text-right font-normal w-20">卖一价</th>
              <th className="px-2 py-2 text-right font-normal w-16">涨速</th>
              <th className="px-2 py-2 text-right font-normal w-20">成交额</th>
              <th className="px-2 py-2 text-left font-normal w-20">交易所</th>
              <th className="px-2 py-2 text-left font-normal w-24">所属行业</th>
              <th className="px-2 py-2 text-right font-normal w-20">最高</th>
              <th className="px-2 py-2 text-right font-normal w-20">最低</th>
              <th className="px-2 py-2 text-right font-normal w-20">开盘</th>
            </tr>
          </thead>
          <tbody>
            {contracts.map((c, idx) => {
              const t = ticks[c.symbol]
              if (!t) return null
              const up = t.changePct > 0.005
              const dn = t.changePct < -0.005
              // A 股：红涨绿跌
              const priceColor = up ? "text-red-400" : dn ? "text-green-400" : "text-neutral-300"
              const flash = t.last !== t.prevLast
              return (
                <tr
                  key={c.symbol}
                  className={`border-b border-neutral-800/40 hover:bg-neutral-800/20 transition-colors ${
                    flash ? "animate-[pulse_0.3s_ease-in-out]" : ""
                  }`}
                >
                  <td className="px-2 py-1.5 text-neutral-600">{idx + 1}</td>
                  <td className="px-2 py-1.5 font-mono text-orange-400">{c.symbol}</td>
                  <td className="px-2 py-1.5 text-neutral-200">{c.name}</td>
                  {/* 最新 */}
                  <td className={`px-2 py-1.5 text-right font-mono font-medium tabular-nums ${priceColor}`}>
                    {fmtPrice(t.last, c.tick)}
                  </td>
                  {/* 涨幅 */}
                  <td className={`px-2 py-1.5 text-right font-mono tabular-nums ${priceColor}`}>
                    {pct(t.changePct)}
                  </td>
                  {/* 涨跌 */}
                  <td className={`px-2 py-1.5 text-right font-mono tabular-nums ${priceColor}`}>
                    {t.change >= 0 ? "+" : ""}{fmtPrice(t.change, c.tick)}
                  </td>
                  {/* 成交量 */}
                  <td className="px-2 py-1.5 text-right font-mono text-neutral-300 tabular-nums">
                    {fmtVol(t.volume)}
                  </td>
                  {/* 现量 */}
                  <td className="px-2 py-1.5 text-right font-mono text-neutral-400 tabular-nums">
                    {t.curVol}手
                  </td>
                  {/* 买一价 — 绿色（买方出价，价格低） */}
                  <td className="px-2 py-1.5 text-right font-mono text-green-400 tabular-nums">
                    {fmtPrice(t.bid, c.tick)}
                  </td>
                  {/* 卖一价 — 红色（卖方挂单，价格高） */}
                  <td className="px-2 py-1.5 text-right font-mono text-red-400 tabular-nums">
                    {fmtPrice(t.ask, c.tick)}
                  </td>
                  {/* 涨速 */}
                  <td className={`px-2 py-1.5 text-right font-mono tabular-nums ${
                    t.velocity > 0 ? "text-red-400" : t.velocity < 0 ? "text-green-400" : "text-neutral-500"
                  }`}>
                    {t.velocity > 0 ? "+" : ""}{t.velocity.toFixed(3)}%
                  </td>
                  {/* 成交额 */}
                  <td className="px-2 py-1.5 text-right font-mono text-neutral-400 tabular-nums">
                    {fmtTurnover(t.turnover)}
                  </td>
                  {/* 交易所 */}
                  <td className="px-2 py-1.5 text-neutral-500">{c.exchange}</td>
                  {/* 行业 */}
                  <td className="px-2 py-1.5 text-neutral-500">{c.sector}</td>
                  {/* 最高 — 红 */}
                  <td className="px-2 py-1.5 text-right font-mono text-red-400/80 tabular-nums">
                    {fmtPrice(t.high, c.tick)}
                  </td>
                  {/* 最低 — 绿 */}
                  <td className="px-2 py-1.5 text-right font-mono text-green-400/80 tabular-nums">
                    {fmtPrice(t.low, c.tick)}
                  </td>
                  {/* 开盘 */}
                  <td className="px-2 py-1.5 text-right font-mono text-neutral-500 tabular-nums">
                    {fmtPrice(t.open, c.tick)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* ── 底部状态栏 ── */}
      <div className="shrink-0 px-4 py-1.5 bg-neutral-900 border-t border-neutral-700 flex items-center gap-4 text-xs text-neutral-600">
        <span>共 {contracts.length} 个品种</span>
        <span className="text-neutral-700">·</span>
        <span>CTP 接入前使用模拟行情 · 连接 CTP 后自动切换实时数据</span>
        <span className="ml-auto">
          {paused
            ? <span className="text-amber-400">⏸ 已暂停更新</span>
            : <span className="text-green-400">● 秒级更新中</span>
          }
        </span>
      </div>
    </div>
  )
}
