"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { ResearchReport as ResearchReportType, FuturesSymbolData, StockMover } from "@/lib/api/researcher"

interface ResearchReportProps {
  report: ResearchReportType
}

export function ResearchReport({ report }: ResearchReportProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>报告概览</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">报告 ID</div>
              <div className="font-mono text-sm">{report.report_id}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">时段</div>
              <Badge>{report.segment}</Badge>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">生成时间</div>
              <div className="text-sm">
                {new Date(report.generated_at).toLocaleString("zh-CN")}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">模型</div>
              <div className="text-sm">{report.model}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="futures" className="space-y-4">
        <TabsList>
          <TabsTrigger value="futures">期货市场</TabsTrigger>
          <TabsTrigger value="stocks">股票市场</TabsTrigger>
        </TabsList>

        <TabsContent value="futures" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>期货市场综述</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-muted-foreground mb-2">
                    覆盖品种：{report.futures_summary.symbols_covered} 个
                  </div>
                  <div className="prose prose-sm max-w-none">
                    {report.futures_summary.market_overview}
                  </div>
                </div>

                {Object.keys(report.futures_summary.symbols).length > 0 && (
                  <div className="space-y-2">
                    <div className="font-medium">品种详情</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(report.futures_summary.symbols).map(([symbol, data]: [string, FuturesSymbolData]) => (
                        <Card key={symbol}>
                          <CardContent className="p-4">
                            <div className="font-medium mb-2">{symbol}</div>
                            <div className="text-sm text-muted-foreground">
                              {JSON.stringify(data, null, 2)}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stocks" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>股票市场综述</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-muted-foreground mb-2">
                    覆盖股票：{report.stocks_summary.symbols_covered} 只
                  </div>
                  <div className="prose prose-sm max-w-none">
                    {report.stocks_summary.market_overview}
                  </div>
                </div>

                {report.stocks_summary.top_movers.length > 0 && (
                  <div className="space-y-2">
                    <div className="font-medium">异动股票</div>
                    <div className="space-y-2">
                      {report.stocks_summary.top_movers.map((mover: StockMover, idx: number) => (
                        <Card key={idx}>
                          <CardContent className="p-4">
                            <div className="text-sm text-muted-foreground">
                              {JSON.stringify(mover, null, 2)}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
