"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function CommandCenterPage() {
  return (
    <div className="p-6 space-y-6">
      {/* 主仪表板网格 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 策略分配概览 */}
        <Card className="lg:col-span-4 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">策略分配</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-white font-mono">12</div>
                <div className="text-xs text-neutral-500">运行中</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white font-mono">8</div>
                <div className="text-xs text-neutral-500">待测试</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white font-mono">5</div>
                <div className="text-xs text-neutral-500">已归档</div>
              </div>
            </div>

            <div className="space-y-2">
              {[
                { id: "STR-001", name: "均线突破策略", status: "active" },
                { id: "STR-002", name: "布林带反转策略", status: "standby" },
                { id: "STR-003", name: "MACD动量策略", status: "active" },
                { id: "STR-004", name: "RSI超卖策略", status: "compromised" },
              ].map((strategy) => (
                <div
                  key={strategy.id}
                  className="flex items-center justify-between p-2 bg-neutral-800 rounded hover:bg-neutral-700 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        strategy.status === "active"
                          ? "bg-white"
                          : strategy.status === "standby"
                            ? "bg-neutral-500"
                            : "bg-red-500"
                      }`}
                    ></div>
                    <div>
                      <div className="text-xs text-white font-mono">{strategy.id}</div>
                      <div className="text-xs text-neutral-500">{strategy.name}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 回测日志 */}
        <Card className="lg:col-span-4 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">回测日志</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {[
                {
                  time: "2025/06/25 09:29",
                  strategy: "均线突破",
                  action: "完成回测",
                  contract: "螺纹钢2510",
                  result: "盈利 +12.5%",
                },
                {
                  time: "2025/06/25 08:12",
                  strategy: "MACD动量",
                  action: "开始回测",
                  contract: "沪铜2509",
                  result: null,
                },
                {
                  time: "2025/06/24 22:55",
                  strategy: "布林带反转",
                  action: "回测失败",
                  contract: "豆粕2509",
                  result: null,
                },
                {
                  time: "2025/06/24 21:33",
                  strategy: "RSI超卖",
                  action: "完成回测",
                  contract: "棕榈油2510",
                  result: "亏损 -3.2%",
                },
                {
                  time: "2025/06/24 19:45",
                  strategy: "海龟交易",
                  action: "完成回测",
                  contract: "沪金2512",
                  result: "盈利 +8.7%",
                },
              ].map((log, index) => (
                <div
                  key={index}
                  className="text-xs border-l-2 border-orange-500 pl-3 hover:bg-neutral-800 p-2 rounded transition-colors"
                >
                  <div className="text-neutral-500 font-mono">{log.time}</div>
                  <div className="text-white">
                    策略 <span className="text-orange-500 font-mono">{log.strategy}</span> {log.action}{" "}
                    <span className="text-white font-mono">{log.contract}</span>
                    {log.result && (
                      <span>
                        {" "}
                        结果: <span className={`font-mono ${log.result.includes("+") ? "text-green-400" : "text-red-400"}`}>{log.result}</span>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 实时行情监控 */}
        <Card className="lg:col-span-4 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">
              实时行情监控
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            {/* 行情指示器 */}
            <div className="relative w-32 h-32 mb-4">
              <div className="absolute inset-0 border-2 border-white rounded-full opacity-60 animate-pulse"></div>
              <div className="absolute inset-2 border border-white rounded-full opacity-40"></div>
              <div className="absolute inset-4 border border-white rounded-full opacity-20"></div>
              {/* 网格线 */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-full h-px bg-white opacity-30"></div>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-px h-full bg-white opacity-30"></div>
              </div>
            </div>

            <div className="text-xs text-neutral-500 space-y-1 w-full font-mono">
              <div className="flex justify-between">
                <span># 2025-06-17 14:23 CST</span>
              </div>
              <div className="text-white">{"> [数据源:CTP] ::: 连接中 >> ^^^ 加载行情数据"}</div>
              <div className="text-orange-500">{"> 螺纹钢2510 | 3852.00 +1.25%"}</div>
              <div className="text-white">{"> 沪铜2509 | 78650.00 -0.32%"}</div>
              <div className="text-neutral-400">
                {'> 状态 >> "...行情接收正常... 等待策略信号"'}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 收益曲线图表 */}
        <Card className="lg:col-span-8 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">
              收益曲线概览
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 relative">
              {/* 图表网格 */}
              <div className="absolute inset-0 grid grid-cols-8 grid-rows-6 opacity-20">
                {Array.from({ length: 48 }).map((_, i) => (
                  <div key={i} className="border border-neutral-700"></div>
                ))}
              </div>

              {/* 图表曲线 */}
              <svg className="absolute inset-0 w-full h-full">
                <polyline
                  points="0,120 50,100 100,110 150,90 200,95 250,85 300,100 350,80"
                  fill="none"
                  stroke="#f97316"
                  strokeWidth="2"
                />
                <polyline
                  points="0,140 50,135 100,130 150,125 200,130 250,135 300,125 350,120"
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                />
              </svg>

              {/* Y轴标签 */}
              <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-neutral-500 -ml-5 font-mono">
                <span>50万</span>
                <span>40万</span>
                <span>30万</span>
                <span>20万</span>
              </div>

              {/* X轴标签 */}
              <div className="absolute bottom-0 left-0 w-full flex justify-between text-xs text-neutral-500 -mb-6 font-mono">
                <span>2025年1月</span>
                <span>2025年6月</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 回测统计信息 */}
        <Card className="lg:col-span-4 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">回测统计</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                  <span className="text-xs text-white font-medium">盈利策略</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">高收益策略</span>
                    <span className="text-white font-bold font-mono">8</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">中等收益策略</span>
                    <span className="text-white font-bold font-mono">15</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">低收益策略</span>
                    <span className="text-white font-bold font-mono">23</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span className="text-xs text-red-500 font-medium">亏损策略</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">高风险亏损</span>
                    <span className="text-white font-bold font-mono">3</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">中等风险亏损</span>
                    <span className="text-white font-bold font-mono">7</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">低风险亏损</span>
                    <span className="text-white font-bold font-mono">12</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
