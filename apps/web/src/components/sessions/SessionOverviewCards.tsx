import {
  CalendarClock,
  Lock,
  NotebookPen,
  Stethoscope,
  UserRound,
  Users,
  Wrench,
} from "lucide-react"

import { DetailCard, DetailGrid, DetailRow, LinkRow } from "@/components/common/DetailPrimitives"
import { StatusBadge } from "@/components/common/StatusBadge"
import { CATEGORY_LABELS } from "@/components/ServiceFormSheet"
import { SessionDeliveryLabel } from "@/components/sessions/SessionAttribution"
import { useHasClinicalScope } from "@/hooks/useCanWrite"
import { memberLabel } from "@/lib/display"
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
    <DetailCard title="Schedule" icon={CalendarClock}>
      <DetailGrid>
        <DetailRow label="Scheduled at" value={formatDateTime(session.scheduled_at)} />
        <DetailRow
          label="Completed at"
          value={session.completed_at ? formatDateTime(session.completed_at) : null}
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
function DeliveryCard({
  session,
  service,
  provider,
}: Omit<CardProps, "member" | "diagnosisLabel">) {
  const serviceName = service?.name ?? session.service_name
  const practitionerName = provider?.display_name ?? session.provider_display_name
  const practitionerMeta = [provider?.provider_profile.tier, provider?.provider_profile.region]
    .filter(Boolean)
    .join(" · ")
  return (
    <DetailCard title="Service and practitioner" icon={Wrench}>
      <DetailGrid>
        {serviceName ? (
          <LinkRow
            label="Service"
            value={serviceName}
            meta={service?.category ? CATEGORY_LABELS[service.category] : null}
            to="/services/$serviceId"
            params={{ serviceId: session.service_id }}
          />
        ) : null}
        {practitionerName && session.provider_id ? (
          <LinkRow
            label="Practitioner"
            value={practitionerName}
            meta={practitionerMeta || null}
            to="/providers/$providerId"
            params={{ providerId: session.provider_id }}
          />
        ) : (
          <DetailRow label="Practitioner" value={null} />
        )}
        <DetailRow label="Delivered through" value={<SessionDeliveryLabel session={session} />} />
      </DetailGrid>
    </DetailCard>
  )
}

/** What a company-wide session records instead of a subject. */
function EngagementCard({ session }: { session: ServiceSession }) {
  return (
    <DetailCard title="Engagement" icon={Users}>
      <DetailGrid>
        <LinkRow
          label="Client"
          value={session.client_name ?? "Open client"}
          to="/clients/$clientId"
          params={{ clientId: session.client_id }}
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
      <DetailCard title="Subject" icon={UserRound}>
        <p className="text-xs text-fg-muted">No member is attached to this session.</p>
      </DetailCard>
    )
  }
  return (
    <DetailCard title="Subject" icon={UserRound}>
      <DetailGrid>
        <LinkRow
          label="Member"
          value={label}
          meta={member ? getStatusLabel(member.relation) : null}
          to="/members/$memberId"
          params={{ memberId: session.member_id }}
        />
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
      <DetailCard title="Clinical" icon={Stethoscope}>
        <p className="text-xs text-fg-muted">Checking access…</p>
      </DetailCard>
    )
  }
  if (!hasScope) {
    return (
      <DetailCard title="Clinical" icon={Stethoscope}>
        <p className="flex items-center gap-1.5 text-xs text-fg-muted">
          <Lock className="size-3 shrink-0" aria-hidden />
          Clinical detail needs the clinical access scope.
        </p>
      </DetailCard>
    )
  }
  return (
    <DetailCard title="Clinical" icon={Stethoscope} phiLabel="Encrypted at rest">
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
  const { hasScope, isLoading } = useHasClinicalScope()

  if (isLoading) {
    return (
      <DetailCard title="Notes" icon={NotebookPen}>
        <p className="text-xs text-fg-muted">Checking access…</p>
      </DetailCard>
    )
  }
  if (!hasScope) {
    return (
      <DetailCard title="Notes" icon={NotebookPen}>
        <p className="flex items-center gap-1.5 text-xs text-fg-muted">
          <Lock className="size-3 shrink-0" aria-hidden />
          Notes need the clinical access scope.
        </p>
      </DetailCard>
    )
  }
  return (
    <DetailCard title="Notes" icon={NotebookPen} phiLabel="Encrypted at rest">
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
    session.clinical_outcome || session.issue_topic || session.diagnosis_id || session.partner_name,
  )

  return (
    <div className="space-y-4 lg:columns-2 lg:gap-4 lg:space-y-0 [&>*]:break-inside-avoid lg:[&>*]:mb-4">
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
