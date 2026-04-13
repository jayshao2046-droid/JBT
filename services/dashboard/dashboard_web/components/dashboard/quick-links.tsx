"use client"

import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface QuickLink {
  title: string
  href: string
  description?: string
  icon?: React.ReactNode
}

interface QuickLinksProps {
  links?: QuickLink[]
}

const defaultLinks: QuickLink[] = [
  {
    title: "模拟交易",
    href: "/sim-trading",
    description: "查看实盘模拟交易状态",
  },
  {
    title: "回测分析",
    href: "/backtest",
    description: "策略回测与性能分析",
  },
  {
    title: "决策中心",
    href: "/decision",
    description: "智能决策与信号监控",
  },
  {
    title: "数据管理",
    href: "/data",
    description: "数据采集与质量监控",
  },
  {
    title: "系统设置",
    href: "/settings",
    description: "配置系统参数与权限",
  },
]

export function QuickLinks({ links = defaultLinks }: QuickLinksProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>快捷入口</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          {links.map((link) => (
            <Link key={link.href} href={link.href}>
              <Button
                variant="outline"
                className="w-full justify-start text-left h-auto py-3"
              >
                <div className="flex flex-col items-start gap-1">
                  <div className="font-medium">{link.title}</div>
                  {link.description && (
                    <div className="text-xs text-muted-foreground">
                      {link.description}
                    </div>
                  )}
                </div>
              </Button>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
