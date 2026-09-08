import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { AlertTriangle } from "lucide-react"

import { providerAffiliationsApi } from "@/api/endpoints/provider-affiliations"
import { providersApi } from "@/api/endpoints/providers"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { FormField } from "@/components/common/FormField"
import { ProviderNonCompetePanel } from "@/components/providers/ProviderNonCompetePanel"
import { ReasonDialog } from "@/components/providers/ReasonDialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import { addDaysToDay, formatDay } from "@/lib/format"
import type { ProviderAffiliation } from "@/types/entities"
import { OrganisationApprovalStatus } from "@/types/enums"

/**
 * Whether organisation delivery through this firm would be accepted today.
 * A preview only: the booking write re-checks it.
 */
function deliverable(affiliation: ProviderAffiliation): boolean {
  return (
    affiliation.organisation_is_active &&
    affiliation.organisation_approval_status === OrganisationApprovalStatus.APPROVED
  )
}

function hasEnded(affiliation: ProviderAffiliation, today: string): boolean {
  return Boolean(affiliation.valid_until && affiliation.valid_until <= today)
}

/**
 * Stored end dates are exclusive, so the last covered day is the day before.
 * The reader is shown the covered period; the stored value stays available
 * where it is edited, because attribution depends on the exact boundary.
 */
function coverageLabel(affiliation: ProviderAffiliation): string {
  const from = formatDay(affiliation.valid_from)
  if (!affiliation.valid_until) return `${from} onwards`
  return `${from} to ${formatDay(addDaysToDay(affiliation.valid_until, -1))}`
}

function AffiliationRow({
  affiliation,
  sessionCount,
  onSetEnd,
  ended,
}: {
  affiliation: ProviderAffiliation
  sessionCount?: number
  onSetEnd?: () => void
  ended: boolean
}) {
  const blocked = !deliverable(affiliation)
  return (
    <li className="border border-fg/10 p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            to="/provider-organisations/$organisationId"
            params={{ organisationId: affiliation.organisation_id }}
            className="text-sm font-medium text-primary hover:underline"
          >
            {affiliation.organisation_name}
          </Link>
          <p className="mt-0.5 text-xs text-fg-muted">
            {coverageLabel(affiliation)}
            {affiliation.valid_until ? (
              <span className="text-fg-subtle"> · ends before {affiliation.valid_until}</span>
            ) : null}
          </p>
          {sessionCount ? (
            <p className="mt-0.5 text-xs text-fg/70">
              {sessionCount} session{sessionCount === 1 ? "" : "s"} attributed to this firm
            </p>
          ) : null}
        </div>
        {onSetEnd ? (
          <Button type="button" variant="outline" size="sm" onClick={onSetEnd}>
            {ended ? "Change end" : "Set end"}
          </Button>
        ) : null}
      </div>
      {blocked && !ended ? (
        <p className="mt-2 flex items-start gap-1.5 border-t border-fg/10 pt-2 text-xs text-danger-fg">
          <AlertTriangle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <span>
            {affiliation.organisation_is_active
              ? `Supplier approval is ${affiliation.organisation_approval_status}.`
              : "This firm is inactive."}{" "}
            A booking delivered through it will be refused.
          </span>
        </p>
      ) : null}
    </li>
  )
}

/**
 * The practitioner's commitments: who they represent, and what they have signed.
 *
 * The two are kept apart rather than interleaved. An affiliation is
 * organisation-specific and load-bearing, deciding both session attribution and
 * whether an organisation-delivered booking is accepted. A non-compete clause
 * carries no organisation at all and restricts nothing. Showing them as peers
 * would imply an equivalence the model does not have.
 */
export function ProviderCommitmentsPanel({ providerId }: { providerId: string }) {
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
  const delivery = useQuery({
    queryKey: ["providers", providerId, "delivery-stats"],
    queryFn: () => providersApi.getDeliveryStats(providerId),
  })

  const sessionsByOrganisation = new Map(
    (delivery.data?.by_organisation ?? []).map((entry) => [
      entry.organisation_id,
      entry.session_count,
    ]),
  )

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

  const today = new Date().toISOString().slice(0, 10)
  const items = query.data?.items ?? []
  const current = items.filter((item) => !hasEnded(item, today))
  const ended = items.filter((item) => hasEnded(item, today))

  return (
    <div className="space-y-4">
      <DetailCard title="Organisation affiliations">
        <p className="mb-4 text-sm text-fg-muted">
          The firms this practitioner represents, and when. An affiliation decides which
          organisation a session is attributed to, and organisation delivery needs one that covers
          the session date. Concurrent affiliations with different firms are allowed.
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
          <div className="space-y-4">
            <section className="space-y-2">
              <h4 className="text-xs font-semibold tracking-wide text-fg-muted">Current</h4>
              {current.length === 0 ? (
                <p className="text-sm text-fg-muted">
                  None. This practitioner currently delivers directly.
                </p>
              ) : (
                <ul className="space-y-2">
                  {current.map((affiliation) => (
                    <AffiliationRow
                      key={affiliation.id}
                      affiliation={affiliation}
                      ended={false}
                      sessionCount={sessionsByOrganisation.get(affiliation.organisation_id)}
                      onSetEnd={canWrite ? () => openEdit(affiliation) : undefined}
                    />
                  ))}
                </ul>
              )}
            </section>

            {ended.length > 0 ? (
              <section className="space-y-2 border-t border-fg/10 pt-4">
                <h4 className="text-xs font-semibold tracking-wide text-fg-muted">Ended</h4>
                <p className="text-xs text-fg-muted">
                  Kept because sessions delivered then are still attributed to these firms.
                </p>
                <ul className="space-y-2">
                  {ended.map((affiliation) => (
                    <AffiliationRow
                      key={affiliation.id}
                      affiliation={affiliation}
                      ended
                      sessionCount={sessionsByOrganisation.get(affiliation.organisation_id)}
                      onSetEnd={canWrite ? () => openEdit(affiliation) : undefined}
                    />
                  ))}
                </ul>
              </section>
            ) : null}
          </div>
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

      <ProviderNonCompetePanel providerId={providerId} />
    </div>
  )
}
