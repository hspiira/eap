import { useCallback, useMemo, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  ChevronRight,
  FileCheck,
  FileSignature,
  Pencil,
  Plus,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { contractsApi } from "@/api/endpoints/contracts"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { renderDetailState } from "@/components/common/DetailStates"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ContractFormSheet } from "@/components/ContractFormSheet"
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
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey, entityListKey, useEntityDetail } from "@/lib/queries"
import { cn } from "@/lib/utils"
import type { Client, Contract, ServiceAssignment } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/contracts/$contractId")({
  component: ContractDetailPage,
})

type TabValue = "overview" | "services" | "billing" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "services", "billing", "history"]

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
          const next = new Date(contract.period.end_date)
          next.setFullYear(next.getFullYear() + 1)
          await contractsApi.renew(id, { new_end_date: next.toISOString() })
        }
        await queryClient.invalidateQueries({ queryKey: ["contracts"] })
        toast.showSuccess("Status updated")
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Action failed — please try again"))
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

  const number = contract.id

  return (
    <PageShell
      icon={FileSignature}
      breadcrumb={`Commercial · Contracts · ${number}`}
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
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Lifecycle">
                    <DetailGrid>
                      <DetailRow label="Status" value={<StatusBadge status={contract.status} />} />
                      <DetailRow label="Start date" value={formatDate(contract.period.start_date)} />
                      <DetailRow label="End date" value={formatDate(contract.period.end_date)} />
                      <DetailRow
                        label="Auto-renew"
                        value={contract.is_auto_renew ? "Yes" : "No"}
                      />
                    </DetailGrid>
                    {lifecycleSummary ? (
                      <p className="mt-3 text-xs text-fg/60">{lifecycleSummary}</p>
                    ) : null}
                  </DetailCard>

                  <DetailCard title="Identity">
                    <DetailGrid>
                      <DetailRow
                        label="Reference"
                        value={<span className="font-mono">{contract.id}</span>}
                      />
                      <DetailRow
                        label="Contract ID"
                        value={<span className="font-mono text-xs">{contract.id}</span>}
                        fullWidth
                      />
                    </DetailGrid>
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

              <TabPanel value="billing">
                <DetailCard title="Billing terms">
                  <DetailGrid>
                    <DetailRow label="Frequency" value={contract.payment_frequency} />
                    <DetailRow label="Payment status" value={contract.payment_status} />
                    <DetailRow label="Amount" value={formatMoney(contract)} />
                    <DetailRow label="Currency" value={contract.billing_rate.currency} />
                  </DetailGrid>
                </DetailCard>
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
      <h1 className="shrink truncate font-mono text-base font-semibold leading-tight text-fg">
        {contract.id.slice(0, 8)}
      </h1>
      {client ? (
        <Link
          to="/clients/$clientId"
          params={{ clientId: client.id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          {client.name}
          <span className="ml-1.5 font-mono text-fg/45">{client.code}</span>
        </Link>
      ) : (
        <span className="font-mono text-xs text-fg/45">{contract.client_id.slice(0, 8)}</span>
      )}
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
              className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
            >
              {initial(client.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">{client.name}</p>
              <p className="truncate font-mono text-[11px] text-fg/55">{client.code}</p>
            </div>
          </Link>
        ) : (
          <p className="text-xs text-fg/55">Loading client…</p>
        )}
      </RailSection>

      <RailSection title="Billing snapshot">
        <DetailGrid>
          <DetailRow label="Amount" value={
            formatMoney(contract)
          } />
          <DetailRow label="Frequency" value={contract.payment_frequency} />
          <DetailRow label="Payment" value={contract.payment_status} fullWidth />
        </DetailGrid>
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

function DetailCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-sm border border-fg/10 bg-surface p-4">
      <h3 className="mb-3 text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

function RailSection({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={cn("space-y-2", className)}>
      <h3 className="text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-sm border border-fg/10 bg-surface px-3 py-2">
      <div className="text-[11px] font-medium tracking-wide text-fg/55">{label}</div>
      <div className="mt-0.5 font-mono text-base font-semibold text-fg">{value}</div>
    </div>
  )
}

function DetailGrid({ children }: { children: React.ReactNode }) {
  return <dl className="grid grid-cols-2 gap-x-3 gap-y-2.5">{children}</dl>
}

function DetailRow({
  label,
  value,
  fullWidth,
}: {
  label: string
  value: React.ReactNode
  fullWidth?: boolean
}) {
  return (
    <div className={cn(fullWidth && "col-span-2")}>
      <dt className="text-[11px] font-medium tracking-wide text-fg/55">{label}</dt>
      <dd className="mt-0.5 truncate text-sm text-fg">
        {value || <span className="text-fg/40">—</span>}
      </dd>
    </div>
  )
}

/** Wire dates are ISO datetimes; these rows show the calendar day. */
function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString()
}

/** `billing_rate.amount` is a decimal string on the wire. */
function formatMoney(c: Contract): string {
  const parsed = Number(c.billing_rate.amount)
  return Number.isFinite(parsed)
    ? `${c.billing_rate.currency} ${parsed.toLocaleString()}`
    : `${c.billing_rate.currency} ${c.billing_rate.amount}`
}

function termInDays(c: Contract): string {
  const start = new Date(c.period.start_date).getTime()
  const end = new Date(c.period.end_date).getTime()
  return `${Math.max(0, Math.round((end - start) / 86_400_000)).toLocaleString()}d`
}

/** The server computes this; it knows the term and does not depend on clock skew. */
function daysToRenewal(c: Contract): string {
  return `${c.days_remaining}d`
}

function buildLifecycleSummary(c: Contract | null): string | null {
  if (!c) return null
  const label = c.is_auto_renew ? "renewal" : "end date"
  const days = c.days_remaining
  if (days < 0) return `Past ${label} by ${Math.abs(days)} days.`
  if (days === 0) return `${label.charAt(0).toUpperCase() + label.slice(1)} is today.`
  return `${days} days until ${label}.`
}

function initial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
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
        <p className="text-xs text-fg/55">
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
          <TableHeader className="border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
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
                    className="font-mono text-sm text-fg group-hover:text-primary"
                  >
                    {a.service_id.slice(0, 8)}
                  </Link>
                </TableCell>
                <TableCell>
                  <StatusBadge status={a.status} />
                </TableCell>
                <TableCell className="text-sm text-fg/75 truncate max-w-[24ch]">
                  {a.notes ?? <span className="text-fg/40">—</span>}
                </TableCell>
                <TableCell className="text-right">
                  <Link
                    to="/service-assignments/$assignmentId"
                    params={{ assignmentId: a.id }}
                    aria-label="Open assignment"
                    className="inline-grid size-7 place-items-center rounded-sm text-fg/55 hover:bg-surface-hover hover:text-fg"
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
