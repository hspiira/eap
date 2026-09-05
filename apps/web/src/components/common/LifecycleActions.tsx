import { useState } from "react"

import { Button } from "@/components/ui/button"
import { useCanWrite, useCurrentRole } from "@/hooks/useCanWrite"
import { TenantRole } from "@/types/enums"
import { getAllowedLifecycleActions, type LifecycleAction } from "@/utils/lifecycleConfig"

import { ConfirmDialog } from "./ConfirmDialog"

const ACTION_LABELS: Record<LifecycleAction, string> = {
  activate: "Activate",
  deactivate: "Deactivate",
  suspend: "Suspend",
  terminate: "Terminate",
  archive: "Archive",
  restore: "Restore",
  renew: "Renew",
  verify: "Verify",
  ban: "Ban",
  complete: "Complete",
  cancel: "Cancel",
  "no-show": "No-show",
  reschedule: "Reschedule",
  publish: "Publish",
}

const DESTRUCTIVE_ACTIONS: LifecycleAction[] = ["terminate", "archive", "ban", "cancel"]

export interface LifecycleActionsProps {
  entityId: string
  currentStatus: string
  kind:
    | "base"
    | "user"
    | "tenant"
    | "client"
    | "member"
    | "contract"
    | "service"
    | "session"
    | "document"
  onAction: (entityId: string, action: LifecycleAction) => void | Promise<void>
  loading?: boolean
  adminOnlyActions?: ReadonlyArray<LifecycleAction>
}

export function LifecycleActions({
  entityId,
  currentStatus,
  kind,
  onAction,
  loading = false,
  adminOnlyActions = [],
}: LifecycleActionsProps) {
  const [confirmState, setConfirmState] = useState<{
    action: LifecycleAction
    open: boolean
  } | null>(null)

  const canWrite = useCanWrite()
  const currentRole = useCurrentRole()
  const adminOnly = new Set(adminOnlyActions)
  const allowed = getAllowedLifecycleActions(currentStatus, kind).filter(
    (action) => !adminOnly.has(action) || currentRole === TenantRole.ADMIN,
  )
  if (!canWrite || allowed.length === 0) return null

  const handleClick = (action: LifecycleAction) => {
    if (DESTRUCTIVE_ACTIONS.includes(action)) {
      setConfirmState({ action, open: true })
    } else {
      onAction(entityId, action)
    }
  }

  const handleConfirm = async () => {
    if (!confirmState) return
    await onAction(entityId, confirmState.action)
    setConfirmState(null)
  }

  return (
    <>
      <div className="flex flex-wrap gap-2">
        {allowed.map((action) => (
          <Button
            key={action}
            variant="secondary"
            size="sm"
            className="rounded-none"
            onClick={() => handleClick(action)}
            disabled={loading}
          >
            {ACTION_LABELS[action] ?? action}
          </Button>
        ))}
      </div>
      {confirmState && (
        <ConfirmDialog
          open={confirmState.open}
          onOpenChange={(open) => !open && setConfirmState(null)}
          title={`${ACTION_LABELS[confirmState.action]}?`}
          description="This action may not be reversible. Are you sure?"
          confirmLabel={ACTION_LABELS[confirmState.action]}
          onConfirm={handleConfirm}
          destructive
          loading={loading}
        />
      )}
    </>
  )
}
