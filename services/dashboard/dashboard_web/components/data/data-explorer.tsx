"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Folder,
  FolderOpen,
  FileText,
  ChevronRight,
  ChevronDown,
  Search,
  Database,
  RefreshCw,
  AlertCircle,
  HardDrive,
  FileStack,
} from "lucide-react"
import { dataApi, StorageTotals, DirectoryEntry, TreeNode } from "@/lib/api/data"

export default function DataExplorer() {
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set())
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [fileTypeFilter, setFileTypeFilter] = useState("all")
  const [sortBy, setSortBy] = useState<"name" | "size">("name")
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [totals, setTotals] = useState<StorageTotals | null>(null)
  const [directories, setDirectories] = useState<DirectoryEntry[]>([])
  const [tree, setTree] = useState<TreeNode[]>([])

  const fetchData = async () => {
    setIsLoading(true)
    setFetchError(false)
    try {
      const data = await dataApi.getStorage(2, 20)
      setTotals(data.totals)
      setDirectories(data.directories ?? [])
      setTree(data.tree ?? [])
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const toggleFolder = (path: string) => {
    const next = new Set(expandedPaths)
    if (next.has(path)) next.delete(path)
    else next.add(path)
    setExpandedPaths(next)
  }

  const getFileExtension = (name: string) => {
    const parts = name.split(".")
    return parts.length > 1 ? parts[parts.length - 1] : ""
  }

  const matchesFilter = (node: TreeNode): boolean => {
    if (node.type === "folder") return true
    if (fileTypeFilter === "all") return true
    const ext = getFileExtension(node.name)
    if (fileTypeFilter === "csv" && ext === "csv") return true
    if (fileTypeFilter === "parquet" && ext === "parquet") return true
    if (fileTypeFilter === "json" && ext === "json") return true
    if (fileTypeFilter === "other" && !["csv", "parquet", "json"].includes(ext)) return true
    return false
  }

  const renderNode = (node: TreeNode, depth = 0): React.ReactElement | null => {
    const isExpanded = expandedPaths.has(node.path)
    const isSelected = selectedNode?.path === node.path
    const searchLower = searchTerm.toLowerCase()
    const matchesSearch = !searchTerm || node.name.toLowerCase().includes(searchLower) || node.path.toLowerCase().includes(searchLower)

    if (!matchesSearch || !matchesFilter(node)) {
      return null
    }
    return (
      <div key={node.path}>
        <div
          className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer transition-colors ${
            isSelected ? "bg-orange-500/20 text-orange-400" : "text-foreground hover:bg-muted"
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => {
            if (node.type === "folder") toggleFolder(node.path)
            setSelectedNode(node)
          }}
        >
          {node.type === "folder" ? (
            <>
              {node.children && node.children.length > 0 ? (
                isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                )
              ) : (
                <span className="w-4 flex-shrink-0" />
              )}
              {isExpanded ? <FolderOpen className="w-4 h-4 text-orange-400 flex-shrink-0" /> : <Folder className="w-4 h-4 text-muted-foreground flex-shrink-0" />}
            </>
          ) : (
            <>
              <span className="w-4 flex-shrink-0" />
              <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            </>
          )}
          <span className="text-sm truncate flex-1">{node.name}</span>
          {node.size_human && <span className="text-xs text-muted-foreground ml-auto flex-shrink-0">{node.size_human}</span>}
        </div>
        {node.type === "folder" && isExpanded && node.children && node.children.length > 0 && <div>{node.children.map((child) => renderNode(child, depth + 1))}</div>}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-12 w-64" />
        <div className="flex gap-4 h-[600px]">
          <Skeleton className="w-72" />
          <Skeleton className="flex-1" />
        </div>
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 text-muted-foreground">
        <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
        <p className="text-sm mb-4">数据加载失败，请稍后重试</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          重新加载
        </Button>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col">
      {totals && (
        <div className="flex items-center gap-6 px-6 py-3 border-b border-border bg-card/50">
          <div className="flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-orange-400" />
            <span className="text-sm text-muted-foreground">存储用量</span>
            <span className="text-sm font-bold text-foreground">{totals.size_human}</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-2">
            <FileStack className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-muted-foreground">文件数</span>
            <span className="text-sm font-bold text-foreground">{totals.files.toLocaleString()}</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-2">
            <Folder className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">目录数</span>
            <span className="text-sm font-bold text-foreground">{totals.directories}</span>
          </div>
          {totals.last_modified && (
            <>
              <div className="h-4 w-px bg-neutral-700" />
              <span className="text-xs text-muted-foreground">最近更新: {totals.last_modified}</span>
            </>
          )}
          <div className="ml-auto">
            <Button variant="outline" size="sm" className="h-8" onClick={fetchData}>
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              刷新
            </Button>
          </div>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        <div className="w-72 border-r border-border flex flex-col bg-card/50 flex-shrink-0">
          <div className="p-3 border-b border-border space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input placeholder="搜索文件/路径..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-9 h-8 text-sm" />
            </div>
            <div className="flex items-center gap-2">
              <select value={fileTypeFilter} onChange={(e) => setFileTypeFilter(e.target.value)} className="flex-1 h-8 px-2 text-xs bg-background border border-input text-foreground rounded-md">
                <option value="all">全部类型</option>
                <option value="csv">CSV</option>
                <option value="parquet">Parquet</option>
                <option value="json">JSON</option>
                <option value="other">其他</option>
              </select>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value as "name" | "size")} className="flex-1 h-8 px-2 text-xs bg-background border border-input text-foreground rounded-md">
                <option value="name">按名称</option>
                <option value="size">按大小</option>
              </select>
            </div>
          </div>
          <ScrollArea className="flex-1 p-2">
            <div className="text-xs text-muted-foreground uppercase tracking-wider px-2 py-1.5 mb-1">数据存储目录</div>
            {tree.length === 0 ? <p className="text-xs text-muted-foreground px-2 py-4">目录为空或配置未就绪</p> : tree.map((node) => renderNode(node))}
          </ScrollArea>
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          {selectedNode ? (
            <>
              <div className="p-4 border-b border-border bg-card/30">
                <div className="flex items-start gap-3">
                  {selectedNode.type === "folder" ? <FolderOpen className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" /> : <FileText className="w-6 h-6 text-muted-foreground flex-shrink-0 mt-0.5" />}
                  <div className="flex-1 min-w-0">
                    <h2 className="text-lg font-semibold text-foreground truncate">{selectedNode.name}</h2>
                    <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">{selectedNode.path}</p>
                  </div>
                  {selectedNode.suffix && (
                    <Badge variant="outline" className="text-xs flex-shrink-0">
                      {selectedNode.suffix}
                    </Badge>
                  )}
                </div>

                <div className="grid grid-cols-4 gap-3 mt-4">
                  <div className="bg-muted/50 rounded-lg p-3">
                    <p className="text-xs text-muted-foreground mb-1">大小</p>
                    <p className="text-base font-bold text-foreground font-mono">{selectedNode.size_human || "—"}</p>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <p className="text-xs text-muted-foreground mb-1">文件数</p>
                    <p className="text-base font-bold text-foreground font-mono">{selectedNode.file_count}</p>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <p className="text-xs text-muted-foreground mb-1">子目录数</p>
                    <p className="text-base font-bold text-foreground font-mono">{selectedNode.dir_count}</p>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <p className="text-xs text-muted-foreground mb-1">最近更新</p>
                    <p className="text-base font-bold text-foreground font-mono text-sm">{selectedNode.last_modified || "—"}</p>
                  </div>
                </div>
              </div>

              <div className="flex-1 flex items-center justify-center">
                <div className="text-center max-w-sm">
                  <Database className="w-12 h-12 text-neutral-700 mx-auto mb-4" />
                  <h3 className="text-base font-medium text-muted-foreground mb-2">暂无行情预览</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    行情图表和表格预览需通过行情 API 查询。
                    <br />
                    此页面仅展示目录结构与存储统计信息。
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Database className="w-16 h-16 text-neutral-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-muted-foreground mb-2">选择文件或目录</h3>
                <p className="text-sm text-muted-foreground">从左侧目录树选择节点查看存储信息</p>
              </div>
            </div>
          )}
        </div>

        <div className="w-64 border-l border-border bg-card/50 flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-border">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">顶层目录统计</h3>
          </div>
          <ScrollArea className="flex-1 p-3">
            {directories.length === 0 ? (
              <p className="text-xs text-muted-foreground py-4 text-center">暂无目录数据</p>
            ) : (
              <div className="space-y-2">
                {directories.map((dir) => (
                  <div key={dir.path} className="p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                    <div className="flex items-center gap-2 mb-2">
                      <Folder className="w-3.5 h-3.5 text-neutral-400 flex-shrink-0" />
                      <span className="text-xs font-medium text-foreground truncate">{dir.name}</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">大小</span>
                        <span className="text-foreground font-mono">{dir.size_human}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">文件数</span>
                        <span className="text-foreground font-mono">{dir.file_count}</span>
                      </div>
                      {dir.last_modified && (
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">更新</span>
                          <span className="text-muted-foreground font-mono text-xs">{dir.last_modified.split(" ")[0]}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}
