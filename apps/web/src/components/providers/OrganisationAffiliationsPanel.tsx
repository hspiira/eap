import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"

import { providerAffiliationsApi } from "@/api/endpoints/provider-affiliations"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { ProviderPicker } from "@/components/common/EntityPicker"
import { FormField } from "@/components/common/FormField"
import { ProviderNameLink } from "@/components/providers/ProviderNameLink"
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
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite } from "@/hooks/useCanWrite"
import { isApiError, normalizeErrorMessage } from "@/lib/errors"

/**
 * The practitioners representing this firm, and when.
 *
 * A period runs from its start date up to, but not including, its end date.
 * Two periods for the same practitioner and firm may not overlap; the server
 * rejects an overlap and names the conflicting period.
 */
export function OrganisationAffiliationsPanel({ organisationId }: { organisationId: string }) {
  const toast = useToast()
  const canWrite = useCanWrite()
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = useState(false)
  const [providerId, setProviderId] = useState("")
  const [validFrom, setValidFrom] = useState("")
  const [validUntil, setValidUntil] = useState("")
  const [conflict, setConflict] = useState<string | null>(null)

  const query = useQuery({
    queryKey: [
      "provider-affiliations",
      "list",
      { organisation_id: organisationId, include_ended: true },
    ],
    queryFn: () =>
      providerAffiliationsApi.list({
        organisation_id: organisationId,
        include_ended: true,
        limit: 100,
      }),
  })

  const reset = () => {
    setProviderId("")
    setValidFrom("")
    setValidUntil("")
    setConflict(null)
  }

  const create = async () => {
    setConflict(null)
    try {
      await providerAffiliationsApi.create(organisationId, {
        provider_id: providerId,
        valid_from: validFrom,
        valid_until: validUntil || null,
      })
      await queryClient.invalidateQueries({ queryKey: ["provider-affiliations"] })
      setAddOpen(false)
      reset()
      toast.showSuccess("Affiliation added")
    } catch (error) {
      if (isApiError(error) && error.status === 409) {
        // The top-level message is the sentence naming the conflicting period.
        // `details` currently carries the field name as a value rather than as
        // a field error, so it is not readable text; see PROVIDERS_FRONTEND.md.
        setConflict(error.message)
        return
      }
      toast.showError(normalizeErrorMessage(error, "Could not add the affiliation"))
    }
  }

  const items = query.data?.items ?? []

  return (
    <DetailCard
      title="Affiliated practitioners"
      action={
        canWrite ? (
          <Button type="button" variant="outline" size="sm" onClick={() => setAddOpen(true)}>
            Add affiliation
          </Button>
        ) : null
      }
    >
      {query.isPending ? (
        <p className="text-sm text-fg-muted">Loading affiliations…</p>
      ) : query.isError ? (
        <p role="alert" className="text-sm text-danger-fg">
          {normalizeErrorMessage(query.error, "Could not load affiliations")}
        </p>
      ) : items.length === 0 ? (
        <p className="text-sm text-fg-muted">No practitioner represents this firm yet.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((affiliation) => (
            <li key={affiliation.id} className="border border-fg/10 p-3">
              <ProviderNameLink providerId={affiliation.provider_id} />
              <p className="mt-0.5 text-xs text-fg-muted">
                {affiliation.valid_until
                  ? `${affiliation.valid_from} until ${affiliation.valid_until} exclusive`
                  : `From ${affiliation.valid_from}, open ended`}
              </p>
            </li>
          ))}
        </ul>
      )}

      <Dialog
        open={addOpen}
        onOpenChange={(open) => {
          setAddOpen(open)
          if (!open) reset()
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add an affiliation</DialogTitle>
            <DialogDescription>
              Records that a practitioner represents this firm for a period. A practitioner may
              represent several firms at once, but two periods with this firm cannot overlap.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3.5">
            {conflict ? (
              <p
                role="alert"
                className="border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-fg"
              >
                {conflict}
              </p>
            ) : null}
            <FormField label="Practitioner" required>
              <ProviderPicker value={providerId} onChange={setProviderId} />
            </FormField>
            <FormField label="Starts on" required htmlFor="affiliation-from">
              <Input
                id="affiliation-from"
                type="date"
                value={validFrom}
                onChange={(event) => setValidFrom(event.target.value)}
              />
            </FormField>
            <FormField
              label="Ends before"
              optional
              description="The last covered day is the day before this date. Leave empty for an open-ended affiliation."
              htmlFor="affiliation-until"
            >
              <Input
                id="affiliation-until"
                type="date"
                value={validUntil}
                onChange={(event) => setValidUntil(event.target.value)}
              />
            </FormField>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" size="sm" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              disabled={!providerId || !validFrom}
              onClick={() => void create()}
            >
              Add affiliation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DetailCard>
  )
}
