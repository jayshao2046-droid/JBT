'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface DataSourceConfigEditorProps {
  onSave?: (config: any) => void
}

export function DataSourceConfigEditor({ onSave }: DataSourceConfigEditorProps) {
  const [config, setConfig] = useState({
    interval: 300,
    timeout: 30,
    retry_count: 3,
    retry_delay: 5,
    batch_size: 50,
  })

  const handleSave = () => {
    if (onSave) {
      onSave(config)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>数据源配置编辑器</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>采集频率 (秒)</Label>
          <Input
            type="number"
            value={config.interval}
            onChange={(e) => setConfig({ ...config, interval: parseInt(e.target.value) })}
          />
        </div>

        <div className="space-y-2">
          <Label>超时时间 (秒)</Label>
          <Input
            type="number"
            value={config.timeout}
            onChange={(e) => setConfig({ ...config, timeout: parseInt(e.target.value) })}
          />
        </div>

        <div className="space-y-2">
          <Label>重试次数</Label>
          <Input
            type="number"
            value={config.retry_count}
            onChange={(e) => setConfig({ ...config, retry_count: parseInt(e.target.value) })}
          />
        </div>

        <div className="space-y-2">
          <Label>重试延迟 (秒)</Label>
          <Input
            type="number"
            value={config.retry_delay}
            onChange={(e) => setConfig({ ...config, retry_delay: parseInt(e.target.value) })}
          />
        </div>

        <div className="space-y-2">
          <Label>批量大小</Label>
          <Input
            type="number"
            value={config.batch_size}
            onChange={(e) => setConfig({ ...config, batch_size: parseInt(e.target.value) })}
          />
        </div>

        <Button onClick={handleSave} className="w-full">
          保存配置
        </Button>
      </CardContent>
    </Card>
  )
}
