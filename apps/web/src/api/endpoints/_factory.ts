/**
 * Endpoint factories — remove the copy-pasted CRUD and lifecycle method shapes
 * repeated across entity endpoint modules. Spread the result into an entity's
 * `xxxApi` object and add bespoke routes alongside:
 *
 *   export const clientsApi = {
 *     ...makeCrudEndpoints<Client, ClientCreate, ClientUpdate, ClientListParams>('clients'),
 *     ...makeLifecycleEndpoints<Client>('clients'),
 *     setTier, verify, getStats,   // entity-specific
 *   }
 *
 * NOTE: `makeLifecycleEndpoints` encodes one body convention — no body on
 * activate/archive/restore, `{ reason }` on suspend/terminate, and an optional
 * `{ reason }` on deactivate. Only adopt it where the existing endpoints already
 * match this convention exactly, so request payloads are unchanged.
 */

import apiClient from '../client'
import type { ListParams, PaginatedResponse } from '../types'

export function makeCrudEndpoints<T, TCreate, TUpdate, P extends ListParams = ListParams>(
  base: string,
) {
  return {
    create: (data: TCreate): Promise<T> => apiClient.post<T>(`/${base}`, data),
    getById: (id: string): Promise<T> => apiClient.get<T>(`/${base}/${id}`),
    list: (params?: P): Promise<PaginatedResponse<T>> =>
      apiClient.get<PaginatedResponse<T>>(`/${base}`, params as Record<string, unknown> | undefined),
    update: (id: string, data: TUpdate): Promise<T> => apiClient.patch<T>(`/${base}/${id}`, data),
  }
}

export function makeLifecycleEndpoints<T>(base: string) {
  return {
    activate: (id: string): Promise<T> => apiClient.post<T>(`/${base}/${id}/activate`),
    deactivate: (id: string, reason?: string): Promise<T> =>
      apiClient.post<T>(`/${base}/${id}/deactivate`, reason != null ? { reason } : undefined),
    suspend: (id: string, reason: string): Promise<T> =>
      apiClient.post<T>(`/${base}/${id}/suspend`, { reason }),
    terminate: (id: string, reason: string): Promise<T> =>
      apiClient.post<T>(`/${base}/${id}/terminate`, { reason }),
    archive: (id: string): Promise<T> => apiClient.post<T>(`/${base}/${id}/archive`),
    restore: (id: string): Promise<T> => apiClient.post<T>(`/${base}/${id}/restore`),
  }
}
