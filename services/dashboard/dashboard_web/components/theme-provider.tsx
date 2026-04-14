"use client"

import { createContext, useContext, useState, useEffect } from "react"

type Theme = "dark" | "light"

interface ThemeContextValue {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "dark",
  toggleTheme: () => {},
})

export function useTheme() {
  return useContext(ThemeContext)
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // 初始值从 localStorage 读取，避免水合不一致
  const [theme, setTheme] = useState<Theme>("dark")
  const [mounted, setMounted] = useState(false)

  // 客户端挂载后读取实际主题
  useEffect(() => {
    const stored = localStorage.getItem("jbt_theme") as Theme | null
    if (stored) {
      setTheme(stored)
    }
    setMounted(true)
  }, [])

  const applyTheme = (t: Theme) => {
    const root = document.documentElement
    if (t === "dark") {
      root.classList.add("dark")
      root.style.backgroundColor = "hsl(0,0%,4%)"
    } else {
      root.classList.remove("dark")
      root.style.backgroundColor = "hsl(0,0%,100%)"
    }
  }

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark"
      applyTheme(next)
      localStorage.setItem("jbt_theme", next)
      return next
    })
  }

  // 避免水合不匹配：在挂载前不渲染子组件
  if (!mounted) {
    return null
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
