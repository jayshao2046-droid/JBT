'use client'

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, XCircle, AlertCircle, Info, X, Loader2 } from 'lucide-react'

// Extended Toast type that supports both old (message) and new (title+description) patterns
export interface Toast {
  id: string
  type: 'success' | 'error' | 'info' | 'warning' | 'loading'
  message?: string
  title?: string
  description?: string
  duration?: number
}

interface ToastContextValue {
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// Convenience methods
export function useToastActions() {
  const { addToast } = useToast()
  
  return {
    success: (message: string) => addToast({ type: 'success', message }),
    error: (message: string) => addToast({ type: 'error', message }),
    warning: (message: string) => addToast({ type: 'warning', message }),
    info: (message: string) => addToast({ type: 'info', message }),
    loading: (title: string, description?: string) => addToast({ type: 'loading', title, description, duration: 999999 }),
  }
}

const toastIcons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
  loading: Loader2,
}

const toastStyles = {
  success: 'bg-emerald-950/80 border-emerald-800/50 text-emerald-200',
  error: 'bg-red-950/80 border-red-800/50 text-red-200',
  warning: 'bg-amber-950/80 border-amber-800/50 text-amber-200',
  info: 'bg-blue-950/80 border-blue-800/50 text-blue-200',
  loading: 'bg-card border-border text-foreground',
}

const iconStyles = {
  success: 'text-emerald-400',
  error: 'text-red-400',
  warning: 'text-amber-400',
  info: 'text-blue-400',
  loading: 'text-muted-foreground animate-spin',
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
  const Icon = toastIcons[toast.type]
  // Support both old (message) and new (title + description) patterns
  const displayTitle = toast.title ?? toast.message
  const displayDescription = toast.description

  return (
    <motion.div
      initial={{ opacity: 0, x: 50, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 50, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className={`
        flex items-start gap-3 p-4 rounded-lg border shadow-lg
        min-w-[320px] max-w-[420px]
        ${toastStyles[toast.type]}
      `}
    >
      <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${iconStyles[toast.type]}`} />
      <div className="flex-1 min-w-0">
        {displayTitle && <p className="text-sm font-medium leading-relaxed">{displayTitle}</p>}
        {displayDescription && <p className="text-xs opacity-75 mt-0.5 leading-relaxed">{displayDescription}</p>}
      </div>
      <button
        onClick={onRemove}
        className="flex-shrink-0 p-1 rounded hover:bg-white/10 transition-colors"
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4 opacity-60" />
      </button>
    </motion.div>
  )
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const newToast: Toast = { ...toast, id }
    
    setToasts(prev => {
      // Keep max 3 toasts
      const updated = [...prev, newToast]
      if (updated.length > 3) {
        return updated.slice(-3)
      }
      return updated
    })
    
    // Auto-dismiss after duration (default 3 seconds)
    const duration = toast.duration ?? 3000
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, duration)
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      
      {/* Toast Container */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        <AnimatePresence mode="popLayout">
          {toasts.map(toast => (
            <ToastItem
              key={toast.id}
              toast={toast}
              onRemove={() => removeToast(toast.id)}
            />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}
