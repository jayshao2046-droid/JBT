"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/", label: "首页" },
  { href: "/research", label: "策略研究" },
  { href: "/import", label: "策略导入" },
  { href: "/optimizer", label: "参数调优" },
  { href: "/reports", label: "回测报告" },
]

export function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="border-b border-neutral-800 bg-neutral-950">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-bold text-white">
              JBT 决策看板
            </Link>
            <div className="flex gap-4">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "px-3 py-2 rounded text-sm font-medium transition",
                    pathname === item.href
                      ? "bg-neutral-800 text-white"
                      : "text-neutral-400 hover:text-white hover:bg-neutral-900"
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="text-sm text-neutral-500">Phase C · Decision v0.1</div>
        </div>
      </div>
    </nav>
  )
}
