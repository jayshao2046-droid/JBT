"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Eye, EyeOff, Lock, User, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!username || !password) {
      return
    }

    setIsLoading(true)

    setTimeout(() => {
      if (username === "admin" && password === "admin123") {
        if (rememberMe) {
          localStorage.setItem("jbt_remember", "true")
        }
        localStorage.setItem("jbt_user", JSON.stringify({ username }))
        router.push("/")
      }
      setIsLoading(false)
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-background flex dark">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-neutral-900 via-neutral-950 to-neutral-900 relative overflow-hidden">
        <div className="relative z-10 flex flex-col justify-center px-16">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center">
              <Activity className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-wide">JBT 量化研究室</h1>
            </div>
          </div>

          <h2 className="text-4xl font-bold text-white mb-4 leading-tight">
            专业量化交易
            <br />
            <span className="text-orange-500">统一管理平台</span>
          </h2>

          <p className="text-neutral-400 text-lg mb-12 max-w-md leading-relaxed">
            集成模拟交易、策略回测、智能决策、数据采集四大核心模块
          </p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-b from-neutral-900 via-neutral-950 to-neutral-900">
        <div className="w-full max-w-md">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-white mb-2">欢迎登录</h2>
            <p className="text-neutral-400">请输入您的账号和密码</p>
          </div>

          <div className="glass-card p-8 rounded-xl border border-neutral-700/30 backdrop-blur-xl">
            <form onSubmit={handleLogin} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm text-neutral-300 block">账号</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                  <Input
                    type="text"
                    placeholder="请输入账号"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-12 h-12 bg-neutral-800/50 border-neutral-700/50 text-white"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm text-neutral-300 block">密码</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="请输入密码"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-12 pr-12 h-12 bg-neutral-800/50 border-neutral-700/50 text-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-400"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(checked) => setRememberMe(checked === true)}
                />
                <label htmlFor="remember" className="text-sm text-neutral-400 cursor-pointer">
                  记住登录状态
                </label>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full h-12 bg-orange-500 hover:bg-orange-600 text-white"
              >
                {isLoading ? "登录中..." : "登录"}
              </Button>
            </form>

            <div className="mt-8 text-center">
              <p className="text-neutral-600 text-sm">测试账号: admin / admin123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
