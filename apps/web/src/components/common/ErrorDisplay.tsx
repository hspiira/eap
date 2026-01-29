/**
 * Error Display Component
 * Displays error messages with optional retry functionality
 */

import { AlertCircle, RefreshCw } from 'lucide-react'
import { formatError } from '@/utils/errorHandler'
import type { FieldErrors } from '@/api/types'

interface ErrorDisplayProps {
  error: unknown
  onRetry?: () => void
  fieldErrors?: FieldErrors
  className?: string
}

export function ErrorDisplay({ error, onRetry, fieldErrors, className = '' }: ErrorDisplayProps) {
  const formatted = formatError(error)

  return (
    <div className={`p-4 bg-danger-light border-[0.5px] border-danger rounded-none ${className}`}>
      <div className="flex items-start gap-3">
        <AlertCircle size={20} className="text-danger flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-safe font-semibold mb-1">{formatted.title}</h3>
          <p className="text-safe text-sm mb-2">{formatted.message}</p>
          
          {formatted.details && (
            <p className="text-safe-light text-xs mb-2">{formatted.details}</p>
          )}

          {fieldErrors && Object.keys(fieldErrors).length > 0 && (
            <div className="mt-3 space-y-1">
              {Object.entries(fieldErrors).map(([field, message]) => (
                <p key={field} className="text-safe text-xs">
                  <span className="font-medium">{field}:</span> {message}
                </p>
              ))}
            </div>
          )}

          {formatted.retryable && onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 px-4 py-2 bg-natural hover:bg-natural-dark text-white text-sm font-medium rounded-none transition-colors flex items-center gap-2"
            >
              <RefreshCw size={16} />
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
