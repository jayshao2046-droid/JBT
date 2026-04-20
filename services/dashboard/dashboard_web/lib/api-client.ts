/**
 * API Client for JBot Quant Dashboard
 *
 * Provides unified API access to all backend services:
 * - Sim Trading (8101)
 * - Backtest (8103)
 * - Decision (8104)
 * - Data (8105)
 */

const API_BASE_URLS = {
  simTrading: process.env.NEXT_PUBLIC_SIM_TRADING_URL || 'http://localhost:8101',
  backtest: process.env.NEXT_PUBLIC_BACKTEST_URL || 'http://localhost:8103',
  decision: process.env.NEXT_PUBLIC_DECISION_URL || 'http://localhost:8104',
  data: process.env.NEXT_PUBLIC_DATA_URL || 'http://localhost:8105',
}

export type ServiceName = keyof typeof API_BASE_URLS

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>
}

class ApiClient {
  private getBaseUrl(service: ServiceName): string {
    return API_BASE_URLS[service]
  }

  private buildUrl(service: ServiceName, path: string, params?: Record<string, string | number | boolean>): string {
    const baseUrl = this.getBaseUrl(service)
    const url = new URL(path, baseUrl)

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value))
      })
    }

    return url.toString()
  }

  async request<T>(
    service: ServiceName,
    path: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { params, ...fetchOptions } = options
    const url = this.buildUrl(service, path, params)

    const response = await fetch(url, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Convenience methods
  async get<T>(service: ServiceName, path: string, params?: Record<string, string | number | boolean>): Promise<T> {
    return this.request<T>(service, path, { method: 'GET', params })
  }

  async post<T>(service: ServiceName, path: string, data?: unknown): Promise<T> {
    return this.request<T>(service, path, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async put<T>(service: ServiceName, path: string, data?: unknown): Promise<T> {
    return this.request<T>(service, path, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async delete<T>(service: ServiceName, path: string): Promise<T> {
    return this.request<T>(service, path, { method: 'DELETE' })
  }

  // Service-specific health checks
  async checkHealth(service: ServiceName): Promise<{ status: string; timestamp: string }> {
    try {
      return await this.get(service, '/health')
    } catch {
      return {
        status: 'error',
        timestamp: new Date().toISOString(),
      }
    }
  }
}

export const apiClient = new ApiClient()
