/**
 * Audit API Endpoints
 * Read-only audit log viewing
 */

import apiClient from "../client"
import type { AuditLog, EntityChange, ListParams, PaginatedResponse } from "../types"

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
    return apiClient.get<PaginatedResponse<AuditLog>>("/audit/logs", params)
  },

  async getChanges(logId: string): Promise<AuditLogChange[] | Record<string, unknown>> {
    const res = await apiClient.get<
      AuditLogChange[] | { changes: AuditLogChange[] } | Record<string, unknown>
    >(`/audit/logs/${logId}/changes`)
    if (Array.isArray(res)) return res
    if (
      res &&
      typeof res === "object" &&
      "changes" in res &&
      Array.isArray((res as { changes: AuditLogChange[] }).changes)
    ) {
      return (res as { changes: AuditLogChange[] }).changes
    }
    return (res as Record<string, unknown>) ?? {}
  },

  /**
   * One record's activity, newest first.
   *
   * Read from `/audit/logs` rather than `/audit/entity/{type}/{id}/changes`,
   * because an entity change carries no timestamp and a trail without times is
   * not a trail. Field names come from `getEntityFieldChanges`.
   */
  async getEntityHistory(
    entityType: string,
    entityId: string,
    params?: { limit?: number },
  ): Promise<AuditLog[]> {
    const res = await apiClient.get<PaginatedResponse<AuditLog>>("/audit/logs", {
      resource_type: entityType,
      resource_id: entityId,
      sort_by: "occurred_at",
      sort_desc: true,
      limit: params?.limit ?? 50,
    })
    return res.items ?? []
  },

  /** Which fields each change touched, keyed by the audit log that recorded it. */
  async getEntityFieldChanges(entityType: string, entityId: string): Promise<EntityChange[]> {
    const res = await apiClient.get<PaginatedResponse<EntityChange>>(
      `/audit/entity/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/changes`,
    )
    return res.items ?? []
  },
}
