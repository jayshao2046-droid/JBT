"""键盘快捷键管理"""

type KeyHandler = () => void

interface ShortcutConfig {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  handler: KeyHandler
  description: string
}

class KeyboardManager {
  private shortcuts: Map<string, ShortcutConfig> = new Map()
  private enabled = true

  register(config: ShortcutConfig): void {
    const key = this.getShortcutKey(config)
    this.shortcuts.set(key, config)
  }

  unregister(key: string): void {
    this.shortcuts.delete(key)
  }

  enable(): void {
    this.enabled = true
  }

  disable(): void {
    this.enabled = false
  }

  handleKeyDown(event: KeyboardEvent): void {
    if (!this.enabled) return

    // 忽略输入框中的快捷键
    const target = event.target as HTMLElement
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
      return
    }

    const key = this.getEventKey(event)
    const config = this.shortcuts.get(key)

    if (config) {
      event.preventDefault()
      config.handler()
    }
  }

  getShortcuts(): ShortcutConfig[] {
    return Array.from(this.shortcuts.values())
  }

  private getShortcutKey(config: ShortcutConfig): string {
    const parts: string[] = []
    if (config.ctrl) parts.push('ctrl')
    if (config.shift) parts.push('shift')
    if (config.alt) parts.push('alt')
    parts.push(config.key.toLowerCase())
    return parts.join('+')
  }

  private getEventKey(event: KeyboardEvent): string {
    const parts: string[] = []
    if (event.ctrlKey || event.metaKey) parts.push('ctrl')
    if (event.shiftKey) parts.push('shift')
    if (event.altKey) parts.push('alt')
    parts.push(event.key.toLowerCase())
    return parts.join('+')
  }
}

export const keyboardManager = new KeyboardManager()

// 数据看板快捷键
export function registerDataShortcuts(handlers: {
  startCollection?: () => void
  stopCollection?: () => void
  viewResults?: () => void
  optimize?: () => void
  refresh?: () => void
  toggleTheme?: () => void
  focusSearch?: () => void
  showHelp?: () => void
}): void {
  if (handlers.startCollection) {
    keyboardManager.register({
      key: 's',
      ctrl: true,
      description: '开始采集',
      handler: handlers.startCollection,
    })
  }

  if (handlers.stopCollection) {
    keyboardManager.register({
      key: 'x',
      ctrl: true,
      description: '停止采集',
      handler: handlers.stopCollection,
    })
  }

  if (handlers.viewResults) {
    keyboardManager.register({
      key: 'r',
      ctrl: true,
      description: '查看结果',
      handler: handlers.viewResults,
    })
  }

  if (handlers.optimize) {
    keyboardManager.register({
      key: 'o',
      ctrl: true,
      description: '参数优化',
      handler: handlers.optimize,
    })
  }

  if (handlers.refresh) {
    keyboardManager.register({
      key: 'r',
      ctrl: true,
      shift: true,
      description: '刷新数据',
      handler: handlers.refresh,
    })
  }

  if (handlers.toggleTheme) {
    keyboardManager.register({
      key: 't',
      ctrl: true,
      description: '切换主题',
      handler: handlers.toggleTheme,
    })
  }

  if (handlers.focusSearch) {
    keyboardManager.register({
      key: 'k',
      ctrl: true,
      description: '聚焦搜索',
      handler: handlers.focusSearch,
    })
  }

  if (handlers.showHelp) {
    keyboardManager.register({
      key: '?',
      shift: true,
      description: '显示帮助',
      handler: handlers.showHelp,
    })
  }
}
