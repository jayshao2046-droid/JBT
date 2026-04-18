"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { researcherApi, type ReportListItem } from "@/lib/api/researcher"
import Link from "next/link"

export default function ResearcherReportsPage() {
  const [reports, setReports] = useState<{ date: string; segments: ReportListItem[] }[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchReports = async () => {
      try {
        // 获取最近 7 天的报告
        const today = new Date()
        const dates = Array.from({ length: 7 }, (_, i) => {
          const d = new Date(today)
          d.setDate(d.getDate() - i)
          return d.toISOString().split("T")[0]
        })

        const results = await Promise.allSettled(
          dates.map((date) => researcherApi.getReportsByDate(date))
        )

        const validReports = results
          .filter((r) => r.status === "fulfilled")
          .map((r: any) => r.value)
          .filter((r) => r.segments && r.segments.length > 0)

        setReports(validReports)
      } catch (err) {
        console.error("Failed to fetch reports:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchReports()
  }, [])

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">研究员报告</h1>
        <div className="text-muted-foreground">加载中...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">研究员报告</h1>
        <Button asChild>
          <Link href="/researcher">返回控制台</Link>
        </Button>
      </div>

      {reports.length === 0 ? (
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-muted-foreground">暂无报告</div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {reports.map((dayReport) => (
            <Card key={dayReport.date}>
              <CardHeader>
                <CardTitle>{dayReport.date}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {dayReport.segments.map((segment) => (
                    <Link
                      key={segment.report_id}
                      href={`/researcher/reports/${dayReport.date}/${segment.segment}`}
                    >
                      <Card className="hover:bg-accent cursor-pointer transition-colors">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-2">
                            <Badge>{segment.segment}</Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(segment.generated_at).toLocaleTimeString("zh-CN")}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {segment.report_id}
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
