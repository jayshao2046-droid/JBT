"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Eye, EyeOff, Lock, User, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { toast } from "sonner"

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
      toast.error("请输入账号和密码")
      return
    }

    setIsLoading(true)

    // 模拟登录验证
    setTimeout(() => {
      if (username === "admin" && password === "admin123") {
        toast.success("登录成功")
        if (rememberMe) {
          localStorage.setItem("jbt_remember", "true")
        }
        localStorage.setItem("jbt_user", username)
        router.push("/")
      } else {
        toast.error("账号或密码错误")
      }
      setIsLoading(false)
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-background flex dark">
      {/* 左侧装饰区域 */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-neutral-900 via-neutral-950 to-neutral-900 relative overflow-hidden">
        {/* 蜂窝背景 */}
        <div className="absolute inset-0 opacity-30">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="honeycomb" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M30,0 L60,17.32 L60,51.96 L30,69.28 L0,51.96 L0,17.32 Z" fill="none" stroke="hsl(0,0%,40%)" strokeWidth="0.5" opacity="0.3"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#honeycomb)" />
          </svg>
        </div>

        {/* 背景光晕 */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-20 w-72 h-72 bg-orange-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/3 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl" />
        </div>

        {/* 内容 */}
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
            集成模拟交易、策略回测、智能决策、数据采集四大核心模块，
            为您提供完整的期货量化交易解决方案。
          </p>

          {/* 特性列表 */}
          <div className="grid grid-cols-2 gap-6">
            {[
              { label: "模拟交易", desc: "实时行情与风控" },
              { label: "策略回测", desc: "高性能回测引擎" },
              { label: "智能决策", desc: "多因子信号系统" },
              { label: "数据采集", desc: "多源数据整合" },
            ].map((item) => (
              <div
                key={item.label}
                className="p-4 glass-card rounded-lg"
              >
                <h3 className="text-white font-medium mb-1">{item.label}</h3>
                <p className="text-neutral-500 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 右侧登录表单 */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-b from-neutral-900 via-neutral-950 to-neutral-900 relative overflow-hidden">
        {/* 背景蜂窝纹理 */}
        <div className="absolute inset-0 opacity-20">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="honeycomb2" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M30,0 L60,17.32 L60,51.96 L30,69.28 L0,51.96 L0,17.32 Z" fill="none" stroke="hsl(0,0%,40%)" strokeWidth="0.5" opacity="0.3"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#honeycomb2)" />
          </svg>
        </div>

        <div className="w-full max-w-md relative z-10">
          {/* 移动端 Logo */}
          <div className="lg:hidden flex items-center gap-3 mb-12 justify-center">
            <div className="w-10 h-10 bg-orange-500 rounded-xl flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">JBT 量化研究室</h1>
            </div>
          </div>

          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-white mb-2">欢迎登录</h2>
            <p className="text-neutral-400">请输入您的账号和密码</p>
          </div>

          {/* 表单卡片 */}
          <div className="glass-card p-8 rounded-xl border border-neutral-700/30 backdrop-blur-xl">
            <form onSubmit={handleLogin} className="space-y-6">
              {/* 用户名输入 */}
              <div className="space-y-2">
                <label className="text-sm text-neutral-300 block">账号</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                  <Input
                    type="text"
                    placeholder="请输入账号"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-12 h-12 bg-neutral-800/50 border-neutral-700/50 text-white placeholder:text-neutral-500 focus:border-orange-500 focus:ring-orange-500/20 backdrop-blur-sm"
                  />
                </div>
              </div>

              {/* 密码输入 */}
              <div className="space-y-2">
                <label className="text-sm text-neutral-300 block">密码</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="请输入密码"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-12 pr-12 h-12 bg-neutral-800/50 border-neutral-700/50 text-white placeholder:text-neutral-500 focus:border-orange-500 focus:ring-orange-500/20 backdrop-blur-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-300"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {/* 记住登录 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="remember"
                    checked={rememberMe}
                    onCheckedChange={(checked) => setRememberMe(checked === true)}
                    className="border-neutral-600 data-[state=checked]:bg-orange-500 data-[state=checked]:border-orange-500"
                  />
                  <label
                    htmlFor="remember"
                    className="text-sm text-neutral-400 cursor-pointer"
                  >
                    记住登录状态
                  </label>
                </div>
                <button
                  type="button"
                  className="text-sm text-orange-500 hover:text-orange-400"
                >
                  忘记密码？
                </button>
              </div>

              {/* 登录按钮 */}
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full h-12 bg-orange-500 hover:bg-orange-600 text-white font-medium text-base"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    登录中...
                  </span>
                ) : (
                  "登录"
                )}
              </Button>
            </form>

            {/* 底部提示 */}
            <div className="mt-8 text-center">
              <p className="text-neutral-600 text-sm">
                测试账号: admin / admin123
              </p>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-neutral-800 text-center">
            <p className="text-neutral-600 text-xs">
              JBT 量化研究室 v1.0.0
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
