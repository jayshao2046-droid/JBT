// 全局键盘快捷键管理
import { useEffect, useCallback } from "react"
import { toast } from "sonner"

export type ShortcutAction =
  | "quick_buy"
  | "quick_sell"
  | "close_all"
  | "pause_trading"
  | "resume_trading"
  | "refresh_data"
  | "toggle_theme"
  | "focus_search"

interface Shortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  action: ShortcutAction
  description: string
}

const DEFAULT_SHORTCUTS: Shortcut[] = [
  { key: "b", ctrl: true, action: "quick_buy", description: "快速买入" },
  { key: "s", ctrl: true, action: "quick_sell", description: "快速卖出" },
  { key: "q", ctrl: true, action: "close_all", description: "全部平仓" },
  { key: "p", ctrl: true, action: "pause_trading", description: "暂停交易" },
  { key: "r", ctrl: true, action: "resume_trading", description: "恢复交易" },
  { key: "r", ctrl: true, shift: true, action: "refresh_data", description: "刷新数据" },
  { key: "t", ctrl: true, action: "toggle_theme", description: "切换主题" },
  { key: "k", ctrl: true, action: "focus_search", description: "聚焦搜索" },
]

export function useKeyboardShortcuts(
  handlers: Partial<Record<ShortcutAction, () => void>>
) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // 忽略输入框中的快捷键
      const target = event.target as HTMLElement
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        // 除了 Ctrl+K (focus_search) 外，其他快捷键在输入框中不生效
        if (!(event.ctrlKey && event.key === "k")) {
          return
        }
      }

      for (const shortcut of DEFAULT_SHORTCUTS) {
        const ctrlMatch = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey
        const altMatch = shortcut.alt ? event.altKey : !event.altKey
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase()

        if (ctrlMatch && shiftMatch && altMatch && keyMatch) {
          event.preventDefault()
          const handler = handlers[shortcut.action]
          if (handler) {
            handler()
          } else {
            toast.info(`快捷键: ${shortcut.description}`)
          }
          break
        }
      }
    },
    [handlers]
  )

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])
}

export function getShortcutLabel(action: ShortcutAction): string {
  const shortcut = DEFAULT_SHORTCUTS.find(s => s.action === action)
  if (!shortcut) return ""

  const parts: string[] = []
  if (shortcut.ctrl) parts.push("Ctrl")
  if (shortcut.shift) parts.push("Shift")
  if (shortcut.alt) parts.push("Alt")
  parts.push(shortcut.key.toUpperCase())

  return parts.join("+")
}

export function getAllShortcuts(): Shortcut[] {
  return DEFAULT_SHORTCUTS
}
