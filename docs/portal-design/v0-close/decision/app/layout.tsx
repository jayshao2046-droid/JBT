import type React from "react"
import type { Metadata } from "next"
import { Navbar } from "@/components/Navbar"
import "./globals.css"

export const metadata: Metadata = {
  title: "JBT 决策看板",
  description: "JBT 量化交易决策端控制台",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" className="bg-neutral-950">
      <body className="bg-neutral-950 text-white antialiased">
        <Navbar />
        {children}
      </body>
    </html>
  )
}
