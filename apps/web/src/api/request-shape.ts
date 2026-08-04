/**
 * URL and header construction for outgoing requests. Pure functions — the
 * caller supplies whatever session state (token, tenant id, csrf) it holds
 * rather than these functions reaching into a store themselves.
 */

import type { QueryParams } from '@/types/api'

/**
 * Paths that must work WITHOUT tenant context (auth, tenant bootstrap).
 * All other endpoints require tenant_id: we add ?tenant_id= and x-tenant-id for every
 * GET/POST/PATCH/DELETE (list, create, update, etc.). Backend requires tenant context
 * for all data fetch and post operations.
 * See docs/FRONTEND_DEVELOPMENT_GUIDE.md – Tenant context.
 */
export function shouldSkipTenantId(endpoint: string): boolean {
  const pathname = new URL(endpoint, 'http://x').pathname
  if (pathname.startsWith('/auth/')) return true
  if (pathname === '/tenants') return true
  if (pathname.startsWith('/tenants/check-code')) return true
  if (/^\/tenants\/[^/]+$/.test(pathname)) return true // GET /tenants/:id
  return false
}

/** Build request URL with query parameters. */
export function buildUrl(
  baseUrl: string,
  endpoint: string,
  tenantId: string | null,
  params?: QueryParams,
): string {
  const url = new URL(endpoint, baseUrl)
  const skipTenant = shouldSkipTenantId(endpoint)
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

export interface SessionContext {
  token: string | null
  csrfToken: string | null
  tenantId: string | null
  useCookies: boolean
}

/** Build request headers. */
export function buildHeaders(
  session: SessionContext,
  customHeaders?: Record<string, string>,
  endpoint?: string,
  excludeSensitiveHeaders?: boolean,
): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  }

  if (!excludeSensitiveHeaders) {
    if (!session.useCookies) {
      if (session.token) {
        headers['Authorization'] = `Bearer ${session.token}`
      }
    } else if (session.csrfToken) {
      headers['X-CSRF-Token'] = session.csrfToken
    }
    const skipTenant = endpoint != null && shouldSkipTenantId(endpoint)
    if (session.tenantId && !skipTenant) {
      headers['x-tenant-id'] = session.tenantId
    }
  }

  return headers
}

/** Build auth-only headers (no Content-Type) for FormData/blob requests. */
export function buildAuthHeaders(
  session: SessionContext,
  endpoint?: string,
): Record<string, string> {
  const headers: Record<string, string> = {}
  if (!session.useCookies) {
    if (session.token) {
      headers['Authorization'] = `Bearer ${session.token}`
    }
  } else if (session.csrfToken) {
    headers['X-CSRF-Token'] = session.csrfToken
  }
  const skipTenant = endpoint != null && shouldSkipTenantId(endpoint)
  if (session.tenantId && !skipTenant) {
    headers['x-tenant-id'] = session.tenantId
  }
  return headers
}
