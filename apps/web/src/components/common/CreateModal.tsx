/**
 * Create Modal Component
 * Modal for create forms. Closes only via explicit Close (X) or Cancel button.
 * Does not close on overlay click or Escape.
 */

import { X } from 'lucide-react'

export interface CreateModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  /** Disable Close/Cancel during submit */
  loading?: boolean
}

export function CreateModal({
  isOpen,
  onClose,
  title,
  children,
  loading = false,
}: CreateModalProps) {
  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-safe/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-modal-title"
    >
      <div
        className="bg-calm border border-[0.5px] border-safe max-w-2xl w-full max-h-[90vh] flex flex-col shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[0.5px] border-safe shrink-0">
          <h2 id="create-modal-title" className="text-lg font-semibold text-safe">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="p-2 hover:bg-calm-dark text-safe rounded-none transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body - scrollable; form includes Submit + Cancel */}
        <div className="overflow-y-auto flex-1 p-4">{children}</div>
      </div>
    </div>
  )
}
