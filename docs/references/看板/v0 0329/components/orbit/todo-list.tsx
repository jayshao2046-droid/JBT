'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { ViewType } from './command-dock'

interface Todo {
  id: number
  priority: 'P0' | 'P1' | 'P2'
  title: string
  time?: string
  link?: ViewType
  completed?: boolean
}

interface TodoListProps {
  isExpanded: boolean
  onNavigate?: (view: ViewType) => void
}

const mockTodos: Todo[] = [
  { id: 1, priority: 'P0', title: '确认 AU2412 买入信号', time: '10 分钟前', link: 'china-futures' },
  { id: 2, priority: 'P1', title: '审核风控参数调整', link: 'risk-params' },
  { id: 3, priority: 'P1', title: '检查 IF2403 止损设置', link: 'risk-monitor' },
  { id: 4, priority: 'P2', title: '更新策略权重配置', link: 'strategy-params' },
  { id: 5, priority: 'P2', title: '导出周度交易报告' },
]

const getPriorityColor = (priority: 'P0' | 'P1' | 'P2') => {
  if (priority === 'P0') return 'bg-red-500'
  if (priority === 'P1') return 'bg-yellow-500'
  return 'bg-green-500'
}

export function TodoList({ isExpanded, onNavigate }: TodoListProps) {
  const [todos] = useState<Todo[]>(mockTodos)
  const pendingCount = todos.filter(t => !t.completed).length

  if (!isExpanded) {
    return (
      <div className="flex flex-col items-center gap-2">
        {todos.slice(0, 3).map((todo) => (
          <div
            key={todo.id}
            className={cn('w-2 h-2 rounded-full', getPriorityColor(todo.priority))}
            title={todo.title}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-0">
      <div className="flex items-center justify-between px-2.5 py-2">
        <span className="text-[13px] font-medium">📋 待办事项</span>
        <span className="text-[11px] text-muted-foreground">{pendingCount} 待处理</span>
      </div>

      <div className="space-y-0.5 px-1">
        {todos.map((todo) => (
          <button
            key={todo.id}
            onClick={() => todo.link && onNavigate?.(todo.link)}
            className="w-full flex items-start gap-2 px-2.5 py-2 rounded-md text-left hover:bg-secondary/50 transition-colors group"
            title={todo.title}
          >
            <div className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1', getPriorityColor(todo.priority))} />
            <div className="flex-1 min-w-0">
              <p className="text-[12px] text-foreground/80 truncate group-hover:text-foreground">
                {todo.title}
              </p>
              {todo.time && (
                <p className="text-[10px] text-muted-foreground">
                  {todo.time}
                </p>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
