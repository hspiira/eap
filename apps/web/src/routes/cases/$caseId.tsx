import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, HeartPulse } from "lucide-react"

import { casesApi } from "@/api/endpoints/cases"
import { clinicalNotesApi } from "@/api/endpoints/clinical-notes"
import {
  AdvanceDialog,
  AssignCounsellorDialog,
  CloseCaseDialog,
  CreateNoteDialog,
  DetailRail,
  Hero,
  NotesPanel,
  OverviewPanel,
  ReferOutDialog,
} from "@/components/cases/CaseDetailWidgets"
import { renderDetailState } from "@/components/common/DetailStates"
import { PageShell } from "@/components/common/PageShell"
import { RequireClinicalScope } from "@/components/common/RequireClinicalScope"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey, useEntityDetail } from "@/lib/queries"
import type { CaseClosureReason, CaseStatus, ClinicalNoteType } from "@/types/enums"

export const Route = createFileRoute("/cases/$caseId")({
  component: () => (
    <RequireClinicalScope>
      <CaseDetailPage />
    </RequireClinicalScope>
  ),
})

type TabValue = "overview" | "notes"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "notes"]

function CaseDetailPage() {
  const { caseId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [actionLoading, setActionLoading] = useState(false)

  const [assignOpen, setAssignOpen] = useState(false)
  const [advanceOpen, setAdvanceOpen] = useState(false)
  const [closeOpen, setCloseOpen] = useState(false)
  const [referOutOpen, setReferOutOpen] = useState(false)
  const [noteOpen, setNoteOpen] = useState(false)

  const caseQuery = useEntityDetail({
    resource: "cases",
    id: caseId,
    detailFn: casesApi.getById,
  })
  const caseData = caseQuery.data ?? null

  const notesQuery = useQuery({
    queryKey: ["clinical-notes", "for-case", caseId],
    queryFn: () => clinicalNotesApi.listForCase(caseId),
    enabled: !!caseData,
  })
  const notes = notesQuery.data ?? []

  const refreshCase = () => queryClient.invalidateQueries({ queryKey: entityDetailKey("cases", caseId) })
  const refreshNotes = () => queryClient.invalidateQueries({ queryKey: ["clinical-notes", "for-case", caseId] })

  const runAction = async (action: () => Promise<unknown>, successMessage: string) => {
    setActionLoading(true)
    try {
      await action()
      await refreshCase()
      showSuccess(successMessage)
    } catch (err) {
      showError(normalizeErrorMessage(err, "Action failed — please try again"))
      throw err
    } finally {
      setActionLoading(false)
    }
  }

  const handleAssignCounsellor = (counsellorId: string) =>
    runAction(
      () => casesApi.assignCounsellor(caseId, { counsellor_id: counsellorId }),
      "Counsellor assigned",
    )

  const handleAdvance = (target: CaseStatus) =>
    runAction(() => casesApi.advance(caseId, { target }), "Status updated")

  const handleClose = (reason: CaseClosureReason) =>
    runAction(() => casesApi.close(caseId, { reason }), "Case closed")

  const handleReferOut = (notesText: string) =>
    runAction(() => casesApi.referOut(caseId, { notes: notesText }), "Case referred out")

  const handleCreateNote = async (noteType: ClinicalNoteType, body: Record<string, string>) => {
    try {
      await clinicalNotesApi.create({ case_id: caseId, note_type: noteType, body })
      await refreshNotes()
      showSuccess("Note saved")
    } catch (err) {
      showError(normalizeErrorMessage(err, "Could not save note"))
      throw err
    }
  }

  const handleSignNote = async (noteId: string) => {
    try {
      await clinicalNotesApi.sign(noteId)
      await refreshNotes()
      showSuccess("Note signed")
    } catch (err) {
      showError(normalizeErrorMessage(err, "Could not sign note"))
    }
  }

  const state = renderDetailState(caseQuery, {
    icon: HeartPulse,
    breadcrumb: "Clinical · Cases",
    entity: "case",
    backTo: () => navigate({ to: "/cases" }),
    backLabel: "Back to cases",
  })
  if (state || !caseData) return state

  return (
    <PageShell
      icon={HeartPulse}
      breadcrumb={`Clinical · Cases · ${caseData.clinical_subject_id}`}
      actions={
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => navigate({ to: "/cases" })}
          aria-label="Back to cases"
          title="Back to cases"
          className="size-7 p-0 text-fg/70"
        >
          <ArrowLeft className="size-3.5" />
        </Button>
      }
    >
      <Hero caseData={caseData} />

      <AssignCounsellorDialog
        open={assignOpen}
        onOpenChange={setAssignOpen}
        onConfirm={handleAssignCounsellor}
      />
      <AdvanceDialog
        open={advanceOpen}
        onOpenChange={setAdvanceOpen}
        caseData={caseData}
        onConfirm={handleAdvance}
      />
      <CloseCaseDialog
        open={closeOpen}
        onOpenChange={setCloseOpen}
        caseData={caseData}
        onConfirm={handleClose}
      />
      <ReferOutDialog open={referOutOpen} onOpenChange={setReferOutOpen} onConfirm={handleReferOut} />
      <CreateNoteDialog open={noteOpen} onOpenChange={setNoteOpen} onConfirm={handleCreateNote} />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="notes" count={notes.length}>
                  Notes
                </Tab>
              </TabsList>

              <TabPanel value="overview">
                <OverviewPanel caseData={caseData} />
              </TabPanel>

              <TabPanel value="notes">
                <NotesPanel
                  caseId={caseId}
                  notes={notes}
                  loading={notesQuery.isPending}
                  onAddNote={() => setNoteOpen(true)}
                  onSign={handleSignNote}
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              caseData={caseData}
              onAssignCounsellor={() => setAssignOpen(true)}
              onAdvance={() => setAdvanceOpen(true)}
              onClose={() => setCloseOpen(true)}
              onReferOut={() => setReferOutOpen(true)}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}
