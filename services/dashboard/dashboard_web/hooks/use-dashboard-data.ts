"use client"

import { useState, useEffect } from "react"
import { simTradingApi } from "@/lib/api/sim-trading"
import { decisionApi } from "@/lib/api/decision"
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
      simTradingApi.getAccount().then(setAccount),
      simTradingApi.getPerformance().then(setPerformance),
      simTradingApi.getRiskL1().then(setRisk),
      simTradingApi.getPositions().then(setPositions),
      simTradingApi.getOrders().then(setOrders),
      decisionApi.getSignals().then(setSignals),
      dataApi.getCollectors().then(setCollectors),
      dataApi.getNews().then(setNews),
    ])
      .then((results) => {
        const failed = results.filter((r) => r.status === "rejected")
        if (failed.length > 0) {
          setError(`${failed.length} 个数据接口加载失败`)
        }
        setLastUpdate(new Date())
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
