"use client";

import { useState, useEffect } from "react";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // 检查本地存储或系统偏好
    const savedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    
    if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
      setIsDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);
    
    if (newIsDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  if (!mounted) {
    return (
      <button className="w-10 h-10 rounded-md flex items-center justify-center bg-secondary/40">
        <Sun className="w-5 h-5 text-muted-foreground" />
      </button>
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        "w-10 h-10 rounded-md flex items-center justify-center transition-colors",
        "hover:bg-secondary/60 bg-secondary/40"
      )}
      title={isDark ? "切换到日间模式" : "切换到夜间模式"}
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-warning" strokeWidth={1.5} />
      ) : (
        <Moon className="w-5 h-5 text-muted-foreground" strokeWidth={1.5} />
      )}
    </button>
  );
}
