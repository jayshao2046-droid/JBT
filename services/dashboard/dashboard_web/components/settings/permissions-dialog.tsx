'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ShieldCheck, ShieldAlert } from 'lucide-react'
import { PERMISSION_GROUPS, ALL_PERMISSIONS } from '@/lib/permissions'
import type { User } from '@/lib/api/auth'

interface PermissionsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  user: User | null
  onSave: (userId: number, permissions: string[]) => Promise<void>
}

export function PermissionsDialog({ open, onOpenChange, user, onSave }: PermissionsDialogProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    if (!user) return
    if (isAdmin) {
      setSelected(new Set(ALL_PERMISSIONS))
    } else {
      setSelected(new Set(user.permissions ?? []))
    }
    setError('')
  }, [user, isAdmin, open])

  const toggle = (key: string) => {
    if (isAdmin) return
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const toggleGroup = (groupKeys: string[], allSelected: boolean) => {
    if (isAdmin) return
    setSelected(prev => {
      const next = new Set(prev)
      if (allSelected) groupKeys.forEach(k => next.delete(k))
      else groupKeys.forEach(k => next.add(k))
      return next
    })
  }

  const toggleAll = () => {
    if (isAdmin) return
    setSelected(selected.size === ALL_PERMISSIONS.length ? new Set() : new Set(ALL_PERMISSIONS))
  }

  const handleSave = async () => {
    if (!user) return
    setSaving(true)
    setError('')
    try {
      await onSave(user.id, Array.from(selected))
      onOpenChange(false)
    } catch (err: unknown) {
      setError((err as { message?: string }).message ?? '保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl flex flex-col" style={{ maxHeight: '90vh' }}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-orange-500" />
            权限管理 — {user?.username}
          </DialogTitle>
          <DialogDescription className="flex items-center gap-2">
            管理该用户可访问的系统功能模块
            {isAdmin && (
              <Badge variant="outline" className="text-orange-400 border-orange-500/40 text-xs">
                管理员（全部权限锁定）
              </Badge>
            )}
          </DialogDescription>
        </DialogHeader>

        {/* 全选工具栏 */}
        {!isAdmin && (
          <div className="flex items-center justify-between px-1 pb-2 border-b border-border">
            <span className="text-sm text-muted-foreground">
              已开启{' '}
              <span className="text-foreground font-semibold">{selected.size}</span>
              {' '}/ {ALL_PERMISSIONS.length} 项权限
            </span>
            <Button variant="outline" size="sm" onClick={toggleAll} className="h-7 text-xs">
              {selected.size === ALL_PERMISSIONS.length ? '取消全选' : '全部开启'}
            </Button>
          </div>
        )}

        {isAdmin && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-500/5 border border-orange-500/20 text-sm text-orange-400">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            管理员账号始终拥有系统全部权限，无法限制。
          </div>
        )}

        {/* 权限列表 */}
        <ScrollArea className="flex-1 pr-1 overflow-y-auto" style={{ maxHeight: '52vh' }}>
          <div className="space-y-5 py-1">
            {PERMISSION_GROUPS.map(group => {
              const groupKeys = group.permissions.map(p => p.key)
              const allGroupSelected = groupKeys.every(k => selected.has(k))

              return (
                <div key={group.id}>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-semibold text-foreground tracking-wide">
                      {group.label}
                    </h4>
                    {!isAdmin && (
                      <button
                        type="button"
                        className="text-xs text-muted-foreground hover:text-orange-400 transition-colors"
                        onClick={() => toggleGroup(groupKeys, allGroupSelected)}
                      >
                        {allGroupSelected ? '取消本组' : '全选本组'}
                      </button>
                    )}
                  </div>
                  <div className="rounded-lg border border-border bg-muted/10 divide-y divide-border/50">
                    {group.permissions.map(perm => {
                      const checked = selected.has(perm.key)
                      return (
                        <div
                          key={perm.key}
                          className={`flex items-center gap-3 px-3 py-2.5 transition-colors ${
                            !isAdmin ? 'cursor-pointer hover:bg-muted/30' : ''
                          } ${checked && !isAdmin ? 'bg-orange-500/5' : ''}`}
                          onClick={() => toggle(perm.key)}
                        >
                          <Checkbox
                            id={`perm-${perm.key}`}
                            checked={checked}
                            disabled={isAdmin}
                            onCheckedChange={() => toggle(perm.key)}
                            className="shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <Label
                              htmlFor={`perm-${perm.key}`}
                              className={`text-sm font-medium ${!isAdmin ? 'cursor-pointer' : ''}`}
                            >
                              {perm.label}
                            </Label>
                            <p className="text-xs text-muted-foreground truncate">{perm.description}</p>
                          </div>
                          {checked && (
                            <Badge
                              variant="outline"
                              className="text-[10px] shrink-0 text-green-400 border-green-500/30"
                            >
                              开启
                            </Badge>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </ScrollArea>

        {error && (
          <div className="rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2">
            <p className="text-destructive text-sm">{error}</p>
          </div>
        )}

        <DialogFooter className="pt-3 border-t border-border gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {isAdmin ? '关闭' : '取消'}
          </Button>
          {!isAdmin && (
            <Button onClick={handleSave} disabled={saving}>
              {saving ? '保存中...' : '保存权限'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
