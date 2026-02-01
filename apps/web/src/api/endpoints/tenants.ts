/**
 * Tenants API Endpoints
 */

import apiClient from '../client'
import type { Tenant, PaginatedResponse, ListParams } from '../types'

export interface TenantCreate {
  name: string // Required, 1-255 characters
  code: string // Required, 3-15 characters, lowercase alphanumeric with hyphens
  subscription_tier?: string // Optional, default: "Free"
  settings?: {
    max_users?: number // Optional, default: 10, minimum: 1
    max_clients?: number // Optional, default: 5, minimum: 1
    features_enabled?: string[] // Optional, default: []
    custom_branding?: boolean // Optional, default: false
  }
}

export interface TenantCreateResponse {
  id: string // Tenant ID (CUID)
  name: string
  code: string
  status: string // Always "Active" on creation
  subscription_tier: string
  settings: {
    max_users: number
    max_clients: number
    features_enabled: string[]
    custom_branding: boolean
  }
  is_active: boolean // Always true on creation
  admin_email: string // ⚠️ ONLY present on creation: "admin@{code}.local"
  admin_password: string // ⚠️ ONLY present on creation: 16-character secure password
}

export const tenantsApi = {
  /**
   * Create a new tenant (also creates admin user in background)
   * Returns tenant info and admin password
   */
  async create(tenantData: TenantCreate): Promise<TenantCreateResponse> {
    return apiClient.post<TenantCreateResponse>('/tenants', tenantData)
  },

  /**
   * Get tenant by ID
   */
  async getById(tenantId: string): Promise<Tenant> {
    return apiClient.get<Tenant>(`/tenants/${tenantId}`)
  },

  /**
   * List tenants
   */
  async list(params?: ListParams): Promise<PaginatedResponse<Tenant>> {
    return apiClient.get<PaginatedResponse<Tenant>>('/tenants', params as Record<string, unknown>)
  },

  /**
   * Update tenant
   */
  async update(tenantId: string, data: Partial<TenantCreate>): Promise<Tenant> {
    return apiClient.patch<Tenant>(`/tenants/${tenantId}`, data)
  },

  /**
   * Check if tenant code is available
   */
  async checkCode(code: string): Promise<{ available: boolean; code: string }> {
    return apiClient.get<{ available: boolean; code: string }>(`/tenants/check-code/${code}`)
  },
}
