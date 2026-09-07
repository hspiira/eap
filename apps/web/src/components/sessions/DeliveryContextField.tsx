import { useQuery } from "@tanstack/react-query"

import { providerAffiliationsApi } from "@/api/endpoints/provider-affiliations"
import { FormField } from "@/components/common/FormField"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { ProviderAffiliation } from "@/types/entities"
import { OrganisationApprovalStatus, SessionDeliveryContext } from "@/types/enums"

/**
 * The wall-clock date of a `datetime-local` value.
 *
 * Taken as typed rather than converted, because the server resolves the
 * scheduled time to a day in the tenant timezone and is the authority on
 * whether an affiliation covers it.
 */
function scheduledDate(scheduledAt: string): string | undefined {
  return /^\d{4}-\d{2}-\d{2}/.test(scheduledAt) ? scheduledAt.slice(0, 10) : undefined
}

/** The two contexts a new booking may choose. `Unknown` is not one of them. */
type BookableContext = SessionDeliveryContext.DIRECT | SessionDeliveryContext.ORGANISATION

function optionLabel(affiliation: ProviderAffiliation): string {
  if (!affiliation.organisation_is_active) return `${affiliation.organisation_name} (inactive)`
  if (affiliation.organisation_approval_status !== OrganisationApprovalStatus.APPROVED) {
    return `${affiliation.organisation_name} (${affiliation.organisation_approval_status})`
  }
  return affiliation.organisation_name
}

/**
 * Explicit choice between direct and organisation delivery.
 *
 * There is no default: a booking records who the session is delivered
 * through, and guessing it would misattribute the session. `Unknown` is not
 * offered, because it belongs only to historical records.
 */
export function DeliveryContextField({
  providerId,
  scheduledAt,
  context,
  affiliationId,
  onContextChange,
  onAffiliationChange,
  contextError,
  affiliationError,
}: {
  providerId: string
  scheduledAt: string
  context: BookableContext | undefined
  affiliationId: string
  onContextChange: (value: BookableContext) => void
  onAffiliationChange: (value: string) => void
  contextError?: string
  affiliationError?: string
}) {
  const validAt = scheduledDate(scheduledAt)
  const query = useQuery({
    queryKey: ["provider-affiliations", "list", { provider_id: providerId, valid_at: validAt }],
    queryFn: () =>
      providerAffiliationsApi.list({ provider_id: providerId, valid_at: validAt, limit: 100 }),
    enabled: Boolean(providerId && validAt),
  })

  const affiliations = query.data?.items ?? []
  const isOrganisation = context === SessionDeliveryContext.ORGANISATION

  return (
    <>
      <FormField
        label="Delivered through"
        required
        error={contextError}
        htmlFor="ss-delivery-context"
      >
        <Select
          value={context ?? ""}
          onValueChange={(value) => onContextChange(value as BookableContext)}
        >
          <SelectTrigger id="ss-delivery-context">
            <SelectValue placeholder="Direct or organisation" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={SessionDeliveryContext.DIRECT}>Direct</SelectItem>
            <SelectItem value={SessionDeliveryContext.ORGANISATION}>An organisation</SelectItem>
          </SelectContent>
        </Select>
      </FormField>

      {isOrganisation ? (
        <FormField
          label="Organisation"
          required
          description="Only firms represented on the scheduled date."
          error={affiliationError}
          htmlFor="ss-affiliation"
        >
          <AffiliationSelect
            pending={query.isPending}
            hasDate={Boolean(validAt)}
            affiliations={affiliations}
            value={affiliationId}
            onChange={onAffiliationChange}
          />
        </FormField>
      ) : null}
    </>
  )
}

function AffiliationSelect({
  pending,
  hasDate,
  affiliations,
  value,
  onChange,
}: {
  pending: boolean
  hasDate: boolean
  affiliations: ProviderAffiliation[]
  value: string
  onChange: (value: string) => void
}) {
  if (!hasDate) {
    return <p className="text-xs text-fg-muted">Set the scheduled time first.</p>
  }
  if (pending) return <p className="text-xs text-fg-muted">Loading affiliations…</p>
  if (affiliations.length === 0) {
    return (
      <p className="text-xs text-danger-fg">
        This practitioner represents no organisation on the scheduled date. Add an affiliation, or
        book the session as direct delivery.
      </p>
    )
  }
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger id="ss-affiliation">
        <SelectValue placeholder="Choose an organisation" />
      </SelectTrigger>
      <SelectContent>
        {affiliations.map((affiliation) => (
          <SelectItem key={affiliation.id} value={affiliation.id}>
            {optionLabel(affiliation)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
