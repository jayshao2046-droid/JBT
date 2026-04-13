"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Keyboard } from "lucide-react"
import { getAllShortcuts } from "@/lib/keyboard"

export function KeyboardShortcutsHelp() {
  const shortcuts = getAllShortcuts()

  const getKeyBadge = (key: string) => (
    <Badge variant="outline" className="font-mono">
      {key}
    </Badge>
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Keyboard className="h-4 w-4" />
          键盘快捷键
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {shortcuts.map((shortcut, index) => {
            const keys: string[] = []
            if (shortcut.ctrl) keys.push("Ctrl")
            if (shortcut.shift) keys.push("Shift")
            if (shortcut.alt) keys.push("Alt")
            keys.push(shortcut.key.toUpperCase())

            return (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{shortcut.description}</span>
                <div className="flex gap-1">
                  {keys.map((key, i) => (
                    <span key={i}>
                      {getKeyBadge(key)}
                      {i < keys.length - 1 && <span className="mx-1">+</span>}
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
