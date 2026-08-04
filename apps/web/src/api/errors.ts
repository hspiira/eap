/**
 * Response body -> ApiError normalization. Pure functions — no client state.
 */

import type { FieldErrors } from '@/types/api'
import { ApiError } from '@/types/api'

export async function parseError(response: Response): Promise<ApiError> {
  let body: unknown
  try {
    body = await response.json()
  } catch (_err) {
    body = null
  }

  const message = normalizeErrorMessageBody(body, response)
  const errorCode = normalizeErrorCodeBody(body, response.status)
  const fieldErrors = normalizeFieldErrorsBody(body)
  const data = normalizeErrorDataBody(body)

  return new ApiError(message, errorCode, response.status, fieldErrors, data)
}

/**
 * Pass through server-provided extra fields (e.g. `retry_after_seconds` for lockout)
 * minus the ones we already extract into typed fields.
 */
function normalizeErrorDataBody(body: unknown): Record<string, unknown> | undefined {
  if (!body || typeof body !== 'object') return undefined
  const b = body as Record<string, unknown>
  const reserved = new Set(['error', 'message', 'detail', 'details', 'timestamp', 'path', 'request_id'])
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(b)) {
    if (!reserved.has(k)) out[k] = v
  }
  return Object.keys(out).length > 0 ? out : undefined
}

function normalizeErrorMessageBody(body: unknown, response: Response): string {
  if (body && typeof body === 'object') {
    const b = body as Record<string, unknown>
    if (typeof b.message === 'string' && b.message) return b.message
    const detail = b.detail
    if (typeof detail === 'string' && detail) return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (first && typeof first === 'object' && first !== null && 'msg' in first && typeof (first as { msg: unknown }).msg === 'string') {
        return (first as { msg: string }).msg
      }
      return String(first)
    }
  }
  return response.statusText || 'An unknown error occurred'
}

function normalizeErrorCodeBody(body: unknown, status: number): string {
  if (body && typeof body === 'object') {
    const b = body as Record<string, unknown>
    if (typeof b.error === 'string' && b.error) return b.error
  }
  switch (status) {
    case 401:
      return 'AUTHENTICATION_ERROR'
    case 403:
      return 'AUTHORIZATION_ERROR'
    case 404:
      return 'NOT_FOUND'
    default:
      return 'HTTP_ERROR'
  }
}

function normalizeFieldErrorsBody(body: unknown): FieldErrors | undefined {
  if (!body || typeof body !== 'object') return undefined
  const b = body as Record<string, unknown>
  const details = b.details
  if (!Array.isArray(details)) return undefined
  const acc: FieldErrors = {}
  for (const d of details) {
    if (d && typeof d === 'object' && d !== null && 'field' in d && (d as { field: unknown }).field) {
      const field = String((d as { field: unknown }).field)
      const msg = typeof (d as { message?: unknown }).message === 'string'
        ? (d as { message: string }).message
        : String(d)
      acc[field] = msg
    }
  }
  return Object.keys(acc).length > 0 ? acc : undefined
}
