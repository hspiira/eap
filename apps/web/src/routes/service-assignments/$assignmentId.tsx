import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  FileCheck,
  FileSignature,
  Pencil,
  Wrench,
} from "lucide-react"

import { contractsApi } from "@/api/endpoints/contracts"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { servicesApi } from "@/api/endpoints/services"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
} from "@/components/common/DetailPrimitives"
import { renderDetailState } from "@/components/common/DetailStates"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ServiceAssignmentFormSheet } from "@/components/ServiceAssignmentFormSheet"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey, useEntityDetail } from "@/lib/queries"
import type { Contract, Service, ServiceAssignment } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/service-assignments/$assignmentId")({
  component: ServiceAssignmentDetailPage,
})

type TabValue = "overview" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "history"]

function ServiceAssignmentDetailPage() {
  const { assignmentId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [actionLoading, setActionLoading] = useState(false)
  const toast = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)

  const assignmentQuery = useEntityDetail<ServiceAssignment>({
    resource: "service-assignments",
    id: assignmentId,
    detailFn: serviceAssignmentsApi.getById,
  })
  const assignment = assignmentQuery.data ?? null

  const contractId = assignment?.contract_id
  const { data: contract = null } = useQuery({
    queryKey: entityDetailKey("contracts", contractId ?? ""),
    queryFn: () => contractsApi.getById(contractId as string),
    enabled: !!contractId,
  })

  const serviceId = assignment?.service_id
  const { data: service = null } = useQuery({
    queryKey: entityDetailKey("services", serviceId ?? ""),
    queryFn: () => servicesApi.getById(serviceId as string),
    enabled: !!serviceId,
  })

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await serviceAssignmentsApi.activate(id)
        else if (action === "deactivate") await serviceAssignmentsApi.deactivate(id)
        else if (action === "archive") await serviceAssignmentsApi.archive(id)
        else if (action === "restore") await serviceAssignmentsApi.restore(id)
        await queryClient.invalidateQueries({ queryKey: ["service-assignments"] })
        toast.showSuccess("Status updated")
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Action failed — please try again"))
      } finally {
        setActionLoading(false)
      }
    },
    [queryClient, toast],
  )

  const state = renderDetailState(assignmentQuery, {
    icon: FileCheck,
    breadcrumb: "Commercial · Service assignments",
    entity: "assignment",
    backTo: () => navigate({ to: "/service-assignments" }),
    backLabel: "Back to assignments",
  })
  if (state || !assignment) return state

  const label = `${assignment.contract_id.slice(0, 8)} · ${
    service?.name ?? assignment.service_id.slice(0, 8)
  }`

  return (
    <PageShell
      icon={FileCheck}
      breadcrumb={`Commercial · Service Assignments · ${label}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/service-assignments" })}
            aria-label="Back to assignments"
            title="Back to assignments"
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
      <Hero assignment={assignment} contract={contract} service={service} />

      <ServiceAssignmentFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        assignment={assignment}
        contract={contract}
        onSaved={(updated) =>
          queryClient.setQueryData(
            entityDetailKey("service-assignments", updated.id),
            updated,
          )
        }
      />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Coverage">
                    <DetailGrid>
                      <DetailRow
                        label="Status"
                        value={<StatusBadge status={assignment.status} />}
                      />
                      <DetailRow label="Notes" value={assignment.notes ?? "—"} fullWidth />
                      <DetailRow
                        label="Assignment ID"
                        value={
                          <span className="font-mono text-xs">{assignment.id}</span>
                        }
                        fullWidth
                      />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Contract">
                    {contract ? (
                      <Link
                        to="/contracts/$contractId"
                        params={{ contractId: contract.id }}
                        className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
                      >
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
                        >
                          <FileSignature className="size-3.5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-mono text-sm font-medium text-fg">
                            {contract.id.slice(0, 8)}
                          </p>
                          <p className="truncate text-[11px] text-fg/55">
                            {contract.status} · client {contract.client_id.slice(0, 8)}
                          </p>
                        </div>
                      </Link>
                    ) : (
                      <p className="text-xs text-fg/55">Loading contract…</p>
                    )}
                  </DetailCard>

                  <DetailCard title="Service">
                    {service ? (
                      <div className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2">
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
                        >
                          <Wrench className="size-3.5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">
                            {service.name}
                          </p>
                          <p className="truncate text-[11px] text-fg/55">
                            {service.service_type ?? service.category ?? "—"}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-fg/55">Loading service…</p>
                    )}
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Assignment lifecycle changes will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              assignment={assignment}
              contract={contract}
              onAction={handleAction}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({
  assignment,
  contract,
  service,
}: {
  assignment: ServiceAssignment
  contract: Contract | null
  service: Service | null
}) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <FileCheck className="size-4" />
      </span>
      {contract ? (
        <Link
          to="/contracts/$contractId"
          params={{ contractId: contract.id }}
          className="font-mono text-sm font-semibold text-fg hover:text-primary"
        >
          {contract.id.slice(0, 8)}
        </Link>
      ) : (
        <span className="font-mono text-sm font-semibold text-fg">
          {assignment.contract_id.slice(0, 8)}
        </span>
      )}
      <span className="text-fg/45">·</span>
      <span className="truncate text-sm font-semibold text-fg">
        {service?.name ?? assignment.service_id.slice(0, 8)}
      </span>
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={assignment.status} />
    </div>
  )
}

interface DetailRailProps {
  assignment: ServiceAssignment
  contract: Contract | null
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

function DetailRail({ assignment, contract, onAction, actionLoading }: DetailRailProps) {
  return (
    <div className="space-y-5">
      <RailSection title="Active period">
        <DetailGrid>
          <DetailRow
            label="Start"
            value={
              contract ? new Date(contract.period.start_date).toLocaleDateString() : "—"
            }
          />
          <DetailRow
            label="End"
            value={
              contract ? new Date(contract.period.end_date).toLocaleDateString() : "—"
            }
          />
        </DetailGrid>
        <p className="mt-2 text-[11px] text-fg/50">Inherited from the parent contract.</p>
      </RailSection>

      {contract ? (
        <RailSection title="Contract">
          <Link
            to="/contracts/$contractId"
            params={{ contractId: contract.id }}
            className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
          >
            <span
              aria-hidden
              className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
            >
              <FileSignature className="size-3.5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-mono text-sm font-medium text-fg">
                {contract.id.slice(0, 8)}
              </p>
              <p className="truncate text-[11px] text-fg/55">
                {contract.status}
              </p>
            </div>
          </Link>
        </RailSection>
      ) : null}

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={assignment.id}
          currentStatus={assignment.status}
          kind="base"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>
    </div>
  )
}

