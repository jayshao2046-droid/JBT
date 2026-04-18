"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp } from "lucide-react"

interface ParamGridProps {
  results: Array<{
    params: Record<string, number>
    score: number
  }>
}

export function ParamGrid({ results }: ParamGridProps) {
  const topResults = results.slice(0, 10)

  return (
    <Card>
      <CardHeader>
        <CardTitle>优化结果 (Top 10)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {topResults.map((result, index) => (
            <div key={index} className="p-4 border rounded space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant={index === 0 ? "default" : "secondary"}>
                    #{index + 1}
                  </Badge>
                  <span className="font-medium text-lg">
                    得分: {result.score.toFixed(2)}
                  </span>
                  {index === 0 && <TrendingUp className="w-4 h-4 text-green-500" />}
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                {Object.entries(result.params).map(([key, value]) => (
                  <div key={key} className="p-2 bg-muted rounded">
                    <span className="text-muted-foreground">{key}:</span>{" "}
                    <span className="font-medium">{value.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
