import { useEffect, useState } from "react"

import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"

export interface ReasonDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel: string
  /** Rendered above the reason field, e.g. the target status selector. */
  children?: React.ReactNode
  /** Disables confirm while the caller's own inputs are incomplete. */
  disabled?: boolean
  onConfirm: (reason: string) => Promise<void>
}

/**
 * Confirmation for a command the API will reject without a reason.
 *
 * The reason is required here rather than defaulted, because the audit record
 * is the point: a generated reason would record nothing.
 */
export function ReasonDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  children,
  disabled,
  onConfirm,
}: ReasonDialogProps) {
  const [reason, setReason] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) setReason("")
  }, [open])

  const confirm = async () => {
    setSaving(true)
    try {
      await onConfirm(reason.trim())
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="space-y-3.5">
          {children}
          <FormField
            label="Reason"
            required
            description="Recorded on the audit trail with your name and the time."
            htmlFor="reason"
          >
            <Textarea
              id="reason"
              rows={3}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="e.g. accreditation certificate verified with the authority"
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={() => void confirm()}
            disabled={saving || disabled || !reason.trim()}
          >
            {saving ? "Saving…" : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
