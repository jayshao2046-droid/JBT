"use client"

import { useState, useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"
import { AppSidebar } from "./app-sidebar"
import { AppHeader } from "./app-header"
import { AnimatedGridBg } from "./animated-grid-bg"
import { cn } from "@/lib/utils"

interface MainLayoutProps {
  children: React.ReactNode
  title?: string
  subtitle?: string
  onRefresh?: () => void
  isRefreshing?: boolean
  lastUpdate?: Date | null
}

export function MainLayout({
  children,
  title = "总控台",
  subtitle,
  onRefresh,
  isRefreshing,
  lastUpdate,
}: MainLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const pathname = usePathname()
  const router = useRouter()

  // Wait for client mount to avoid SSR/hydration mismatch
  useEffect(() => {
    setMounted(true)
  }, [])

  // Check auth on mount (only client-side)
  useEffect(() => {
    if (!mounted) return
    const user = localStorage.getItem("jbt_user")
    if (!user && pathname !== "/login") {
      router.push("/login")
    }
  }, [mounted, pathname, router])

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [pathname])

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden md:block shrink-0">
        <AppSidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div
        className={cn(
          "fixed left-0 top-0 h-full z-50 md:hidden transition-transform duration-300",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <AppSidebar collapsed={false} onToggle={() => setMobileMenuOpen(false)} />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <AppHeader
          title={title}
          subtitle={subtitle}
          onRefresh={onRefresh}
          isRefreshing={isRefreshing}
          lastUpdate={lastUpdate}
          onMenuToggle={() => setMobileMenuOpen(true)}
        />
        <main className="flex-1 overflow-auto bg-background relative">
          <AnimatedGridBg />
          <div className="relative z-10">{children}</div>
        </main>
      </div>
    </div>
  )
}
