import { useState } from "react"

import { ConfirmDialog } from "@/components/common/ConfirmDialog"
import { Button } from "@/components/ui/button"
import { type BulkActionOptions, useBulkAction } from "@/hooks/useBulkAction"

interface BulkActionProps extends BulkActionOptions {
  ids: ReadonlySet<string>
  /** Button text, also the confirm button text. */
  label: string
  confirmTitle: string
  /** Receives the selection size so the copy can name it. */
  confirmDescription: (count: number) => string
  destructive?: boolean
}

/** Bulk action for a table selection, behind a confirm step. */
export function BulkAction({
  ids,
  label,
  confirmTitle,
  confirmDescription,
  destructive,
  ...options
}: BulkActionProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const { run, running } = useBulkAction(options)

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
      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={confirmTitle}
        description={confirmDescription(ids.size)}
        confirmLabel={label}
        destructive={destructive}
        loading={running}
        onConfirm={() => run(ids)}
      />
    </>
  )
}
