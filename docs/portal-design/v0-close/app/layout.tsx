import type React from "react"
import type { Metadata, Viewport } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Toaster } from "sonner"
import { ThemeProvider } from "@/components/theme-provider"
import "./globals.css"

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
})

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
})

export const metadata: Metadata = {
  title: "JBT 量化研究室",
  description: "JBT 量化研究室 - 期货量化交易统一门户系统",
}

export const viewport: Viewport = {
  themeColor: "#f97316",
  width: "device-width",
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        {/*
          在 DOM 解析阶段同步执行，读取存储的主题并立即设置 class，
          彻底消除页面导航时的黑色闪烁（FOUC）。
          必须是内联 script，不能 defer / async。
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var t = localStorage.getItem('jbt_theme');
                  var theme = (t === 'light' || t === 'dark') ? t : 'dark';
                  var root = document.documentElement;
                  if (theme === 'dark') {
                    root.classList.add('dark');
                    root.style.backgroundColor = 'hsl(0,0%,4%)';
                  } else {
                    root.classList.remove('dark');
                    root.style.backgroundColor = 'hsl(210,14%,97.3%)';
                  }
                } catch(e) {
                  document.documentElement.classList.add('dark');
                  document.documentElement.style.backgroundColor = 'hsl(0,0%,4%)';
                }
              })();
            `,
          }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased bg-background text-foreground`}
      >
        <ThemeProvider>
          {children}
          <Toaster richColors position="top-center" />
        </ThemeProvider>
      </body>
    </html>
  )
}
