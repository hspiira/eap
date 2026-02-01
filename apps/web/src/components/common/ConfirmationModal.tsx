/**
 * Confirmation Modal
 * Reusable confirm/cancel modal with optional reason textarea (e.g. lifecycle suspend/terminate).
 */

import { useState, useEffect, useRef, useCallback } from 'react'
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
  info: 'bg-neutral hover:bg-neutral-dark text-white border-neutral-dark',
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
  const dialogRef = useRef<HTMLDivElement>(null)
  const previousActiveElement = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (isOpen) setReason('')
  }, [isOpen])

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !loading) onClose()
    },
    [onClose, loading]
  )

  useEffect(() => {
    if (!isOpen) return
    previousActiveElement.current = document.activeElement as HTMLElement | null
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        if (!loading) onClose()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    requestAnimationFrame(() => {
      const firstFocusable = dialogRef.current?.querySelector<HTMLElement>(
        'button:not([disabled])'
      )
      firstFocusable?.focus()
    })
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      previousActiveElement.current?.focus()
    }
  }, [isOpen, onClose, loading])

  const handleConfirm = () => {
    if (requireReason && !reason.trim()) return
    void Promise.resolve(onConfirm(requireReason ? reason.trim() : undefined))
  }

  const canConfirm = !requireReason || reason.trim().length > 0

  if (!isOpen) return null

  const content = (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] p-4"
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirmation-modal-title"
        aria-describedby="confirmation-modal-message"
        className="bg-surface border border-[0.5px] border-border max-w-md w-full rounded-none"
      >
        <div className="flex items-center justify-between px-3 py-2 border-b border-[0.5px] border-border">
          <h3 id="confirmation-modal-title" className="text-base font-semibold text-text">
            {title}
          </h3>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="p-2 hover:bg-surface-hover text-text rounded-none transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4">
          <p id="confirmation-modal-message" className="text-text text-sm mb-4">{message}</p>

          {requireReason && (
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={reasonPlaceholder}
              className="w-full px-4 py-2 bg-surface border border-[0.5px] border-border rounded-none focus:outline-none focus:border-border-focus text-text mb-4 min-h-[80px]"
              rows={3}
              disabled={loading}
            />
          )}

          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 bg-surface hover:bg-surface-hover text-text border border-[0.5px] border-border rounded-none transition-colors disabled:opacity-50"
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
