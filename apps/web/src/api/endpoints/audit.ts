/**
 * Audit API Endpoints
 * Read-only audit log viewing
 */

import apiClient from '../client'
import type { AuditLog, PaginatedResponse, ListParams } from '../types'

export type AuditListParams = ListParams & {
  action_type?: string
  resource_type?: string
  user_id?: string
  date_from?: string
  date_to?: string
}

export interface AuditLogChange {
  field?: string
  old_value?: unknown
  new_value?: unknown
}

export const auditApi = {
  async getById(logId: string): Promise<AuditLog> {
    return apiClient.get<AuditLog>(`/audit/logs/${logId}`)
  },

  async list(params?: AuditListParams): Promise<PaginatedResponse<AuditLog>> {
    return apiClient.get<PaginatedResponse<AuditLog>>('/audit/logs', params as Record<string, unknown>)
  },

  async getChanges(logId: string): Promise<AuditLogChange[] | Record<string, unknown>> {
    const res = await apiClient.get<AuditLogChange[] | { changes: AuditLogChange[] } | Record<string, unknown>>(
      `/audit/logs/${logId}/changes`
    )
    if (Array.isArray(res)) return res
    if (res && typeof res === 'object' && 'changes' in res && Array.isArray((res as { changes: AuditLogChange[] }).changes)) {
      return (res as { changes: AuditLogChange[] }).changes
    }
    return (res as Record<string, unknown>) ?? {}
  },

  async getEntityHistory(entityType: string, entityId: string): Promise<AuditLog[]> {
    const res = await apiClient.get<{ items: AuditLog[] } | AuditLog[]>(
      `/audit/entity/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`
    )
    return Array.isArray(res) ? res : (res.items ?? [])
  },
}
