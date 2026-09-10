import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, SquarePen, Users } from "lucide-react"

import { membersApi } from "@/api/endpoints/members"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { MemberLink } from "@/components/common/MemberLink"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { SessionHistory } from "@/components/common/SessionHistory"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { MemberAccountCard } from "@/components/MemberAccountCard"
import { MemberBeneficiaries, MemberNextOfKinCard } from "@/components/MemberDetailSections"
import { MemberFormSheet } from "@/components/MemberFormSheet"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite, useHasClinicalScope } from "@/hooks/useCanWrite"
import { nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import { entityDetailKey } from "@/lib/queries"
import type { Member } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/members/$memberId")({ component: MemberDetailPage })

function MemberDetailPage() {
  const { memberId } = Route.useParams()
  const navigate = useNavigate()
  const query = useQuery({
    queryKey: entityDetailKey("members", memberId),
    queryFn: () => membersApi.getById(memberId),
  })

  if (query.isPending) return <DetailSkeleton />
  if (query.isError || !query.data) {
    return (
      <EmptyState
        title="Member not found"
        description="This member may have been removed or belongs to another tenant."
        action={
          <Button className="rounded-none" onClick={() => navigate({ to: "/members" })}>
            Back to members
          </Button>
        }
      />
    )
  }

  return <MemberDetail key={memberId} member={query.data} />
}

function MemberDetail({ member }: { member: Member }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const canWrite = useCanWrite()
  const toast = useToast()
  const [editing, setEditing] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [tab, setTab] = useState("overview")
  const { hasScope: hasClinicalScope, isLoading: clinicalScopeLoading } = useHasClinicalScope()

  const label = member.display_label ?? member.employer_member_id
  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        const updated =
          action === "suspend"
            ? await membersApi.suspend(id)
            : action === "terminate"
              ? await membersApi.terminate(id)
              : await membersApi.reinstate(id)
        queryClient.setQueryData(entityDetailKey("members", id), updated)
        await queryClient.invalidateQueries({ queryKey: ["members"] })
        toast.showSuccess("Member status updated")
      } catch (error) {
        toast.showError(normalizeErrorMessage(error, "Could not update member status"))
      } finally {
        setActionLoading(false)
      }
    },
    [queryClient, toast],
  )

  return (
    <PageShell
      icon={Users}
      breadcrumb={`Members · ${label}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="size-7 rounded-none p-0"
            onClick={() => navigate({ to: "/members" })}
            aria-label="Back to members"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
          {canWrite ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 rounded-none gap-1.5 px-2.5"
              onClick={() => setEditing(true)}
            >
              <SquarePen className="size-3.5" />
              Edit
            </Button>
          ) : null}
        </>
      }
    >
      <MemberFormSheet
        open={editing}
        onOpenChange={setEditing}
        member={member}
        onSaved={(updated) =>
          queryClient.setQueryData(entityDetailKey("members", updated.id), updated)
        }
      />

      <div className="flex min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid w-full grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={setTab}>
              <TabsList className="mb-5 px-0">
                <Tab value="overview">Overview</Tab>
                <Tab value="sessions" disabled={clinicalScopeLoading || !hasClinicalScope}>
                  Service history
                </Tab>
                <Tab value="account">Account access</Tab>
              </TabsList>
              <TabPanel value="overview">
                <div className="mb-5 flex items-center gap-3 border-b border-fg/10 bg-surface px-4 py-3">
                  <span
                    aria-hidden
                    className="grid size-9 place-items-center bg-primary/10 text-xs font-semibold text-primary"
                  >
                    {nameInitials(label)}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-base font-semibold text-fg">{label}</p>
                    <p className="text-xs text-fg-muted">{member.employer_member_id}</p>
                  </div>
                  <StatusBadge status={member.status} />
                </div>
                <div className="grid gap-4 lg:grid-cols-2">
                  <DetailCard title="Membership">
                    <DetailGrid>
                      <DetailRow label="Relationship" value={getStatusLabel(member.relation)} />
                      <DetailRow
                        label="Client"
                        value={
                          <Link
                            to="/clients/$clientId"
                            params={{ clientId: member.client_id }}
                            className="text-primary hover:underline"
                          >
                            {member.client_name || "Open client"}
                          </Link>
                        }
                      />
                    </DetailGrid>
                  </DetailCard>
                  <DetailCard title="Personal details">
                    <DetailGrid>
                      <DetailRow label="Date of birth" value={member.date_of_birth} />
                      <DetailRow label="Gender" value={member.gender} />
                    </DetailGrid>
                  </DetailCard>
                  <DetailCard title="Contact">
                    <DetailGrid>
                      <DetailRow label="Phone" value={member.phone} />
                      <DetailRow label="Work email" value={member.work_email} />
                      <DetailRow label="Personal email" value={member.personal_email} />
                    </DetailGrid>
                  </DetailCard>
                  <DetailCard title="Identification">
                    <DetailGrid>
                      <DetailRow label="Staff ID" value={member.import_source_id} />
                      <DetailRow
                        label="Staff number (reference only)"
                        value={member.staff_number}
                      />
                      <DetailRow label="National ID" value={member.national_id} />
                      <DetailRow label="Passport" value={member.passport_number} />
                    </DetailGrid>
                  </DetailCard>
                  <MemberEmploymentCard member={member} />
                  <MemberNextOfKinCard member={member} />
                </div>
              </TabPanel>
              <TabPanel value="sessions">
                <SessionHistory memberId={member.id} limit={20} />
              </TabPanel>
              <TabPanel value="account">
                <MemberAccountCard
                  member={member}
                  onChanged={(updated) =>
                    queryClient.setQueryData(entityDetailKey("members", updated.id), updated)
                  }
                />
              </TabPanel>
            </Tabs>
          </div>
          <aside className="col-span-12 min-w-0 space-y-5 lg:sticky lg:top-3 lg:col-span-4 lg:max-h-[80vh] lg:overflow-y-auto lg:pt-14">
            <MemberGlanceSection member={member} />
            <BeneficiaryRelationSection member={member} />
            {member.relation === "Employee" && <MemberBeneficiaries member={member} />}
            <MemberStatusHistory member={member} />
            <RailSection title="Lifecycle">
              <LifecycleActions
                entityId={member.id}
                currentStatus={member.status}
                kind="member"
                onAction={handleAction}
                loading={actionLoading}
              />
            </RailSection>
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function GlanceStat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="border border-fg/10 bg-surface px-3 py-2">
      <p className="text-[11px] text-fg-muted">{label}</p>
      <div className="mt-0.5 truncate text-sm font-medium text-fg">{value}</div>
    </div>
  )
}

/**
 * Roster facts the record already carries and the page used to drop: when the
 * member joined, when the roster last confirmed them, and whether cover is
 * live today.
 */
/** Only rendered when the employer's roster carried these optional columns. */
function MemberEmploymentCard({ member }: { member: Member }) {
  const employment = member.employment
  if (!employment) return null
  return (
    <DetailCard title="Employment">
      <DetailGrid>
        <DetailRow label="Job title" value={employment.job_title} />
        <DetailRow label="Classification" value={employment.job_classification} />
        <DetailRow label="Skill" value={employment.skill} />
        <DetailRow label="Department" value={employment.department} />
        <DetailRow label="Unit" value={employment.unit} />
        <DetailRow label="Contract" value={employment.employment_type} />
      </DetailGrid>
    </DetailCard>
  )
}

function BeneficiaryRelationSection({ member }: { member: Member }) {
  return (
    <RailSection title="Beneficiary relationship">
      {member.relation === "Employee" ? (
        <p className="text-xs text-fg-muted">This is a primary employee member.</p>
      ) : member.primary_employee_member_id ? (
        <MemberLink memberId={member.primary_employee_member_id} />
      ) : (
        <p className="text-xs text-danger-fg">Primary employee missing</p>
      )}
    </RailSection>
  )
}

function CoverTodayValue({ eligible }: { eligible: boolean | undefined }) {
  if (eligible === undefined) return <>-</>
  return (
    <span className={eligible ? "text-success-fg" : "text-fg-muted"}>
      {eligible ? "Eligible" : "Not eligible"}
    </span>
  )
}

function CoverageWindow({ member }: { member: Member }) {
  if (!member.coverage_start && !member.coverage_end) {
    return (
      <p className="text-xs text-fg-muted">
        No coverage window recorded. Cover is set at the client or programme level.
      </p>
    )
  }
  return (
    <p className="text-xs text-fg-muted">
      Cover {member.coverage_start ? formatDate(member.coverage_start) : "open"} to{" "}
      {member.coverage_end ? formatDate(member.coverage_end) : "open ended"}
    </p>
  )
}

function MemberGlanceSection({ member }: { member: Member }) {
  return (
    <RailSection title="At a glance">
      <div className="grid grid-cols-2 gap-2">
        <GlanceStat label="Member since" value={formatDate(member.created_at)} />
        <GlanceStat
          label="Roster confirmed"
          value={member.last_imported_at ? formatDate(member.last_imported_at) : "Not imported"}
        />
        <GlanceStat label="Portal account" value={member.user_id ? "Linked" : "None"} />
        <GlanceStat
          label="Cover today"
          value={<CoverTodayValue eligible={member.is_currently_eligible} />}
        />
      </div>
      <CoverageWindow member={member} />
    </RailSection>
  )
}

/** Only the transitions that actually happened, newest first. */
function MemberStatusHistory({ member }: { member: Member }) {
  const events = [
    { label: "Terminated", at: member.terminated_at },
    { label: "Suspended", at: member.suspended_at },
    { label: "Added to roster", at: member.created_at },
  ].filter((event): event is { label: string; at: string } => Boolean(event.at))

  return (
    <RailSection title="Status history">
      <ul className="space-y-1.5">
        {events.map((event) => (
          <li key={event.label} className="flex items-baseline justify-between gap-2 text-xs">
            <span className="text-fg">{event.label}</span>
            <span className="text-fg-muted">{formatDate(event.at)}</span>
          </li>
        ))}
      </ul>
    </RailSection>
  )
}
