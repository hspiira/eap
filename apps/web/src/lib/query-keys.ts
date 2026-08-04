/**
 * Central query-key factory. Single source of truth for TanStack Query keys so
 * that reads and `useEntityMutation` invalidations always agree on the same key
 * shape. Prefer `resourceKeys('<resource>')` (or `queryKeys.<resource>`) over
 * hand-typing `['<resource>', 'detail', id]` arrays in components.
 *
 * Key shapes (kept in sync with `lib/queries.ts`):
 *   all    → ['<resource>']
 *   list   → ['<resource>', 'list', params?]
 *   detail → ['<resource>', 'detail', id]
 *   sub    → ['<resource>', '<name>', id]   (nested/related caches)
 */

import type { QueryKey } from '@tanstack/react-query'

import { entityDetailKey, entityListKey } from '@/lib/queries'

export interface ResourceKeys {
  all: QueryKey
  list: (params?: object) => QueryKey
  detail: (id: string) => QueryKey
  sub: (id: string, name: string) => QueryKey
}

export function resourceKeys(resource: string): ResourceKeys {
  return {
    all: [resource],
    list: (params?: object) => entityListKey(resource, params),
    detail: (id: string) => entityDetailKey(resource, id),
    sub: (id: string, name: string) => [resource, name, id],
  }
}

/**
 * Convenience accessors for common resources. Extend as call sites migrate off
 * hand-typed key arrays. The resource string must match the one the endpoint's
 * `useEntityMutation({ resource })` uses, so keys and invalidations line up.
 */
export const queryKeys = {
  users: resourceKeys('users'),
  clients: resourceKeys('clients'),
  persons: resourceKeys('persons'),
  contracts: resourceKeys('contracts'),
  engagements: resourceKeys('engagements'),
  services: resourceKeys('services'),
  serviceAssignments: resourceKeys('service-assignments'),
  serviceSessions: resourceKeys('service-sessions'),
  tenants: resourceKeys('tenants'),
  providers: resourceKeys('providers'),
  incidents: resourceKeys('incidents'),
  surveys: resourceKeys('surveys'),
  questionnaires: resourceKeys('questionnaires'),
  nonCompete: resourceKeys('non-compete'),
  careCallbackCampaigns: resourceKeys('care-callback-campaigns'),
  careCallbackCases: resourceKeys('care-callback-cases'),
} as const
