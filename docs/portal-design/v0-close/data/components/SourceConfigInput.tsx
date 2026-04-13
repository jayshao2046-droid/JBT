'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { dataAPI } from '@/lib/data-api'

interface SourceConfigInputProps {
  sourceType: string
  onValidated?: (result: any) => void
}

export function SourceConfigInput({ sourceType, onValidated }: SourceConfigInputProps) {
  const [config, setConfig] = useState<Record<string, string>>({})
  const [validating, setValidating] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleValidate = async () => {
    setValidating(true)
    try {
      const validationResult = await dataAPI.validateSource(sourceType, config)
      setResult(validationResult)
      if (onValidated) {
        onValidated(validationResult)
      }
    } catch (error) {
      console.error('验证失败:', error)
    } finally {
      setValidating(false)
    }
  }

  const getFieldsForType = (type: string) => {
    switch (type) {
      case 'tushare':
        return [{ name: 'token', label: 'Token', type: 'password' }]
      case 'tqsdk':
        return [
          { name: 'username', label: '用户名', type: 'text' },
          { name: 'password', label: '密码', type: 'password' },
        ]
      default:
        return []
    }
  }

  const fields = getFieldsForType(sourceType)

  return (
    <Card>
      <CardHeader>
        <CardTitle>数据源配置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {fields.map((field) => (
          <div key={field.name} className="space-y-2">
            <Label htmlFor={field.name}>{field.label}</Label>
            <Input
              id={field.name}
              type={field.type}
              value={config[field.name] || ''}
              onChange={(e) => setConfig({ ...config, [field.name]: e.target.value })}
              placeholder={`请输入${field.label}`}
            />
          </div>
        ))}

        <Button onClick={handleValidate} disabled={validating} className="w-full">
          {validating ? '验证中...' : '验证配置'}
        </Button>

        {result && (
          <div className="space-y-2 pt-4 border-t">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">验证结果:</span>
              <Badge variant={result.ok ? 'default' : 'destructive'}>
                {result.ok ? '通过' : '失败'}
              </Badge>
            </div>

            {result.validation && (
              <div className="text-sm">
                <span className="text-muted-foreground">配置: </span>
                <span>{result.validation.message}</span>
              </div>
            )}

            {result.connection && (
              <div className="text-sm">
                <span className="text-muted-foreground">连接: </span>
                <span>{result.connection.message}</span>
              </div>
            )}

            {result.permissions && result.permissions.permissions && (
              <div className="text-sm">
                <span className="text-muted-foreground">权限: </span>
                <span>{result.permissions.permissions.join(', ')}</span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
