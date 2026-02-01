/**
 * Confirmation Modal
 * Reusable confirm/cancel modal with optional reason textarea (e.g. lifecycle suspend/terminate).
 */

import { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

export interface ConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (reason?: string) => void | Promise<void>
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  /** When true, show a required reason textarea and pass its value to onConfirm */
  requireReason?: boolean
  reasonPlaceholder?: string
  loading?: boolean
  variant?: 'danger' | 'warning' | 'info'
}

const variantColors = {
  danger: 'bg-danger hover:bg-danger-dark text-white border-danger-dark',
  warning: 'bg-nurturing hover:bg-nurturing-dark text-white border-nurturing-dark',
  info: 'bg-safe hover:bg-safe-dark text-white border-safe-dark',
}

export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  requireReason = false,
  reasonPlaceholder = 'Enter reason...',
  loading = false,
  variant = 'warning',
}: ConfirmationModalProps) {
  const [reason, setReason] = useState('')

  useEffect(() => {
    if (isOpen) setReason('')
  }, [isOpen])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loading) onClose()
    },
    [loading, onClose]
  )

  useEffect(() => {
    if (!isOpen) return
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, handleKeyDown])

  const handleConfirm = () => {
    if (requireReason && !reason.trim()) return
    void Promise.resolve(onConfirm(requireReason ? reason.trim() : undefined))
  }

  const canConfirm = !requireReason || reason.trim().length > 0

  if (!isOpen) return null

  const content = (
    <div
      className="fixed inset-0 bg-safe/50 flex items-center justify-center z-[100] p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmation-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) onClose()
      }}
    >
      <div
        className="bg-white border border-[0.5px] border-safe/30 max-w-md w-full rounded-none"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-3 py-2 border-b border-[0.5px] border-safe/30">
          <h3 id="confirmation-modal-title" className="text-base font-semibold text-safe">
            {title}
          </h3>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="p-2 hover:bg-gray-100 text-safe rounded-none transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4">
          <p className="text-safe text-sm mb-4">{message}</p>

          {requireReason && (
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={reasonPlaceholder}
              className="w-full px-4 py-2 bg-white border border-[0.5px] border-safe/30 rounded-none focus:outline-none focus:border-natural text-safe mb-4 min-h-[80px]"
              rows={3}
              disabled={loading}
            />
          )}

          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 bg-white hover:bg-gray-100 text-safe border border-[0.5px] border-safe/30 rounded-none transition-colors disabled:opacity-50"
            >
              {cancelLabel}
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={loading || !canConfirm}
              className={`px-4 py-2 rounded-none transition-colors disabled:opacity-50 ${variantColors[variant]}`}
            >
              {loading ? 'Processing...' : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  return createPortal(content, document.body)
}
