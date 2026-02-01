/**
 * useErrorHandler Hook
 * Convenience hook for handling errors with toast notifications
 */

import { useCallback } from 'react'
import { useToast } from '@/contexts/ToastContext'
import { getErrorMessage, getFieldErrors, isRetryableError } from '@/utils/errorHandler'

export function useErrorHandler() {
  const { showError, showSuccess } = useToast()

  const handleError = useCallback(
    (error: unknown, options?: { showToast?: boolean; customMessage?: string }) => {
      const message = options?.customMessage || getErrorMessage(error)
      const fieldErrors = getFieldErrors(error)

      if (options?.showToast !== false) {
        showError(message)
      }

      return {
        message,
        fieldErrors,
        retryable: isRetryableError(error),
      }
    },
    [showError]
  )

  const handleSuccess = useCallback(
    (message: string, duration?: number) => {
      showSuccess(message, duration)
    },
    [showSuccess]
  )

  return {
    handleError,
    handleSuccess,
  }
}
