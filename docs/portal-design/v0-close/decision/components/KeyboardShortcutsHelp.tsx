"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Keyboard, X } from "lucide-react"
import { getShortcuts } from "@/lib/keyboard"

export function KeyboardShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false)
  const [shortcuts, setShortcuts] = useState<any[]>([])

  useEffect(() => {
    setShortcuts(getShortcuts())
  }, [])

  if (!isOpen) {
    return (
      <Button
        size="sm"
        variant="outline"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-50"
      >
        <Keyboard className="w-4 h-4 mr-2" />
        快捷键
      </Button>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setIsOpen(false)}>
      <Card className="bg-neutral-800 border-neutral-700 w-full max-w-2xl" onClick={(e) => e.stopPropagation()}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Keyboard className="w-5 h-5 text-blue-500" />
              键盘快捷键
            </CardTitle>
            <Button size="sm" variant="ghost" onClick={() => setIsOpen(false)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {shortcuts.length === 0 ? (
              <div className="text-center text-neutral-400 py-8">暂无快捷键</div>
            ) : (
              shortcuts.map((shortcut, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-neutral-900 rounded-lg">
                  <span className="text-sm text-neutral-300">{shortcut.description}</span>
                  <div className="flex gap-1">
                    {shortcut.ctrl && (
                      <kbd className="px-2 py-1 text-xs bg-neutral-700 text-white rounded">Ctrl</kbd>
                    )}
                    {shortcut.shift && (
                      <kbd className="px-2 py-1 text-xs bg-neutral-700 text-white rounded">Shift</kbd>
                    )}
                    {shortcut.alt && <kbd className="px-2 py-1 text-xs bg-neutral-700 text-white rounded">Alt</kbd>}
                    <kbd className="px-2 py-1 text-xs bg-neutral-700 text-white rounded uppercase">
                      {shortcut.key}
                    </kbd>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
