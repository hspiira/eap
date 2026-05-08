/**
 * Typed branching helpers over `ApiError`.
 *
 * Use these in catch blocks instead of inspecting `error.message`. Status codes and
 * `code` strings are stable; messages are not.
 */

import { ApiError } from '@/types/api'

export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError
}

export function isAuthError(err: unknown): err is ApiError {
  return isApiError(err) && err.status === 401
}

export function isForbidden(err: unknown): err is ApiError {
  return isApiError(err) && err.status === 403
}

export function isNotFound(err: unknown): err is ApiError {
  return isApiError(err) && err.status === 404
}

export function isConflict(err: unknown): err is ApiError {
  return isApiError(err) && err.status === 409
}

export function isValidationError(err: unknown): err is ApiError {
  return isApiError(err) && (err.status === 422 || !!err.fieldErrors)
}

export function isServerError(err: unknown): err is ApiError {
  return isApiError(err) && err.status >= 500
}

export function isNetworkError(err: unknown): err is ApiError {
  return isApiError(err) && err.code === 'NETWORK_ERROR'
}

export function isTimeoutError(err: unknown): err is ApiError {
  return isApiError(err) && err.code === 'TIMEOUT_ERROR'
}

/**
 * User-facing default message for an API error, picked by status/code rather than the
 * raw server message. Caller can still pass a `fallback` for unknown shapes.
 */
export function defaultErrorMessage(err: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (isNetworkError(err)) return "We can't reach the server right now. Check your connection and try again."
  if (isTimeoutError(err)) return 'The request took too long. Try again.'
  if (isAuthError(err)) return 'Your session has expired. Please sign in again.'
  if (isForbidden(err)) return 'You do not have permission to do that.'
  if (isNotFound(err)) return 'That item could not be found.'
  if (isServerError(err)) return 'Server error. Try again in a moment.'
  if (isApiError(err) && err.message) return err.message
  if (err instanceof Error && err.message) return err.message
  return fallback
}
