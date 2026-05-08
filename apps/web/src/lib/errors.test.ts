import { describe, expect, it } from 'vitest'

import {
  defaultErrorMessage,
  getLockoutSecondsRemaining,
  isAccountLocked,
  isApiError,
  isAuthError,
  isConflict,
  isForbidden,
  isNetworkError,
  isNotFound,
  isServerError,
  isTimeoutError,
  isValidationError,
} from '@/lib/errors'
import { ApiError } from '@/types/api'

function err(status: number, code = 'HTTP_ERROR', extras?: Partial<ApiError>) {
  const e = new ApiError('boom', code, status)
  if (extras?.fieldErrors) e.fieldErrors = extras.fieldErrors
  if (extras?.data) e.data = extras.data
  return e
}

describe('isApiError', () => {
  it('matches ApiError instances', () => {
    expect(isApiError(err(500))).toBe(true)
  })
  it('rejects plain errors', () => {
    expect(isApiError(new Error('plain'))).toBe(false)
  })
  it('rejects nullish and primitives', () => {
    expect(isApiError(null)).toBe(false)
    expect(isApiError(undefined)).toBe(false)
    expect(isApiError('string')).toBe(false)
    expect(isApiError(404)).toBe(false)
  })
})

describe('status guards', () => {
  it('isAuthError matches 401', () => {
    expect(isAuthError(err(401))).toBe(true)
    expect(isAuthError(err(403))).toBe(false)
  })
  it('isForbidden matches 403', () => {
    expect(isForbidden(err(403))).toBe(true)
    expect(isForbidden(err(401))).toBe(false)
  })
  it('isNotFound matches 404', () => {
    expect(isNotFound(err(404))).toBe(true)
    expect(isNotFound(err(500))).toBe(false)
  })
  it('isConflict matches 409', () => {
    expect(isConflict(err(409))).toBe(true)
    expect(isConflict(err(400))).toBe(false)
  })
  it('isValidationError matches 422 OR fieldErrors', () => {
    expect(isValidationError(err(422))).toBe(true)
    expect(isValidationError(err(400, 'X', { fieldErrors: { name: 'bad' } }))).toBe(true)
    expect(isValidationError(err(500))).toBe(false)
  })
  it('isServerError matches 5xx', () => {
    expect(isServerError(err(500))).toBe(true)
    expect(isServerError(err(503))).toBe(true)
    expect(isServerError(err(499))).toBe(false)
  })
  it('isNetworkError matches code NETWORK_ERROR', () => {
    expect(isNetworkError(err(0, 'NETWORK_ERROR'))).toBe(true)
    expect(isNetworkError(err(500))).toBe(false)
  })
  it('isTimeoutError matches code TIMEOUT_ERROR', () => {
    expect(isTimeoutError(err(0, 'TIMEOUT_ERROR'))).toBe(true)
    expect(isTimeoutError(err(0, 'NETWORK_ERROR'))).toBe(false)
  })
})

describe('isAccountLocked + getLockoutSecondsRemaining', () => {
  it('isAccountLocked matches code ACCOUNT_LOCKED', () => {
    expect(isAccountLocked(err(401, 'ACCOUNT_LOCKED'))).toBe(true)
    expect(isAccountLocked(err(401, 'AUTHENTICATION_ERROR'))).toBe(false)
  })

  it('reads retry_after_seconds when provided', () => {
    const e = err(401, 'ACCOUNT_LOCKED', { data: { retry_after_seconds: 120 } })
    expect(getLockoutSecondsRemaining(e)).toBe(120)
  })

  it('reads locked_until ISO datetime when provided', () => {
    const future = new Date(Date.now() + 90_000).toISOString()
    const e = err(401, 'ACCOUNT_LOCKED', { data: { locked_until: future } })
    const seconds = getLockoutSecondsRemaining(e)
    expect(seconds).toBeGreaterThan(80)
    expect(seconds).toBeLessThanOrEqual(91)
  })

  it('returns null when neither field present', () => {
    expect(getLockoutSecondsRemaining(err(401, 'ACCOUNT_LOCKED'))).toBeNull()
  })

  it('returns null when locked_until is in the past', () => {
    const past = new Date(Date.now() - 10_000).toISOString()
    const e = err(401, 'ACCOUNT_LOCKED', { data: { locked_until: past } })
    expect(getLockoutSecondsRemaining(e)).toBeNull()
  })

  it('returns null for non-lockout errors', () => {
    expect(getLockoutSecondsRemaining(err(401, 'AUTHENTICATION_ERROR'))).toBeNull()
  })

  it('returns null for retry_after_seconds <= 0', () => {
    const e = err(401, 'ACCOUNT_LOCKED', { data: { retry_after_seconds: 0 } })
    expect(getLockoutSecondsRemaining(e)).toBeNull()
  })
})

describe('defaultErrorMessage', () => {
  it('returns network-specific copy for NETWORK_ERROR', () => {
    expect(defaultErrorMessage(err(0, 'NETWORK_ERROR'))).toMatch(/can't reach/i)
  })
  it('returns timeout copy for TIMEOUT_ERROR', () => {
    expect(defaultErrorMessage(err(0, 'TIMEOUT_ERROR'))).toMatch(/too long/i)
  })
  it('returns auth copy for 401', () => {
    expect(defaultErrorMessage(err(401))).toMatch(/session/i)
  })
  it('returns forbidden copy for 403', () => {
    expect(defaultErrorMessage(err(403))).toMatch(/permission/i)
  })
  it('returns server copy for 5xx', () => {
    expect(defaultErrorMessage(err(500))).toMatch(/server error/i)
  })
  it('falls back to err.message for unknown ApiError', () => {
    expect(defaultErrorMessage(err(418))).toBe('boom')
  })
  it('falls back to plain Error.message', () => {
    expect(defaultErrorMessage(new Error('plain'))).toBe('plain')
  })
  it('uses provided fallback for unknown shapes', () => {
    expect(defaultErrorMessage('weird', 'fallback')).toBe('fallback')
    expect(defaultErrorMessage(undefined, 'fallback')).toBe('fallback')
  })
})
