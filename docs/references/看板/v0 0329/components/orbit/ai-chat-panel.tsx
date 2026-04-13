'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Send, 
  Paperclip,
  Sparkles,
  TrendingUp,
  BarChart3,
  Lightbulb,
  Loader2,
  ChevronDown,
  Check,
  Circle,
  X
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

// Message types
interface Message {
  id: string
  role: 'system' | 'user' | 'assistant'
  content: string
  timestamp: Date
}

// Model options with local/online indicator
const models = [
  { id: 'deepseek-v3-14b', name: 'DeepSeek V3 (14B)', description: '推理速度 1.2s/token', isLocal: true, recommended: true },
  { id: 'deepseek-v3-32b', name: 'DeepSeek V3 (32B)', description: '更强推理能力，速度 2.1s/token', isLocal: true },
  { id: 'deepseek-v3-70b', name: 'DeepSeek V3 (70B)', description: '最强推理能力，速度 4.5s/token', isLocal: true },
  { id: 'qwen-max', name: 'Qwen-Max', description: '阿里云大模型，速度 1.8s/token', isLocal: false },
  { id: 'kimi-2.5', name: 'Kimi 2.5', description: '月之暗面大模型，速度 1.5s/token', isLocal: false },
  { id: 'gpt-4o', name: 'GPT-4o', description: 'OpenAI 大模型，速度 0.8s/token', isLocal: false },
]

// Quick commands
const quickCommands = [
  { id: 'quote', label: '行情查询', icon: TrendingUp, prompt: '查询今日 rb2405 的行情' },
  { id: 'factor', label: '因子分析', icon: BarChart3, prompt: '分析北向资金因子最近一周的有效性' },
  { id: 'strategy', label: '策略建议', icon: Lightbulb, prompt: '基于当前市场给出一个日内短线策略建议' },
]

// Simulated AI responses
const mockResponses: Record<string, string> = {
  '查询今日 rb2405 的行情': `**rb2405 实时行情**

| 指标 | 数值 |
|------|------|
| 最新价 | 3,200 元/吨 |
| 涨跌幅 | +2.3% |
| 开盘价 | 3,128 元 |
| 最高价 | 3,215 元 |
| 最低价 | 3,120 元 |
| 成交量 | 128.5 万手 |
| 持仓量 | 156.8 万手 |

**技术面分析：**
- MACD 金叉，短期看涨
- 5日均线上穿10日均线
- RSI 指标 62，处于中性偏强区间`,

  '分析北向资金因子最近一周的有效性': `**北向资金因子有效性分析（最近一周）**

**1. 整体表现**
- IC 均值：0.052（正向有效）
- IC 标准差：0.031
- ICIR：1.68（较强）
- 胜率：71.4%（5/7 天）

**2. 分行业表现**
| 行业 | IC值 | 有效性 |
|------|------|--------|
| 银行 | 0.078 | 强 |
| 食品饮料 | 0.065 | 强 |
| 新能源 | 0.042 | 中等 |
| 医药 | 0.028 | 弱 |

**3. 结论**
北向资金因子在本周表现良好，尤其在消费和金融板块预测能力较强，建议在选股模型中维持该因子权重。`,

  '基于当前市场给出一个日内短线策略建议': `**日内短线策略建议**

**市场状态判断：**
- 今日大盘震荡偏强，成交量放大
- 板块轮动明显，资金活跃度高
- 北向资金净流入 28 亿

**推荐策略：动量突破**

\`\`\`
入场条件：
1. 价格突破5分钟布林带上轨
2. 成交量放大至均量1.5倍以上
3. MACD 0轴上方金叉

出场条件：
1. 止盈：2%
2. 止损：0.8%
3. 尾盘强制平仓
\`\`\`

**风险提示：**
- 注意控制单笔仓位不超过总资金的 10%
- 关注板块联动效应
- 避免追涨尾盘拉升个股`,
}

interface AIChatPanelProps {
  isOpen?: boolean
  onOpenChange?: (open: boolean) => void
  embedded?: boolean // New prop for embedded mode (not floating)
}

export function AIChatPanel({ isOpen: initialOpen = false, onOpenChange, embedded = false }: AIChatPanelProps) {
  const [isOpen, setIsOpen] = useState(initialOpen)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'system',
      content: '欢迎使用 JBotQuant 助手！我可以帮你查询行情、分析因子、提供策略建议。',
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState(models[0])
  
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [messages])

  // Sync isOpen state with parent
  useEffect(() => {
    setIsOpen(initialOpen)
  }, [initialOpen])

  // Notify parent of state changes
  useEffect(() => {
    onOpenChange?.(isOpen)
  }, [isOpen, onOpenChange])

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    // Auto-resize
    const textarea = e.target
    textarea.style.height = '48px'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }

  // Send message
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = '48px'
    }
    setIsLoading(true)

    // Simulate AI response
    await new Promise(resolve => setTimeout(resolve, 1500))

    const response = mockResponses[content.trim()] || `收到您的问题：「${content.trim()}」\n\n我正在分析中，这是一个模拟回复。在实际应用中，这里会返回基于您的问题的智能分析结果。`

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, assistantMessage])
    setIsLoading(false)
  }, [isLoading])

  // Handle quick command click
  const handleQuickCommand = (prompt: string) => {
    setInput(prompt)
    inputRef.current?.focus()
  }

  // Handle key press - Enter to send, Shift+Enter for newline
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  // Render message content with basic markdown support
  const renderMessageContent = (content: string) => {
    const lines = content.split('\n')
    return lines.map((line, i) => {
      line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      if (line.startsWith('```')) {
        return null
      }
      line = line.replace(/`(.+?)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-xs">$1</code>')
      if (line.startsWith('|')) {
        const cells = line.split('|').filter(Boolean).map(c => c.trim())
        if (cells.every(c => c.match(/^-+$/))) {
          return null
        }
        return (
          <div key={i} className="flex gap-4 text-xs py-0.5">
            {cells.map((cell, j) => (
              <span key={j} className={j === 0 ? 'w-20 text-muted-foreground' : 'flex-1'}>{cell}</span>
            ))}
          </div>
        )
      }
      if (line.startsWith('**') && line.endsWith('**')) {
        return <div key={i} className="font-medium mt-2 mb-1" dangerouslySetInnerHTML={{ __html: line }} />
      }
      if (line.startsWith('- ')) {
        return <div key={i} className="ml-2 text-sm" dangerouslySetInnerHTML={{ __html: '• ' + line.slice(2) }} />
      }
      if (line.trim()) {
        return <div key={i} className="text-sm" dangerouslySetInnerHTML={{ __html: line }} />
      }
      return <div key={i} className="h-2" />
    })
  }

  // Render chat content (shared between embedded and floating modes)
  const renderChatContent = () => (
    <div className={cn(
      "flex flex-col h-full",
      embedded ? "bg-background" : "bg-background border-l border-border shadow-2xl"
    )}>
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-4 border-b border-border bg-card/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-primary" />
          </div>
          <span className="font-semibold text-sm">BQ助手</span>
        </div>
        
        <div className="flex items-center gap-1">
          {/* Model Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 px-2 text-xs gap-1">
                {selectedModel.name.split(' ')[0]}
                <span className={cn(
                  "text-[10px] px-1 py-0.5 rounded ml-1",
                  selectedModel.isLocal 
                    ? "bg-red-500/10 text-red-500" 
                    : "bg-emerald-500/10 text-emerald-500"
                )}>
                  {selectedModel.isLocal ? '本地' : '在线'}
                </span>
                <ChevronDown className="w-3 h-3 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72">
              {models.map((model) => (
                <DropdownMenuItem
                  key={model.id}
                  onClick={() => setSelectedModel(model)}
                  className="flex flex-col items-start gap-0.5 py-2"
                >
                  <div className="flex items-center gap-2 w-full">
                    <span className="font-medium text-sm">{model.name}</span>
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded",
                      model.isLocal 
                        ? "bg-red-500/10 text-red-500" 
                        : "bg-emerald-500/10 text-emerald-500"
                    )}>
                      {model.isLocal ? '本地' : '在线'}
                    </span>
                    {model.recommended && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary">推荐</span>
                    )}
                    {selectedModel.id === model.id && (
                      <Check className="w-4 h-4 ml-auto text-primary" />
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground">{model.description}</span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Close Button - only show in floating mode */}
          {!embedded && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setIsOpen(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-2",
                message.role === 'user' && "flex-row-reverse"
              )}
            >
              {/* Avatar */}
              <div className={cn(
                "w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-medium",
                message.role === 'system' && "bg-blue-500/10 text-blue-500",
                message.role === 'user' && "bg-emerald-500/10 text-emerald-500",
                message.role === 'assistant' && "bg-primary/10 text-primary"
              )}>
                {message.role === 'system' && '系'}
                {message.role === 'user' && '我'}
                {message.role === 'assistant' && 'AI'}
              </div>

              {/* Content */}
              <div className={cn(
                "flex-1 rounded-lg px-3 py-2 text-sm",
                message.role === 'system' && "bg-blue-500/5 border border-blue-500/10",
                message.role === 'user' && "bg-emerald-500/5 border border-emerald-500/10",
                message.role === 'assistant' && "bg-muted/50 border border-border"
              )}>
                {renderMessageContent(message.content)}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex gap-2">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                <Loader2 className="w-4 h-4 text-primary animate-spin" />
              </div>
              <div className="flex-1 rounded-lg px-3 py-2 bg-muted/50 border border-border">
                <div className="flex items-center gap-1">
                  <span className="text-sm text-muted-foreground">思考中</span>
                  <span className="animate-pulse">...</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Quick Commands */}
      <div className="px-4 py-2 border-t border-border bg-card/30">
        <div className="flex gap-1.5">
          {quickCommands.map((cmd) => (
            <button
              key={cmd.id}
              onClick={() => handleQuickCommand(cmd.prompt)}
              className={cn(
                "flex items-center gap-1 px-2 py-1 rounded-md text-[11px]",
                "text-muted-foreground hover:text-foreground",
                "transition-colors"
              )}
            >
              <cmd.icon className="w-3 h-3" />
              {cmd.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-card/50">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="输入问题..."
              disabled={isLoading}
              className={cn(
                "w-full resize-none rounded-lg border border-border/50 bg-background",
                "px-3 py-3 text-[14px] placeholder:text-muted-foreground",
                "focus:outline-none focus:border-border/50",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "min-h-[48px] max-h-[120px]"
              )}
              style={{ height: '48px' }}
            />
          </div>
          
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-10 w-10"
              disabled={isLoading}
            >
              <Paperclip className="w-4 h-4" />
            </Button>
            <Button
              size="icon"
              className="h-10 w-10"
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isLoading}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Status Bar - only show online status */}
      <div className="h-8 px-4 flex items-center justify-end text-[10px] text-muted-foreground border-t border-border bg-muted/30">
        <div className="flex items-center gap-1">
          <Circle className="w-2 h-2 fill-emerald-500 text-emerald-500" />
          <span>在线</span>
        </div>
      </div>
    </div>
  )

  // Embedded mode - render directly without floating animation
  if (embedded) {
    return renderChatContent()
  }

  // Floating mode - with toggle button and slide animation
  return (
    <>
      {/* Floating Toggle Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            onClick={() => setIsOpen(true)}
            className={cn(
              "fixed bottom-6 right-6 z-50",
              "w-14 h-14 rounded-full",
              "bg-primary text-primary-foreground",
              "shadow-lg shadow-primary/25",
              "flex items-center justify-center",
              "hover:scale-105 active:scale-95 transition-transform",
              "group"
            )}
            title="AI 助手"
          >
            <Sparkles className="w-6 h-6" />
            <span className="absolute -top-8 right-0 px-2 py-1 rounded bg-popover text-popover-foreground text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-md border border-border">
              AI 助手
            </span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: 340, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 340, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            className="fixed top-0 right-0 bottom-0 z-50 w-[340px]"
          >
            {renderChatContent()}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
