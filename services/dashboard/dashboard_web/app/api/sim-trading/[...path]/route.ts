import { NextRequest, NextResponse } from 'next/server'

const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'content-length',
  'host',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
])

export const runtime = 'nodejs'

type RouteContext = {
  params: Promise<{
    path: string[]
  }>
}

function buildTargetUrl(pathSegments: string[], req: NextRequest): URL {
  const baseUrl = process.env.SIM_TRADING_URL ?? 'http://192.168.31.187:8101'
  const upstreamUrl = new URL(pathSegments.join('/'), `${baseUrl.replace(/\/$/, '')}/`)
  upstreamUrl.search = req.nextUrl.search
  return upstreamUrl
}

function buildUpstreamHeaders(req: NextRequest): Headers {
  const headers = new Headers()

  const accept = req.headers.get('accept')
  if (accept) {
    headers.set('accept', accept)
  }

  const contentType = req.headers.get('content-type')
  if (contentType) {
    headers.set('content-type', contentType)
  }

  const apiKey = process.env.SIM_API_KEY ?? ''
  if (apiKey) {
    headers.set('X-API-Key', apiKey)
  }
  return headers
}

async function proxy(req: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params
  if (!path || path.length === 0) {
    return NextResponse.json({ error: 'missing upstream path' }, { status: 400 })
  }

  const targetUrl = buildTargetUrl(path, req)
  const headers = buildUpstreamHeaders(req)
  const body = req.method === 'GET' || req.method === 'HEAD'
    ? undefined
    : await req.arrayBuffer()

  try {
    const upstream = await fetch(targetUrl, {
      method: req.method,
      headers,
      body,
      redirect: 'manual',
      signal: AbortSignal.timeout(15000),
    })

    const responseHeaders = new Headers(upstream.headers)
    for (const header of HOP_BY_HOP_HEADERS) {
      responseHeaders.delete(header)
    }

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'sim-trading service unreachable', detail: String(error) },
      { status: 503 },
    )
  }
}

export async function GET(req: NextRequest, context: RouteContext) {
  return proxy(req, context)
}

export async function POST(req: NextRequest, context: RouteContext) {
  return proxy(req, context)
}

export async function PUT(req: NextRequest, context: RouteContext) {
  return proxy(req, context)
}

export async function PATCH(req: NextRequest, context: RouteContext) {
  return proxy(req, context)
}

export async function DELETE(req: NextRequest, context: RouteContext) {
  return proxy(req, context)
}

export async function HEAD(req: NextRequest, context: RouteContext) {
  return proxy(req, context)
}