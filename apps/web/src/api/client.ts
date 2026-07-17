/**
 * API Client
 * Centralized API client with authentication, tenant context, and error handling.
 * API spec: https://eap-ten.vercel.app/redoc (same API when running locally).
 */

import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'
import type {
  ApiClientConfig,
  FieldErrors,
  QueryParams,
  RequestOptions,
} from '@/types/api'
import { ApiError } from '@/types/api'

const DEFAULT_TIMEOUT = 30000 // 30 seconds
const DEFAULT_RETRY_ATTEMPTS = 3
const DEFAULT_RETRY_DELAY = 1000 // 1 second

function useCookies(): boolean {
  return import.meta.env.VITE_AUTH_USE_COOKIES === 'true'
}

type AuthErrorCallback = () => void

class ApiClient {
  private baseUrl: string
  private timeout: number
  private retryAttempts: number
  private retryDelay: number
  private onAuthError: AuthErrorCallback | null = null
  private refreshPromise: Promise<boolean> | null = null

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '') // Remove trailing slash
    this.timeout = config.timeout ?? DEFAULT_TIMEOUT
    this.retryAttempts = config.retryAttempts ?? DEFAULT_RETRY_ATTEMPTS
    this.retryDelay = config.retryDelay ?? DEFAULT_RETRY_DELAY
  }

  /**
   * Set callback for auth errors (401). Called after clearing auth.
   * Use this to handle navigation in React context.
   */
  setAuthErrorCallback(callback: AuthErrorCallback | null): void {
    this.onAuthError = callback
  }

  /**
   * Set authentication token. Optionally pass `expiresInSeconds` to record when the token
   * expires; AppBootstrap uses that to schedule a silent refresh.
   */
  setToken(token: string | null, expiresInSeconds?: number): void {
    useAuthStore.getState().setToken(token, expiresInSeconds)
  }

  /** Epoch ms when the current access token expires, or null if unknown. */
  getTokenExpiresAt(): number | null {
    if (useCookies()) return null
    return useAuthStore.getState().tokenExpiresAt
  }

  setCsrfToken(token: string | null): void {
    useAuthStore.getState().setCsrfToken(token)
  }
  getCsrfToken(): string | null {
    return useAuthStore.getState().csrfToken
  }

  getToken(): string | null {
    return useAuthStore.getState().token
  }

  setRefreshToken(token: string | null): void {
    useAuthStore.getState().setRefreshToken(token)
  }

  getRefreshToken(): string | null {
    return useAuthStore.getState().refreshToken
  }

  /**
   * Public proactive refresh. Same wire as the reactive 401 path but exposed so a scheduler
   * can rotate the access token before it expires.
   */
  async refreshAccessToken(): Promise<boolean> {
    return this.tryRefreshToken()
  }

  private async tryRefreshToken(): Promise<boolean> {
    if (this.refreshPromise) return this.refreshPromise

    this.refreshPromise = (async () => {
      if (useCookies()) {
        try {
          const response = await fetch(`${this.baseUrl}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
            credentials: 'include',
          })
          if (!response.ok) return false
          // BE may rotate the CSRF token on refresh; honor it if returned.
          try {
            const data = await response.clone().json()
            if (data && typeof data.csrf_token === 'string') this.setCsrfToken(data.csrf_token)
          } catch (_err) {
            // body may be empty — fine
          }
          return true
        } catch (_err) {
          return false
        } finally {
          this.refreshPromise = null
        }
      }

      const refreshToken = this.getRefreshToken()
      if (!refreshToken) return false

      try {
        const response = await fetch(`${this.baseUrl}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })

        if (!response.ok) return false

        const data = await response.json()
        const expiresIn =
          typeof data.expires_in === 'number' ? data.expires_in : undefined
        this.setToken(data.access_token, expiresIn)
        this.setRefreshToken(data.refresh_token)
        return true
      } catch (_err) {
        return false
      } finally {
        this.refreshPromise = null
      }
    })()

    return this.refreshPromise
  }

  setTenantId(tenantId: string | null): void {
    useTenantStore.getState().setCurrentTenantId(tenantId)
  }

  getTenantId(): string | null {
    return useTenantStore.getState().currentTenantId
  }

  /**
   * Clear authentication and tenant context
   */
  clearAuth(): void {
    useAuthStore.getState().clearAuth()
    useTenantStore.getState().clear()
  }

  /**
   * When using cookie auth, check if the session is still valid (refresh succeeds).
   * Used by initAuth to restore auth state on reload.
   */
  async validateSession(): Promise<boolean> {
    if (!useCookies()) return !!this.getToken()
    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
        credentials: 'include',
      })
      return response.ok
    } catch (_err) {
      return false
    }
  }

  /**
   * Paths that must work WITHOUT tenant context (auth, tenant bootstrap).
   * All other endpoints require tenant_id: we add ?tenant_id= and x-tenant-id for every
   * GET/POST/PATCH/DELETE (list, create, update, etc.). Backend requires tenant context
   * for all data fetch and post operations.
   * See docs/FRONTEND_DEVELOPMENT_GUIDE.md – Tenant context.
   */
  private shouldSkipTenantId(endpoint: string): boolean {
    const pathname = new URL(endpoint, 'http://x').pathname
    if (pathname.startsWith('/auth/')) return true
    if (pathname === '/tenants') return true
    if (pathname.startsWith('/tenants/check-code')) return true
    if (/^\/tenants\/[^/]+$/.test(pathname)) return true // GET /tenants/:id
    return false
  }

  /**
   * Build request URL with query parameters
   */
  private buildUrl(endpoint: string, params?: QueryParams): string {
    const url = new URL(endpoint, this.baseUrl)
    const tenantId = this.getTenantId()
    const skipTenant = this.shouldSkipTenantId(endpoint)
    const entries = params ? Object.entries(params) : []
    const hasExplicitTenant = entries.some(
      ([key, value]) => key === 'tenant_id' && value !== undefined && value !== null,
    )

    if (tenantId && !skipTenant && !hasExplicitTenant) {
      url.searchParams.set('tenant_id', tenantId)
    }

    entries.forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach((v) => url.searchParams.append(key, String(v)))
        } else {
          url.searchParams.set(key, String(value))
        }
      }
    })

    return url.toString()
  }

  /**
   * Build request headers
   */
  private buildHeaders(
    customHeaders?: Record<string, string>,
    endpoint?: string,
    excludeSensitiveHeaders?: boolean
  ): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }

    if (!excludeSensitiveHeaders) {
      if (!useCookies()) {
        const token = this.getToken()
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }
      } else {
        const csrf = this.getCsrfToken()
        if (csrf) headers['X-CSRF-Token'] = csrf
      }
      const tenantId = this.getTenantId()
      const skipTenant = endpoint != null && this.shouldSkipTenantId(endpoint)
      if (tenantId && !skipTenant) {
        headers['x-tenant-id'] = tenantId
      }
    }

    return headers
  }

  /**
   * Build auth-only headers (no Content-Type) for FormData/blob requests
   */
  private buildAuthHeaders(endpoint?: string): Record<string, string> {
    const headers: Record<string, string> = {}
    if (!useCookies()) {
      const token = this.getToken()
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
    } else {
      const csrf = this.getCsrfToken()
      if (csrf) headers['X-CSRF-Token'] = csrf
    }
    const tenantId = this.getTenantId()
    const skipTenant = endpoint != null && this.shouldSkipTenantId(endpoint)
    if (tenantId && !skipTenant) {
      headers['x-tenant-id'] = tenantId
    }
    return headers
  }

  /**
   * POST FormData with auth headers, returns parsed JSON
   */
  async postFormData<T>(path: string, formData: FormData): Promise<T> {
    const url = this.buildUrl(path)
    const headers = this.buildAuthHeaders(path)

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers,
      ...(useCookies() ? { credentials: 'include' as RequestCredentials } : {}),
    })

    if (response.status === 401 && !path.includes('/auth/')) {
      const refreshed = await this.tryRefreshToken()
      if (refreshed) {
        const retryHeaders = this.buildAuthHeaders(path)
        const retryResponse = await fetch(url, {
          method: 'POST',
          body: formData,
          headers: retryHeaders,
          credentials: useCookies() ? 'include' : undefined,
        })
        if (retryResponse.ok) {
          const ct = retryResponse.headers.get('content-type')
          if (!ct || !ct.includes('application/json')) return {} as T
          return (await retryResponse.json()) as T
        }
      }
      this.handleAuthError(401)
    }

    if (response.status === 403) {
      this.handleAuthError(403)
    }

    if (!response.ok) {
      const error = await this.parseError(response)
      throw error
    }

    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      return {} as T
    }
    return (await response.json()) as T
  }

  /**
   * GET with blob response (e.g. file download)
   */
  async getBlob(path: string): Promise<Blob> {
    const url = this.buildUrl(path)
    const headers = this.buildAuthHeaders(path)

    const response = await fetch(url, {
      method: 'GET',
      headers,
      credentials: useCookies() ? 'include' : undefined,
    })

    if (response.status === 401) {
      const refreshed = await this.tryRefreshToken()
      if (refreshed) {
        const retryHeaders = this.buildAuthHeaders(path)
        const retryResponse = await fetch(url, {
          method: 'GET',
          headers: retryHeaders,
          credentials: useCookies() ? 'include' : undefined,
        })
        if (retryResponse.ok) {
          return retryResponse.blob()
        }
      }
      this.handleAuthError(401)
    }

    if (response.status === 403) {
      this.handleAuthError(403)
    }

    if (!response.ok) {
      throw new ApiError(
        'Failed to download document',
        'DOWNLOAD_ERROR',
        response.status
      )
    }

    return response.blob()
  }

  /**
   * Parse error response.
   * Supports both EAP shape ({ error, message, details? }) and FastAPI HTTPException ({ detail: string | array }).
   */
  private async parseError(response: Response): Promise<ApiError> {
    let body: unknown
    try {
      body = await response.json()
    } catch (_err) {
      body = null
    }

    const message = this.normalizeErrorMessageBody(body, response)
    const errorCode = this.normalizeErrorCodeBody(body, response.status)
    const fieldErrors = this.normalizeFieldErrorsBody(body)
    const data = this.normalizeErrorDataBody(body)

    return new ApiError(message, errorCode, response.status, fieldErrors, data)
  }

  /**
   * Pass through server-provided extra fields (e.g. `retry_after_seconds` for lockout)
   * minus the ones we already extract into typed fields.
   */
  private normalizeErrorDataBody(body: unknown): Record<string, unknown> | undefined {
    if (!body || typeof body !== 'object') return undefined
    const b = body as Record<string, unknown>
    const reserved = new Set(['error', 'message', 'detail', 'details', 'timestamp', 'path', 'request_id'])
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(b)) {
      if (!reserved.has(k)) out[k] = v
    }
    return Object.keys(out).length > 0 ? out : undefined
  }

  private normalizeErrorMessageBody(body: unknown, response: Response): string {
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

  private normalizeErrorCodeBody(body: unknown, status: number): string {
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

  private normalizeFieldErrorsBody(body: unknown): FieldErrors | undefined {
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

  /**
   * Handle authentication errors
   */
  private handleAuthError(status: number): void {
    if (status === 401) {
      this.clearAuth()
      // Notify React context to handle navigation (avoids hard redirect)
      this.onAuthError?.()
    }
  }

  /**
   * Retry logic with exponential backoff
   */
  private async retryRequest(
    requestFn: () => Promise<Response>,
    attempt = 1
  ): Promise<Response> {
    try {
      return await requestFn()
    } catch (error) {
      if (attempt >= this.retryAttempts) {
        throw error
      }

      // Only retry on network errors or 5xx errors
      if (
        error instanceof TypeError ||
        (error instanceof ApiError && error.status >= 500)
      ) {
        const delay = this.retryDelay * Math.pow(2, attempt - 1)
        await new Promise((resolve) => setTimeout(resolve, delay))
        return this.retryRequest(requestFn, attempt + 1)
      }

      throw error
    }
  }

  /**
   * Make HTTP request with timeout and retry
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit & RequestOptions = {}
  ): Promise<T> {
    const { signal, timeout, headers, ...fetchOptions } = options

    // Create abort controller for timeout
    const controller = new AbortController()
    const timeoutId = timeout
      ? setTimeout(() => controller.abort(), timeout)
      : setTimeout(() => controller.abort(), this.timeout)

    // Combine signals
    const requestSignal = signal
      ? AbortSignal.any([signal, controller.signal])
      : controller.signal

    // endpoint may already be a full URL or a relative path
    const isAbsoluteUrl = endpoint.startsWith('http')
    const isSameOrigin =
      !isAbsoluteUrl ||
      new URL(endpoint).origin === new URL(this.baseUrl).origin

    const url = isAbsoluteUrl ? endpoint : this.buildUrl(endpoint)
    const pathForHeaders = isAbsoluteUrl
      ? new URL(endpoint).pathname + new URL(endpoint).search
      : endpoint

    const sanitizedHeaders = isSameOrigin
      ? (headers as Record<string, string>)
      : (() => {
          const { Authorization: _auth, 'x-tenant-id': _tenant, ...rest } =
            (headers as Record<string, string>) || {}
          return rest
        })()

    const requestHeaders = this.buildHeaders(
      sanitizedHeaders,
      pathForHeaders,
      !isSameOrigin
    )

    const requestFn = () =>
      fetch(url, {
        ...fetchOptions,
        headers: requestHeaders,
        signal: requestSignal,
        ...(useCookies() && isSameOrigin ? { credentials: 'include' as RequestCredentials } : {}),
      })

    try {
      const response = await this.retryRequest(requestFn)

      clearTimeout(timeoutId)

      // Handle 401 - try refresh token before giving up
      if (response.status === 401 && !endpoint.includes('/auth/')) {
        const refreshed = await this.tryRefreshToken()
        if (refreshed) {
          const retryController = new AbortController()
          const retryTimeoutId = timeout
            ? setTimeout(() => retryController.abort(), timeout)
            : setTimeout(() => retryController.abort(), this.timeout)
          const retrySignal = signal
            ? AbortSignal.any([signal, retryController.signal])
            : retryController.signal
          const retryHeaders = this.buildHeaders(
            sanitizedHeaders,
            pathForHeaders,
            !isSameOrigin
          )
          try {
            const retryResponse = await fetch(url, {
              ...fetchOptions,
              headers: retryHeaders,
              signal: retrySignal,
              ...(useCookies() && isSameOrigin ? { credentials: 'include' as RequestCredentials } : {}),
            })
            clearTimeout(retryTimeoutId)
            if (retryResponse.ok) {
              const ct = retryResponse.headers.get('content-type')
              if (!ct || !ct.includes('application/json')) return {} as T
              return (await retryResponse.json()) as T
            }
          } catch (retryError) {
            clearTimeout(retryTimeoutId)
            throw retryError
          }
        }
        this.handleAuthError(401)
      }

      if (response.status === 403) {
        this.handleAuthError(403)
      }

      // Handle errors
      if (!response.ok) {
        const error = await this.parseError(response)
        throw error
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        return {} as T
      }

      return (await response.json()) as T
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof ApiError) {
        throw error
      }

      // Handle network errors
      if (error instanceof TypeError) {
        throw new ApiError(
          'Network error: Unable to connect to the server',
          'NETWORK_ERROR',
          0
        )
      }

      // Handle abort errors
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError(
          'Request timeout: The request took too long',
          'TIMEOUT_ERROR',
          0
        )
      }

      throw error
    }
  }

  /**
   * GET request
   */
  async get<T>(
    endpoint: string,
    params?: QueryParams,
    options?: RequestOptions
  ): Promise<T> {
    const fullUrl = this.buildUrl(endpoint, params)
    return this.request<T>(fullUrl, {
      method: 'GET',
      ...options,
    })
  }

  /**
   * POST request
   */
  async post<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })
  }

  /**
   * PATCH request
   */
  async patch<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })
  }

  /**
   * DELETE request
   */
  async delete<T>(
    endpoint: string,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
      ...options,
    })
  }
}

const apiClient = new ApiClient({
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: DEFAULT_TIMEOUT,
  retryAttempts: DEFAULT_RETRY_ATTEMPTS,
  retryDelay: DEFAULT_RETRY_DELAY,
})

export default apiClient
