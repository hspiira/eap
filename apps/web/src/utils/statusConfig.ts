/**
 * Single source of truth for status display (label + color).
 * Use this and src/types/enums in UI; no ad-hoc status strings.
 */

import {
  getStatusColors,
  getStatusLabel,
  type StatusColorConfig,
} from '@/utils/statusColors'

export type StatusDisplay = StatusColorConfig & { label: string }

const cache = new Map<string, StatusDisplay>()

export function getStatusConfig(status: string): StatusDisplay {
  const key = status.trim()
  if (!cache.has(key)) {
    cache.set(key, {
      label: getStatusLabel(key),
      ...getStatusColors(key),
    })
  }
  return cache.get(key)!
}
