'use client'
"use client"

import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'

export interface AuthUser {
  id: number
  username: string
  role: 'admin' | 'user'
  created_at: string
  permissions?: string[]
}

interface AuthContextType {
  user: AuthUser | null
  token: string | null
  isLoading: boolean
  login: (user: AuthUser, token: string) => void
  logout: () => Promise<void>
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

const TOKEN_KEY = 'jbt_token'
const USER_KEY = 'jbt_user'

function setCookie(name: string, value: string, days: number) {
  const expires = new Date()
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000)
  document.cookie = `${name}=${value}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`
}

function deleteCookie(name: string) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax`
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // 从 localStorage 恢复会话
    try {
      const storedToken = localStorage.getItem(TOKEN_KEY)
      const storedUser = localStorage.getItem(USER_KEY)
      if (storedToken && storedUser) {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
      }
    } catch {
      // 忽略解析错误
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = useCallback((authUser: AuthUser, authToken: string) => {
    setUser(authUser)
    setToken(authToken)
    localStorage.setItem(TOKEN_KEY, authToken)
    localStorage.setItem(USER_KEY, JSON.stringify(authUser))
    setCookie(TOKEN_KEY, authToken, 30)
  }, [])

  const logout = useCallback(async () => {
    try {
      const currentToken = localStorage.getItem(TOKEN_KEY)
      if (currentToken) {
        const API_BASE = process.env.NEXT_PUBLIC_DASHBOARD_API_URL || 'http://localhost:3006'
        await fetch(`${API_BASE}/api/v1/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${currentToken}` },
        }).catch(() => {}) // 登出失败不阻塞本地清理
      }
    } finally {
      setUser(null)
      setToken(null)
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      deleteCookie(TOKEN_KEY)
      router.push('/login')
    }
  }, [router])

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        isAdmin: user?.role === 'admin',
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
