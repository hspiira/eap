import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { providerAffiliationsApi } from "@/api/endpoints/provider-affiliations"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { FormField } from "@/components/common/FormField"
import { ReasonDialog } from "@/components/providers/ReasonDialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import type { ProviderAffiliation } from "@/types/entities"
import { ProviderApprovalStatus } from "@/types/enums"

/**
 * Whether this firm could satisfy organisation delivery today. A display hint
 * only: the booking write re-checks it.
 */
function deliverable(affiliation: ProviderAffiliation): boolean {
  return (
    affiliation.organisation_is_active &&
    affiliation.organisation_approval_status === ProviderApprovalStatus.APPROVED
  )
}

function intervalLabel(affiliation: ProviderAffiliation): string {
  if (!affiliation.valid_until) return `From ${affiliation.valid_from}, open ended`
  return `${affiliation.valid_from} until ${affiliation.valid_until} exclusive`
}

/**
 * The organisations a practitioner represents, and when.
 *
 * Intervals are start-inclusive and end-exclusive, so the last covered day is
 * the day before `valid_until`. Ended affiliations are shown because past
 * sessions still refer to them.
 */
export function ProviderAffiliationsPanel({ providerId }: { providerId: string }) {
  const toast = useToast()
  const canWrite = useCanWrite()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<ProviderAffiliation | null>(null)
  const [validUntil, setValidUntil] = useState("")

  const query = useQuery({
    queryKey: ["provider-affiliations", "list", { provider_id: providerId, include_ended: true }],
    queryFn: () =>
      providerAffiliationsApi.list({ provider_id: providerId, include_ended: true, limit: 100 }),
  })

  const openEdit = (affiliation: ProviderAffiliation) => {
    setValidUntil(affiliation.valid_until ?? "")
    setEditing(affiliation)
  }

  const save = async (reason: string) => {
    if (!editing) return
    try {
      await providerAffiliationsApi.setValidUntil(editing.id, validUntil || null, reason)
      await queryClient.invalidateQueries({ queryKey: ["provider-affiliations"] })
      setEditing(null)
      toast.showSuccess("Affiliation updated")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not update the affiliation"))
    }
  }

  const items = query.data?.items ?? []

  return (
    <DetailCard title="Organisation affiliations">
      <p className="mb-4 text-sm text-fg-muted">
        Periods during which this practitioner represents a supplier firm. A period covers its start
        date up to, but not including, its end date. Concurrent affiliations with different firms
        are allowed.
      </p>

      {query.isPending ? (
        <p className="text-sm text-fg-muted">Loading affiliations…</p>
      ) : query.isError ? (
        <p role="alert" className="text-sm text-danger-fg">
          {normalizeErrorMessage(query.error, "Could not load affiliations")}
        </p>
      ) : items.length === 0 ? (
        <p className="text-sm text-fg-muted">
          No affiliations on record. This practitioner delivers directly.
        </p>
      ) : (
        <ul className="space-y-2">
          {items.map((affiliation) => (
            <li
              key={affiliation.id}
              className="flex flex-wrap items-start justify-between gap-3 border border-fg/10 p-3"
            >
              <div className="min-w-0">
                <Link
                  to="/provider-organisations/$organisationId"
                  params={{ organisationId: affiliation.organisation_id }}
                  className="text-sm font-medium text-primary hover:underline"
                >
                  {affiliation.organisation_name}
                </Link>
                <p className="mt-0.5 text-xs text-fg-muted">{intervalLabel(affiliation)}</p>
                {deliverable(affiliation) ? null : (
                  <p className="mt-1 text-xs text-danger-fg">
                    {affiliation.organisation_is_active
                      ? `Supplier approval is ${affiliation.organisation_approval_status}`
                      : "This firm is inactive"}
                    . Organisation delivery through it will be refused.
                  </p>
                )}
              </div>
              {canWrite ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => openEdit(affiliation)}
                >
                  Set end
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      <ReasonDialog
        open={editing !== null}
        onOpenChange={(open) => (open ? null : setEditing(null))}
        title="Set the end of this affiliation"
        description="The practitioner and the firm cannot be changed. Only the end of the period is editable, and the end date itself is not covered. Moving an end date can affect sessions already attributed to this firm, so the change is recorded as a correction."
        confirmLabel="Save"
        onConfirm={save}
      >
        <FormField
          label="Ends before"
          optional
          description="The last covered day is the day before this date. Leave empty for an open-ended affiliation."
          htmlFor="affiliation-valid-until"
        >
          <Input
            id="affiliation-valid-until"
            type="date"
            value={validUntil}
            onChange={(event) => setValidUntil(event.target.value)}
          />
        </FormField>
      </ReasonDialog>
    </DetailCard>
  )
}
