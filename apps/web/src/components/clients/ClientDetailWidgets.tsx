import type { ClientStatsResponse } from "@/api/generated"

function fmtCount(n: number | null | undefined): string {
  if (n == null) return "-"
  return n.toLocaleString()
}

/** A single "label: value" line for the At a glance grid. */
function GlanceStat({
  label,
  value,
  fullWidth,
}: {
  label: string
  value: string
  fullWidth?: boolean
}) {
  return (
    <p className={cn("truncate text-sm", fullWidth && "col-span-2")}>
      <span className="text-fg-muted">{label}: </span>
      <span className="font-medium tabular-nums text-fg">{value}</span>
    </p>
  )
}

type MilestonesState = "loading" | "error" | "ready"

interface DetailRailProps {
  client: Client
  stats: ClientStatsResponse | null
  statsLoading: boolean
  nextRenewal?: string
  milestonesState?: MilestonesState
  tags: ClientTag[]
  tagsLoading: boolean
  children: Client[]
  childrenLoading: boolean
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
  onTierChange: (tier: ClientTier | null) => Promise<void>
  tierLoading: boolean
  onVerify: () => Promise<void>
}

const ROW_BORDER = "border-fg/8"

import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ArrowLeft, BadgeCheck, ChevronRight, Plus } from "lucide-react"

import { type ContractMetricsItem, contractsApi } from "@/api/endpoints/contracts"
import { ContractServicesCard } from "@/components/clients/ContractServicesCard"
import { DetailGrid, DetailRow, RailSection } from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { FilterBar } from "@/components/common/FilterBar"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import {
  compareSort,
  fieldValue,
  nextSort,
  SortHeader,
  type SortState,
} from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { TierBadge } from "@/components/common/TierBadge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { contractLabel, contractValue, moneyLabel, nameInitials } from "@/lib/display"
import { formatDay } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { Client, ClientTag, Contract } from "@/types/entities"
import { ClientTier } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export function Hero({ client, verified }: { client: Client; verified: boolean }) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-xs font-semibold text-primary"
      >
        {nameInitials(client.name)}
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {client.name}
      </h1>
      <span className="text-xs text-fg-muted">{client.code}</span>
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={client.status} />
      <TierBadge tier={client.tier} />
      {verified ? (
        <span className="inline-flex items-center gap-1 rounded-sm border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[11px] font-medium text-primary">
          <BadgeCheck className="size-3" />
          Verified
        </span>
      ) : null}
    </div>
  )
}

export function ContractsPanel({
  contracts,
  total,
  loading,
  error,
  onAdd,
  clientId,
}: {
  contracts: Contract[]
  /** Server-side total, which can exceed the page held in `contracts`. */
  total?: number
  loading: boolean
  onAdd?: () => void
  error?: boolean
  clientId: string
}) {
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const sorted = compareSort(contracts, sort, (row, field) => {
    if (field === "number") return row.period.start_date
    // The term is nested under `period`; a bare field lookup would miss it.
    if (field === "start_date") return row.period.start_date
    if (field === "end_date") return row.period.end_date
    return fieldValue(row, field)
  })
  const selected = contracts.find((c) => c.id === selectedId) ?? defaultContract(sorted)
  const metrics = useContractMetrics(clientId)

  if (error)
    return (
      <p role="alert" className="border border-fg/15 p-6 text-sm">
        Contracts could not be loaded. Refresh to try again.
      </p>
    )
  if (loading) {
    return <p className="text-sm text-fg/65">Loading contracts…</p>
  }
  if (contracts.length === 0) {
    return (
      <EmptyState
        title="No contracts yet"
        description="Add a contract once it's signed."
        action={
          onAdd ? (
            <Button size="sm" className="gap-1.5" onClick={onAdd}>
              <Plus className="size-4" />
              Add contract
            </Button>
          ) : undefined
        }
      />
    )
  }
  return (
    <div className="grid grid-cols-12 gap-3 lg:h-[70vh]">
      <div className="col-span-12 flex min-h-0 min-w-0 flex-col border border-fg/10 bg-surface lg:col-span-8 lg:h-full">
        <FilterBar>
          <p className="text-xs text-fg-muted">
            {total != null && total > contracts.length
              ? `Showing ${contracts.length} of ${total} contracts`
              : `${contracts.length} contract${contracts.length === 1 ? "" : "s"}`}
          </p>
          <div className="ml-auto" />
          <div className="flex items-center gap-2">
            {total != null && total > contracts.length ? (
              <Link
                to="/contracts"
                search={{ client_id: clientId }}
                className="inline-flex items-center gap-0.5 text-xs text-fg-muted hover:text-fg"
              >
                View all
                <ChevronRight className="size-3" />
              </Link>
            ) : null}
            {onAdd && (
              <Button size="sm" className="h-8 shrink-0 gap-1.5 px-2.5" onClick={onAdd}>
                <Plus className="size-3.5" />
                Add contract
              </Button>
            )}
          </div>
        </FilterBar>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <Table className="w-full caption-bottom text-sm" scrollable={false}>
            <TableHeader className={STICKY_TABLE_HEAD}>
              <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                <TableHead>
                  <SortHeader field="number" sort={sort} onToggle={toggleSort}>
                    Contract term
                  </SortHeader>
                </TableHead>
                <TableHead className="text-center">
                  <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                    <span className="sr-only">Status</span>
                  </SortHeader>
                </TableHead>
                <TableHead className="text-right text-fg/65">Services</TableHead>
                <TableHead className="text-right text-fg/65">Value</TableHead>
                <TableHead className="text-right text-fg/65">Spent</TableHead>
                <TableHead className="w-10 text-right text-fg/65">
                  <span className="sr-only">Open</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.map((c) => (
                <ContractRow
                  key={c.id}
                  contract={c}
                  metrics={metrics.get(c.id)}
                  selected={selected?.id === c.id}
                  onSelect={() => setSelectedId(c.id)}
                />
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      <div className="col-span-12 flex min-h-0 min-w-0 flex-col lg:col-span-4 lg:h-full">
        {selected && <ContractServicesCard contract={selected} />}
      </div>
    </div>
  )
}

/**
 * Services covered and session spend per term, in one request.
 *
 * The server does the counting: a per-row query here would be one request per
 * contract, and the spend has to be summed over sessions the browser never
 * holds.
 */
function useContractMetrics(clientId: string): Map<string, ContractMetricsItem> {
  const { data } = useQuery({
    queryKey: ["contracts", "metrics", clientId],
    queryFn: () => contractsApi.metricsByClient(clientId),
  })
  return new Map((data?.items ?? []).map((item) => [item.contract_id, item]))
}

/** Says what the spend does and does not cover, for the cell's tooltip. */
function spentCoverage(metrics: ContractMetricsItem): string {
  if (!metrics.sessions) return "No sessions recorded in this term"
  return `${metrics.sessions_priced} of ${metrics.sessions} sessions in this term carry a rate`
}

/** The term in force, else the row at the top of the table as it is sorted. */
function defaultContract(sorted: Contract[]): Contract | null {
  return sorted.find((c) => c.is_active) ?? sorted[0] ?? null
}

function ContractRow({
  contract,
  metrics,
  selected,
  onSelect,
}: {
  contract: Contract
  /** Undefined until the metrics request lands. */
  metrics: ContractMetricsItem | undefined
  selected: boolean
  onSelect: () => void
}) {
  return (
    <TableRow
      onClick={onSelect}
      className={cn(
        "group h-9 cursor-pointer",
        ROW_BORDER,
        selected && "bg-primary/5 hover:bg-primary/5",
      )}
    >
      <TableCell>
        <span className={cn("text-sm font-medium", selected ? "text-primary" : "text-fg")}>
          {contractLabel(contract)}
        </span>
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={contract.status} iconOnly />
      </TableCell>
      <TableCell className="text-right tabular-nums text-xs text-fg/70">
        {metrics?.services ?? <span className="text-fg-subtle">…</span>}
      </TableCell>
      <TableCell className="whitespace-nowrap text-right tabular-nums text-xs text-fg/70">
        {contractValue(contract)}
      </TableCell>
      <TableCell
        className="whitespace-nowrap text-right tabular-nums text-xs text-fg/70"
        title={metrics ? spentCoverage(metrics) : undefined}
      >
        {metrics ? moneyLabel(metrics.spent) : <span className="text-fg-subtle">…</span>}
      </TableCell>
      <TableCell className="text-right">
        <Link
          to="/contracts/$contractId"
          params={{ contractId: contract.id }}
          aria-label={`Open the contract running ${contractLabel(contract)}`}
          onClick={(event) => event.stopPropagation()}
          className="inline-grid size-7 place-items-center rounded-sm text-fg/65 opacity-0 transition-opacity hover:bg-surface-hover hover:text-fg group-hover:opacity-100 focus:opacity-100"
        >
          <ChevronRight className="size-3.5" />
        </Link>
      </TableCell>
    </TableRow>
  )
}

export function DetailRail({
  client,
  stats,
  statsLoading,
  nextRenewal,
  milestonesState = "ready",
  tags,
  tagsLoading,
  children,
  childrenLoading,
  onAction,
  actionLoading,
  onTierChange,
  tierLoading,
  onVerify,
}: DetailRailProps) {
  return (
    <div className="space-y-4">
      <AtAGlanceSection
        stats={stats}
        statsLoading={statsLoading}
        nextRenewal={nextRenewal}
        milestonesState={milestonesState}
      />
      <ContactSection client={client} />
      <BillingSection client={client} />
      <HierarchySection client={client} childClients={children} childrenLoading={childrenLoading} />
      <TagsSection tags={tags} tagsLoading={tagsLoading} />
      <TierSection client={client} onTierChange={onTierChange} tierLoading={tierLoading} />
      <LifecycleSection
        client={client}
        onAction={onAction}
        actionLoading={actionLoading}
        onVerify={onVerify}
      />
    </div>
  )
}

function milestoneLabel(milestonesState: MilestonesState, nextRenewal?: string): string {
  if (milestonesState === "loading") return "Loading…"
  if (milestonesState === "error") return "Contract dates unavailable"
  if (nextRenewal) return formatDay(nextRenewal)
  return "None"
}

function AtAGlanceSection({
  stats,
  statsLoading,
  nextRenewal,
  milestonesState,
}: {
  stats: ClientStatsResponse | null
  statsLoading: boolean
  nextRenewal?: string
  milestonesState: MilestonesState
}) {
  return (
    <RailSection title="At a glance">
      <div className="grid grid-cols-2 gap-x-3 gap-y-2">
        <GlanceStat
          label="Employees"
          value={statsLoading ? "…" : fmtCount(stats?.employee_members_count)}
        />
        <GlanceStat
          label="Spouses"
          value={statsLoading ? "…" : fmtCount(stats?.spouse_members_count)}
        />
        <GlanceStat
          label="Children"
          value={statsLoading ? "…" : fmtCount(stats?.child_members_count)}
        />
        <GlanceStat
          label="Others"
          value={statsLoading ? "…" : fmtCount(stats?.other_members_count)}
        />
        <GlanceStat
          label="Contracts"
          value={
            statsLoading
              ? "…"
              : `${fmtCount(stats?.active_contracts_count)} of ${fmtCount(stats?.total_contracts_count)} Active`
          }
        />
        <GlanceStat
          label="Child clients"
          value={statsLoading ? "…" : fmtCount(stats?.child_clients_count)}
        />
        <GlanceStat
          label="Next milestone (90d)"
          value={milestoneLabel(milestonesState, nextRenewal)}
          fullWidth
        />
      </div>
    </RailSection>
  )
}

function ContactSection({ client }: { client: Client }) {
  return (
    <RailSection title="Contact">
      <DetailGrid>
        <DetailRow label="Email" value={client.contact_info?.email} />
        <DetailRow label="Phone" value={client.contact_info?.phone} />
        <DetailRow label="Address" value={client.contact_info?.address} fullWidth />
        {client.preferred_contact_method ? (
          <DetailRow label="Preferred" value={client.preferred_contact_method} />
        ) : null}
      </DetailGrid>
    </RailSection>
  )
}

function BillingSection({ client }: { client: Client }) {
  const ba = client.billing_address
  const hasBilling = !!(ba?.street || ba?.city || ba?.postal_code || ba?.country)
  return (
    <RailSection title="Billing address">
      {hasBilling && (
        <DetailGrid>
          {ba?.street ? <DetailRow label="Street" value={ba.street} fullWidth /> : null}
          {ba?.city ? <DetailRow label="City" value={ba.city} /> : null}
          {ba?.postal_code ? <DetailRow label="Postal" value={ba.postal_code} /> : null}
          {ba?.country ? <DetailRow label="Country" value={ba.country} /> : null}
        </DetailGrid>
      )}
      {!hasBilling && client.contact_info?.address && (
        <div className="text-xs text-fg-muted">
          <p>Same as contact address.</p>
          <p className="mt-1 text-sm text-fg/75">{client.contact_info.address}</p>
        </div>
      )}
      {!hasBilling && !client.contact_info?.address && (
        <p className="text-xs text-fg-muted">No billing address on file.</p>
      )}
    </RailSection>
  )
}

function HierarchySection({
  client,
  childClients,
  childrenLoading,
}: {
  client: Client
  childClients: Client[]
  childrenLoading: boolean
}) {
  if (!client.parent_client_id && childClients.length === 0) return null
  return (
    <RailSection title="Hierarchy">
      {client.parent_client_id && (
        <Link
          to="/clients/$clientId"
          params={{ clientId: client.parent_client_id }}
          className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
        >
          <ArrowLeft className="size-3.5" />
          Parent client
        </Link>
      )}
      {childrenLoading && <p className="mt-2 text-xs text-fg-muted">Loading children…</p>}
      {!childrenLoading && childClients.length > 0 && (
        <>
          <ul className="mt-2 space-y-1">
            {childClients.map((c) => (
              <li key={c.id}>
                <Link
                  to="/clients/$clientId"
                  params={{ clientId: c.id }}
                  className="inline-flex items-center gap-1.5 text-sm text-fg hover:text-primary"
                >
                  <ChevronRight className="size-3.5 text-fg-subtle" />
                  <span className="truncate">{c.name}</span>
                  <span className="text-[11px] text-fg-muted">{c.code}</span>
                </Link>
              </li>
            ))}
          </ul>
          <Link
            to="/clients"
            search={{ parent_client_id: client.id }}
            className="mt-2 inline-flex items-center gap-0.5 text-xs text-fg-muted hover:text-fg"
          >
            View all child clients
            <ChevronRight className="size-3" />
          </Link>
        </>
      )}
    </RailSection>
  )
}

function TagsSection({ tags, tagsLoading }: { tags: ClientTag[]; tagsLoading: boolean }) {
  return (
    <RailSection title="Tags">
      {tagsLoading && <p className="text-xs text-fg-muted">Loading…</p>}
      {!tagsLoading && tags.length === 0 && (
        <p className="text-xs text-fg-muted">No tags assigned.</p>
      )}
      {!tagsLoading && tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((t) => (
            <span
              key={t.id}
              className="inline-flex items-center gap-1.5 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-xs text-fg"
            >
              <span
                aria-hidden
                className="block size-2 border border-fg/15"
                style={t.color ? { backgroundColor: t.color } : undefined}
              />
              {t.name}
            </span>
          ))}
        </div>
      )}
    </RailSection>
  )
}

function TierSection({
  client,
  onTierChange,
  tierLoading,
}: {
  client: Client
  onTierChange: (tier: ClientTier | null) => Promise<void>
  tierLoading: boolean
}) {
  return (
    <RailSection title="Tier">
      <Select
        value={client.tier ?? "none"}
        onValueChange={(v) => {
          void onTierChange(v === "none" ? null : (v as ClientTier))
        }}
        disabled={tierLoading}
      >
        <SelectTrigger className="h-7 w-full text-xs">
          <SelectValue placeholder="Unassigned" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="none">Unassigned</SelectItem>
          <SelectItem value={ClientTier.A}>Tier A</SelectItem>
          <SelectItem value={ClientTier.B}>Tier B</SelectItem>
          <SelectItem value={ClientTier.C}>Tier C</SelectItem>
        </SelectContent>
      </Select>
    </RailSection>
  )
}

function LifecycleSection({
  client,
  onAction,
  actionLoading,
  onVerify,
}: {
  client: Client
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
  onVerify: () => Promise<void>
}) {
  return (
    <RailSection title="Lifecycle">
      <div className="flex flex-nowrap items-center gap-1.5 overflow-x-auto">
        {!client.is_verified && (
          <Button
            size="sm"
            variant="secondary"
            className="shrink-0 gap-1.5 rounded-none"
            onClick={() => void onVerify()}
            disabled={actionLoading}
          >
            <BadgeCheck className="size-3.5" />
            Verify
          </Button>
        )}
        <LifecycleActions
          entityId={client.id}
          currentStatus={client.status}
          kind="client"
          onAction={onAction}
          loading={actionLoading}
          adminOnlyActions={["archive", "terminate"]}
        />
      </div>
    </RailSection>
  )
}
