"use client"

import { useState, useEffect } from "react"
import { simTradingApi } from "@/lib/api/sim-trading"
import { decisionApi } from "@/lib/api/decision"
import { dataApi } from "@/lib/api/data"
import { backtestApi } from "@/lib/api/backtest"

export type ServiceName = "sim-trading" | "decision" | "data" | "backtest"
export type ServiceStatus = "ok" | "error" | "loading"

export function useServiceStatus(intervalMs = 30000) {
  const [statuses, setStatuses] = useState<Record<ServiceName, ServiceStatus>>({
    "sim-trading": "loading",
    decision: "loading",
    data: "loading",
    backtest: "loading",
  })

  const checkAll = () => {
    const check = (name: ServiceName, promise: Promise<unknown>) => {
      promise
        .then(() => setStatuses((prev) => ({ ...prev, [name]: "ok" })))
        .catch(() => setStatuses((prev) => ({ ...prev, [name]: "error" })))
    }
    check("sim-trading", simTradingApi.getStatus())
    check("decision", decisionApi.getHealth())
    check("data", dataApi.getHealth())
    check("backtest", backtestApi.getHealth())
  }

  useEffect(() => {
    checkAll()
    const timer = setInterval(checkAll, intervalMs)
    return () => clearInterval(timer)
  }, [intervalMs])

  return statuses
}
