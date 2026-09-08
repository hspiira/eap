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
import { addDaysToDay, formatDay } from "@/lib/format"
import type { ProviderAffiliation } from "@/types/entities"

function coverageLabel(affiliation: ProviderAffiliation): string {
  const from = formatDay(affiliation.valid_from)
  if (!affiliation.valid_until) return `${from} onwards`
  return `${from} to ${formatDay(addDaysToDay(affiliation.valid_until, -1))}`
}

function PractitionerRow({ affiliation }: { affiliation: ProviderAffiliation }) {
  return (
    <li className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5 border-b border-fg/10 py-2 last:border-b-0">
      <ProviderNameLink providerId={affiliation.provider_id} />
      <span className="text-xs text-fg-muted">
        {coverageLabel(affiliation)}
        {affiliation.valid_until ? (
          <span className="text-fg-subtle"> · ends before {affiliation.valid_until}</span>
        ) : null}
      </span>
    </li>
  )
}

/**
 * Who represents this firm, current before past.
 *
 * Past periods are kept because sessions delivered then are still attributed
 * through them, but they are not who represents the firm today, so they do not
 * share a list with those who do.
 */
function PractitionerList({ items }: { items: ProviderAffiliation[] }) {
  const today = new Date().toISOString().slice(0, 10)
  const current = items.filter((item) => !item.valid_until || item.valid_until > today)
  const past = items.filter((item) => item.valid_until && item.valid_until <= today)

  return (
    <div className="space-y-4">
      <section>
        <h4 className="mb-1 text-xs font-semibold tracking-wide text-fg-muted">
          Represents this firm now
          <span className="ml-1.5 font-normal text-fg-subtle">{current.length}</span>
        </h4>
        {current.length === 0 ? (
          <p className="py-2 text-sm text-fg-muted">Nobody currently represents this firm.</p>
        ) : (
          <ul>
            {current.map((affiliation) => (
              <PractitionerRow key={affiliation.id} affiliation={affiliation} />
            ))}
          </ul>
        )}
      </section>

      {past.length > 0 ? (
        <section className="border-t border-fg/10 pt-3">
          <h4 className="mb-1 text-xs font-semibold tracking-wide text-fg-muted">
            Represented before
            <span className="ml-1.5 font-normal text-fg-subtle">{past.length}</span>
          </h4>
          <p className="mb-1 text-xs text-fg-muted">
            Kept because sessions delivered then are attributed through these periods.
          </p>
          <ul>
            {past.map((affiliation) => (
              <PractitionerRow key={affiliation.id} affiliation={affiliation} />
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}

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
  const [conflict, setConflict] = useState<{ field: string | null; message: string } | null>(null)

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
        // The server names which end of the interval conflicts, so the message
        // goes under that input. It falls back to the top-level sentence,
        // which says the same thing.
        const detail = error.fieldErrors ? Object.keys(error.fieldErrors)[0] : null
        const field = detail === "valid_from" || detail === "valid_until" ? detail : null
        setConflict({ field, message: error.message })
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
        <PractitionerList items={items} />
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
            {conflict && !conflict.field ? (
              <p
                role="alert"
                className="border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-fg"
              >
                {conflict.message}
              </p>
            ) : null}
            <FormField label="Practitioner" required>
              <ProviderPicker value={providerId} onChange={setProviderId} />
            </FormField>
            <FormField
              label="Starts on"
              required
              error={conflict?.field === "valid_from" ? conflict.message : undefined}
              htmlFor="affiliation-from"
            >
              <Input
                id="affiliation-from"
                type="date"
                value={validFrom}
                onChange={(event) => setValidFrom(event.target.value)}
              />
            </FormField>
            <FormField
              label="Ends before"
              description="The last covered day is the day before this date. Leave empty for an open-ended affiliation."
              error={conflict?.field === "valid_until" ? conflict.message : undefined}
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
