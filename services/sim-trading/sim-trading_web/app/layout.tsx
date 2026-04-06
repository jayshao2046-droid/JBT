import type React from "react"
import type { Metadata } from "next"
import { Geist_Mono as GeistMono } from "next/font/google"
import { Toaster } from "sonner"
import "./globals.css"

const geistMono = GeistMono({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "JBotQuant 模拟交易看板",
  description: "JBotQuant 量化期货模拟交易系统",
  generator: 'v0.app'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={`${geistMono.className} bg-black text-white antialiased`}>
        {children}
        <Toaster
          theme="dark"
          position="top-right"
          richColors
          toastOptions={{
            style: { fontFamily: "inherit" },
          }}
        />
      </body>
    </html>
  )
}
