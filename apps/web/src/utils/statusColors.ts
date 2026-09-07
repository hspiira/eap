/**
 * Status colour mapping.
 *
 * Every status the API can put on a badge is assigned a tone here. A status
 * that falls through to the default reads as inert grey, which is wrong for
 * anything the user has to act on, so new wire values belong in one of the
 * lists below rather than in the fallback.
 *
 * The four tones carry distinct meanings and must stay distinguishable:
 *   success  steady or successfully finished
 *   info     under way, or waiting on someone
 *   warning  paused, lapsed or needing attention, but recoverable
 *   danger   ended for cause, refused, or failed
 *   neutral  inert: never started, archived, or closed without incident
 */

import type {
  BaseStatus,
  ContractStatus,
  DocumentStatus,
  PaymentStatus,
  SessionStatus,
  TenantStatus,
  UserStatus,
  WorkStatus,
} from "@/types/enums"

type StatusType =
  | BaseStatus
  | UserStatus
  | TenantStatus
  | ContractStatus
  | SessionStatus
  | DocumentStatus
  | PaymentStatus
  | WorkStatus
  | string // Allow any string for flexibility

export type StatusTone = "success" | "info" | "warning" | "danger" | "neutral"

export interface StatusColorConfig {
  tone: StatusTone
  bg: string
  text: string
  border?: string
}

/**
 * Solid fills in the light theme, tinted fills in the dark one. The dark
 * palette makes each role a *light* colour (--danger is #f87171 there), so
 * white-on-role renders at about 2:1 and the `-soft` / `-fg` pair is what the
 * token set provides for a badge.
 */
const TONE_COLORS: Record<StatusTone, StatusColorConfig> = {
  success: {
    tone: "success",
    bg: "bg-primary dark:bg-success-soft",
    text: "text-white dark:text-success-fg",
    border: "border-primary dark:border-success/40",
  },
  info: {
    tone: "info",
    bg: "bg-info dark:bg-info-soft",
    text: "text-white dark:text-info-fg",
    border: "border-info-fg dark:border-info/40",
  },
  warning: {
    tone: "warning",
    bg: "bg-warning dark:bg-warning-soft",
    text: "text-white dark:text-warning-fg",
    border: "border-warning-fg dark:border-warning/40",
  },
  danger: {
    tone: "danger",
    bg: "bg-danger dark:bg-danger-soft",
    text: "text-white dark:text-danger-fg",
    border: "border-danger-fg dark:border-danger/40",
  },
  neutral: {
    tone: "neutral",
    bg: "bg-muted",
    text: "text-safe-dark",
    border: "border-safe-dark",
  },
}

/**
 * Wire values are matched with punctuation, spacing and case removed, so a
 * status reads the same whether the API sends `In Progress`, `in_progress` or
 * `InProgress`.
 */
const TONE_BY_STATUS: Record<StatusTone, readonly string[]> = {
  success: [
    "active",
    "accepted",
    "accredited",
    "approved",
    "completed",
    "delivered",
    "extended",
    "paid",
    "published",
    "renewed",
    "resolved",
    "verified",
  ],
  info: [
    "assessment",
    "assigned",
    "collecting",
    "contacted",
    "inprogress",
    "intake",
    "invoiced",
    "open",
    "pending",
    "pendingverification",
    "processing",
    "referred",
    "rescheduled",
    "scheduled",
    "tobecontinued",
  ],
  warning: [
    "declined",
    "exhausted",
    "extensionrequested",
    "lapsed",
    "noshow",
    "noshowclosed",
    "onleave",
    "suspended",
    "unreachable",
  ],
  danger: [
    "banned",
    "error",
    "escalated",
    "failed",
    "overdue",
    "rejected",
    "removed",
    "revoked",
    "terminated",
  ],
  neutral: [
    "archived",
    "cancelled",
    "closed",
    "deleted",
    "draft",
    "expired",
    "inactive",
    "referredout",
    "refunded",
    "resigned",
    "unknown",
  ],
}

const TONE_LOOKUP: ReadonlyMap<string, StatusTone> = new Map(
  Object.entries(TONE_BY_STATUS).flatMap(([tone, statuses]) =>
    statuses.map((status) => [status, tone as StatusTone] as const),
  ),
)

function statusKey(status: StatusType): string {
  return status.toLowerCase().replace(/[^a-z0-9]/g, "")
}

/** Maps a status value to its tone's colour configuration. */
export function getStatusColors(status: StatusType): StatusColorConfig {
  return TONE_COLORS[TONE_LOOKUP.get(statusKey(status)) ?? "neutral"]
}

/**
 * Get human-readable status label
 */
export function getStatusLabel(status: StatusType): string {
  if (status.includes(" ")) return status

  // Wire values are PascalCase. Split on the case boundary, and on the boundary
  // between an acronym and a following word, so CISMResponse reads as two words.
  // A word that is all capitals is an acronym and keeps its case.
  return status
    .split(/[_\s-]/)
    .flatMap((part) => part.split(/(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])/))
    .map((word) =>
      word === word.toUpperCase()
        ? word
        : word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
    )
    .join(" ")
}
