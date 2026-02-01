/**
 * Create Person Modal
 * Modal wrapper for adding a client employee or dependent to the roster.
 */

import { CreateModal } from '@/components/common/CreateModal'
import { CreatePersonForm } from './CreatePersonForm'
import type { Person } from '@/types/entities'

export interface CreatePersonModalProps {
  isOpen: boolean
  onClose: () => void
  /** Pre-fill client (e.g. when adding from client detail) */
  initialClientId?: string
  /** Called after successful create; use to refresh list and/or close modal */
  onCreated?: (person: Person) => void
}

export function CreatePersonModal({
  isOpen,
  onClose,
  initialClientId,
  onCreated,
}: CreatePersonModalProps) {
  const handleSuccess = (person: Person) => {
    onCreated?.(person)
    onClose()
  }

  return (
    <CreateModal
      isOpen={isOpen}
      onClose={onClose}
      title="Add person to roster"
    >
      <CreatePersonForm
        initialClientId={initialClientId}
        onSuccess={handleSuccess}
        onCancel={onClose}
      />
    </CreateModal>
  )
}
