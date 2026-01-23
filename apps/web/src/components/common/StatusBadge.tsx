/**
 * Status Badge Component
 * Displays status with color coding based on status type
 */

import { getStatusColors, getStatusLabel } from '@/utils/statusColors'
import type {
  BaseStatus,
  UserStatus,
  TenantStatus,
  ContractStatus,
  SessionStatus,
  DocumentStatus,
  PaymentStatus,
  WorkStatus,
} from '@/types/enums'
import { LucideIcon } from 'lucide-react'

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

export interface StatusBadgeProps {
  status: StatusType
  size?: 'sm' | 'md' | 'lg'
  icon?: LucideIcon
  showLabel?: boolean
  className?: string
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-1.5 text-base',
}

const iconSizeClasses = {
  sm: 12,
  md: 14,
  lg: 16,
}

export function StatusBadge({
  status,
  size = 'md',
  icon: Icon,
  showLabel = true,
  className = '',
}: StatusBadgeProps) {
  const colors = getStatusColors(status)
  const label = showLabel ? getStatusLabel(status) : ''

  return (
    <span
      className={`inline-flex items-center gap-1.5 ${colors.bg} ${colors.text} border border-[0.5px] ${colors.border || 'border-transparent'} ${sizeClasses[size]} font-medium rounded-none ${className}`}
    >
      {Icon && <Icon size={iconSizeClasses[size]} />}
      {label}
    </span>
  )
}
