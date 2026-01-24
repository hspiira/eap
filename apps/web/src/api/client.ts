/**
 * API Client
 * Centralized API client with authentication, tenant context, and error handling
 */

import type {
  ApiClientConfig,
  RequestOptions,
  ErrorResponse,
  FieldErrors,
} from '@/types/api'
import { ApiError } from '@/types/api'

const DEFAULT_TIMEOUT = 30000 // 30 seconds
const DEFAULT_RETRY_ATTEMPTS = 3
const DEFAULT_RETRY_DELAY = 1000 // 1 second

class ApiClient {
  private baseUrl: string
  private token: string | null = null
  private tenantId: string | null = null
  private timeout: number
  private retryAttempts: number
  private retryDelay: number

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '') // Remove trailing slash
    this.timeout = config.timeout ?? DEFAULT_TIMEOUT
    this.retryAttempts = config.retryAttempts ?? DEFAULT_RETRY_ATTEMPTS
    this.retryDelay = config.retryDelay ?? DEFAULT_RETRY_DELAY
  }

  /**
   * Set authentication token
   */
  setToken(token: string | null): void {
    this.token = token
    if (token) {
      localStorage.setItem('auth_token', token)
    } else {
      localStorage.removeItem('auth_token')
    }
  }

  /**
   * Get authentication token
   */
  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token')
    }
    return this.token
  }

  /**
   * Set tenant ID
   */
  setTenantId(tenantId: string | null): void {
    this.tenantId = tenantId
    if (tenantId) {
      localStorage.setItem('tenant_id', tenantId)
    } else {
      localStorage.removeItem('tenant_id')
    }
  }

  /**
   * Get tenant ID.
   * Uses in-memory value, then localStorage 'tenant_id', then 'current_tenant_id' (TenantContext).
   * Ensures tenant is available even before TenantContext sync (e.g. after SSR hydrate).
   */
  getTenantId(): string | null {
    if (this.tenantId) return this.tenantId
    if (typeof window === 'undefined') return null
    const fromTenant = localStorage.getItem('tenant_id')
    const fromCurrent = localStorage.getItem('current_tenant_id')
    const id = fromTenant || fromCurrent || null
    if (id) this.tenantId = id
    return id
  }

  /**
   * Clear authentication and tenant context
   */
  clearAuth(): void {
    this.token = null
    this.tenantId = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('tenant_id')
      localStorage.removeItem('current_tenant_id')
    }
  }

  /**
   * Paths that must work without tenant context (auth, get-by-id bootstrap).
   * See docs/FRONTEND_DEVELOPMENT_GUIDE.md – Tenant context; GET /tenants/{id} used to load current tenant.
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
  private buildUrl(endpoint: string, params?: Record<string, unknown>): string {
    const url = new URL(endpoint, this.baseUrl)
    const tenantId = this.getTenantId()
    const skipTenant = this.shouldSkipTenantId(endpoint)

    if (tenantId && !skipTenant && !params?.tenant_id) {
      url.searchParams.set('tenant_id', tenantId)
    }

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach((v) => url.searchParams.append(key, String(v)))
          } else {
            url.searchParams.set(key, String(value))
          }
        }
      })
    }

    return url.toString()
  }

  /**
   * Build request headers
   */
  private buildHeaders(
    customHeaders?: Record<string, string>,
    endpoint?: string
  ): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }

    const token = this.getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const tenantId = this.getTenantId()
    const skipTenant = endpoint != null && this.shouldSkipTenantId(endpoint)
    if (tenantId && !skipTenant) {
      headers['x-tenant-id'] = tenantId
    }

    return headers
  }

  /**
   * Parse error response
   */
  private async parseError(response: Response): Promise<ApiError> {
    let errorData: ErrorResponse

    try {
      errorData = await response.json()
    } catch {
      // If response is not JSON, create a generic error
      errorData = {
        error: 'UNKNOWN_ERROR',
        message: response.statusText || 'An unknown error occurred',
        timestamp: new Date().toISOString(),
      }
    }

    // Extract field-specific errors
    const fieldErrors: FieldErrors | undefined = errorData.details
      ? errorData.details.reduce((acc, detail) => {
          if (detail.field) {
            acc[detail.field] = detail.message
          }
          return acc
        }, {} as FieldErrors)
      : undefined

    return new ApiError(
      errorData.message,
      errorData.error,
      response.status,
      fieldErrors
    )
  }

  /**
   * Handle authentication errors
   */
  private handleAuthError(status: number): void {
    if (status === 401) {
      // Clear auth and redirect to login
      this.clearAuth()
      // Note: In TanStack Start, we'll handle redirects via router
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
    }
  }

  /**
   * Retry logic with exponential backoff
   */
  private async retryRequest<T>(
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
    // If it starts with http, use it directly, otherwise build URL
    const url = endpoint.startsWith('http') 
      ? endpoint 
      : this.buildUrl(endpoint)
    const requestHeaders = this.buildHeaders(
      headers as Record<string, string>,
      endpoint.startsWith('http') ? new URL(endpoint).pathname + new URL(endpoint).search : endpoint
    )

    const requestFn = () =>
      fetch(url, {
        ...fetchOptions,
        headers: requestHeaders,
        signal: requestSignal,
      })

    try {
      const response = await this.retryRequest(requestFn)

      clearTimeout(timeoutId)

      // Handle authentication errors
      if (response.status === 401 || response.status === 403) {
        this.handleAuthError(response.status)
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
    params?: Record<string, unknown>,
    options?: RequestOptions
  ): Promise<T> {
    // Build full URL with params and pass as endpoint
    const fullUrl = this.buildUrl(endpoint, params)
    // Extract relative path from full URL for request method
    const urlObj = new URL(fullUrl)
    const relativePath = urlObj.pathname + urlObj.search
    return this.request<T>(relativePath, {
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

// Create singleton instance
const apiClient = new ApiClient({
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: DEFAULT_TIMEOUT,
  retryAttempts: DEFAULT_RETRY_ATTEMPTS,
  retryDelay: DEFAULT_RETRY_DELAY,
})

// Initialize token and tenant from localStorage if available (client-only).
// Use both tenant_id and current_tenant_id (TenantContext) so we have tenant before sync.
if (typeof window !== 'undefined') {
  const storedToken = localStorage.getItem('auth_token')
  const storedTenantId =
    localStorage.getItem('tenant_id') || localStorage.getItem('current_tenant_id')
  if (storedToken) {
    apiClient.setToken(storedToken)
  }
  if (storedTenantId) {
    apiClient.setTenantId(storedTenantId)
  }
}

export default apiClient
