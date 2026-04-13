import { User } from '@/types';

// Mock auth - 实际实现需要对接后端
export async function login(username: string, password: string): Promise<User | null> {
  // TODO: 实现真实的登录逻辑
  if (username && password) {
    return {
      id: '1',
      username,
      email: `${username}@jbt.com`,
      role: 'admin',
      membershipLevel: 'enterprise',
    };
  }
  return null;
}

export async function logout(): Promise<void> {
  // TODO: 实现真实的登出逻辑
  localStorage.removeItem('user');
}

export function getCurrentUser(): User | null {
  // TODO: 从 token 或 session 获取当前用户
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}

export function isAuthenticated(): boolean {
  return getCurrentUser() !== null;
}
