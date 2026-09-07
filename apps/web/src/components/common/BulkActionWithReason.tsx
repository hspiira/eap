import { useState } from "react"

import { ReasonDialog } from "@/components/providers/ReasonDialog"
import { Button } from "@/components/ui/button"
import { type BulkActionOptions, useBulkAction } from "@/hooks/useBulkAction"

interface BulkActionWithReasonProps extends Omit<BulkActionOptions, "action"> {
  ids: ReadonlySet<string>
  /** Button text, also the confirm button text. */
  label: string
  confirmTitle: string
  /** Receives the selection size so the copy can name it. */
  confirmDescription: (count: number) => string
  /** Applied to one id with the reason collected once for the whole run. */
  action: (id: string, reason: string) => Promise<unknown>
  destructive?: boolean
}

/**
 * Bulk action for a table selection, behind a required-reason confirm step.
 *
 * Sibling to `BulkAction`: same fan-out via `useBulkAction`, but the API
 * rejects these commands without an audit reason, so the confirm step is a
 * `ReasonDialog` instead of a plain `ConfirmDialog`. One reason is collected
 * and applied to every row in the selection, not one per row.
 */
export function BulkActionWithReason({
  ids,
  label,
  confirmTitle,
  confirmDescription,
  action,
  destructive,
  ...options
}: BulkActionWithReasonProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  // `run` always supplies a reason here; the fallback never actually fires,
  // it only satisfies useBulkAction's shared (optional-reason) action type.
  const { run, running } = useBulkAction({
    ...options,
    action: (id, reason) => action(id, reason ?? ""),
  })

  return (
    <>
      <Button
        type="button"
        variant={destructive ? "destructive" : "outline"}
        size="sm"
        className="h-7 px-2.5"
        disabled={running}
        onClick={() => setConfirmOpen(true)}
      >
        {label}
      </Button>
      <ReasonDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={confirmTitle}
        description={confirmDescription(ids.size)}
        confirmLabel={label}
        disabled={running}
        onConfirm={async (reason) => {
          await run(ids, reason)
          setConfirmOpen(false)
        }}
      />
    </>
  )
}
