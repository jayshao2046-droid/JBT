// 浏览器端使用相对路径（Next.js rewrites 代理到后端），服务端使用可配置绝对地址
const SERVER_BASE = process.env.BACKEND_BASE_URL || 'http://localhost:8004'
const BASE = typeof window !== 'undefined' ? '' : SERVER_BASE
const DEFAULT_TIMEOUT = 5000

async function fetchWithTimeout(input: RequestInfo, init: RequestInit = {}, timeout = DEFAULT_TIMEOUT) {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  try {
    const res = await fetch(input, { signal: controller.signal, ...init })
    clearTimeout(id)
    if (!res.ok) {
      let detail = ''
      try {
        const ct = (res.headers.get('content-type') || '').toLowerCase()
        if (ct.includes('application/json')) {
          const j = await res.clone().json()
          detail = String(j?.detail || j?.message || JSON.stringify(j))
        } else {
          detail = (await res.clone().text()).trim()
        }
      } catch (_) {
        detail = ''
      }
      throw new Error(detail ? `${res.status} ${res.statusText}: ${detail}` : `${res.status} ${res.statusText}`)
    }
    return res
  } finally {
    clearTimeout(id)
  }
}

async function fetchWithRetry(input: RequestInfo, init: RequestInit = {}, retries = 3, timeout = DEFAULT_TIMEOUT) {
  let lastErr
  for (let i = 0; i < retries; i++) {
    try {
      return await fetchWithTimeout(input, init, timeout)
    } catch (e) {
      lastErr = e
      // 等待 2s * (i+1) 后重试
      await new Promise((r) => setTimeout(r, 2000 * (i + 1)))
    }
  }
  // 最后再尝试一次，确保达到预期的重试次数
  try {
    return await fetchWithTimeout(input, init, timeout)
  } catch (e) {
    throw e
  }
}

// 导出供页面直接使用的网络工具（例如需要自定义超时/重试的页面）
export { fetchWithRetry, fetchWithTimeout, DEFAULT_TIMEOUT }

export async function getSummary() {
  const r = await fetchWithRetry(`${BASE}/api/backtest/summary`, { method: 'GET' })
  return r.json()
}

export async function getResults() {
  const r = await fetchWithRetry(`${BASE}/api/backtest/results`, { method: 'GET' })
  return r.json()
}

export async function runBacktest(payload: any) {
  const r = await fetchWithRetry(`${BASE}/api/backtest/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  return r.json()
}

export async function getStrategies() {
  const r = await fetchWithRetry(`${BASE}/api/strategies`, { method: 'GET' })
  return r.json()
}

export async function importStrategy(name: string, content: string) {
  // 后端 StrategyImport pydantic model 期望 JSON {name, content}
  const r = await fetchWithRetry(`${BASE}/api/strategy/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, content }),
  })
  return r.json()
}

export async function getResultById(taskId: string) {
  const r = await fetchWithRetry(`${BASE}/api/backtest/results/${encodeURIComponent(taskId)}`, { method: 'GET' })
  return r.json()
}

export async function adjustBacktest(payload: any) {
  const r = await fetchWithRetry(`${BASE}/api/backtest/adjust`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  return r.json()
}

export async function getHistory(strategyId: string) {
  const r = await fetchWithRetry(`${BASE}/api/backtest/history/${encodeURIComponent(strategyId)}`, { method: 'GET' })
  return r.json()
}

export async function getResultEquity(taskId: string) {
  const r = await fetchWithRetry(`${BASE}/api/backtest/results/${encodeURIComponent(taskId)}/equity`, { method: 'GET' })
  return r.json()
}

export async function getResultTrades(taskId: string) {
  const r = await fetchWithRetry(`${BASE}/api/backtest/results/${encodeURIComponent(taskId)}/trades`, { method: 'GET' })
  return r.json()
}

export async function getProgress(taskId: string) {
  // 不使用重试机制，轮询时快速返回
  const r = await fetchWithTimeout(`${BASE}/api/backtest/progress/${encodeURIComponent(taskId)}`, { method: 'GET' }, 3000)
  return r.json()
}

export async function cancelBacktest(taskId: string) {
  const r = await fetchWithRetry(`${BASE}/api/backtest/cancel/${encodeURIComponent(taskId)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
  return r.json()
}

export async function getSystemStatus() {
  const r = await fetchWithRetry(`${BASE}/api/system/status`, { method: 'GET' })
  return r.json()
}

export async function getSystemLogs() {
  const r = await fetchWithRetry(`${BASE}/api/system/logs`, { method: 'GET' })
  return r.text()
}

export async function getEquityCurve() {
  const r = await fetchWithRetry(`${BASE}/api/backtest/equity-curve`, { method: 'GET' })
  return r.json()
}

export async function getMarketQuotes() {
  const r = await fetchWithRetry(`${BASE}/api/market/quotes`, { method: 'GET' })
  return r.json()
}

export async function getMainContracts() {
  const r = await fetchWithRetry(`${BASE}/api/market/main-contracts`, { method: 'GET' })
  return r.json()
}

export async function deleteStrategy(name: string) {
  const r = await fetchWithRetry(`${BASE}/api/strategy/${encodeURIComponent(name)}`, { method: 'DELETE' })
  return r.json()
}

// 返回策略 YAML 文本内容（用于前端触发下载）
export async function exportStrategyContent(name: string): Promise<string> {
  const r = await fetchWithRetry(`${BASE}/api/strategy/export/${encodeURIComponent(name)}`, { method: 'GET' })
  return r.text()
}

export function friendlyError(err: any) {
  if (!err) return '未知错误'
  const msg = String(err.message || err || '')
  if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('AbortError')) {
    return '资源或网络加载失败，请检查后端服务（http://localhost:8004）并重试'
  }
  if (msg.match(/\b404\b/)) return '资源未找到（404）'
  if (msg.match(/\b500\b/)) return '服务器内部错误（500）'
  return msg
}

export async function batchDeleteBacktests(taskIds: string[]) {
  const r = await fetchWithRetry(`${BASE}/api/backtest/results/batch`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids: taskIds }),
  })
  return r.json()
}

export async function saveStrategyParams(name: string, params: Record<string, any>) {
  // 导出当前 YAML，更新 params 字段后重新导入（覆盖同名文件）
  const r = await fetchWithRetry(`${BASE}/api/strategy/export/${encodeURIComponent(name)}`, { method: 'GET' })
  const yamlText = await r.text()
  // 将 params 序列化追加到 YAML 末尾（简单键值注入）
  let updated = yamlText
  for (const [k, v] of Object.entries(params)) {
    const numVal = typeof v === 'string' ? (isNaN(Number(v)) ? v : Number(v)) : v
    const line = `${k}: ${numVal}`
    const re = new RegExp(`^${k}:.*$`, 'm')
    if (re.test(updated)) {
      updated = updated.replace(re, line)
    } else {
      updated += `\n${line}`
    }
  }
  const ir = await fetchWithRetry(`${BASE}/api/strategy/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, content: updated }),
  })
  return ir.json()
}

// ─── 策略审批（保存到生产）───────────────────────────────────────
// 将已通过回测的策略标记为"已审批"，持久化到 localStorage 并触发下载
// 后端版本：POST /api/strategy/approve — 待 TASK-0004 Token 后启用
export function approveStrategyLocal(
  strategyName: string,
  yamlContent: string,
  meta?: { resultId?: string; totalReturn?: number; sharpeRatio?: number }
): { date: string; path: string } {
  const today = new Date().toISOString().slice(0, 10)
  const safeName = strategyName.endsWith('.yaml') || strategyName.endsWith('.yml')
    ? strategyName
    : `${strategyName}.yaml`
  const path = `approved_strategies/${today}/${safeName}`

  // 保存到 localStorage（管理已审批列表，内容也存储以备决策端读取）
  if (typeof window !== 'undefined') {
    try {
      const raw = localStorage.getItem('jbt_approved_strategies') ?? '[]'
      const existing: Array<{ name: string; date: string; path: string; totalReturn?: number; sharpeRatio?: number; yamlContent?: string; delivered?: boolean }> = JSON.parse(raw)
      const next = existing.filter((s) => s.name !== strategyName)
      next.unshift({ name: strategyName, date: today, path, ...meta, yamlContent, delivered: false })
      localStorage.setItem('jbt_approved_strategies', JSON.stringify(next))
    } catch (_) {}
    // 注意：文件不自动下载，需使用策略列表中的"下载"按钮手动保存并放入决策端目录
  }

  return { date: today, path }
}

export function getApprovedStrategies(): Array<{
  name: string; date: string; path: string; totalReturn?: number; sharpeRatio?: number; yamlContent?: string; delivered?: boolean
}> {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem('jbt_approved_strategies') ?? '[]')
  } catch {
    return []
  }
}

export function markStrategyDelivered(strategyName: string, delivered: boolean): void {
  if (typeof window === 'undefined') return
  try {
    const raw = localStorage.getItem('jbt_approved_strategies') ?? '[]'
    const existing = JSON.parse(raw)
    const next = existing.map((s: any) => s.name === strategyName ? { ...s, delivered } : s)
    localStorage.setItem('jbt_approved_strategies', JSON.stringify(next))
  } catch (_) {}
}

export function isStrategyApproved(strategyName: string): boolean {
  return getApprovedStrategies().some((s) => s.name === strategyName)
}

export function revokeApprovedStrategy(strategyName: string): void {
  if (typeof window === 'undefined') return
  try {
    const raw = localStorage.getItem('jbt_approved_strategies') ?? '[]'
    const existing = JSON.parse(raw)
    const next = existing.filter((s: any) => s.name !== strategyName)
    localStorage.setItem('jbt_approved_strategies', JSON.stringify(next))
  } catch (_) {}
}

export default {
  getSummary,
  getResults,
  runBacktest,
  getStrategies,
  importStrategy,
  getResultById,
  adjustBacktest,
  getHistory,
  getResultEquity,
  getResultTrades,
  getProgress,
  cancelBacktest,
  getSystemStatus,
  getSystemLogs,
  getEquityCurve,
  getMarketQuotes,
  getMainContracts,
  deleteStrategy,
  exportStrategyContent,
  batchDeleteBacktests,
  saveStrategyParams,
  approveStrategyLocal,
  getApprovedStrategies,
  isStrategyApproved,
  revokeApprovedStrategy,
  markStrategyDelivered,
  friendlyError,
}
