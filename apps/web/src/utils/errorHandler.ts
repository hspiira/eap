/**
 * Error Handler Utilities
 * Comprehensive error handling for API responses and application errors
 */

import type { ErrorResponse, ApiError, FieldErrors } from '@/types/api'

/**
 * Error code to user-friendly message mapping
 */
const ERROR_MESSAGES: Record<string, string> = {
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  CONFLICT: 'This action conflicts with the current state.',
  AUTHENTICATION_ERROR: 'Please sign in to continue.',
  AUTHORIZATION_ERROR: 'You do not have permission to perform this action.',
  DOMAIN_ERROR: 'This operation cannot be completed.',
  INTERNAL_ERROR: 'An internal error occurred. Please try again later.',
  NETWORK_ERROR: 'Unable to connect to the server. Please check your connection.',
  TIMEOUT_ERROR: 'The request took too long. Please try again.',
  UNKNOWN_ERROR: 'An unexpected error occurred.',
}

/**
 * Parse API error response
 */
export function parseApiError(error: unknown): {
  message: string
  code: string
  fieldErrors?: FieldErrors
  status?: number
} {
  if (error instanceof Error && 'status' in error) {
    const apiError = error as ApiError
    return {
      message: apiError.message || ERROR_MESSAGES[apiError.code] || ERROR_MESSAGES.UNKNOWN_ERROR,
      code: apiError.code,
      fieldErrors: apiError.fieldErrors,
      status: apiError.status,
    }
  }

  if (error instanceof Error) {
    return {
      message: error.message || ERROR_MESSAGES.UNKNOWN_ERROR,
      code: 'UNKNOWN_ERROR',
    }
  }

  return {
    message: ERROR_MESSAGES.UNKNOWN_ERROR,
    code: 'UNKNOWN_ERROR',
  }
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  const parsed = parseApiError(error)
  return parsed.message
}

/**
 * Get field-specific errors
 */
export function getFieldErrors(error: unknown): FieldErrors | undefined {
  const parsed = parseApiError(error)
  return parsed.fieldErrors
}

/**
 * Check if error is retryable (5xx errors or network errors)
 */
export function isRetryableError(error: unknown): boolean {
  if (error instanceof Error && 'status' in error) {
    const apiError = error as ApiError
    return apiError.status >= 500 || apiError.status === 0
  }

  if (error instanceof TypeError) {
    return true // Network errors are retryable
  }

  return false
}

/**
 * Check if error is authentication error (401)
 */
export function isAuthenticationError(error: unknown): boolean {
  if (error instanceof Error && 'status' in error) {
    const apiError = error as ApiError
    return apiError.status === 401
  }
  return false
}

/**
 * Check if error is authorization error (403)
 */
export function isAuthorizationError(error: unknown): boolean {
  if (error instanceof Error && 'status' in error) {
    const apiError = error as ApiError
    return apiError.status === 403
  }
  return false
}

/**
 * Retry logic with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let lastError: unknown

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error

      // Don't retry if it's not a retryable error
      if (!isRetryableError(error)) {
        throw error
      }

      // Don't retry on last attempt
      if (attempt === maxRetries) {
        break
      }

      // Calculate delay with exponential backoff
      const delay = initialDelay * Math.pow(2, attempt)
      await new Promise((resolve) => setTimeout(resolve, delay))
    }
  }

  throw lastError
}

/**
 * Format error for display
 */
export function formatError(error: unknown): {
  title: string
  message: string
  details?: string
  retryable: boolean
} {
  const parsed = parseApiError(error)

  return {
    title: 'Error',
    message: parsed.message,
    details: parsed.status ? `Status: ${parsed.status}` : undefined,
    retryable: isRetryableError(error),
  }
}
