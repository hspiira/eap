import { useEffect, useState } from "react"

import { useQueries } from "@tanstack/react-query"

import type { ProviderAlias } from "@/api/endpoints/provider-aliases"
import { providersApi } from "@/api/endpoints/providers"
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
import { queryKeys } from "@/lib/query-keys"
import { AliasResolutionState } from "@/types/enums"

/**
 * Name a practitioner for one source spelling.
 *
 * Candidates are offered as one-click picks because an ambiguous alias already
 * carries the shortlist the importer found, but choosing one is still the
 * person's decision: nothing is preselected, including when only one candidate
 * exists.
 */
export function AliasResolveDialog({
  alias,
  open,
  onOpenChange,
  onConfirm,
}: {
  alias: ProviderAlias | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (providerId: string) => Promise<void>
}) {
  const [providerId, setProviderId] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) setProviderId("")
  }, [open, alias?.id])

  const candidateIds = alias?.candidate_provider_ids ?? []
  const candidates = useQueries({
    queries: candidateIds.map((id) => ({
      queryKey: queryKeys.providers.detail(id),
      queryFn: () => providersApi.getById(id),
      staleTime: 5 * 60_000,
    })),
  })

  if (alias === null) return null

  const reassigning = alias.state === AliasResolutionState.RESOLVED

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
            Attribute every imported row spelling {alias.source_value} in {alias.source_system} to
            the practitioner you choose.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3.5">
          {reassigning ? (
            <p className="border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-fg/80">
              This name is already resolved. Choosing a different practitioner reattributes every
              session already imported under it.
            </p>
          ) : null}

          {candidateIds.length > 0 ? (
            <FormField
              label="Candidates the importer found"
              description="Suggestions only. Nothing is chosen until you pick one."
            >
              <ul className="space-y-1">
                {candidateIds.map((id, index) => {
                  const candidate = candidates[index]
                  const label = candidate?.data?.display_name ?? id
                  return (
                    <li key={id}>
                      <Button
                        type="button"
                        variant={providerId === id ? "default" : "outline"}
                        size="sm"
                        className="h-auto w-full justify-start px-3 py-1.5 text-left text-xs font-normal"
                        onClick={() => setProviderId(id)}
                      >
                        {candidate?.isPending ? "Loading…" : label}
                      </Button>
                    </li>
                  )
                })}
              </ul>
            </FormField>
          ) : null}

          <FormField
            label="Practitioner"
            required
            description="Search the full directory. Accreditation and panel status do not limit this list, because a historical session may name someone no longer eligible to take new work."
          >
            <ProviderPicker value={providerId} onChange={setProviderId} />
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
            disabled={saving || !providerId}
          >
            {saving ? "Saving…" : reassigning ? "Reattribute" : "Resolve"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
