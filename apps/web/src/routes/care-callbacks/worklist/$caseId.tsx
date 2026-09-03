import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, Headphones } from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import {
  DetailRail,
  EscalateDialog,
  Hero,
  TerminateDialog,
} from "@/components/care-callbacks/CaseTriageWidgets"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey } from "@/lib/queries"
import { useAuthStore } from "@/store/slices/authSlice"

export const Route = createFileRoute("/care-callbacks/worklist/$caseId")({
  component: CaseDetailPage,
})

function CaseDetailPage() {
  const { caseId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()
  const userId = useAuthStore((s) => s.user_id)
  const [actionLoading, setActionLoading] = useState(false)
  const [terminateOpen, setTerminateOpen] = useState(false)
  const [escalateOpen, setEscalateOpen] = useState(false)

  const outreachQuery = useQuery({
    queryKey: entityDetailKey("outreach-records", caseId),
    queryFn: () => careCallbacksApi.getOutreach(caseId),
  })

  const campaignId = outreachQuery.data?.campaign_id
  const campaignQuery = useQuery({
    queryKey: ["care-callback-campaigns", "detail", campaignId ?? ""],
    queryFn: () => careCallbacksApi.getCampaign(campaignId as string),
    enabled: !!campaignId,
  })
  const campaign = campaignQuery.data

  const refresh = () => queryClient.invalidateQueries({ queryKey: entityDetailKey("outreach-records", caseId) })

  const runAction = async (action: () => Promise<unknown>, successMessage: string) => {
    setActionLoading(true)
    try {
      await action()
      await refresh()
      showSuccess(successMessage)
    } catch (err) {
      showError(normalizeErrorMessage(err, "Action failed — please try again"))
    } finally {
      setActionLoading(false)
    }
  }

  const handleAssignToMe = () => {
    if (!userId) return
    return runAction(() => careCallbacksApi.assign(caseId, userId), "Claimed")
  }
  const handleLogAttempt = () =>
    runAction(() => careCallbacksApi.recordAttempt(caseId), "Attempt logged")
  const handleTerminate = (action: "complete" | "unreachable" | "decline", notes: string) => {
    const input = { notes: notes || null }
    const call =
      action === "complete"
        ? careCallbacksApi.complete(caseId, input)
        : action === "unreachable"
          ? careCallbacksApi.markUnreachable(caseId, input)
          : careCallbacksApi.markDeclined(caseId, input)
    return runAction(() => call, "Record closed")
  }
  const handleEscalate = (notes: string) =>
    runAction(() => careCallbacksApi.escalate(caseId, { notes }), "Escalated")

  if (outreachQuery.isPending) {
    return (
      <PageShell icon={Headphones} breadcrumb="Care · My worklist · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton mainPanels={2} />
        </div>
      </PageShell>
    )
  }
  if (!outreachQuery.data) {
    return (
      <PageShell icon={Headphones} breadcrumb="Care · My worklist · Not found">
        <EmptyState
          icon={Headphones}
          title="Record not found"
          description="It may have been reassigned or the campaign archived."
          action={
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/care-callbacks/worklist" })}
            >
              <ArrowLeft className="size-4" />
              Back to worklist
            </Button>
          }
        />
      </PageShell>
    )
  }

  const outreach = outreachQuery.data
  const isMine = !!userId && outreach.counsellor_id === userId

  return (
    <PageShell
      icon={Headphones}
      breadcrumb={`Care · My worklist · ${outreach.person_id}`}
      actions={
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => navigate({ to: "/care-callbacks/worklist" })}
          aria-label="Back to worklist"
          title="Back to worklist"
          className="size-7 p-0 text-fg/70"
        >
          <ArrowLeft className="size-3.5" />
        </Button>
      }
    >
      <Hero outreach={outreach} campaignName={campaign?.name ?? null} />

      <TerminateDialog
        open={terminateOpen}
        onOpenChange={setTerminateOpen}
        onConfirm={handleTerminate}
      />
      <EscalateDialog open={escalateOpen} onOpenChange={setEscalateOpen} onConfirm={handleEscalate} />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            {outreach.notes ? (
              <div className="rounded-sm border border-fg/10 bg-surface p-4">
                <h3 className="mb-2 text-xs font-semibold tracking-wide text-fg/55">Notes</h3>
                <p className="whitespace-pre-wrap text-sm text-fg/85">{outreach.notes}</p>
              </div>
            ) : (
              <EmptyState
                icon={Headphones}
                title={isMine ? "No notes yet" : "Not assigned to you"}
                description={
                  isMine
                    ? "Log a contact attempt or close this record — notes recorded there appear here."
                    : "Claim this record to work it, or ask whoever holds it to hand it off."
                }
              />
            )}
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              outreach={outreach}
              campaignId={outreach.campaign_id}
              campaignName={campaign?.name ?? null}
              isMine={isMine}
              actionLoading={actionLoading}
              onAssignToMe={handleAssignToMe}
              onLogAttempt={handleLogAttempt}
              onOpenTerminate={() => setTerminateOpen(true)}
              onOpenEscalate={() => setEscalateOpen(true)}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}
