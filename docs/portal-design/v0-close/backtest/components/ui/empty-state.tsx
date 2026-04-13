"use client"

import { Inbox, Database } from "lucide-react"
import { Button } from "@/components/ui/button"

type Props = {
  title?: string
  description?: string
  icon?: 'inbox' | 'database'
  actionLabel?: string
  onAction?: () => void
}

export default function EmptyState({ title = '暂无数据', description = '暂无条目', icon = 'inbox', actionLabel, onAction }: Props) {
  const Icon = icon === 'database' ? Database : Inbox
  return (
    <div className="w-full flex flex-col items-center justify-center py-12">
      <Icon className="w-12 h-12 text-neutral-400 mb-4" />
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-sm text-neutral-500 mb-4 text-center max-w-xs">{description}</p>
      {actionLabel && (
        <Button variant="outline" onClick={onAction} className="border-neutral-700 text-neutral-300">
          {actionLabel}
        </Button>
      )}
    </div>
  )
}
