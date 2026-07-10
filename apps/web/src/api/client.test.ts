import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import apiClient from '@/api/client'
import { ApiError } from '@/types/api'

const ORIGIN = 'http://localhost:8000'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}

function emptyResponse(status: number): Response {
  return new Response(null, { status })
}

let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  apiClient.clearAuth()
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('apiClient — token + tenant headers', () => {
  it('includes Authorization header when token set', async () => {
    apiClient.setToken('tok-1')
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { ok: true }))

    await apiClient.get('/things')

    const [, init] = fetchMock.mock.calls[0]
    const headers = init.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer tok-1')
  })

  it('includes x-tenant-id header when tenant set', async () => {
    apiClient.setToken('tok-1')
    apiClient.setTenantId('t-abc')
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { ok: true }))

    await apiClient.get('/things')

    const [, init] = fetchMock.mock.calls[0]
    const headers = init.headers as Record<string, string>
    expect(headers['x-tenant-id']).toBe('t-abc')
  })

  it('skips tenant header for /auth/* endpoints', async () => {
    apiClient.setTenantId('t-abc')
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { ok: true }))

    await apiClient.post('/auth/login', { email: 'a@b' })

    const [, init] = fetchMock.mock.calls[0]
    const headers = init.headers as Record<string, string>
    expect(headers['x-tenant-id']).toBeUndefined()
  })

  it('skips tenant header for GET /tenants/:id', async () => {
    apiClient.setTenantId('t-abc')
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { id: 't1' }))

    await apiClient.get('/tenants/t1')

    const [, init] = fetchMock.mock.calls[0]
    const headers = init.headers as Record<string, string>
    expect(headers['x-tenant-id']).toBeUndefined()
  })
})

describe('apiClient — refresh-on-401', () => {
  it('attempts /auth/refresh on a 401, retries the original request, returns success', async () => {
    apiClient.setToken('old-tok')
    apiClient.setRefreshToken('refresh-1')

    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { error: 'EXPIRED', message: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: 'new-tok', refresh_token: 'refresh-2' }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }))

    const result = await apiClient.get<{ ok: boolean }>('/things')

    expect(result.ok).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(3)
    const refreshCall = fetchMock.mock.calls[1][0] as string
    expect(refreshCall).toContain('/auth/refresh')
    expect(apiClient.getToken()).toBe('new-tok')
  })

  it('clears auth and throws when refresh also fails', async () => {
    apiClient.setToken('old-tok')
    apiClient.setRefreshToken('refresh-1')
    const errorCallback = vi.fn()
    apiClient.setAuthErrorCallback(errorCallback)

    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { error: 'EXPIRED', message: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(401, { error: 'INVALID_REFRESH' }))

    await expect(apiClient.get('/things')).rejects.toBeInstanceOf(ApiError)
    expect(errorCallback).toHaveBeenCalled()
    expect(apiClient.getToken()).toBeNull()
    apiClient.setAuthErrorCallback(null)
  })

  it('does not attempt refresh on /auth/* endpoints (avoids loop)', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(401, { error: 'BAD_CREDS', message: 'bad' }))

    await expect(apiClient.post('/auth/login', { email: 'a' })).rejects.toBeInstanceOf(ApiError)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})

describe('apiClient — network errors and 5xx', () => {
  it('throws ApiError for 5xx (no retry — fetch resolved successfully)', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(500, { error: 'BOOM', message: 'boom' }))

    await expect(apiClient.get('/things')).rejects.toBeInstanceOf(ApiError)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('translates network failure (TypeError) to NETWORK_ERROR after retries', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    try {
      await apiClient.get('/things')
      throw new Error('should have thrown')
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError)
      expect((e as ApiError).code).toBe('NETWORK_ERROR')
    }
  }, 15_000)
})

describe('apiClient — error parsing', () => {
  it('parses fieldErrors out of details[]', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(422, {
        error: 'VALIDATION',
        message: 'Invalid',
        details: [
          { field: 'email', message: 'bad email' },
          { field: 'name', message: 'required' },
        ],
      }),
    )

    try {
      await apiClient.post('/things')
      throw new Error('should have thrown')
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError)
      const err = e as ApiError
      expect(err.status).toBe(422)
      expect(err.fieldErrors).toEqual({ email: 'bad email', name: 'required' })
    }
  })

  it('preserves arbitrary extra fields into err.data (e.g. retry_after_seconds)', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(401, {
        error: 'ACCOUNT_LOCKED',
        message: 'Locked',
        retry_after_seconds: 120,
      }),
    )

    try {
      await apiClient.post('/auth/login')
      throw new Error('should have thrown')
    } catch (e) {
      const err = e as ApiError
      expect(err.code).toBe('ACCOUNT_LOCKED')
      expect(err.data?.retry_after_seconds).toBe(120)
    }
  })

  it('does not put reserved fields into err.data', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(500, {
        error: 'BOOM',
        message: 'boom',
        timestamp: '2026-05-08T00:00:00Z',
        request_id: 'req-1',
        custom_field: 'preserved',
      }),
    )

    try {
      await apiClient.get('/things')
      throw new Error('should have thrown')
    } catch (e) {
      const err = e as ApiError
      expect(err.data).toEqual({ custom_field: 'preserved' })
    }
  }, 10_000)

  it('handles 204 (empty) responses gracefully', async () => {
    fetchMock.mockResolvedValueOnce(emptyResponse(204))
    const r = await apiClient.delete('/things/1')
    expect(r).toEqual({})
  })
})

describe('apiClient — clearAuth', () => {
  it('wipes token, refresh, tenant', () => {
    apiClient.setToken('t')
    apiClient.setRefreshToken('r')
    apiClient.setTenantId('tn')

    apiClient.clearAuth()

    expect(apiClient.getToken()).toBeNull()
    expect(apiClient.getRefreshToken()).toBeNull()
    expect(apiClient.getTenantId()).toBeNull()
  })
})

describe('apiClient — URL building', () => {
  it('appends tenant_id query param for non-skip endpoints', async () => {
    apiClient.setTenantId('t-1')
    fetchMock.mockResolvedValueOnce(jsonResponse(200, {}))

    await apiClient.get('/things')

    const url = fetchMock.mock.calls[0][0] as string
    expect(url).toContain('tenant_id=t-1')
    expect(url.startsWith(ORIGIN)).toBe(true)
  })

  it('forwards extra params as query string', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, {}))

    await apiClient.get('/things', { page: 2, search: 'foo bar' })

    const url = fetchMock.mock.calls[0][0] as string
    expect(url).toContain('page=2')
    expect(url).toContain('search=foo')
  })
})
