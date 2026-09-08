import { useCallback, useMemo, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, ChevronRight, FileCheck, FileSignature, Pencil, Plus } from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { contractsApi } from "@/api/endpoints/contracts"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { renderDetailState } from "@/components/common/DetailStates"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { TABLE_HEAD } from "@/components/common/tableStyles"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ContractFormSheet } from "@/components/ContractFormSheet"
import { ContractAttachments } from "@/components/contracts/ContractAttachments"
import { ContractUtilisationPanel } from "@/components/contracts/ContractUtilisationPanel"
import { ServiceAssignmentFormSheet } from "@/components/ServiceAssignmentFormSheet"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { addYearsToDay, daysBetweenDays, formatDay } from "@/lib/format"
import { entityDetailKey, entityListKey, useEntityDetail } from "@/lib/queries"
import type { Client, Contract, ServiceAssignment } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/contracts/$contractId")({
  component: ContractDetailPage,
})

type TabValue = "overview" | "services" | "attachments" | "billing" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = [
  "overview",
  "services",
  "attachments",
  "billing",
  "history",
]

function ContractDetailPage() {
  const { contractId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [actionLoading, setActionLoading] = useState(false)
  const toast = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)
  const [addAssignmentOpen, setAddAssignmentOpen] = useState(false)

  const contractQuery = useEntityDetail<Contract>({
    resource: "contracts",
    id: contractId,
    detailFn: contractsApi.getById,
  })
  const contract = contractQuery.data ?? null

  const assignmentsQuery = useQuery({
    queryKey: entityListKey("service-assignments", { contract_id: contractId, limit: 50 }),
    queryFn: () => serviceAssignmentsApi.list({ limit: 50, contract_id: contractId }),
  })
  const assignments = assignmentsQuery.data?.items ?? []

  const clientId = contract?.client_id
  const { data: client = null } = useQuery({
    queryKey: entityDetailKey("clients", clientId ?? ""),
    queryFn: () => clientsApi.getById(clientId as string),
    enabled: !!clientId,
  })

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await contractsApi.activate(id)
        else if (action === "terminate") {
          await contractsApi.terminate(id, { reason: "Terminated from UI" })
        } else if (action === "renew") {
          if (!contract) return
          await contractsApi.renew(id, {
            new_end_date: addYearsToDay(contract.period.end_date, 1),
          })
        }
        await queryClient.invalidateQueries({ queryKey: ["contracts"] })
        toast.showSuccess("Status updated")
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Action failed: please try again"))
      } finally {
        setActionLoading(false)
      }
    },
    [contract, queryClient, toast],
  )

  const lifecycleSummary = useMemo(() => buildLifecycleSummary(contract), [contract])

  const state = renderDetailState(contractQuery, {
    icon: FileSignature,
    breadcrumb: "Commercial · Contracts",
    entity: "contract",
    backTo: () => navigate({ to: "/contracts" }),
    backLabel: "Back to contracts",
  })
  if (state || !contract) return state

  const title = client?.name ?? "Contract"

  return (
    <PageShell
      icon={FileSignature}
      breadcrumb={`Commercial · Contracts · ${title}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/contracts" })}
            aria-label="Back to contracts"
            title="Back to contracts"
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
      <Hero contract={contract} client={client} />

      <ContractFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        contract={contract}
        client={client}
        onSaved={(updated) =>
          queryClient.setQueryData(entityDetailKey("contracts", updated.id), updated)
        }
      />

      <ServiceAssignmentFormSheet
        open={addAssignmentOpen}
        onOpenChange={setAddAssignmentOpen}
        contractId={contract.id}
        contract={contract}
        onSaved={() => {
          void queryClient.invalidateQueries({ queryKey: ["service-assignments"] })
          setTab("services")
        }}
      />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="services" count={assignments.length}>
                  Services
                </Tab>
                <Tab value="billing">Billing</Tab>
                <Tab value="attachments">Attachments</Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Lifecycle">
                    <DetailGrid>
                      <DetailRow label="Status" value={<StatusBadge status={contract.status} />} />
                      <DetailRow label="Start date" value={formatDay(contract.period.start_date)} />
                      <DetailRow label="End date" value={formatDay(contract.period.end_date)} />
                      <DetailRow label="Auto-renew" value={contract.is_auto_renew ? "Yes" : "No"} />
                    </DetailGrid>
                    {lifecycleSummary ? (
                      <p className="mt-3 text-xs text-fg/60">{lifecycleSummary}</p>
                    ) : null}
                  </DetailCard>

                  <DetailCard title="Signature">
                    <DetailGrid>
                      <DetailRow label="Signed by" value={contract.signed_by || "-"} />
                      <DetailRow label="Signed on" value={formatDay(contract.signed_at)} />
                      <DetailRow
                        label="Contract ID"
                        value={<span className="font-mono text-xs">{contract.id}</span>}
                        fullWidth
                      />
                    </DetailGrid>
                    {contract.termination_reason ? (
                      <p className="mt-3 text-xs text-danger">
                        Terminated: {contract.termination_reason}
                      </p>
                    ) : null}
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="services">
                <ServicesPanel
                  assignments={assignments}
                  loading={assignmentsQuery.isPending}
                  onAdd={() => setAddAssignmentOpen(true)}
                />
              </TabPanel>

              <TabPanel value="attachments">
                <ContractAttachments key={contractId} contractId={contractId} />
              </TabPanel>
              <TabPanel value="billing" className="space-y-4">
                <DetailCard title="Billing terms">
                  <DetailGrid>
                    <DetailRow label="Amount" value={formatMoney(contract)} />
                    <DetailRow label="Frequency" value={contract.payment_frequency} />
                    <DetailRow
                      label="Payment status"
                      value={<StatusBadge status={contract.payment_status} />}
                    />
                    <DetailRow label="Auto-renew" value={contract.is_auto_renew ? "Yes" : "No"} />
                    <DetailRow label="Last billed" value={formatDay(contract.last_billing_date)} />
                    <DetailRow label="Next billing" value={formatDay(contract.next_billing_date)} />
                  </DetailGrid>
                </DetailCard>
                <ContractUtilisationPanel contractId={contractId} />
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Lifecycle changes and amendments will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              contract={contract}
              client={client}
              onAction={handleAction}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({ contract, client }: { contract: Contract; client: Client | null }) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <FileSignature className="size-4" />
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {client ? (
          <Link
            to="/clients/$clientId"
            params={{ clientId: client.id }}
            className="hover:text-primary"
          >
            {client.name}
          </Link>
        ) : (
          "Contract"
        )}
      </h1>
      {client?.code ? <span className="shrink-0 text-xs text-fg-subtle">{client.code}</span> : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <span className="shrink-0 whitespace-nowrap text-xs text-fg/65">
        {formatDay(contract.period.start_date)} to {formatDay(contract.period.end_date)}
      </span>
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={contract.status} />
    </div>
  )
}

interface DetailRailProps {
  contract: Contract
  client: Client | null
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

function DetailRail({ contract, client, onAction, actionLoading }: DetailRailProps) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Term" value={termInDays(contract)} />
          <Stat label="Days to renewal" value={daysToRenewal(contract)} />
        </div>
      </RailSection>

      <RailSection title="Client">
        {client ? (
          <Link
            to="/clients/$clientId"
            params={{ clientId: client.id }}
            className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
          >
            <span
              aria-hidden
              className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
            >
              {nameInitials(client.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">{client.name}</p>
              <p className="truncate text-[11px] text-fg-muted">{client.code}</p>
            </div>
          </Link>
        ) : (
          <p className="text-xs text-fg-muted">Loading client…</p>
        )}
      </RailSection>

      <RailSection title="Billing">
        <p className="tabular-nums text-lg font-semibold leading-tight text-fg">
          {formatMoney(contract)}
        </p>
        <p className="mt-0.5 text-xs text-fg-muted">{contract.payment_frequency}</p>
        <div className="mt-3">
          <StatusBadge status={contract.payment_status} size="sm" />
        </div>
      </RailSection>

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={contract.id}
          currentStatus={contract.status}
          kind="contract"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>
    </div>
  )
}

/** `billing_rate.amount` is a decimal string on the wire. */
function formatMoney(c: Contract): string {
  const parsed = Number(c.billing_rate.amount)
  return Number.isFinite(parsed)
    ? `${c.billing_rate.currency} ${parsed.toLocaleString()}`
    : `${c.billing_rate.currency} ${c.billing_rate.amount}`
}

function termInDays(c: Contract): string {
  const days = daysBetweenDays(c.period.start_date, c.period.end_date)
  if (days == null) return "-"
  return `${Math.max(0, days).toLocaleString()}d`
}

/** Server-computed whole days left in the term. Zero on the last day. */
function daysToRenewal(c: Contract): string {
  return `${c.days_remaining}d`
}

function buildLifecycleSummary(c: Contract | null): string | null {
  if (!c) return null
  const label = c.is_auto_renew ? "renewal" : "end date"
  const days = c.days_remaining
  const magnitude = Math.abs(days)
  const dayWord = magnitude === 1 ? "day" : "days"
  if (days < 0) return `Past ${label} by ${magnitude} ${dayWord}.`
  if (days === 0) return `${label.charAt(0).toUpperCase() + label.slice(1)} is today.`
  return `${days} ${dayWord} until ${label}.`
}

function ServicesPanel({
  assignments,
  loading,
  onAdd,
}: {
  assignments: ServiceAssignment[]
  loading: boolean
  onAdd: () => void
}) {
  if (loading) {
    return <p className="text-sm text-fg/65">Loading assignments…</p>
  }
  if (assignments.length === 0) {
    return (
      <EmptyState
        icon={FileCheck}
        title="No services assigned yet"
        description="Link a service to start billing sessions against this contract."
        action={
          <Button size="sm" className="gap-1.5" onClick={onAdd}>
            <Plus className="size-4" />
            Add service
          </Button>
        }
      />
    )
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg-muted">
          {assignments.length} service
          {assignments.length === 1 ? "" : "s"} covered.
        </p>
        <Button size="sm" variant="outline" className="h-7 gap-1.5 px-2.5" onClick={onAdd}>
          <Plus className="size-3.5" />
          Add service
        </Button>
      </div>
      <div className="overflow-hidden border border-fg/10 bg-surface">
        <Table className="w-full caption-bottom text-sm">
          <TableHeader className={TABLE_HEAD}>
            <TableRow className="border-fg/8 hover:bg-transparent">
              <TableHead>Service</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Notes</TableHead>
              <TableHead className="w-10 text-right text-fg/65">
                <span className="sr-only">Open</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {assignments.map((a) => (
              <TableRow key={a.id} className="group border-fg/8">
                <TableCell>
                  <Link
                    to="/service-assignments/$assignmentId"
                    params={{ assignmentId: a.id }}
                    className="text-sm text-fg group-hover:text-primary"
                  >
                    {a.service_id.slice(0, 8)}
                  </Link>
                </TableCell>
                <TableCell>
                  <StatusBadge status={a.status} />
                </TableCell>
                <TableCell className="text-sm text-fg/75 truncate max-w-[24ch]">
                  {a.notes ?? <span className="text-fg-subtle">-</span>}
                </TableCell>
                <TableCell className="text-right">
                  <Link
                    to="/service-assignments/$assignmentId"
                    params={{ assignmentId: a.id }}
                    aria-label="Open assignment"
                    className="inline-grid size-7 place-items-center rounded-sm text-fg-muted hover:bg-surface-hover hover:text-fg"
                  >
                    <ChevronRight className="size-3.5" />
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
