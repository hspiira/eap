/**
 * Tenants API Endpoints
 *
 * Mirrors the BE `/tenants` router. Includes lifecycle transitions, settings,
 * subscription, and Azure AD SSO config.
 */

import apiClient from '../client'
import type { ListParams, PaginatedResponse, Tenant } from '../types'

export interface TenantSettingsInput {
  max_users?: number
  max_clients?: number
  features_enabled?: string[]
  custom_branding?: boolean
}

export interface TenantCreate {
  name: string
  code: string
  admin_email?: string | null
  subscription_tier?: string
  settings?: TenantSettingsInput
}

export interface TenantUpdate {
  name?: string
}

export interface TenantUpdateSettings {
  max_users?: number
  max_clients?: number
  features_enabled?: string[]
  custom_branding?: boolean
}

export interface TenantAzureSsoUpdate {
  azure_tenant_id?: string | null
  enabled: boolean
}

export interface TenantCreateResponse extends Tenant {
  admin_email?: string
  admin_password?: string
  set_password_url?: string | null
  set_password_expires_at?: string | null
}

export interface TenantStats {
  tenant_id: string
  current_user_count: number
  current_client_count: number
  max_users: number
  max_clients: number
}

export const tenantsApi = {
  async create(data: TenantCreate): Promise<TenantCreateResponse> {
    return apiClient.post<TenantCreateResponse>('/tenants', data)
  },

  async getById(tenantId: string): Promise<Tenant> {
    return apiClient.get<Tenant>(`/tenants/${tenantId}`)
  },

  async list(params?: ListParams): Promise<PaginatedResponse<Tenant>> {
    return apiClient.get<PaginatedResponse<Tenant>>(
      '/tenants',
      params,
    )
  },

  async update(tenantId: string, data: TenantUpdate): Promise<Tenant> {
    return apiClient.patch<Tenant>(`/tenants/${tenantId}`, data)
  },

  async updateSettings(tenantId: string, data: TenantUpdateSettings): Promise<Tenant> {
    return apiClient.patch<Tenant>(`/tenants/${tenantId}/settings`, data)
  },

  async updateSubscription(tenantId: string, tier: string): Promise<Tenant> {
    return apiClient.post<Tenant>(`/tenants/${tenantId}/subscription`, {
      subscription_tier: tier,
    })
  },

  async updateAzureSso(
    tenantId: string,
    data: TenantAzureSsoUpdate,
  ): Promise<Tenant> {
    return apiClient.patch<Tenant>(`/tenants/${tenantId}/azure-sso`, data)
  },

  async activate(tenantId: string): Promise<Tenant> {
    return apiClient.post<Tenant>(`/tenants/${tenantId}/activate`, {})
  },

  async suspend(tenantId: string, reason: string): Promise<Tenant> {
    return apiClient.post<Tenant>(`/tenants/${tenantId}/suspend`, { reason })
  },

  async terminate(tenantId: string, reason: string): Promise<Tenant> {
    return apiClient.post<Tenant>(`/tenants/${tenantId}/terminate`, { reason })
  },

  async archive(tenantId: string): Promise<Tenant> {
    return apiClient.post<Tenant>(`/tenants/${tenantId}/archive`, {})
  },

  async restore(tenantId: string): Promise<Tenant> {
    return apiClient.post<Tenant>(`/tenants/${tenantId}/restore`, {})
  },

  async stats(tenantId: string): Promise<TenantStats> {
    return apiClient.get<TenantStats>(`/tenants/${tenantId}/stats`)
  },

  async checkCode(code: string): Promise<{ available: boolean; code: string }> {
    return apiClient.get<{ available: boolean; code: string }>(
      `/tenants/check-code/${code}`,
    )
  },
}
