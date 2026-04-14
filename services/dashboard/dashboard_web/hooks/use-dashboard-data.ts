"use client"

import { useState, useEffect } from "react"
import { simTradingApi } from "@/lib/api/sim-trading"
import { fetchSignals } from "@/lib/api/decision"
import { dataApi } from "@/lib/api/data"
import type {
  AccountInfo,
  PerformanceStats,
  RiskL1,
  Position,
  StrategySignal,
  CollectorStatus,
  NewsItem,
  Order,
} from "@/lib/api/types"

export function useDashboardData() {
  const [account, setAccount] = useState<AccountInfo | null>(null)
  const [performance, setPerformance] = useState<PerformanceStats | null>(null)
  const [risk, setRisk] = useState<RiskL1 | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [signals, setSignals] = useState<StrategySignal[]>([])
  const [collectors, setCollectors] = useState<CollectorStatus[]>([])
  const [news, setNews] = useState<NewsItem[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchData = () => {
    setLoading(true)
    setError(null)
    Promise.allSettled([
      simTradingApi.getAccount().then(setAccount).catch(() => setAccount(null)),
      simTradingApi.getPerformance().then(setPerformance).catch(() => setPerformance(null)),
      simTradingApi.getRiskL1().then(setRisk).catch(() => setRisk(null)),
      simTradingApi.getPositions().then(setPositions).catch(() => setPositions([])),
      simTradingApi.getOrders().then(setOrders).catch(() => setOrders([])),
      fetchSignals().then((data) => {
        const adapted = data.map((s, idx) => ({
          id: s.decision_id,
          strategy_name: s.strategy_id,
          instrument_id: s.symbol || s.strategy_id,
          direction: (s.action === "long" ? "long" : "short") as "long" | "short",
          confidence: s.confidence,
          status: "pending" as const,
          timestamp: s.generated_at,
        }))
        setSignals(adapted)
      }).catch(() => setSignals([])),
      dataApi.getCollectors().then(setCollectors).catch(() => setCollectors([])),
      dataApi.getNews().then(setNews).catch(() => setNews([])),
    ])
      .then((results) => {
        const failed = results.filter((r) => r.status === "rejected")
        if (failed.length > 0) {
          console.error('Failed requests:', results.filter((r) => r.status === "rejected"))
          setError(`${failed.length} 个数据接口加载失败`)
        }
        setLastUpdate(new Date())
      })
      .catch((err) => {
        console.error('Fetch data error:', err)
        setError('数据加载失败')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  return {
    account,
    performance,
    risk,
    positions,
    signals,
    collectors,
    news,
    orders,
    loading,
    error,
    lastUpdate,
    refetch: fetchData
  }
}
