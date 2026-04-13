'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface Template {
  id: string
  name: string
  type: string
  config: Record<string, any>
}

const PRESET_TEMPLATES: Template[] = [
  {
    id: 'futures',
    name: '期货数据',
    type: 'futures_minute',
    config: { interval: 60, timeout: 30, retry_count: 3 },
  },
  {
    id: 'stock',
    name: '股票数据',
    type: 'stock_minute',
    config: { interval: 60, timeout: 30, retry_count: 3 },
  },
  {
    id: 'news',
    name: 'RSS新闻',
    type: 'news_rss',
    config: { interval: 600, timeout: 15, retry_count: 2 },
  },
  {
    id: 'macro',
    name: '宏观数据',
    type: 'macro_global',
    config: { interval: 14400, timeout: 60, retry_count: 3 },
  },
]

interface DataSourceTemplatesProps {
  onLoad?: (template: Template) => void
}

export function DataSourceTemplates({ onLoad }: DataSourceTemplatesProps) {
  const [customTemplates, setCustomTemplates] = useState<Template[]>([])

  const handleLoad = (template: Template) => {
    if (onLoad) {
      onLoad(template)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>数据源模板</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="text-sm font-medium mb-2">预设模板</div>
          <div className="grid grid-cols-2 gap-2">
            {PRESET_TEMPLATES.map((template) => (
              <div key={template.id} className="border rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{template.name}</span>
                  <Badge variant="outline">{template.type}</Badge>
                </div>
                <Button size="sm" variant="outline" onClick={() => handleLoad(template)} className="w-full">
                  加载
                </Button>
              </div>
            ))}
          </div>
        </div>

        {customTemplates.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">自定义模板</div>
            <div className="space-y-2">
              {customTemplates.map((template) => (
                <div key={template.id} className="border rounded p-3 flex items-center justify-between">
                  <span>{template.name}</span>
                  <Button size="sm" variant="outline" onClick={() => handleLoad(template)}>
                    加载
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
