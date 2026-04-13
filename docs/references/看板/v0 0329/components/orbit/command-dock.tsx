'use client'
// Navigation dock with Chinese label support and top status bar
import { useState, useEffect } from 'react'
import {
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  Sparkles,
  RefreshCw,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ThemeToggle } from './theme-toggle'
import { TodoList } from './todo-list'
import { navItems, systemStatus } from './nav-items'

export type ViewType =
  | 'dashboard'
  | 'accounts'
  | 'analytics'
  | 'settings'
  | 'china-futures'
  | 'china-a-stock'
  | 'strategy-china-futures'
  | 'strategy-china-a-stock'
  | 'data-collection'
  | 'api-quota'
  | 'storage'
  | 'risk-monitor'
  | 'alert-records'
  | 'compliance-report'
  | 'device-heartbeat'
  | 'process-monitor'
  | 'log-records'
  | 'strategy-params'
  | 'risk-params'
  | 'collection-params'
  | 'notification-config'
  | 'futures-detail'
  | 'stock-detail'

interface CommandDockProps {
  activeView: ViewType
  onViewChange: (view: ViewType) => void
  onAIChatOpen?: () => void
}

export function CommandDock({ activeView, onViewChange, onAIChatOpen }: CommandDockProps) {
  const [expandedItems, setExpandedItems] = useState<string[]>(['strategy'])
  const [isExpanded, setIsExpanded] = useState(true)
  const [mounted, setMounted] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date())

  useEffect(() => {
    setMounted(true)
  }, [])

  const toggleExpand = (id: string) => {
    setExpandedItems((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    )
  }

  const handleNavClick = (item: (typeof navItems)[number]) => {
    if (item.children) {
      toggleExpand(item.id)
    }
    if (item.viewType) {
      onViewChange(item.viewType)
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    // 模拟刷新延迟
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setLastUpdateTime(new Date())
    setIsRefreshing(false)
  }

  const getStatusColor = (status: 'online' | 'offline' | 'warning') => {
    if (status === 'online') return 'bg-emerald-500'
    if (status === 'offline') return 'bg-red-500'
    return 'bg-amber-500'
  }

  const getStatusText = (status: 'online' | 'offline' | 'warning') => {
    if (status === 'online') return '在线'
    if (status === 'offline') return '离线'
    return '警告'
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  // Render a skeleton with the same dimensions during SSR to avoid hydration mismatch
  if (!mounted) {
    return (
      <div className="h-full w-[200px] flex-shrink-0 bg-card/80 border-r border-border/50" />
    )
  }

  return (
    <div
      className={cn(
        'h-full flex flex-col bg-card/80 backdrop-blur-sm transition-all duration-200 border-r border-border/50 flex-shrink-0',
        isExpanded ? 'w-[200px]' : 'w-[60px]'
      )}
    >
      {/* Header: Collapse Toggle + Status Display */}
      <div className="h-12 flex items-center justify-between border-b border-border/40 shrink-0 px-2 gap-2">
        <button
          onClick={() => setIsExpanded((prev) => !prev)}
          className="w-8 h-8 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors flex-shrink-0"
          title={isExpanded ? '收起侧栏' : '展开侧栏'}
        >
          <PanelLeftClose className="w-4 h-4" strokeWidth={1.5} />
        </button>

        {isExpanded && (
          <>
            {/* Status indicators */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {systemStatus.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center gap-1"
                  title={`${s.label}: ${getStatusText(s.status)}`}
                >
                  <div className={cn('w-1.5 h-1.5 rounded-full', getStatusColor(s.status))} />
                </div>
              ))}
            </div>

            {/* Refresh button and time */}
            <div className="flex items-center gap-1">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="w-7 h-7 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors disabled:opacity-50"
                title="刷新"
              >
                <RefreshCw className={cn('w-4 h-4', isRefreshing && 'animate-spin')} strokeWidth={1.5} />
              </button>
              <span className="text-[10px] text-muted-foreground/70 whitespace-nowrap" suppressHydrationWarning>
                {formatTime(lastUpdateTime)}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-2 overflow-y-auto overflow-x-hidden">
        {navItems.map((item) => {
          const isActive = item.viewType === activeView
          const isItemExpanded = expandedItems.includes(item.id)
          const Icon = item.icon

          return (
            <div key={item.id} className="mb-0.5">
              <button
                onClick={() => handleNavClick(item)}
                className={cn(
                  'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md transition-all duration-150 group relative',
                  isActive
                    ? 'text-primary bg-primary/8'
                    : 'text-muted-foreground/70 hover:text-foreground hover:bg-secondary/50'
                )}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-4 bg-primary rounded-r-full" />
                )}
                <Icon className="w-[18px] h-[18px] flex-shrink-0" strokeWidth={1.5} />

                {isExpanded && (
                  <>
                    <span className="text-[13px] font-medium flex-1 text-left truncate" suppressHydrationWarning>{item.label}</span>
                    {item.children && (
                      isItemExpanded
                        ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground/50 flex-shrink-0" />
                        : <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/50 flex-shrink-0" />
                    )}
                  </>
                )}

                {!isExpanded && (
                  <span className="absolute left-14 px-2.5 py-1.5 bg-foreground text-background rounded-md text-[11px] font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 shadow-lg" suppressHydrationWarning>
                    {item.label}
                  </span>
                )}
              </button>

              {item.children && isItemExpanded && isExpanded && (
                <div className="ml-4 mt-0.5 pl-3 border-l border-border/50">
                  {item.children.map((child) => {
                    const ChildIcon = child.icon
                    const isChildActive = child.viewType === activeView
                    return (
                      <button
                        key={child.id}
                        onClick={() => child.viewType && onViewChange(child.viewType)}
                        className={cn(
                          'w-full flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors relative',
                          isChildActive
                            ? 'text-primary bg-primary/8 font-medium'
                            : 'text-muted-foreground/50 hover:text-foreground hover:bg-secondary/30'
                        )}
                      >
                        {isChildActive && (
                          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-3 bg-primary rounded-r-full" />
                        )}
                        <ChildIcon
                          className={cn('w-[14px] h-[14px] flex-shrink-0', isChildActive && 'text-primary')}
                          strokeWidth={1.5}
                        />
                        <span className="text-[12px] truncate" suppressHydrationWarning>{child.label}</span>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </nav>

      {/* System Status - Removed, replaced with Todo List below */}

      {/* Todo List */}
      <div className={cn('border-t border-border/50 p-3', !isExpanded && 'px-2')}>
        <TodoList 
          isExpanded={isExpanded} 
          onNavigate={onViewChange}
        />
      </div>

      {/* Theme toggle and AI Chat button */}
      <div
        className={cn(
          'border-t border-border/50 p-2',
          !isExpanded ? 'flex flex-col items-center gap-2' : 'flex items-center justify-between'
        )}
      >
        <ThemeToggle />
        <button
          onClick={onAIChatOpen}
          className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 transition-colors shadow-md hover:shadow-lg hover:shadow-primary/25"
          title="AI 助手"
        >
          <Sparkles className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
