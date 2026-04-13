// 键盘快捷键管理（从 backtest 复用并修改）

type ShortcutHandler = () => void

interface Shortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  handler: ShortcutHandler
  description: string
}

const shortcuts: Shortcut[] = []

export function registerShortcut(
  key: string,
  handler: ShortcutHandler,
  description: string,
  modifiers?: { ctrl?: boolean; shift?: boolean; alt?: boolean }
): void {
  shortcuts.push({
    key: key.toLowerCase(),
    ctrl: modifiers?.ctrl,
    shift: modifiers?.shift,
    alt: modifiers?.alt,
    handler,
    description,
  })
}

export function initKeyboardShortcuts(): void {
  if (typeof window === "undefined") return

  window.addEventListener("keydown", (e: KeyboardEvent) => {
    // 忽略输入框中的快捷键
    const target = e.target as HTMLElement
    if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
      return
    }

    const key = e.key.toLowerCase()

    for (const shortcut of shortcuts) {
      const ctrlMatch = shortcut.ctrl === undefined || shortcut.ctrl === (e.ctrlKey || e.metaKey)
      const shiftMatch = shortcut.shift === undefined || shortcut.shift === e.shiftKey
      const altMatch = shortcut.alt === undefined || shortcut.alt === e.altKey

      if (shortcut.key === key && ctrlMatch && shiftMatch && altMatch) {
        e.preventDefault()
        shortcut.handler()
        break
      }
    }
  })
}

export function getShortcuts(): Shortcut[] {
  return shortcuts
}

export function clearShortcuts(): void {
  shortcuts.length = 0
}
