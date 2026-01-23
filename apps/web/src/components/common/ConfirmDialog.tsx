/**
 * Confirm Dialog Component
 * Reusable confirmation modal for destructive actions
 */

import { X, AlertTriangle } from 'lucide-react'

export interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'warning' | 'info'
  loading?: boolean
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  loading = false,
}: ConfirmDialogProps) {
  if (!isOpen) return null

  const variantColors = {
    danger: {
      bg: 'bg-natural-dark',
      text: 'text-white',
      border: 'border-natural-dark',
    },
    warning: {
      bg: 'bg-nurturing',
      text: 'text-white',
      border: 'border-nurturing-dark',
    },
    info: {
      bg: 'bg-safe',
      text: 'text-white',
      border: 'border-safe-dark',
    },
  }

  const colors = variantColors[variant]

  const handleConfirm = () => {
    onConfirm()
  }

  return (
    <div className="fixed inset-0 bg-safe/50 flex items-center justify-center z-50 p-4">
      <div className="bg-calm border border-[0.5px] border-safe max-w-md w-full">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <AlertTriangle
                size={24}
                className={variant === 'danger' ? 'text-natural-dark' : 'text-nurturing'}
              />
              <h3 className="text-lg font-semibold text-safe">{title}</h3>
            </div>
            <button
              onClick={onClose}
              disabled={loading}
              className="p-1 hover:bg-calm transition-colors rounded-none text-safe"
              aria-label="Close"
            >
              <X size={20} />
            </button>
          </div>

          {/* Message */}
          <p className="text-safe mb-6">{message}</p>

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 bg-calm hover:bg-calm-dark text-safe border border-[0.5px] border-safe rounded-none transition-colors disabled:opacity-50"
            >
              {cancelLabel}
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className={`px-4 py-2 ${colors.bg} hover:opacity-90 ${colors.text} rounded-none transition-colors disabled:opacity-50`}
            >
              {loading ? 'Processing...' : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
