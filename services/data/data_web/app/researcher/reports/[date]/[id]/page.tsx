"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { researcherApi, type ResearchReport } from "@/lib/api/researcher"
import { useParams, useRouter } from "next/navigation"
import { ResearchReport as ResearchReportComponent } from "@/components/researcher/ResearchReport"

export default function ReportDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [report, setReport] = useState<ResearchReport | null>(null)
  const [loading, setLoading] = useState(true)

  const date = params.date as string
  const segment = params.id as string

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await researcherApi.getReportByDateSegment(date, segment)
        setReport(data)
      } catch (err) {
        console.error("Failed to fetch report:", err)
      } finally {
        setLoading(false)
      }
    }

    if (date && segment) {
      fetchReport()
    }
  }, [date, segment])

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-muted-foreground">报告不存在</div>
        <Button onClick={() => router.back()} className="mt-4">
          返回
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">{report.segment} 研究报告</h1>
          <div className="text-sm text-muted-foreground mt-1">
            {new Date(report.generated_at).toLocaleString("zh-CN")} · {report.model}
          </div>
        </div>
        <Button onClick={() => router.back()}>返回</Button>
      </div>

      <ResearchReportComponent report={report} />
    </div>
  )
}
