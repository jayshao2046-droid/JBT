"use client"

import { useState, useEffect, useMemo } from "react"
import { RefreshCw, Wifi, WifiOff } from "lucide-react"
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
  const [ticks, setTicks] = useState<Record<string, TickData>>({})
  const [activeTab, setActiveTab] = useState(0)
  const [now, setNow] = useState(() => new Date())
  const [ctpStatus, setCtpStatus] = useState<"disconnected" | "connecting" | "live">("disconnected")

  // 自动连接 CTP + 秒级轮询 /ticks
  useEffect(() => {
    let mounted = true
    let intervalId: ReturnType<typeof setInterval>

    setCtpStatus("connecting")
    fetch("/api/sim/api/v1/ctp/connect", { method: "POST" }).catch(() => {})

    intervalId = setInterval(async () => {
      if (!mounted) return
      try {
        const [ticksRes, statusRes] = await Promise.all([
          fetch("/api/sim/api/v1/ticks"),
          fetch("/api/sim/api/v1/ctp/status"),
        ])

        setNow(new Date())

        if (statusRes.ok) {
          const s = await statusRes.json()
          if (mounted) setCtpStatus(s.md_connected ? "live" : "connecting")
        }

        if (ticksRes.ok) {
          const data = await ticksRes.json()
          const rawTicks: Record<string, any> = data.ticks ?? {}
          if (Object.keys(rawTicks).length > 0 && mounted) {
            setTicks(prev => {
              const next = { ...prev }
              for (const [sym, raw] of Object.entries<any>(rawTicks)) {
                const prevTick = prev[sym]
                const prevClose = raw.prev_close ?? 0
                const last = raw.last ?? 0
                next[sym] = {
                  symbol: sym,
                  last,
                  open: raw.open ?? 0,
                  high: raw.high ?? 0,
                  low: raw.low ?? 0,
                  bid: raw.bid ?? 0,
                  ask: raw.ask ?? 0,
                  change: prevClose > 0 ? last - prevClose : 0,
                  changePct: prevClose > 0 ? ((last - prevClose) / prevClose) * 100 : 0,
                  volume: (raw.volume ?? 0) / 10_000,
                  curVol: 0,
                  turnover: (raw.turnover ?? 0) / 100_000_000,
                  velocity: prevTick
                    ? ((last - prevTick.last) / (prevTick.last || 1)) * 100
                    : 0,
                  prevLast: prevTick?.last ?? last,
                }
              }
              return next
            })
          }
        }
      } catch {
        if (mounted) setCtpStatus("disconnected")
      }
    }, 1000)

    return () => {
      mounted = false
      clearInterval(intervalId)
    }
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
          {/* CTP 连接状态 */}
          {ctpStatus === "live" && (
            <Badge className="bg-green-900/30 text-green-400 border border-green-700/40 text-xs flex items-center gap-1">
              <Wifi className="w-3 h-3" />SimNow 实时
            </Badge>
          )}
          {ctpStatus === "connecting" && (
            <Badge className="bg-amber-900/30 text-amber-400 border border-amber-700/40 text-xs flex items-center gap-1">
              <RefreshCw className="w-3 h-3 animate-spin" />连接中…
            </Badge>
          )}
          {ctpStatus === "disconnected" && (
            <Badge className="bg-neutral-800/60 text-neutral-400 border border-neutral-600 text-xs flex items-center gap-1">
              <WifiOff className="w-3 h-3" />未连接
            </Badge>
          )}
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
              const up = (t?.changePct ?? 0) > 0.005
              const dn = (t?.changePct ?? 0) < -0.005
              // A 股：红涨绿跌
              const priceColor = up ? "text-red-400" : dn ? "text-green-400" : "text-neutral-300"
              const flash = t ? t.last !== t.prevLast : false
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
                    {t ? fmtPrice(t.last, c.tick) : "--"}
                  </td>
                  {/* 涨幅 */}
                  <td className={`px-2 py-1.5 text-right font-mono tabular-nums ${priceColor}`}>
                    {t ? pct(t.changePct) : "--"}
                  </td>
                  {/* 涨跌 */}
                  <td className={`px-2 py-1.5 text-right font-mono tabular-nums ${priceColor}`}>
                    {t ? <>{t.change >= 0 ? "+" : ""}{fmtPrice(t.change, c.tick)}</> : "--"}
                  </td>
                  {/* 成交量 */}
                  <td className="px-2 py-1.5 text-right font-mono text-neutral-300 tabular-nums">
                    {t ? fmtVol(t.volume) : "--"}
                  </td>
                  {/* 现量 */}
                  <td className="px-2 py-1.5 text-right font-mono text-neutral-400 tabular-nums">
                    {t ? `${t.curVol}手` : "--"}
                  </td>
                  {/* 买一价 — 绿色（买方出价，价格低） */}
                  <td className="px-2 py-1.5 text-right font-mono text-green-400 tabular-nums">
                    {t ? fmtPrice(t.bid, c.tick) : <span className="text-neutral-600">--</span>}
                  </td>
                  {/* 卖一价 — 红色（卖方挂单，价格高） */}
                  <td className="px-2 py-1.5 text-right font-mono text-red-400 tabular-nums">
                    {t ? fmtPrice(t.ask, c.tick) : <span className="text-neutral-600">--</span>}
                  </td>
                  {/* 涨速 */}
                  <td className={`px-2 py-1.5 text-right font-mono tabular-nums ${
                    (t?.velocity ?? 0) > 0 ? "text-red-400" : (t?.velocity ?? 0) < 0 ? "text-green-400" : "text-neutral-500"
                  }`}>
                    {t ? `${t.velocity > 0 ? "+" : ""}${t.velocity.toFixed(3)}%` : "--"}
                  </td>
                  {/* 成交额 */}
                  <td className="px-2 py-1.5 text-right font-mono text-neutral-400 tabular-nums">
                    {t ? fmtTurnover(t.turnover) : "--"}
                  </td>
                  {/* 交易所 */}
                  <td className="px-2 py-1.5 text-neutral-500">{c.exchange}</td>
                  {/* 行业 */}
                  <td className="px-2 py-1.5 text-neutral-500">{c.sector}</td>
                  {/* 最高 — 红 */}
                  <td className="px-2 py-1.5 text-right font-mono text-red-400/80 tabular-nums">
                    {t ? fmtPrice(t.high, c.tick) : "--"}
                  </td>
                  {/* 最低 — 绿 */}
                  <td className="px-2 py-1.5 text-right font-mono text-green-400/80 tabular-nums">
                    {t ? fmtPrice(t.low, c.tick) : "--"}
                  </td>
                  {/* 开盘 */}
                  <td className="px-2 py-1.5 text-right font-mono text-neutral-500 tabular-nums">
                    {t ? fmtPrice(t.open, c.tick) : "--"}
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
        {ctpStatus === "live"
          ? <span className="text-green-400">● SimNow 实时行情</span>
          : ctpStatus === "connecting"
          ? <span className="text-amber-400">⟳ 等待 CTP 连接…</span>
          : <span className="text-neutral-500">● CTP 未连接</span>
        }
        <span className="ml-auto font-mono tabular-nums">
          {now.toLocaleTimeString("zh-CN")}
        </span>
      </div>
    </div>
  )
}
