"use client"

import { useEffect, useState } from "react"
import { Calendar, Clock } from "lucide-react"

export function DateTimeDisplay() {
  const [dateTime, setDateTime] = useState<{
    date: string
    time: string
    dayName: string
  } | null>(null)

  useEffect(() => {
    const updateDateTime = () => {
      const now = new Date()

      // 获取日期格式：2026-04-13
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, "0")
      const day = String(now.getDate()).padStart(2, "0")
      const date = `${year}-${month}-${day}`

      // 获取时间格式：16:23:15
      const hours = String(now.getHours()).padStart(2, "0")
      const minutes = String(now.getMinutes()).padStart(2, "0")
      const seconds = String(now.getSeconds()).padStart(2, "0")
      const time = `${hours}:${minutes}:${seconds}`

      // 获取星期几
      const dayNames = [
        "星期日",
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六",
      ]
      const dayName = dayNames[now.getDay()]

      setDateTime({ date, time, dayName })
    }

    updateDateTime()
    const interval = setInterval(updateDateTime, 1000)

    return () => clearInterval(interval)
  }, [])

  if (!dateTime) {
    return <div className="text-xs text-neutral-500">--:--:--</div>
  }

  return (
    <div className="flex items-center gap-3 text-xs">
      {/* 日期显示 */}
      <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-neutral-800/50 rounded-md border border-neutral-700">
        <Calendar className="w-3.5 h-3.5 text-orange-500" />
        <div className="flex flex-col leading-none">
          <span className="text-neutral-300">{dateTime.date}</span>
          <span className="text-neutral-500 text-[10px]">{dateTime.dayName}</span>
        </div>
      </div>

      {/* 时间显示 */}
      <div className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-800/50 rounded-md border border-neutral-700">
        <Clock className="w-3.5 h-3.5 text-orange-500 animate-pulse" />
        <span className="text-neutral-300 font-mono tabular-nums">
          {dateTime.time}
        </span>
      </div>
    </div>
  )
}
