/**
 * Audit API Endpoints
 * Read-only audit log viewing
 */

import apiClient from "../client"
import type { AuditLog, EntityChange, ListParams, PaginatedResponse } from "../types"

export type AuditListParams = ListParams & {
  action_type?: string
  resource_type?: string
  resource_id?: string
  user_id?: string
  /** ISO date string; matches the BE's `start_date` query param. */
  start_date?: string
  /** ISO date string; matches the BE's `end_date` query param. */
  end_date?: string
}

export const auditApi = {
  async getById(logId: string): Promise<AuditLog> {
    return apiClient.get<AuditLog>(`/audit/logs/${logId}`)
  },

  async list(params?: AuditListParams): Promise<PaginatedResponse<AuditLog>> {
    return apiClient.get<PaginatedResponse<AuditLog>>("/audit/logs", params)
  },

  /** The field-level changes this one audit log recorded, if any. A bare array, not a page. */
  async getChanges(logId: string): Promise<EntityChange[]> {
    return apiClient.get<EntityChange[]>(`/audit/logs/${logId}/changes`)
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
