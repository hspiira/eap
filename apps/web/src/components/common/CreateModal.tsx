import { createPortal } from 'react-dom'
import { useEffect, useRef, useCallback } from 'react'
import { X } from 'lucide-react'

export type CreateModalSize = 'sm' | 'md' | 'lg' | 'xl'

const sizeClasses: Record<CreateModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
}

export interface CreateModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  /** Disable Close/Cancel during submit */
  loading?: boolean
  /** Modal width variant */
  size?: CreateModalSize
}

const FOCUSABLE =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

export function CreateModal({
  isOpen,
  onClose,
  title,
  children,
  loading = false,
  size = 'lg',
}: CreateModalProps) {
  const panelRef = useRef<HTMLDivElement>(null)

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loading) {
        onClose()
      }
      if (e.key !== 'Tab' || !panelRef.current) return
      const el = panelRef.current
      const focusable = Array.from(el.querySelectorAll<HTMLElement>(FOCUSABLE))
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault()
          last?.focus()
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault()
          first?.focus()
        }
      }
    },
    [loading, onClose]
  )

  useEffect(() => {
    if (!isOpen) return
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, handleKeyDown])

  useEffect(() => {
    if (!isOpen || !panelRef.current) return
    const first = panelRef.current.querySelector<HTMLElement>(FOCUSABLE)
    first?.focus()
  }, [isOpen])

  if (!isOpen) return null

  const modalContent = (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] p-4 transition-opacity duration-200 ease-out opacity-100"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) onClose()
      }}
    >
      <div
        ref={panelRef}
        className={`bg-surface border border-[0.5px] border-border ${sizeClasses[size]} w-full max-h-[90vh] flex flex-col rounded-none transition-all duration-200 ease-out opacity-100`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-3 py-2 border-b border-[0.5px] border-border shrink-0">
          <h2 id="create-modal-title" className="text-base font-semibold text-text">
            {title}
          </h2>
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

        <div className="overflow-y-auto flex-1 p-3">{children}</div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}
