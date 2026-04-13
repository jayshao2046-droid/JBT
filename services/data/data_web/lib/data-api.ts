"""数据看板 API 客户端"""

const API_BASE = process.env.NEXT_PUBLIC_DATA_API_URL || 'http://localhost:8105'

export interface CollectionHistory {
  collection_id: string
  source: string
  start_time: string
  end_time: string
  status: string
  records_count: number
  duration: number
  error?: string
}

export interface DataQualityMetrics {
  completeness: number
  timeliness: number
  accuracy: number
  consistency: number
  success_rate: number
  avg_latency: number
  error_rate: number
}

export interface DataSourceHealthMetrics {
  availability: number
  response_time: number
  error_rate: number
  freshness: number
  coverage: number
}

export interface ValidationResult {
  ok: boolean
  validation: {
    ok: boolean
    message: string
    missing_fields?: string[]
  }
  connection: {
    ok: boolean
    message: string
  } | null
  permissions: {
    ok: boolean
    message: string
    permissions: string[]
  } | null
}

export interface BatchCollectionTask {
  task_id: string
  source: string
  status: string
  params: Record<string, any>
}

export interface ProgressUpdate {
  collection_id: string
  total_items: number
  completed_items: number
  current_stage: string
  progress_percent: number
  start_time: number
  estimated_completion: number | null
  status: string
}

export interface QueueTask {
  task_id: string
  task_type: string
  params: Record<string, any>
  priority: number
  status: string
  created_at: number
  started_at: number | null
  completed_at: number | null
  result: any
  error: string | null
}

export interface OptimizationResult {
  params: Record<string, any>
  score: number
  objective: string
}

export interface BestPractice {
  source_type: string
  recommended_params: Record<string, any>
  description: string
}

class DataAPI {
  private apiKey: string | null = null

  setApiKey(key: string) {
    this.apiKey = key
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    return response.json()
  }

  // 采集历史
  async collectionHistory(
    startDate?: string,
    endDate?: string,
    source?: string
  ): Promise<{ total: number; history: CollectionHistory[] }> {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    if (source) params.append('source', source)

    return this.request(`/api/v1/data/collection/history?${params}`)
  }

  // 数据源验证
  async validateSource(
    sourceType: string,
    config: Record<string, any>
  ): Promise<ValidationResult> {
    return this.request(`/api/v1/data/source/validate?source_type=${sourceType}`, {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  // 采集进度流
  streamProgress(collectionId: string, onProgress: (progress: ProgressUpdate) => void) {
    const eventSource = new EventSource(
      `${API_BASE}/api/v1/data/collection/progress/${collectionId}/stream`
    )

    eventSource.onmessage = (event) => {
      try {
        const progress = JSON.parse(event.data)
        onProgress(progress)

        if (progress.status === 'completed' || progress.status === 'failed') {
          eventSource.close()
        }
      } catch (error) {
        console.error('Failed to parse progress:', error)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
    }

    return () => eventSource.close()
  }

  // 数据质量指标
  async collectionQuality(collectionId: string): Promise<{
    collection_id: string
    metrics: DataQualityMetrics
  }> {
    return this.request(`/api/v1/data/collection/${collectionId}/quality`)
  }

  // 数据源健康指标
  async sourceHealth(sourceId: string): Promise<{
    source_id: string
    metrics: DataSourceHealthMetrics
  }> {
    return this.request(`/api/v1/data/source/${sourceId}/health`)
  }

  // 批量采集
  async createBatchCollection(
    sources: string[],
    paramGrid?: Record<string, any[]>
  ): Promise<{
    batch_id: string
    total_tasks: number
    tasks: BatchCollectionTask[]
  }> {
    return this.request('/api/v1/data/collection/batch', {
      method: 'POST',
      body: JSON.stringify({ sources, param_grid: paramGrid }),
    })
  }

  // 参数优化 - 网格搜索
  async gridSearch(
    paramGrid: Record<string, any[]>,
    objective: string = 'success_rate'
  ): Promise<OptimizationResult[]> {
    return this.request('/api/v1/data/optimize/grid', {
      method: 'POST',
      body: JSON.stringify({ param_grid: paramGrid, objective }),
    })
  }

  // 参数优化 - 自动调优
  async autoTune(
    currentParams: Record<string, any>,
    objective: string = 'success_rate'
  ): Promise<{
    recommended_params: Record<string, any>
    expected_score: number
    improvement: number
  }> {
    return this.request('/api/v1/data/optimize/auto-tune', {
      method: 'POST',
      body: JSON.stringify({ current_params: currentParams, objective }),
    })
  }

  // 最佳实践推荐
  async bestPractice(sourceType: string): Promise<BestPractice> {
    return this.request(`/api/v1/data/optimize/best-practice?source_type=${sourceType}`)
  }

  // 任务队列 - 获取队列
  async getQueue(status?: string): Promise<QueueTask[]> {
    const params = status ? `?status=${status}` : ''
    return this.request(`/api/v1/data/queue${params}`)
  }

  // 任务队列 - 获取任务
  async getTask(taskId: string): Promise<QueueTask> {
    return this.request(`/api/v1/data/queue/${taskId}`)
  }

  // 任务队列 - 取消任务
  async cancelTask(taskId: string): Promise<{ ok: boolean }> {
    return this.request(`/api/v1/data/queue/${taskId}/cancel`, {
      method: 'POST',
    })
  }

  // 任务队列 - 重试任务
  async retryTask(taskId: string): Promise<{ ok: boolean }> {
    return this.request(`/api/v1/data/queue/${taskId}/retry`, {
      method: 'POST',
    })
  }

  // 任务队列 - 调整优先级
  async updatePriority(taskId: string, priority: number): Promise<{ ok: boolean }> {
    return this.request(`/api/v1/data/queue/${taskId}/priority`, {
      method: 'POST',
      body: JSON.stringify({ priority }),
    })
  }

  // 任务队列 - 统计信息
  async queueStatistics(): Promise<{
    total: number
    pending: number
    running: number
    completed: number
    failed: number
    cancelled: number
  }> {
    return this.request('/api/v1/data/queue/statistics')
  }
}

export const dataAPI = new DataAPI()
