import { useState } from "react"

import type { LucideIcon } from "lucide-react"

import { BulkActionButton } from "@/components/common/BulkActionButton"
import { ConfirmDialog } from "@/components/common/ConfirmDialog"
import { type BulkActionOptions, useBulkAction } from "@/hooks/useBulkAction"

interface BulkActionProps extends BulkActionOptions {
  ids: ReadonlySet<string>
  /** Button text, also the confirm button text. */
  label: string
  confirmTitle: string
  /** Receives the selection size so the copy can name it. */
  confirmDescription: (count: number) => string
  /** The action's icon. The bar is icon-only; the label names it on hover. */
  icon: LucideIcon
  destructive?: boolean
}

/** Bulk action for a table selection, behind a confirm step. */
export function BulkAction({
  ids,
  label,
  confirmTitle,
  confirmDescription,
  icon: Icon,
  destructive,
  ...options
}: BulkActionProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const { run, running } = useBulkAction(options)

  return (
    <>
      <BulkActionButton
        label={label}
        icon={Icon}
        destructive={destructive}
        running={running}
        onClick={() => setConfirmOpen(true)}
      />
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
