"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, CheckCircle, XCircle } from "lucide-react"
import { toast } from "sonner"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8104"

export function StrategyImport() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && (droppedFile.name.endsWith(".yaml") || droppedFile.name.endsWith(".yml"))) {
      setFile(droppedFile)
      setResult(null)
    } else {
      toast.error("请上传 YAML 文件")
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setResult(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    try {
      const content = await file.text()
      const res = await fetch(`${API_BASE}/api/v1/strategy/import/yaml`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content })
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || `${res.status} ${res.statusText}`)
      }

      const data = await res.json()
      setResult(data)
      toast.success("导入成功")
    } catch (err: any) {
      setResult({ success: false, error: err.message })
      toast.error(`导入失败: ${err.message}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <CardHeader>
        <CardTitle className="text-white">YAML 策略上传</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed border-neutral-700 rounded-lg p-12 text-center hover:border-neutral-600 transition cursor-pointer"
        >
          <Upload className="h-12 w-12 text-neutral-500 mx-auto mb-4" />
          <p className="text-neutral-400 mb-2">
            拖拽 YAML 文件到此处，或点击选择文件
          </p>
          <input
            type="file"
            accept=".yaml,.yml"
            onChange={handleFileSelect}
            className="hidden"
            id="file-input"
          />
          <label htmlFor="file-input">
            <Button variant="outline" className="cursor-pointer" asChild>
              <span>选择文件</span>
            </Button>
          </label>
        </div>

        {file && (
          <div className="flex items-center justify-between p-4 bg-neutral-800 rounded">
            <span className="text-white">{file.name}</span>
            <Button onClick={handleUpload} disabled={uploading}>
              {uploading ? "上传中..." : "上传"}
            </Button>
          </div>
        )}

        {result && (
          <Card className={`${result.success ? "bg-green-900/20 border-green-800" : "bg-red-900/20 border-red-800"}`}>
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                {result.success ? (
                  <CheckCircle className="h-5 w-5 text-green-400 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-400 mt-0.5" />
                )}
                <div className="flex-1">
                  <div className={`font-semibold ${result.success ? "text-green-400" : "text-red-400"}`}>
                    {result.success ? "导入成功" : "导入失败"}
                  </div>
                  {result.success && result.strategy && (
                    <div className="mt-2 text-sm text-neutral-300 space-y-1">
                      <div>策略名: {result.strategy.name || "N/A"}</div>
                      <div>类型: {result.strategy.type || "N/A"}</div>
                      <div>参数: {JSON.stringify(result.strategy.params || {})}</div>
                    </div>
                  )}
                  {result.error && (
                    <div className="mt-2 text-sm text-red-300">
                      {result.error}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  )
}
