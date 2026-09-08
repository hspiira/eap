import { useQuery } from "@tanstack/react-query"
import { AlertCircle, CheckCircle2 } from "lucide-react"

import { providerAffiliationsApi } from "@/api/endpoints/provider-affiliations"
import { DetailGrid, DetailRow, RailSection } from "@/components/common/DetailPrimitives"
import { formatDate } from "@/lib/format"
import type { ProviderOrganisation } from "@/types/entities"
import { OrganisationApprovalStatus } from "@/types/enums"

function CheckRow({ ok, label, detail }: { ok: boolean; label: string; detail: string }) {
  const Icon = ok ? CheckCircle2 : AlertCircle
  return (
    <li className="flex items-start gap-2">
      <Icon
        aria-hidden
        className={`mt-0.5 size-3.5 shrink-0 ${ok ? "text-success-fg" : "text-danger-fg"}`}
      />
      <span className="min-w-0">
        <span className="block text-xs text-fg">{label}</span>
        <span className="block text-[11px] text-fg-muted">{detail}</span>
      </span>
    </li>
  )
}

/**
 * Whether this firm can carry delivery, and who represents it.
 *
 * Active and approved are independent facts and both are required, which is
 * why they are shown as two checks rather than one status. A firm can be
 * approved and inactive, and the page has to say which half is missing.
 */
export function OrganisationReadinessRail({
  organisation,
}: {
  organisation: ProviderOrganisation
}) {
  const approved = organisation.approval_status === OrganisationApprovalStatus.APPROVED
  const deliverable = organisation.is_active && approved

  // Same key as the affiliations panel, so this shares its request.
  const affiliations = useQuery({
    queryKey: [
      "provider-affiliations",
      "list",
      { organisation_id: organisation.id, include_ended: true },
    ],
    queryFn: () =>
      providerAffiliationsApi.list({
        organisation_id: organisation.id,
        include_ended: true,
        limit: 100,
      }),
  })

  const today = new Date().toISOString().slice(0, 10)
  const items = affiliations.data?.items ?? []
  const current = items.filter((item) => !item.valid_until || item.valid_until > today)

  return (
    <>
      <RailSection title="Delivery readiness">
        <p className={`text-sm font-semibold ${deliverable ? "text-success-fg" : "text-fg"}`}>
          {deliverable ? "Can carry delivery" : "Cannot carry delivery"}
        </p>
        <ul className="space-y-1.5">
          <CheckRow
            ok={organisation.is_active}
            label="Record active"
            detail={
              organisation.is_active
                ? "The firm is in use."
                : "Reactivate the firm to allow delivery."
            }
          />
          <CheckRow
            ok={approved}
            label="Supplier approved"
            detail={
              approved
                ? "Approved as a supplier."
                : `Approval is ${organisation.approval_status}. Approve the firm to allow delivery.`
            }
          />
        </ul>
        <p className="text-[11px] text-fg-subtle">
          Both are required. Approving a firm accredits nobody: each practitioner is assessed
          separately.
        </p>
      </RailSection>

      <RailSection title="At a glance" className="border-t border-fg/10 pt-4">
        <DetailGrid>
          <DetailRow
            label="Practitioners now"
            value={affiliations.isPending ? "…" : String(current.length)}
          />
          <DetailRow
            label="Ever affiliated"
            value={affiliations.isPending ? "…" : String(items.length)}
          />
          <DetailRow label="On record since" value={formatDate(organisation.created_at)} />
          <DetailRow label="Last updated" value={formatDate(organisation.updated_at)} />
        </DetailGrid>
      </RailSection>
    </>
  )
}
