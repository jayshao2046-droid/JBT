import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// 不需要认证的路径
const PUBLIC_PATHS = ['/login']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // 静态资源和 API 路由不处理
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.')
  ) {
    return NextResponse.next()
  }

  const token = request.cookies.get('jbt_token')?.value
  const isPublicPath = PUBLIC_PATHS.some((p) => pathname.startsWith(p))

  // 未登录访问受保护路径 → 跳转到登录页
  if (!token && !isPublicPath) {
    const loginUrl = new URL('/login', request.url)
    // 保存原始路径，登录成功后可以跳回
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // 已登录访问登录页 → 跳转到主页
  if (token && isPublicPath) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
