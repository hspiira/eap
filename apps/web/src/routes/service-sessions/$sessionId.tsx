import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, CalendarClock, SquarePen } from "lucide-react"

import { diagnosesApi } from "@/api/endpoints/diagnoses"
import { membersApi } from "@/api/endpoints/members"
import { providersApi } from "@/api/endpoints/providers"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { renderDetailState } from "@/components/common/DetailStates"
import { EntityActivityPanel } from "@/components/common/EntityActivityPanel"
import { PageShell } from "@/components/common/PageShell"
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
import { SessionChainCard } from "@/components/sessions/SessionChainCard"
import { SessionOverviewCards } from "@/components/sessions/SessionOverviewCards"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"
import { entityDetailKey, useEntityDetail } from "@/lib/queries"
import type { ServiceSession } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

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
    queryFn: () => membersApi.getById(session!.member_id!),
    enabled: !!session?.member_id,
  })

  const providerId = session?.provider_id
  const { data: provider = null } = useQuery({
    queryKey: entityDetailKey("providers", providerId ?? ""),
    queryFn: () => providersApi.getById(providerId as string),
    enabled: !!providerId,
  })

  const diagnosisLabel = (() => {
    if (!session?.diagnosis_id) return null
    const all = (diagnosisTreeQuery.data?.types ?? []).flatMap((t) => t.diagnoses)
    const found = all.find((d) => d.id === session.diagnosis_id)
    if (found) return `${found.code}: ${found.name}`
    return diagnosisTreeQuery.isPending ? "Loading…" : session.diagnosis_id
  })()

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
    async (duration: number, notes: string, caseId?: string) => {
      if (!session) return
      const { drawdown } = await serviceSessionsApi.complete(session.id, {
        duration,
        notes,
        case_id: caseId ?? null,
      })
      await queryClient.invalidateQueries({ queryKey: ["service-sessions"] })
      if (drawdown.consumed) {
        showSuccess(`Session completed. ${drawdown.sessions_remaining} authorized sessions left.`)
        return
      }
      // A named case that could not be drawn down is worth saying out loud:
      // the session is complete either way, but the entitlement did not move.
      showSuccess(
        caseId && drawdown.reason
          ? `Session completed. Not drawn down: ${drawdown.reason}`
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
            <SquarePen className="size-3.5" />
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
        clientId={member?.client_id}
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
                <SessionOverviewCards
                  session={session}
                  service={service}
                  member={member}
                  provider={provider}
                  diagnosisLabel={diagnosisLabel}
                />
                <section className="mt-4 border border-fg/10 bg-surface p-4">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-fg-muted">
                    Chain of care
                  </h3>
                  <SessionChainCard
                    session={session}
                    onSelectSession={(id) =>
                      void navigate({
                        to: "/service-sessions/$sessionId",
                        params: { sessionId: id },
                      })
                    }
                  />
                </section>
              </TabPanel>

              <TabPanel value="feedback">
                <FeedbackPanel session={session} onSubmit={submitFeedback} />
              </TabPanel>

              <TabPanel value="history">
                <EntityActivityPanel
                  resourceType="ServiceSession"
                  resourceId={session.id}
                  emptyDescription="Reschedules, completions and cancellations appear here. Clinical values are redacted from the trail."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:sticky lg:top-3 lg:col-span-4 lg:max-h-[80vh] lg:overflow-y-auto lg:pt-14">
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
