// 通过 Next.js 代理转发到 dashboard 后端（避免 CORS）
// next.config.ts: /api/dashboard/:path* → http://localhost:3006/:path*
const API_BASE = '/api/dashboard'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  success: boolean
  token?: string
  user?: {
    id: number
    username: string
    role: string
    created_at: string
  }
  message?: string
}

export interface User {
  id: number
  username: string
  role: string
  created_at: string
  permissions: string[]
}

export interface CreateUserRequest {
  username: string
  password: string
  role?: string
  permissions?: string[]
}

export interface UpdatePasswordRequest {
  old_password?: string
  new_password: string
}

export interface UpdateUserRequest {
  username?: string
  password?: string
  role?: string
}

/** 从 localStorage 读取 token 并构造认证请求头 */
function getAuthHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('jbt_token') : null
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (token) {
    ;(headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export const authApi = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Login failed')
    return res.json()
  },

  async me(): Promise<User> {
    const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
      headers: getAuthHeaders(),
    })
    if (!res.ok) throw new Error('Not authenticated')
    return res.json()
  },

  async logout(): Promise<void> {
    await fetch(`${API_BASE}/api/v1/auth/logout`, {
      method: 'POST',
      headers: getAuthHeaders(),
    }).catch(() => {})
  },
}

export const usersApi = {
  async list(): Promise<User[]> {
    const res = await fetch(`${API_BASE}/api/v1/users`, {
      headers: getAuthHeaders(),
    })
    if (!res.ok) throw new Error('Failed to fetch users')
    return res.json()
  },

  async create(data: CreateUserRequest): Promise<User> {
    const res = await fetch(`${API_BASE}/api/v1/users`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const error = await res.json()
      throw new Error(error.detail || 'Failed to create user')
    }
    return res.json()
  },

  async update(userId: number, data: UpdateUserRequest): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/users/${userId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const error = await res.json()
      throw new Error(error.detail || 'Failed to update user')
    }
    return res.json()
  },

  async delete(userId: number): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/users/${userId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    if (!res.ok) {
      const error = await res.json()
      throw new Error(error.detail || 'Failed to delete user')
    }
    return res.json()
  },

  async changePassword(userId: number, data: UpdatePasswordRequest): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/v1/users/${userId}/password`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const error = await res.json()
      throw new Error(error.detail || 'Failed to change password')
    }
    return res.json()
  },

  async updatePermissions(userId: number, permissions: string[]): Promise<{ success: boolean; permissions: string[] }> {
    const res = await fetch(`${API_BASE}/api/v1/users/${userId}/permissions`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ permissions }),
    })
    if (!res.ok) {
      const error = await res.json()
      throw new Error(error.detail || 'Failed to update permissions')
    }
    return res.json()
  },
}
