"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Keyboard } from "lucide-react"

export function KeyboardShortcutsHelp() {
  const shortcuts = [
    { key: "Ctrl + R", description: "开始回测" },
    { key: "Ctrl + S", description: "停止回测" },
    { key: "Ctrl + E", description: "查看结果" },
    { key: "Ctrl + O", description: "参数优化" },
    { key: "Ctrl + F", description: "刷新数据" },
    { key: "Ctrl + T", description: "切换主题" },
    { key: "Ctrl + K", description: "聚焦搜索" },
    { key: "Ctrl + H", description: "显示帮助" },
  ]

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Keyboard className="w-5 h-5 text-purple-500" />
          键盘快捷键
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {shortcuts.map((shortcut, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-neutral-900 rounded border border-neutral-700">
              <span className="text-sm text-neutral-300">{shortcut.description}</span>
              <kbd className="px-2 py-1 text-xs font-mono bg-neutral-800 border border-neutral-600 rounded text-neutral-300">
                {shortcut.key}
              </kbd>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
