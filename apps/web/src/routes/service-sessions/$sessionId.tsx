import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, CalendarClock, Pencil, Wrench } from "lucide-react"

import { diagnosesApi } from "@/api/endpoints/diagnoses"
import { membersApi } from "@/api/endpoints/members"
import { providersApi } from "@/api/endpoints/providers"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { DetailCard, DetailGrid, DetailRow } from "@/components/common/DetailPrimitives"
import { renderDetailState } from "@/components/common/DetailStates"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ServiceSessionFormSheet } from "@/components/ServiceSessionFormSheet"
import {
  CancelDialog,
  CompleteDialog,
  DetailRail,
  FeedbackPanel,
  Hero,
  RescheduleDialog,
} from "@/components/sessions/SessionDetailWidgets"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { memberLabel, nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"
import { entityDetailKey, useEntityDetail } from "@/lib/queries"
import type { ServiceSession } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/service-sessions/$sessionId")({
  component: ServiceSessionDetailPage,
})

type TabValue = "overview" | "feedback" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "feedback", "history"]

function ServiceSessionDetailPage() {
  const { sessionId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()
  const [actionLoading, setActionLoading] = useState(false)
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)
  const [rescheduleOpen, setRescheduleOpen] = useState(false)
  const [completeOpen, setCompleteOpen] = useState(false)
  const [cancelOpen, setCancelOpen] = useState(false)

  const sessionQuery = useEntityDetail<ServiceSession>({
    resource: "service-sessions",
    id: sessionId,
    detailFn: serviceSessionsApi.getById,
  })
  const session = sessionQuery.data ?? null

  const diagnosisTreeQuery = useQuery({
    queryKey: ["diagnoses", "tree"],
    queryFn: () => diagnosesApi.getTree(),
    staleTime: 5 * 60_000,
    enabled: !!session?.diagnosis_id,
  })

  const { data: service = null } = useQuery({
    queryKey: entityDetailKey("services", session?.service_id ?? ""),
    queryFn: () => servicesApi.getById(session!.service_id),
    enabled: !!session?.service_id,
  })

  const { data: member = null } = useQuery({
    queryKey: entityDetailKey("members", session?.member_id ?? ""),
    queryFn: () => membersApi.getById(session!.member_id),
    enabled: !!session?.member_id,
  })

  const providerId = session?.provider_id
  const { data: provider = null } = useQuery({
    queryKey: entityDetailKey("providers", providerId ?? ""),
    queryFn: async () => {
      const res = await providersApi.list({ page: 1, limit: 1, search: providerId as string })
      return (res.items ?? []).find((p) => p.id === providerId) ?? null
    },
    enabled: !!providerId,
  })

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      if (action === "complete") {
        setCompleteOpen(true)
        return
      }
      if (action === "cancel") {
        setCancelOpen(true)
        return
      }
      setActionLoading(true)
      try {
        if (action === "no-show") await serviceSessionsApi.noShow(id)
        else if (action === "archive") await serviceSessionsApi.archive(id)
        else if (action === "restore") await serviceSessionsApi.restore(id)
        else if (action === "reschedule") setRescheduleOpen(true)
        await queryClient.invalidateQueries({ queryKey: ["service-sessions"] })
        await queryClient.invalidateQueries({ queryKey: ["service-sessions", "list"] })
        if (action !== "reschedule") showSuccess("Status updated")
      } catch (err) {
        showError(normalizeErrorMessage(err, "Action failed: please try again"))
      } finally {
        setActionLoading(false)
      }
    },
    [queryClient, queryClient, showSuccess, showError],
  )

  const confirmComplete = useCallback(
    async (duration: number, notes: string) => {
      if (!session) return
      const { drawdown } = await serviceSessionsApi.complete(session.id, { duration, notes })
      await queryClient.invalidateQueries({ queryKey: ["service-sessions"] })
      showSuccess(
        drawdown.consumed
          ? `Session completed. ${drawdown.sessions_remaining} authorized sessions left.`
          : "Session completed",
      )
    },
    [session, queryClient, showSuccess],
  )

  const confirmCancel = useCallback(
    async (reason: string) => {
      if (!session) return
      await serviceSessionsApi.cancel(session.id, { reason })
      await queryClient.invalidateQueries({ queryKey: ["service-sessions"] })
      showSuccess("Session cancelled")
    },
    [session, queryClient, showSuccess],
  )

  const submitFeedback = useCallback(
    async (feedback: string) => {
      if (!session) return
      try {
        if (!feedback.trim()) {
          showError("Write the feedback before saving.")
          return
        }
        const updated = await serviceSessionsApi.updateFeedback(session.id, {
          feedback: feedback.trim(),
        })
        queryClient.setQueryData(entityDetailKey("service-sessions", updated.id), updated)
        showSuccess("Feedback saved")
      } catch (err) {
        showError(err instanceof Error ? err.message : "Failed to save feedback")
      }
    },
    [session, queryClient, showSuccess, showError],
  )

  const state = renderDetailState(sessionQuery, {
    icon: CalendarClock,
    breadcrumb: "Delivery · Sessions",
    entity: "session",
    backTo: () => navigate({ to: "/service-sessions" }),
    backLabel: "Back to sessions",
  })
  if (state || !session) return state

  return (
    <PageShell
      icon={CalendarClock}
      breadcrumb={`Delivery · Sessions · ${formatDateTime(session.scheduled_at)}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/service-sessions" })}
            aria-label="Back to sessions"
            title="Back to sessions"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={() => setEditOpen(true)}
          >
            <Pencil className="size-3.5" />
            Edit
          </Button>
        </>
      }
    >
      <Hero session={session} service={service} member={member} />

      <ServiceSessionFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        session={session}
        service={service}
        member={member}
        onSaved={(updated) =>
          queryClient.setQueryData(entityDetailKey("service-sessions", updated.id), updated)
        }
      />

      <CompleteDialog
        open={completeOpen}
        onOpenChange={setCompleteOpen}
        defaultDuration={service?.duration_minutes ?? 60}
        onConfirm={confirmComplete}
      />
      <CancelDialog open={cancelOpen} onOpenChange={setCancelOpen} onConfirm={confirmCancel} />
      <RescheduleDialog
        open={rescheduleOpen}
        onOpenChange={setRescheduleOpen}
        currentISO={session.scheduled_at}
        onConfirm={async (iso, notes) => {
          // BE `ServiceSessionRescheduleRequest` only carries the new datetime.
          // If reschedule notes are useful, we'd PATCH them via update() after.
          const updated = await serviceSessionsApi.reschedule(session.id, {
            new_scheduled_at: iso,
          })
          if (notes?.trim()) {
            await serviceSessionsApi.update(session.id, { notes: notes.trim() })
          }
          queryClient.setQueryData(entityDetailKey("service-sessions", updated.id), updated)
          await queryClient.invalidateQueries({
            queryKey: ["service-sessions", "list"],
          })
          showSuccess("Session rescheduled")
        }}
      />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="feedback">Feedback</Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Schedule">
                    <DetailGrid>
                      <DetailRow
                        label="Scheduled at"
                        value={formatDateTime(session.scheduled_at)}
                        fullWidth
                      />
                      <DetailRow
                        label="Completed at"
                        value={session.completed_at ? formatDateTime(session.completed_at) : null}
                        fullWidth
                      />
                      <DetailRow label="Status" value={<StatusBadge status={session.status} />} />
                      <DetailRow label="Location" value={session.location} />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Notes" phiLabel="PHI · access logged">
                    {session.notes ? (
                      <p className="text-sm text-fg whitespace-pre-wrap">{session.notes}</p>
                    ) : (
                      <p className="text-xs text-fg-muted">No notes recorded.</p>
                    )}
                  </DetailCard>

                  <DetailCard title="Subject">
                    {member ? (
                      <Link
                        to="/members/$memberId"
                        params={{ memberId: member.id }}
                        className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
                      >
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
                        >
                          {nameInitials(memberLabel(member))}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">
                            {memberLabel(member)}
                          </p>
                          <p className="truncate text-[11px] text-fg-muted">
                            {getStatusLabel(member.relation)}
                          </p>
                        </div>
                      </Link>
                    ) : (
                      <p className="text-xs text-fg-muted">Loading member…</p>
                    )}
                  </DetailCard>

                  <DetailCard title="Service & provider">
                    {service ? (
                      <Link
                        to="/services/$serviceId"
                        params={{ serviceId: service.id }}
                        className="mb-2 flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
                      >
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
                        >
                          <Wrench className="size-3.5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">{service.name}</p>
                          <p className="truncate text-[11px] text-fg-muted">
                            {service.service_type ?? "-"}
                          </p>
                        </div>
                      </Link>
                    ) : null}
                    {provider ? (
                      <div className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2">
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
                        >
                          PR
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg font-mono">
                            {provider.id}
                          </p>
                          <p className="truncate text-[11px] text-fg-muted">
                            {provider.provider_profile.tier} · {provider.provider_profile.region}
                          </p>
                        </div>
                      </div>
                    ) : session.provider_id ? (
                      <p className="text-xs text-fg-muted">Loading provider…</p>
                    ) : (
                      <p className="text-xs text-fg-muted">No provider assigned.</p>
                    )}
                  </DetailCard>

                  <DetailCard title="Clinical">
                    <DetailGrid>
                      <DetailRow
                        label="Diagnosis"
                        value={
                          session.diagnosis_id
                            ? (() => {
                                const all = (diagnosisTreeQuery.data?.types ?? []).flatMap(
                                  (t) => t.diagnoses,
                                )
                                const dx = all.find((d) => d.id === session.diagnosis_id)
                                return dx
                                  ? `${dx.code}: ${dx.name}`
                                  : diagnosisTreeQuery.isPending
                                    ? "Loading…"
                                    : session.diagnosis_id
                              })()
                            : null
                        }
                        fullWidth
                      />
                    </DetailGrid>
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="feedback">
                <FeedbackPanel session={session} onSubmit={submitFeedback} />
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Reschedule and lifecycle events will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              session={session}
              service={service}
              member={member}
              onAction={handleAction}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}
