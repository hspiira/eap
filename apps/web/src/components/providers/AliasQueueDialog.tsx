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
import { Input } from "@/components/ui/input"

/**
 * Open a review queue entry for a name a source file uses.
 *
 * Staging reads decisions and never opens one, so a name nobody has queued has
 * nothing for a reviewer to act on. Queueing attributes nothing: the entry
 * starts unmapped and naming the practitioner is the separate resolve step.
 */
export function AliasQueueDialog({
  sourceSystem,
  open,
  onOpenChange,
  onConfirm,
}: {
  sourceSystem: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (sourceValue: string) => Promise<void>
}) {
  const [sourceValue, setSourceValue] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) setSourceValue("")
  }, [open])

  const confirm = async () => {
    setSaving(true)
    try {
      await onConfirm(sourceValue.trim())
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Queue a name</DialogTitle>
          <DialogDescription>
            Add a spelling from {sourceSystem} to the review queue so it can be reconciled.
          </DialogDescription>
        </DialogHeader>

        <FormField
          label="Name as the source file spells it"
          required
          description="Paste it exactly. Titles and punctuation are dropped for matching, but the original is kept on the record."
          htmlFor="alias-source-value"
        >
          <Input
            id="alias-source-value"
            value={sourceValue}
            onChange={(event) => setSourceValue(event.target.value)}
            placeholder="e.g. Dr. Jane N. Achieng"
          />
        </FormField>

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
            disabled={saving || !sourceValue.trim()}
          >
            {saving ? "Queueing…" : "Queue"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
