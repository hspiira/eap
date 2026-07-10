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
} from '@/types/enums'

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
    statusLower === 'active' ||
    statusLower === 'completed' ||
    statusLower === 'paid' ||
    statusLower === 'verified' ||
    statusLower === 'approved' ||
    statusLower === 'delivered' ||
    statusLower === 'published' ||
    statusLower === 'renewed'
  ) {
    return {
      bg: 'bg-primary',
      text: 'text-white',
      border: 'border-primary',
    }
  }

  // Pending/In Progress states - Yellow/Nurturing
  if (
    statusLower === 'pending' ||
    statusLower === 'pending verification' ||
    statusLower === 'in_progress' ||
    statusLower === 'processing' ||
    statusLower === 'scheduled' ||
    statusLower === 'rescheduled' ||
    statusLower === 'draft' ||
    statusLower === 'assigned'
  ) {
    return {
      bg: 'bg-warning',
      text: 'text-white',
      border: 'border-nurturing-dark',
    }
  }

  // Inactive/Inactive states - Grey/Safe
  if (
    statusLower === 'inactive' ||
    statusLower === 'archived' ||
    statusLower === 'cancelled' ||
    statusLower === 'cancelled' ||
    statusLower === 'suspended' ||
    statusLower === 'banned' ||
    statusLower === 'terminated' ||
    statusLower === 'expired' ||
    statusLower === 'closed' ||
    statusLower === 'deleted' ||
    statusLower === 'no show' ||
    statusLower === 'on leave' ||
    statusLower === 'resigned' ||
    statusLower === 'refunded'
  ) {
    return {
      bg: 'bg-muted',
      text: 'text-white',
      border: 'border-safe-dark',
    }
  }

  if (
    statusLower === 'failed' ||
    statusLower === 'error' ||
    statusLower === 'rejected' ||
    statusLower === 'overdue'
  ) {
    return {
      bg: 'bg-danger',
      text: 'text-white',
      border: 'border-danger-dark',
    }
  }

  // Default - Safe/Grey
  return {
    bg: 'bg-muted',
    text: 'text-white',
    border: 'border-safe',
  }
}

/**
 * Get human-readable status label
 */
export function getStatusLabel(status: StatusType): string {
  // If status is already in Title Case (like enum values), return as is
  if (status.includes(' ') || (status[0] === status[0].toUpperCase() && !status.includes('_'))) {
    return status
  }
  
  // Convert snake_case or camelCase to Title Case
  return status
    .split(/[_\s-]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}
