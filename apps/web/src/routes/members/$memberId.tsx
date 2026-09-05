import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, Pencil, Users } from "lucide-react"

import { membersApi } from "@/api/endpoints/members"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { MemberFormSheet } from "@/components/MemberFormSheet"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite } from "@/hooks/useCanWrite"
import { nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDay } from "@/lib/format"
import { entityDetailKey } from "@/lib/queries"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/members/$memberId")({ component: MemberDetailPage })

function MemberDetailPage() {
  const { memberId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const canWrite = useCanWrite()
  const toast = useToast()
  const [editing, setEditing] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const query = useQuery({
    queryKey: entityDetailKey("members", memberId),
    queryFn: () => membersApi.getById(memberId),
  })

  if (query.isPending)
    return <div className="flex-1 p-6 text-sm text-fg-muted">Loading member…</div>
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

  const member = query.data
  const label = member.display_label ?? member.employer_member_id
  const beneficiariesQuery = useQuery({
    queryKey: ["members", "beneficiaries", member.id],
    queryFn: () => membersApi.listBeneficiaries(member.id),
    enabled: member.relation === "Employee",
  })
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
              <Pencil className="size-3.5" />
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
            <div className="mb-5 flex items-center gap-3 border-b border-fg/10 bg-surface px-4 py-3">
              <span
                aria-hidden
                className="grid size-9 place-items-center bg-primary/10 text-xs font-semibold text-primary"
              >
                {nameInitials(label)}
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-base font-semibold text-fg">{label}</h1>
                <p className="text-xs text-fg-muted">{member.employer_member_id}</p>
              </div>
              <StatusBadge status={member.status} />
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <DetailCard title="Membership">
                <DetailGrid>
                  <DetailRow label="Relationship" value={member.relation} />
                  <DetailRow
                    label="Client"
                    value={<span className="font-mono text-xs">{member.client_id}</span>}
                  />
                  <DetailRow
                    label="Currently eligible"
                    value={member.is_currently_eligible ? "Yes" : "No"}
                  />
                  <DetailRow label="Coverage starts" value={formatDay(member.coverage_start)} />
                  <DetailRow label="Coverage ends" value={formatDay(member.coverage_end)} />
                </DetailGrid>
              </DetailCard>
              <DetailCard title="Contact">
                <DetailGrid>
                  <DetailRow label="Work email" value={member.work_email} />
                  <DetailRow label="Personal email" value={member.personal_email} />
                </DetailGrid>
              </DetailCard>
            </div>
          </div>
          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <RailSection title="Beneficiary relationship">
              {member.relation === "Employee" ? (
                <p className="text-xs text-fg-muted">This is a primary employee member.</p>
              ) : member.primary_employee_member_id ? (
                <Link
                  to="/members/$memberId"
                  params={{ memberId: member.primary_employee_member_id }}
                  className="font-mono text-xs text-primary hover:underline"
                >
                  {member.primary_employee_member_id}
                </Link>
              ) : (
                <p className="text-xs text-danger-fg">Primary employee missing</p>
              )}
            </RailSection>
            {member.relation === "Employee" ? (
              <RailSection title="Beneficiaries">
                {beneficiariesQuery.isPending ? (
                  <p className="text-xs text-fg-muted">Loading beneficiaries…</p>
                ) : beneficiariesQuery.data?.length ? (
                  <div className="space-y-2">
                    {beneficiariesQuery.data.map((beneficiary) => (
                      <Link
                        key={beneficiary.id}
                        to="/members/$memberId"
                        params={{ memberId: beneficiary.id }}
                        className="block border border-fg/10 bg-surface px-2.5 py-2 hover:border-fg/25"
                      >
                        <p className="truncate text-xs font-medium text-fg">
                          {beneficiary.display_label ?? beneficiary.employer_member_id}
                        </p>
                        <p className="text-[11px] text-fg-muted">{beneficiary.relation}</p>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-fg-muted">No beneficiaries linked.</p>
                )}
              </RailSection>
            ) : null}
            <RailSection title="Account access">
              <p className="text-xs text-fg-muted">
                Member records do not require a portal account. Invitations are managed separately.
              </p>
            </RailSection>
            <RailSection title="Service history">
              <p className="text-xs text-fg-muted">
                Clinical history remains behind the privacy wall and is accessed through cases.
              </p>
            </RailSection>
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
