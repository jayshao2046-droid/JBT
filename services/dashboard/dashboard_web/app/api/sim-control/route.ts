/**
 * Server-side proxy for sim-trading control operations (pause / resume).
 * Injects X-API-Key from server environment — never exposed to browser.
 */
import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const SIM_TRADING_URL = process.env.SIM_TRADING_URL ?? 'http://192.168.31.187:8101'
  const SIM_API_KEY     = process.env.SIM_API_KEY     ?? ''

  let body: { action: string; reason?: string }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const { action, reason } = body
  if (action !== 'pause' && action !== 'resume') {
    return NextResponse.json({ error: 'action must be pause or resume' }, { status: 400 })
  }

  const url = `${SIM_TRADING_URL}/api/v1/system/${action}`
  const fetchBody = action === 'pause'
    ? JSON.stringify({ reason: reason ?? '用户手动暂停' })
    : undefined

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (SIM_API_KEY) headers['X-API-Key'] = SIM_API_KEY

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: fetchBody,
      signal: AbortSignal.timeout(5000),
    })
    const data = await res.json().catch(() => ({}))
    return NextResponse.json(data, { status: res.status })
  } catch (e) {
    return NextResponse.json(
      { error: 'sim-trading service unreachable', detail: String(e) },
      { status: 503 },
    )
  }
}
