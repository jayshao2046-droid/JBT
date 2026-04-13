"use client"

import { useState, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Upload, Edit2, Trash2, Play, Pause, AlertCircle, TrendingUp, CheckCircle, XCircle, AlertTriangle, RefreshCw } from "lucide-react"

export default function StrategyManagementPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStrategy, setSelectedStrategy] = useState(null)
  const [importErrors, setImportErrors] = useState([])
  const [importSuccess, setImportSuccess] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [strategies, setStrategies] = useState([
    {
      id: "STR-001",
      name: "均线突破策略",
      type: "趋势跟随",
      status: "运行中",
      contract: "螺纹钢",
      timeframe: "日线",
      parameters: {
        fastMA: 10,
        slowMA: 30,
        stopLoss: 50,
        takeProfit: 150,
      },
      performance: "+18.5%",
      lastUpdate: "2025/06/25 10:30",
      winRate: "62%",
    },
    {
      id: "STR-002",
      name: "布林带反转策略",
      type: "均值回归",
      status: "待测试",
      contract: "豆粕",
      timeframe: "4小时",
      parameters: {
        period: 20,
        stdDev: 2,
        stopLoss: 40,
        takeProfit: 80,
      },
      performance: "-2.3%",
      lastUpdate: "2025/06/24 15:45",
      winRate: "48%",
    },
    {
      id: "STR-003",
      name: "MACD动量策略",
      type: "动量",
      status: "运行中",
      contract: "沪铜",
      timeframe: "小时",
      parameters: {
        fastEMA: 12,
        slowEMA: 26,
        signalLine: 9,
        stopLoss: 30,
      },
      performance: "+25.7%",
      lastUpdate: "2025/06/25 09:15",
      winRate: "68%",
    },
    {
      id: "STR-004",
      name: "RSI超卖策略",
      type: "超卖超买",
      status: "运行中",
      contract: "沪金",
      timeframe: "15分钟",
      parameters: {
        period: 14,
        overbought: 70,
        oversold: 30,
        stopLoss: 20,
      },
      performance: "+12.1%",
      lastUpdate: "2025/06/25 11:20",
      winRate: "71%",
    },
    {
      id: "STR-005",
      name: "海龟交易策略",
      type: "趋势跟随",
      status: "已归档",
      contract: "棕榈油",
      timeframe: "日线",
      parameters: {
        breakoutPeriod: 55,
        stopATR: 2,
        positionSize: 2,
      },
      performance: "+8.9%",
      lastUpdate: "2025/06/20 08:00",
      winRate: "55%",
    },
  ])

  const fileInputRef = useRef(null)
  const multipleFileInputRef = useRef(null)

  const filteredStrategies = strategies.filter(
    (strategy) =>
      strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      strategy.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      strategy.contract.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  // YAML 解析函数
  const parseYAML = (content) => {
    const result = {}
    const lines = content.split("\n")
    
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith("#")) {
        const match = trimmed.match(/^([^:]+):\s*(.+)$/)
        if (match) {
          const key = match[1].trim()
          const value = match[2].trim()
          result[key] = isNaN(value) ? value : Number(value)
        }
      }
    }
    return result
  }

  // 参数验证
  const validateStrategy = (data) => {
    const errors = []
    const warnings = []

    if (!data.name) errors.push("策略名称为必填项")
    if (!data.type) errors.push("策略类型为必填项")
    if (!data.contract) errors.push("合约品种为必填项")
    if (!data.timeframe) errors.push("时间周期为必填项")
    
    if (data.stopLoss && data.stopLoss <= 0) errors.push("止损必须大于 0")
    if (data.takeProfit && data.takeProfit <= 0) errors.push("止盈必须大于 0")
    if (data.stopLoss && data.takeProfit && data.stopLoss >= data.takeProfit) {
      warnings.push("止损不应大于等于止盈")
    }

    return { errors, warnings, isValid: errors.length === 0 }
  }

  // 单文件导入
  const handleImportYAML = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsLoading(true)
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const data = parseYAML(content)
        const validation = validateStrategy(data)

        if (!validation.isValid) {
          setImportErrors(validation.errors)
          setImportSuccess([])
          return
        }

        const newStrategy = {
          id: `STR-${String(strategies.length + 1).padStart(3, "0")}`,
          name: data.name || "新策略",
          type: data.type || "自定义",
          status: "待测试",
          contract: data.contract || "商品期货",
          timeframe: data.timeframe || "日线",
          parameters: Object.entries(data)
            .filter(([key]) => !["name", "type", "contract", "timeframe"].includes(key))
            .reduce((acc, [key, val]) => ({ ...acc, [key]: val }), {}),
          performance: "待测试",
          lastUpdate: new Date().toLocaleString("zh-CN"),
          winRate: "待测试",
        }

        setStrategies([...strategies, newStrategy])
        setImportSuccess([`成功导入策略: ${data.name}`])
        setImportErrors([])
        setLastUpdate(new Date())
      } catch (error) {
        setImportErrors([`导入失败: ${error.message}`])
        setImportSuccess([])
      } finally {
        setIsLoading(false)
        if (fileInputRef.current) fileInputRef.current.value = ""
      }
    }
    reader.readAsText(file)
  }

  // 批量导入
  const handleBatchImport = (event) => {
    const files = event.target.files
    if (!files) return

    setIsLoading(true)
    let successCount = 0
    let errorMessages = []
    let newStrategies = [...strategies]

    Array.from(files).forEach((file) => {
      if (file.name.endsWith(".yaml") || file.name.endsWith(".yml")) {
        const reader = new FileReader()
        reader.onload = (e) => {
          try {
            const content = e.target?.result as string
            const data = parseYAML(content)
            const validation = validateStrategy(data)

            if (!validation.isValid) {
              errorMessages.push(`${file.name}: ${validation.errors.join(", ")}`)
            } else {
              const newStrategy = {
                id: `STR-${String(newStrategies.length + 1).padStart(3, "0")}`,
                name: data.name || "新策略",
                type: data.type || "自定义",
                status: "待测试",
                contract: data.contract || "商品期货",
                timeframe: data.timeframe || "日线",
                parameters: Object.entries(data)
                  .filter(([key]) => !["name", "type", "contract", "timeframe"].includes(key))
                  .reduce((acc, [key, val]) => ({ ...acc, [key]: val }), {}),
                performance: "待测试",
                lastUpdate: new Date().toLocaleString("zh-CN"),
                winRate: "待测试",
              }
              newStrategies.push(newStrategy)
              successCount++
            }
          } catch (error) {
            errorMessages.push(`${file.name}: ${error.message}`)
          }
        }
        reader.readAsText(file)
      }
    })

    setTimeout(() => {
      setStrategies(newStrategies)
      if (successCount > 0) {
        setImportSuccess([`成功导入 ${successCount} 个策略`])
      }
      if (errorMessages.length > 0) {
        setImportErrors(errorMessages)
      } else {
        setImportErrors([])
      }
      setIsLoading(false)
      setLastUpdate(new Date())
      if (multipleFileInputRef.current) multipleFileInputRef.current.value = ""
    }, 500)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.currentTarget.classList.add("bg-orange-500/20")
  }

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove("bg-orange-500/20")
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.currentTarget.classList.remove("bg-orange-500/20")
    if (multipleFileInputRef.current) {
      multipleFileInputRef.current.files = e.dataTransfer.files
      handleBatchImport({ target: multipleFileInputRef.current })
    }
  }

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsLoading(false)
    }, 500)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case "运行中":
        return "bg-white/20 text-white"
      case "待测试":
        return "bg-neutral-600/20 text-neutral-300"
      case "已归档":
        return "bg-neutral-700/20 text-neutral-400"
      default:
        return "bg-gray-600/20 text-gray-400"
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">策略管理</h1>
          <p className="text-sm text-neutral-400">导入、编辑和管理交易策略</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => fileInputRef.current?.click()}
            className="bg-orange-500 hover:bg-orange-600 text-white"
            disabled={isLoading}
          >
            <Upload className="w-4 h-4 mr-2" />
            单个导入
          </Button>
          <Button
            onClick={() => multipleFileInputRef.current?.click()}
            className="bg-orange-500 hover:bg-orange-600 text-white"
            disabled={isLoading}
          >
            <Upload className="w-4 h-4 mr-2" />
            批量导入
          </Button>
          <Button
            onClick={handleRefresh}
            variant="outline"
            className="border-neutral-700 text-neutral-400 hover:bg-neutral-800"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".yaml,.yml"
            onChange={handleImportYAML}
            className="hidden"
          />
          <input
            ref={multipleFileInputRef}
            type="file"
            accept=".yaml,.yml"
            multiple
            onChange={handleBatchImport}
            className="hidden"
          />
        </div>
      </div>

      {/* 导入状态提示 */}
      {importSuccess.length > 0 && (
        <Card className="bg-green-900/20 border-green-600/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
              <div>
                {importSuccess.map((msg, i) => (
                  <p key={i} className="text-sm text-green-300">{msg}</p>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {importErrors.length > 0 && (
        <Card className="bg-red-900/20 border-red-600/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                {importErrors.map((msg, i) => (
                  <p key={i} className="text-sm text-red-300">{msg}</p>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 拖拽导入区 */}
      <Card
        className="bg-neutral-900 border-neutral-700 border-dashed hover:border-orange-500 transition-colors cursor-pointer"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="p-8 flex flex-col items-center justify-center text-center">
          <Upload className="w-12 h-12 text-neutral-500 mb-3" />
          <p className="text-white font-medium mb-1">拖拽 YAML 策略文件到此处（支持多文件）</p>
          <p className="text-sm text-neutral-400">或点击"批量导入"按钮选择多个文件</p>
        </CardContent>
      </Card>

      {/* 搜索、刷新和统计 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card className="lg:col-span-1 bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
              <Input
                placeholder="搜索策略..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-neutral-800 border-neutral-600 text-white placeholder-neutral-400"
              />
            </div>
            <p className="text-xs text-neutral-500 mt-2">更新于: {lastUpdate.toLocaleTimeString("zh-CN")}</p>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">运行中</p>
                <p className="text-2xl font-bold text-white font-mono">
                  {strategies.filter((s) => s.status === "运行中").length}
                </p>
              </div>
              <Play className="w-8 h-8 text-white" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">待测试</p>
                <p className="text-2xl font-bold text-orange-500 font-mono">
                  {strategies.filter((s) => s.status === "待测试").length}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">平均胜率</p>
                <p className="text-2xl font-bold text-green-400 font-mono">61%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 策略列表 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">
            策略列表 ({filteredStrategies.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">策略ID</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">策略名称</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">类型</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">品种</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">周期</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">状态</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">胜率</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">收益</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredStrategies.length > 0 ? (
                  filteredStrategies.map((strategy, index) => (
                    <tr
                      key={strategy.id}
                      className={`border-b border-neutral-800 hover:bg-neutral-800 transition-colors cursor-pointer ${
                        index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-850"
                      }`}
                      onClick={() => setSelectedStrategy(strategy)}
                    >
                      <td className="py-3 px-4 text-sm text-white font-mono">{strategy.id}</td>
                      <td className="py-3 px-4 text-sm text-white">{strategy.name}</td>
                      <td className="py-3 px-4 text-sm text-neutral-300">{strategy.type}</td>
                      <td className="py-3 px-4 text-sm text-neutral-300">{strategy.contract}</td>
                      <td className="py-3 px-4 text-sm text-neutral-300">{strategy.timeframe}</td>
                      <td className="py-3 px-4">
                        <span className={`text-xs px-2 py-1 rounded tracking-wider ${getStatusColor(strategy.status)}`}>
                          {strategy.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-white font-mono">{strategy.winRate}</td>
                      <td className={`py-3 px-4 text-sm font-mono ${strategy.performance.includes("+") ? "text-green-400" : "text-red-400"}`}>
                        {strategy.performance}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-neutral-400 hover:text-orange-500 h-8 w-8"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedStrategy(strategy)
                            }}
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-neutral-400 hover:text-red-500 h-8 w-8"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="9" className="py-8 px-4 text-center">
                      <p className="text-neutral-400">未找到匹配的策略</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 策略详情模态框 */}
      {selectedStrategy && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedStrategy(null)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setSelectedStrategy(null)
          }}
        >
          <Card
            className="bg-neutral-900 border-neutral-700 w-full max-w-3xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader className="flex flex-row items-center justify-between sticky top-0 bg-neutral-900 border-b border-neutral-700">
              <div>
                <CardTitle className="text-lg font-bold text-white tracking-wider">
                  {selectedStrategy.name}
                </CardTitle>
                <p className="text-sm text-neutral-400 font-mono">{selectedStrategy.id}</p>
              </div>
              <Button
                variant="ghost"
                onClick={() => setSelectedStrategy(null)}
                className="text-neutral-400 hover:text-white"
              >
                ✕
              </Button>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              {/* 基本信息 */}
              <div>
                <h3 className="text-sm font-medium text-neutral-300 tracking-wider mb-4">基本信息</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">类型</p>
                    <p className="text-sm text-white">{selectedStrategy.type}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">品种</p>
                    <p className="text-sm text-white">{selectedStrategy.contract}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">周期</p>
                    <p className="text-sm text-white">{selectedStrategy.timeframe}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">状态</p>
                    <span className={`text-xs px-2 py-1 rounded tracking-wider ${getStatusColor(selectedStrategy.status)}`}>
                      {selectedStrategy.status}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">胜率</p>
                    <p className="text-sm text-white">{selectedStrategy.winRate}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">收益</p>
                    <p className={`text-sm font-mono ${selectedStrategy.performance.includes("+") ? "text-green-400" : "text-red-400"}`}>
                      {selectedStrategy.performance}
                    </p>
                  </div>
                </div>
              </div>

              {/* 策略参数 */}
              <div>
                <h3 className="text-sm font-medium text-neutral-300 tracking-wider mb-4">策略参数</h3>
                <div className="bg-neutral-800 rounded border border-neutral-700 p-4 space-y-3">
                  {Object.entries(selectedStrategy.parameters).length > 0 ? (
                    Object.entries(selectedStrategy.parameters).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-sm text-neutral-400">{key}</span>
                        <Input
                          type="number"
                          defaultValue={value}
                          className="w-24 bg-neutral-700 border-neutral-600 text-white text-right"
                        />
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-neutral-500">无参数配置</p>
                  )}
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="flex gap-3 pt-4">
                <Button className="bg-orange-500 hover:bg-orange-600 text-white flex-1">
                  保存修改
                </Button>
                <Button
                  variant="outline"
                  className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-300 bg-transparent flex-1"
                >
                  运行回测
                </Button>
                <Button
                  variant="outline"
                  className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-300 bg-transparent flex-1"
                  onClick={() => setSelectedStrategy(null)}
                >
                  关闭
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
