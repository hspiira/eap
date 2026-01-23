/**
 * Toast Notification Component
 * Displays temporary success/error messages
 */

import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { useEffect } from 'react'

export type ToastType = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  message: string
  type: ToastType
  duration?: number
}

interface ToastProps {
  toast: Toast
  onClose: (id: string) => void
}

export function ToastItem({ toast, onClose }: ToastProps) {
  useEffect(() => {
    const duration = toast.duration ?? 5000
    const timer = setTimeout(() => {
      onClose(toast.id)
    }, duration)

    return () => clearTimeout(timer)
  }, [toast.id, toast.duration, onClose])

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle size={20} className="text-natural" />
      case 'error':
        return <AlertCircle size={20} className="text-nurturing" />
      case 'info':
        return <Info size={20} className="text-safe" />
    }
  }

  const getBgColor = () => {
    switch (toast.type) {
      case 'success':
        return 'bg-natural-light border-natural'
      case 'error':
        return 'bg-nurturing-light border-nurturing'
      case 'info':
        return 'bg-calm border-safe'
    }
  }

  return (
    <div
      className={`p-4 border-[0.5px] rounded-none shadow-lg flex items-start gap-3 min-w-[300px] max-w-md ${getBgColor()}`}
    >
      <div className="flex-shrink-0 mt-0.5">{getIcon()}</div>
      <p className="flex-1 text-safe text-sm">{toast.message}</p>
      <button
        onClick={() => onClose(toast.id)}
        className="flex-shrink-0 text-safe hover:text-natural transition-colors"
        aria-label="Close"
      >
        <X size={18} />
      </button>
    </div>
  )
}
