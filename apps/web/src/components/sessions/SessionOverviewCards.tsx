import { Link } from "@tanstack/react-router"
import { Wrench } from "lucide-react"

import { DetailCard, DetailGrid, DetailRow } from "@/components/common/DetailPrimitives"
import { StatusBadge } from "@/components/common/StatusBadge"
import { CATEGORY_LABELS } from "@/components/ServiceFormSheet"
import { SessionDeliveryLabel } from "@/components/sessions/SessionAttribution"
import { useHasClinicalScope } from "@/hooks/useCanWrite"
import { memberLabel, nameInitials } from "@/lib/display"
import { formatDateTime } from "@/lib/format"
import type { Member, Provider, Service, ServiceSession } from "@/types/entities"
import { SessionAttendance, SessionCategory } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

interface CardProps {
  session: ServiceSession
  service: Service | null
  member: Member | null
  provider: Provider | null
  diagnosisLabel: string | null
}

function ScheduleCard({ session }: { session: ServiceSession }) {
  return (
    <DetailCard title="Schedule">
      <DetailGrid>
        <DetailRow label="Scheduled at" value={formatDateTime(session.scheduled_at)} fullWidth />
        <DetailRow
          label="Completed at"
          value={session.completed_at ? formatDateTime(session.completed_at) : null}
          fullWidth
        />
        <DetailRow label="Status" value={<StatusBadge status={session.status} />} />
        <DetailRow
          label="Duration"
          value={session.duration != null ? `${session.duration} minutes` : null}
        />
        <DetailRow label="Location" value={session.location} />
        {session.cancellation_reason ? (
          <DetailRow label="Cancelled because" value={session.cancellation_reason} fullWidth />
        ) : null}
      </DetailGrid>
    </DetailCard>
  )
}

/** Service and practitioner, plus how the delivery was attributed. */
function DeliveryCard({ session, service, provider }: Omit<CardProps, "member" | "diagnosisLabel">) {
  const serviceName = service?.name ?? session.service_name
  const practitionerName = provider?.display_name ?? session.provider_display_name
  return (
    <DetailCard title="Service and practitioner">
      {serviceName ? (
        <Link
          to="/services/$serviceId"
          params={{ serviceId: session.service_id }}
          className="mb-2 flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
        >
          <span
            aria-hidden
            className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <Wrench className="size-3.5" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-fg">{serviceName}</p>
            <p className="truncate text-[11px] text-fg-muted">
              {service?.category ? CATEGORY_LABELS[service.category] : "-"}
            </p>
          </div>
        </Link>
      ) : null}
      {practitionerName && session.provider_id ? (
        <Link
          to="/providers/$providerId"
          params={{ providerId: session.provider_id }}
          className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
        >
          <span
            aria-hidden
            className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
          >
            {nameInitials(practitionerName)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-fg">{practitionerName}</p>
            <p className="truncate text-[11px] text-fg-muted">
              {provider?.provider_profile.tier || provider?.provider_profile.region
                ? [provider.provider_profile.tier, provider.provider_profile.region]
                    .filter(Boolean)
                    .join(" · ")
                : "Practitioner"}
            </p>
          </div>
        </Link>
      ) : (
        <p className="text-xs text-fg-muted">No practitioner assigned.</p>
      )}
      <div className="mt-2 border-t border-fg/10 pt-2">
        <p className="text-[11px] font-medium tracking-wide text-fg-muted">Delivered through</p>
        <div className="mt-0.5">
          <SessionDeliveryLabel session={session} />
        </div>
      </div>
    </DetailCard>
  )
}

/** What a company-wide session records instead of a subject. */
function EngagementCard({ session }: { session: ServiceSession }) {
  return (
    <DetailCard title="Engagement">
      <DetailGrid>
        <DetailRow
          label="Client"
          value={
            <Link
              to="/clients/$clientId"
              params={{ clientId: session.client_id }}
              className="text-primary hover:underline"
            >
              {session.client_name ?? "Open client"}
            </Link>
          }
        />
        <DetailRow
          label="Mode of delivery"
          value={session.session_type ? getStatusLabel(session.session_type) : null}
        />
        <DetailRow
          label="Format"
          value={session.category ? getStatusLabel(session.category) : null}
        />
        <DetailRow
          label="New or returning"
          value={session.client_type ? getStatusLabel(session.client_type) : null}
        />
      </DetailGrid>
      <p className="mt-3 text-[11px] text-fg-muted">
        Delivered to the client with nobody individual named. No member is attached, and none is
        missing.
      </p>
    </DetailCard>
  )
}

function SubjectCard({ session, member }: { session: ServiceSession; member: Member | null }) {
  const label = member ? memberLabel(member) : session.member_display_label
  if (!label || !session.member_id) {
    return (
      <DetailCard title="Subject">
        <p className="text-xs text-fg-muted">No member is attached to this session.</p>
      </DetailCard>
    )
  }
  return (
    <DetailCard title="Subject">
      <Link
        to="/members/$memberId"
        params={{ memberId: session.member_id }}
        className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
      >
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
        >
          {nameInitials(label)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">{label}</p>
          <p className="truncate text-[11px] text-fg-muted">
            {member ? getStatusLabel(member.relation) : "Member"}
          </p>
        </div>
      </Link>
      <DetailGrid>
        <DetailRow
          label="New or returning"
          value={session.client_type ? getStatusLabel(session.client_type) : null}
        />
      </DetailGrid>
    </DetailCard>
  )
}

/**
 * The clinical record, behind the clinical scope.
 *
 * Encryption at rest does not decide who may read a field, so the page gates
 * what it shows rather than relying on the cipher.
 */
function ClinicalCard({
  session,
  diagnosisLabel,
}: {
  session: ServiceSession
  diagnosisLabel: string | null
}) {
  const { hasScope, isLoading } = useHasClinicalScope()
  const partnered =
    session.category === SessionCategory.COUPLES || session.category === SessionCategory.FAMILY

  if (isLoading) {
    return (
      <DetailCard title="Clinical">
        <p className="text-xs text-fg-muted">Checking access…</p>
      </DetailCard>
    )
  }
  if (!hasScope) {
    return (
      <DetailCard title="Clinical">
        <p className="text-xs text-fg-muted">
          Clinical detail needs the clinical access scope.
        </p>
      </DetailCard>
    )
  }
  return (
    <DetailCard title="Clinical" phiLabel="Encrypted at rest">
      <DetailGrid>
        <DetailRow
          label="Outcome"
          value={session.clinical_outcome ? getStatusLabel(session.clinical_outcome) : null}
        />
        <DetailRow label="Issue or topic" value={session.issue_topic} />
        <DetailRow label="Diagnosis" value={diagnosisLabel} fullWidth />
        {partnered ? (
          <>
            <DetailRow label="Partner" value={session.partner_name} />
            <DetailRow label="Partner relationship" value={session.partner_relationship} />
          </>
        ) : null}
      </DetailGrid>
    </DetailCard>
  )
}

function NotesCard({ session }: { session: ServiceSession }) {
  return (
    <DetailCard title="Notes" phiLabel="Encrypted at rest">
      {session.notes ? (
        <p className="whitespace-pre-wrap text-sm text-fg">{session.notes}</p>
      ) : (
        <p className="text-xs text-fg-muted">No notes recorded.</p>
      )}
    </DetailCard>
  )
}

/**
 * The overview, in the shape the record actually has.
 *
 * A company-wide session is an event delivered to a client: it has a headcount
 * and no subject. An individual session has a member and a clinical record.
 * Rendering one layout for both leaves a company-wide session hunting for a
 * member that does not exist, and buries what it does carry.
 */
export function SessionOverviewCards({
  session,
  service,
  member,
  provider,
  diagnosisLabel,
}: CardProps) {
  const companyWide = session.attendance === SessionAttendance.COMPANY_WIDE
  const hasClinicalContent = Boolean(
    session.clinical_outcome ||
      session.issue_topic ||
      session.diagnosis_id ||
      session.partner_name,
  )

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <ScheduleCard session={session} />
      {companyWide ? (
        <EngagementCard session={session} />
      ) : (
        <SubjectCard session={session} member={member} />
      )}
      <DeliveryCard session={session} service={service} provider={provider} />
      {companyWide && !hasClinicalContent ? null : (
        <ClinicalCard session={session} diagnosisLabel={diagnosisLabel} />
      )}
      <NotesCard session={session} />
    </div>
  )
}
