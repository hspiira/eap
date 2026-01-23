/**
 * Lifecycle Actions Component
 * Context-aware action buttons for entity lifecycle operations
 */

import { useState } from 'react'
import { Power, Archive, Trash2, RotateCcw, CheckCircle, XCircle } from 'lucide-react'
import { ConfirmDialog } from './ConfirmDialog'
import type { BaseStatus } from '@/types/enums'

export type LifecycleAction =
  | 'activate'
  | 'deactivate'
  | 'archive'
  | 'unarchive'
  | 'delete'
  | 'restore'
  | 'approve'
  | 'reject'

export interface LifecycleActionsProps {
  currentStatus: BaseStatus | string
  onAction: (action: LifecycleAction) => Promise<void> | void
  availableActions?: LifecycleAction[]
  loading?: boolean
  className?: string
  // Custom labels
  labels?: Partial<Record<LifecycleAction, string>>
  // Custom confirmation messages
  confirmations?: Partial<Record<LifecycleAction, { title: string; message: string }>>
}

const defaultLabels: Record<LifecycleAction, string> = {
  activate: 'Activate',
  deactivate: 'Deactivate',
  archive: 'Archive',
  unarchive: 'Unarchive',
  delete: 'Delete',
  restore: 'Restore',
  approve: 'Approve',
  reject: 'Reject',
}

const defaultConfirmations: Record<LifecycleAction, { title: string; message: string }> = {
  activate: {
    title: 'Activate Item',
    message: 'Are you sure you want to activate this item?',
  },
  deactivate: {
    title: 'Deactivate Item',
    message: 'Are you sure you want to deactivate this item?',
  },
  archive: {
    title: 'Archive Item',
    message: 'Are you sure you want to archive this item? This action can be reversed.',
  },
  unarchive: {
    title: 'Unarchive Item',
    message: 'Are you sure you want to unarchive this item?',
  },
  delete: {
    title: 'Delete Item',
    message: 'Are you sure you want to delete this item? This action cannot be undone.',
  },
  restore: {
    title: 'Restore Item',
    message: 'Are you sure you want to restore this item?',
  },
  approve: {
    title: 'Approve Item',
    message: 'Are you sure you want to approve this item?',
  },
  reject: {
    title: 'Reject Item',
    message: 'Are you sure you want to reject this item?',
  },
}

const actionIcons: Record<LifecycleAction, typeof Power> = {
  activate: Power,
  deactivate: Power,
  archive: Archive,
  unarchive: RotateCcw,
  delete: Trash2,
  restore: RotateCcw,
  approve: CheckCircle,
  reject: XCircle,
}

/**
 * Determine available actions based on current status
 */
function getAvailableActions(
  currentStatus: BaseStatus | string,
  providedActions?: LifecycleAction[]
): LifecycleAction[] {
  if (providedActions) {
    return providedActions
  }

  const status = currentStatus.toLowerCase()

  // Default logic based on status
  if (status === 'active') {
    return ['deactivate', 'archive']
  }

  if (status === 'inactive') {
    return ['activate', 'archive']
  }

  if (status === 'archived') {
    return ['unarchive', 'delete']
  }

  if (status === 'deleted') {
    return ['restore']
  }

  if (status === 'pending') {
    return ['approve', 'reject']
  }

  // Default: allow activate and archive
  return ['activate', 'archive']
}

/**
 * Determine if action requires confirmation
 */
function requiresConfirmation(action: LifecycleAction): boolean {
  const destructiveActions: LifecycleAction[] = [
    'delete',
    'deactivate',
    'archive',
    'reject',
  ]
  return destructiveActions.includes(action)
}

export function LifecycleActions({
  currentStatus,
  onAction,
  availableActions,
  loading = false,
  className = '',
  labels = {},
  confirmations = {},
}: LifecycleActionsProps) {
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean
    action: LifecycleAction | null
  }>({
    isOpen: false,
    action: null,
  })

  const actions = getAvailableActions(currentStatus, availableActions)

  const handleAction = async (action: LifecycleAction) => {
    if (requiresConfirmation(action)) {
      setConfirmDialog({ isOpen: true, action })
    } else {
      await onAction(action)
    }
  }

  const handleConfirm = async () => {
    if (confirmDialog.action) {
      await onAction(confirmDialog.action)
      setConfirmDialog({ isOpen: false, action: null })
    }
  }

  const handleCancel = () => {
    setConfirmDialog({ isOpen: false, action: null })
  }

  if (actions.length === 0) {
    return null
  }

  const currentAction = confirmDialog.action
  const confirmation = currentAction
    ? confirmations[currentAction] || defaultConfirmations[currentAction]
    : null

  return (
    <>
      <div className={`flex flex-wrap gap-2 ${className}`}>
        {actions.map((action) => {
          const Icon = actionIcons[action]
          const label = labels[action] || defaultLabels[action]
          const isDestructive = requiresConfirmation(action)

          return (
            <button
              key={action}
              onClick={() => handleAction(action)}
              disabled={loading}
              className={`flex items-center gap-2 px-4 py-2 border border-[0.5px] rounded-none transition-colors disabled:opacity-50 ${
                isDestructive
                  ? 'bg-natural-dark hover:bg-natural text-white border-natural-dark'
                  : 'bg-safe hover:bg-safe-dark text-white border-safe-dark'
              }`}
            >
              <Icon size={16} />
              <span>{label}</span>
            </button>
          )
        })}
      </div>

      {confirmation && currentAction && (
        <ConfirmDialog
          isOpen={confirmDialog.isOpen}
          onClose={handleCancel}
          onConfirm={handleConfirm}
          title={confirmation.title}
          message={confirmation.message}
          variant={currentAction === 'delete' ? 'danger' : 'warning'}
          loading={loading}
        />
      )}
    </>
  )
}
