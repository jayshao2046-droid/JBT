"use client"

import { createContext, useContext, useState } from "react"

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
  // 初始值读取 html class，与内联 script 保持同步，避免水合不一致
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof document === "undefined") return "dark"
    return document.documentElement.classList.contains("dark") ? "dark" : "light"
  })

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

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
