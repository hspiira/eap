function fmtCount(n: number | null | undefined): string {
  if (n == null) return "—"
  return n.toLocaleString()
}

interface DetailRailProps {
  client: Client
  stats: ClientStats | null
  statsLoading: boolean
  tags: ClientTag[]
  tagsLoading: boolean
  children: Client[]
  childrenLoading: boolean
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
  onTierChange: (tier: ClientTier | null) => Promise<void>
  tierLoading: boolean
}

const ROW_BORDER = "border-fg/8"

import { useState } from "react"

import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  BadgeCheck,
  ChevronRight,
  Plus,
} from "lucide-react"

import {
  DetailGrid,
  DetailRow,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import {
  compareSort,
  fieldValue,
  nextSort,
  SortHeader,
  type SortState,
} from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
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
import { nameInitials } from "@/lib/display"
import { formatDate } from "@/lib/format"
import type { Client, ClientStats, ClientTag, Contract } from "@/types/entities"
import { ClientTier } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export function Hero({ client, verified }: { client: Client; verified: boolean }) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 font-mono text-xs font-semibold text-primary"
      >
        {nameInitials(client.name)}
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {client.name}
      </h1>
      <span className="font-mono text-xs text-fg/55">{client.code}</span>
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
  loading,
  onAdd,
}: {
  contracts: Contract[]
  loading: boolean
  onAdd: () => void
}) {
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const sorted = compareSort(contracts, sort, (row, field) => {
    if (field === "number") return row.id
    // The term is nested under `period`; a bare field lookup would miss it.
    if (field === "start_date") return row.period.start_date
    if (field === "end_date") return row.period.end_date
    return fieldValue(row, field)
  })

  if (loading) {
    return <p className="text-sm text-fg/65">Loading contracts…</p>
  }
  if (contracts.length === 0) {
    return (
      <EmptyState
        title="No contracts yet"
        description="Add a contract once it's signed."
        action={
          <Button size="sm" className="gap-1.5" onClick={onAdd}>
            <Plus className="size-4" />
            Add contract
          </Button>
        }
      />
    )
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg/55">
          {contracts.length} contract{contracts.length === 1 ? "" : "s"}
        </p>
        <Button size="sm" variant="outline" className="h-7 gap-1.5 px-2.5" onClick={onAdd}>
          <Plus className="size-3.5" />
          Add contract
        </Button>
      </div>
      <div className="overflow-hidden border border-fg/10 bg-surface">
      <Table className="w-full caption-bottom text-sm">
        <TableHeader className="border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
          <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
            <TableHead>
              <SortHeader field="number" sort={sort} onToggle={toggleSort}>
                Number
              </SortHeader>
            </TableHead>
            <TableHead>
              <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                Status
              </SortHeader>
            </TableHead>
            <TableHead>
              <SortHeader field="start_date" sort={sort} onToggle={toggleSort}>
                Start
              </SortHeader>
            </TableHead>
            <TableHead>
              <SortHeader field="end_date" sort={sort} onToggle={toggleSort}>
                End
              </SortHeader>
            </TableHead>
            <TableHead className="w-10 text-right text-fg/65">
              <span className="sr-only">Open</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((c) => (
            <TableRow key={c.id} className={`group ${ROW_BORDER}`}>
              <TableCell>
                <Link
                  to="/contracts/$contractId"
                  params={{ contractId: c.id }}
                  className="font-medium text-fg group-hover:text-primary"
                >
                  {c.id.slice(0, 8)}
                </Link>
              </TableCell>
              <TableCell>
                <StatusBadge status={c.status} />
              </TableCell>
              <TableCell className="text-sm text-fg/75">
                {formatDate(c.period.start_date)}
              </TableCell>
              <TableCell className="text-sm text-fg/75">
                {formatDate(c.period.end_date)}
              </TableCell>
              <TableCell className="text-right">
                <Link
                  to="/contracts/$contractId"
                  params={{ contractId: c.id }}
                  aria-label="Open contract"
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

export function DetailRail({
  client,
  stats,
  statsLoading,
  tags,
  tagsLoading,
  children,
  childrenLoading,
  onAction,
  actionLoading,
  onTierChange,
  tierLoading,
}: DetailRailProps) {
  const ba = client.billing_address
  const hasBilling = !!(ba?.street || ba?.city || ba?.postal_code || ba?.country)
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Child clients" value={statsLoading ? "…" : fmtCount(stats?.child_count)} />
          <Stat label="Contracts" value={statsLoading ? "…" : fmtCount(stats?.contract_count)} />
        </div>
      </RailSection>

      <RailSection title="Contact">
        <DetailGrid>
          <DetailRow label="Email" value={client.contact_info?.email} />
          <DetailRow label="Phone" value={client.contact_info?.phone} />
          <DetailRow label="Address" value={client.contact_info?.address} fullWidth />
          {client.preferred_contact_method ? (
            <DetailRow
              label="Preferred"
              value={client.preferred_contact_method}
            />
          ) : null}
        </DetailGrid>
      </RailSection>

      <RailSection title="Billing address">
        {hasBilling ? (
          <DetailGrid>
            {ba?.street ? <DetailRow label="Street" value={ba.street} fullWidth /> : null}
            {ba?.city ? <DetailRow label="City" value={ba.city} /> : null}
            {ba?.postal_code ? <DetailRow label="Postal" value={ba.postal_code} /> : null}
            {ba?.country ? <DetailRow label="Country" value={ba.country} /> : null}
          </DetailGrid>
        ) : (
          <p className="text-xs text-fg/55">No billing address on file.</p>
        )}
      </RailSection>

      {client.parent_client_id || children.length > 0 ? (
        <RailSection title="Hierarchy">
          {client.parent_client_id ? (
            <Link
              to="/clients/$clientId"
              params={{ clientId: client.parent_client_id }}
              className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
            >
              <ArrowLeft className="size-3.5" />
              Parent client
            </Link>
          ) : null}
          {childrenLoading ? (
            <p className="mt-2 text-xs text-fg/55">Loading children…</p>
          ) : children.length > 0 ? (
            <ul className="mt-2 space-y-1">
              {children.map((c) => (
                <li key={c.id}>
                  <Link
                    to="/clients/$clientId"
                    params={{ clientId: c.id }}
                    className="inline-flex items-center gap-1.5 text-sm text-fg hover:text-primary"
                  >
                    <ChevronRight className="size-3.5 text-fg/45" />
                    <span className="truncate">{c.name}</span>
                    <span className="font-mono text-[11px] text-fg/55">{c.code}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : null}
        </RailSection>
      ) : null}

      <RailSection title="Tags">
        {tagsLoading ? (
          <p className="text-xs text-fg/55">Loading…</p>
        ) : tags.length === 0 ? (
          <p className="text-xs text-fg/55">No tags assigned.</p>
        ) : (
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

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={client.id}
          currentStatus={client.status}
          kind="client"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>
    </div>
  )
}
