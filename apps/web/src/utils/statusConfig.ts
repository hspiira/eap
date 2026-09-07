/**
 * Single source of truth for status display (label + color).
 * Use this and src/types/enums in UI; no ad-hoc status strings.
 */

import type { LucideIcon } from "lucide-react"

import {
  getStatusColors,
  getStatusIcon,
  getStatusLabel,
  type StatusColorConfig,
} from "@/utils/statusColors"

export type StatusDisplay = StatusColorConfig & { label: string; icon: LucideIcon }

const cache = new Map<string, StatusDisplay>()

export function getStatusConfig(status: string): StatusDisplay {
  const key = status.trim()
  if (!cache.has(key)) {
    cache.set(key, {
      label: getStatusLabel(key),
      icon: getStatusIcon(key),
      ...getStatusColors(key),
    })
  }
  return cache.get(key)!
}
