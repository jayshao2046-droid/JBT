// Decision API 客户端
const API_BASE = process.env.NEXT_PUBLIC_DECISION_API_URL || "http://localhost:8003"

export const decisionApi = {
  // 决策历史
  async decisionHistory(startDate?: string, endDate?: string, limit: number = 100) {
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    params.append("limit", limit.toString())

    const response = await fetch(`${API_BASE}/api/v1/decision/history?${params}`)
    if (!response.ok) throw new Error("Failed to fetch decision history")
    return response.json()
  },

  // 参数验证
  async validateParams(data: { strategy_id: string; params: Record<string, any>; schema?: any }) {
    const response = await fetch(`${API_BASE}/api/v1/decision/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error("Failed to validate params")
    return response.json()
  },

  // 绩效 KPI
  async performanceKPI(decisionId: string) {
    const response = await fetch(`${API_BASE}/api/v1/decision/${decisionId}/performance`)
    if (!response.ok) throw new Error("Failed to fetch performance KPI")
    return response.json()
  },

  // 质量 KPI
  async qualityKPI(decisionId: string) {
    const response = await fetch(`${API_BASE}/api/v1/decision/${decisionId}/quality`)
    if (!response.ok) throw new Error("Failed to fetch quality KPI")
    return response.json()
  },

  // 批量决策
  async batchDecision(data: {
    strategy_id: string
    param_grid: Record<string, any[]>
    base_params?: Record<string, any>
  }) {
    const response = await fetch(`${API_BASE}/api/v1/decision/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error("Failed to create batch decision")
    return response.json()
  },
}
