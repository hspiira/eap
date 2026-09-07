/**
 * Status colour, tone and icon mapping.
 *
 * Every status the API can put on a badge is assigned a tone here. A status
 * that falls through to the default reads as inert grey, which is wrong for
 * anything the user has to act on, so new wire values belong in one of the
 * lists below rather than in the fallback.
 *
 * Tones follow IBM Carbon's status indicator pattern, which is the closest
 * published standard to a status badge:
 *   success  green   stability, or a process that finished cleanly
 *   info     blue    additional information, and work actually in flight
 *   warning  amber   a fault condition needing corrective action, recoverable
 *   danger   red     failure, refusal, or ending for cause
 *   neutral  grey    not started, unknown, or inert
 *
 * `pending` is neutral, not blue. Carbon separates "In Progress" (a process
 * started but not finished) from "Not Started" (a job or step that has not
 * begun), and `BaseStatus.PENDING` is the default a row is created with, so it
 * is the latter. Blue is reserved for work that is genuinely under way.
 *
 * Both themes fill with the solid role colour and put white on it. The dark
 * roles are their own values rather than the light ones reused: a fill deep
 * enough to carry white text has to stay clear of a near-black page, so each
 * dark role is set where neither constraint is tight. Measured, white on the
 * fill then the chip against the page:
 *   success 5.07 / 7.00 light   5.35 / 3.70 dark
 *   warning 5.02 / 6.94 light   5.40 / 3.67 dark
 *   danger  8.41 / 4.22 light   5.47 / 3.62 dark
 *   info    6.70 / 5.30 light   5.52 / 3.58 dark
 *   neutral 7.81 / 7.81 light   5.33 / 3.72 dark
 * Text needs 4.5:1 and a component boundary needs 3:1 (WCAG 1.4.11).
 *
 * The success and danger hues come from Cursor's diff colours, sampled from a
 * screenshot: green #1f8a66 at hue 160 and red #d02d56 at hue 345. The hues
 * carry over, the lightness is set per theme to clear both constraints.
 *
 * Icons are keyed by status first and tone second. In an icon-only column the
 * shape is what tells two statuses of the same tone apart, and Carbon asks for
 * at least three of symbol, shape, colour and type to be present.
 */

import {
  AlarmClock,
  AlertCircle,
  AlertTriangle,
  Archive,
  BadgeCheck,
  Ban,
  CalendarClock,
  CalendarX,
  CheckCircle2,
  Circle,
  CircleSlash,
  Clock,
  FileEdit,
  FolderOpen,
  HelpCircle,
  Hourglass,
  Loader,
  type LucideIcon,
  PauseCircle,
  ThumbsDown,
  ThumbsUp,
  Trash2,
  UserX,
  XCircle,
} from "lucide-react"

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

const TONE_COLORS: Record<StatusTone, StatusColorConfig> = {
  success: {
    tone: "success",
    bg: "bg-success",
    text: "text-white",
    border: "border-success",
  },
  info: {
    tone: "info",
    bg: "bg-info",
    text: "text-white",
    border: "border-info",
  },
  warning: {
    tone: "warning",
    bg: "bg-warning",
    text: "text-white",
    border: "border-warning",
  },
  danger: {
    tone: "danger",
    bg: "bg-danger",
    text: "text-white",
    border: "border-danger",
  },
  neutral: {
    tone: "neutral",
    bg: "bg-status-neutral",
    text: "text-white",
    border: "border-status-neutral",
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
    "processing",
    "referred",
    "rescheduled",
    "scheduled",
    "tobecontinued",
  ],
  warning: [
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
    "declined",
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
    "pending",
    "pendingverification",
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
 * Icon per status, so an icon-only column stays readable.
 *
 * Keying only on tone would give every neutral status the same hollow circle,
 * leaving Pending, Inactive, Archived and Deleted apart only by tooltip. A
 * status absent from here falls back to its tone's icon.
 */
const STATUS_ICON: Readonly<Record<string, LucideIcon>> = {
  // neutral: not started, inert, or gone
  pending: Hourglass,
  pendingverification: Hourglass,
  draft: FileEdit,
  archived: Archive,
  deleted: Trash2,
  cancelled: Ban,
  closed: CircleSlash,
  expired: CalendarX,
  inactive: PauseCircle,
  unknown: HelpCircle,
  // info: under way
  inprogress: Loader,
  processing: Loader,
  scheduled: CalendarClock,
  rescheduled: CalendarClock,
  open: FolderOpen,
  // success
  active: CheckCircle2,
  completed: CheckCircle2,
  paid: BadgeCheck,
  verified: BadgeCheck,
  approved: ThumbsUp,
  // warning
  onleave: PauseCircle,
  suspended: PauseCircle,
  noshow: UserX,
  lapsed: CalendarX,
  // danger
  declined: ThumbsDown,
  rejected: ThumbsDown,
  failed: XCircle,
  terminated: XCircle,
  overdue: AlarmClock,
}

const TONE_ICON: Record<StatusTone, LucideIcon> = {
  success: CheckCircle2,
  info: Clock,
  warning: AlertTriangle,
  danger: AlertCircle,
  neutral: Circle,
}

/** The icon for a status: its own if it has one, otherwise its tone's. */
export function getStatusIcon(status: StatusType): LucideIcon {
  const key = statusKey(status)
  return STATUS_ICON[key] ?? TONE_ICON[TONE_LOOKUP.get(key) ?? "neutral"]
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
