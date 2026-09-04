/**
 * Status Color Mapping Utility
 * Maps status values to design system colors
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

export interface StatusColorConfig {
  bg: string
  text: string
  border?: string
}

/**
 * Maps status values to color configurations
 */
export function getStatusColors(status: StatusType): StatusColorConfig {
  const statusLower = status.toLowerCase()

  // Active/Active states - Green/Natural
  if (
    statusLower === "active" ||
    statusLower === "completed" ||
    statusLower === "paid" ||
    statusLower === "verified" ||
    statusLower === "approved" ||
    statusLower === "delivered" ||
    statusLower === "published" ||
    statusLower === "renewed"
  ) {
    return {
      bg: "bg-primary",
      text: "text-white",
      border: "border-primary",
    }
  }

  // Pending/In Progress states - Yellow/Nurturing
  if (
    statusLower === "pending" ||
    statusLower === "pending verification" ||
    statusLower === "in_progress" ||
    statusLower === "processing" ||
    statusLower === "scheduled" ||
    statusLower === "rescheduled" ||
    statusLower === "draft" ||
    statusLower === "assigned"
  ) {
    return {
      bg: "bg-warning",
      text: "text-white",
      border: "border-nurturing-dark",
    }
  }

  // Inactive/Inactive states - Grey/Safe
  if (
    statusLower === "inactive" ||
    statusLower === "archived" ||
    statusLower === "cancelled" ||
    statusLower === "cancelled" ||
    statusLower === "suspended" ||
    statusLower === "banned" ||
    statusLower === "terminated" ||
    statusLower === "expired" ||
    statusLower === "closed" ||
    statusLower === "deleted" ||
    statusLower === "no show" ||
    statusLower === "on leave" ||
    statusLower === "resigned" ||
    statusLower === "refunded"
  ) {
    return {
      bg: "bg-muted",
      text: "text-safe-dark",
      border: "border-safe-dark",
    }
  }

  if (
    statusLower === "failed" ||
    statusLower === "error" ||
    statusLower === "rejected" ||
    statusLower === "overdue"
  ) {
    return {
      bg: "bg-danger",
      text: "text-white",
      border: "border-danger-dark",
    }
  }

  // Default - Safe/Grey
  return {
    bg: "bg-muted",
    text: "text-safe-dark",
    border: "border-safe",
  }
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
