"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function NewsFeed() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>新闻动态</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">新闻动态页面</p>
      </CardContent>
    </Card>
  )
}
