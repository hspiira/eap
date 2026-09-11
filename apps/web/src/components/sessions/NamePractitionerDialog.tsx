import { useEffect, useState } from "react"

import { ProviderPicker } from "@/components/common/EntityPicker"
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

/**
 * Say who a stalled import row meant, without leaving the review.
 *
 * Resolving the name does not rescue the rows already staged: they were judged
 * against the reference data as it stood, and only staging the file again
 * re-judges them. The dialog says so rather than letting a fixed name look
 * like a fixed batch.
 */
export function NamePractitionerDialog({
  sourceName,
  open,
  onOpenChange,
  onConfirm,
}: {
  sourceName: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (providerId: string) => Promise<void>
}) {
  const [providerId, setProviderId] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) setProviderId("")
  }, [open, sourceName])

  if (sourceName === null) return null

  const confirm = async () => {
    setSaving(true)
    try {
      await onConfirm(providerId)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Name the practitioner</DialogTitle>
          <DialogDescription>
            Record who {sourceName} is, so rows spelling it that way stop stalling.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3.5">
          <FormField
            label="Practitioner"
            required
            description="Accreditation and panel status do not limit this list: a past session may name someone no longer eligible to take new work."
          >
            <ProviderPicker value={providerId} onChange={setProviderId} />
          </FormField>
          <p className="border border-fg/15 bg-surface px-3 py-2 text-xs leading-relaxed text-fg/70">
            This batch keeps the outcome it already has. Stage the file again to re-judge these rows
            against the name you just recorded.
          </p>
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
            disabled={saving || !providerId}
          >
            {saving ? "Saving…" : "Record"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
