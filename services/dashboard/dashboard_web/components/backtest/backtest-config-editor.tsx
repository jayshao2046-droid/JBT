"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"

export function BacktestConfigEditor() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>配置编辑器</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>策略名称</Label>
          <Input placeholder="输入策略名称" />
        </div>
        <Button className="w-full">保存配置</Button>
      </CardContent>
    </Card>
  )
}
