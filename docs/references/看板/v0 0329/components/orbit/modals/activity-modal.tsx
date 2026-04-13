'use client'

import React from "react"

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Loader2, Check, Mail, MessageSquare, Phone, Video, Headphones, LogIn, FileText, MoreHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useOrbit } from '../orbit-provider'
import { useToastActions } from '../toast-provider'
import { type TimelineEvent, type EventType, activityTags } from '@/lib/mock-data'

interface ActivityModalProps {
  isOpen: boolean
  onClose: () => void
  accountId: string
  activity?: TimelineEvent // If provided, it's edit mode
}

const eventTypes: { type: EventType; icon: typeof Mail; label: string }[] = [
  { type: 'email', icon: Mail, label: '邮件' },
  { type: 'meeting', icon: Video, label: '会议' },
  { type: 'call', icon: Phone, label: '通话' },
  { type: 'slack', icon: MessageSquare, label: 'Slack' },
  { type: 'support', icon: Headphones, label: '支持' },
  { type: 'login', icon: LogIn, label: '登录' },
  { type: 'note', icon: FileText, label: '备注' },
  { type: 'other', icon: MoreHorizontal, label: '其他' },
]

const healthImpactOptions = [
  { value: 10, label: '积极 (+10)' },
  { value: 5, label: '略微积极 (+5)' },
  { value: 0, label: '中性 (0)' },
  { value: -5, label: '略微消极 (-5)' },
  { value: -10, label: '消极 (-10)' },
]

export function ActivityModal({ isOpen, onClose, accountId, activity }: ActivityModalProps) {
  const { addActivity, updateActivity } = useOrbit()
  const toast = useToastActions()
  const isEditMode = !!activity

  const [formData, setFormData] = useState({
    type: 'email' as EventType,
    title: '',
    description: '',
    timestamp: new Date().toISOString().slice(0, 16),
    tags: [] as string[],
    healthImpact: 0,
  })
  
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isOpen) {
      if (activity) {
        setFormData({
          type: activity.type,
          title: activity.title,
          description: activity.description,
          timestamp: activity.timestamp.toISOString().slice(0, 16),
          tags: activity.tags || [],
          healthImpact: activity.healthImpact || 0,
        })
      } else {
        setFormData({
          type: 'email',
          title: '',
          description: '',
          timestamp: new Date().toISOString().slice(0, 16),
          tags: [],
          healthImpact: 0,
        })
      }
    }
  }, [isOpen, activity])

  const toggleTag = (tag: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : [...prev.tags, tag]
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim() || !formData.description.trim()) {
      toast.error('Please fill in all required fields')
      return
    }
    
    setIsSubmitting(true)
    await new Promise(resolve => setTimeout(resolve, 200))
    
    try {
      if (isEditMode && activity) {
        updateActivity(activity.id, {
          type: formData.type,
          title: formData.title,
          description: formData.description,
          timestamp: new Date(formData.timestamp),
          tags: formData.tags.length > 0 ? formData.tags : undefined,
          healthImpact: formData.healthImpact !== 0 ? formData.healthImpact : undefined,
        })
        toast.success('Activity updated')
      } else {
        addActivity({
          accountId,
          type: formData.type,
          title: formData.title,
          description: formData.description,
          timestamp: new Date(formData.timestamp),
          tags: formData.tags.length > 0 ? formData.tags : undefined,
          healthImpact: formData.healthImpact !== 0 ? formData.healthImpact : undefined,
        })
        toast.success('Activity logged')
      }
      onClose()
    } catch {
      toast.error('Failed to save activity')
    } finally {
      setIsSubmitting(false)
    }
  }

  const isFormValid = formData.title.trim() && formData.description.trim()

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/40"
            onClick={onClose}
          />
          
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-lg mx-4 bg-background border border-border rounded-xl shadow-2xl overflow-hidden"
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 className="text-lg font-semibold text-foreground tracking-tight-ui">
                {isEditMode ? '编辑活动' : '记录活动'}
              </h2>
              <button
                onClick={onClose}
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              {/* Activity Type */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  活动类型 <span className="text-destructive">*</span>
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {eventTypes.map(({ type, icon: Icon, label }) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, type }))}
                      className={cn(
                        'flex flex-col items-center gap-1 p-3 rounded-lg border transition-all',
                        formData.type === type
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'border-border bg-muted/50 text-muted-foreground hover:bg-muted'
                      )}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-xs">{label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  标题 <span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full h-10 px-3 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  placeholder="例如：季度业务回顾"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  描述 <span className="text-destructive">*</span>
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  maxLength={500}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  placeholder="描述发生了什么..."
                />
                <p className="mt-1 text-xs text-muted-foreground text-right">
                  {formData.description.length}/500
                </p>
              </div>

              {/* Date & Time */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  日期和时间 <span className="text-destructive">*</span>
                </label>
                <input
                  type="datetime-local"
                  value={formData.timestamp}
                  onChange={(e) => setFormData(prev => ({ ...prev, timestamp: e.target.value }))}
                  className="w-full h-10 px-3 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  标签
                </label>
                <div className="flex flex-wrap gap-2">
                  {activityTags.map(tag => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleTag(tag)}
                      className={cn(
                        'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                        formData.tags.includes(tag)
                          ? 'bg-primary text-white'
                          : 'bg-muted text-muted-foreground hover:bg-muted/80'
                      )}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              {/* Health Impact */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  健康度影响
                </label>
                <select
                  value={formData.healthImpact}
                  onChange={(e) => setFormData(prev => ({ ...prev, healthImpact: parseInt(e.target.value) }))}
                  className="w-full h-10 px-3 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                >
                  {healthImpactOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </form>

            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border bg-muted/30">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-foreground bg-background border border-border rounded-lg hover:bg-muted transition-colors"
              >
                取消
              </button>
              <button
                type="submit"
                onClick={handleSubmit}
                disabled={!isFormValid || isSubmitting}
                className={cn(
                  'px-4 py-2 text-sm font-medium text-white rounded-lg transition-all flex items-center gap-2',
                  isFormValid && !isSubmitting
                    ? 'bg-primary hover:bg-primary/90'
                    : 'bg-primary/50 cursor-not-allowed'
                )}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    {isEditMode ? '更新' : '记录活动'}
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
