import { useEffect, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Download,
  ExternalLink,
  Headphones,
  MoreHorizontal,
  Phone,
  Plus,
  RotateCw,
} from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { CampaignFormSheet } from "@/components/CampaignFormSheet"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SelectionBar } from "@/components/common/SelectionBar"
import { compareSort, nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useTableSelection } from "@/hooks/useTableSelection"
import { cn } from "@/lib/utils"
import type { CallbackCampaign } from "@/types/entities"
import { CallbackCampaignStatus } from "@/types/enums"

function isStatus(v: unknown): v is CallbackCampaignStatus {
  return (
    v === CallbackCampaignStatus.DRAFT ||
    v === CallbackCampaignStatus.SCHEDULED ||
    v === CallbackCampaignStatus.ACTIVE ||
    v === CallbackCampaignStatus.COMPLETED ||
    v === CallbackCampaignStatus.CANCELLED
  )
}

export const Route = createFileRoute("/care-callbacks/")({
  component: CampaignsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { new?: boolean; search?: string; status?: CallbackCampaignStatus } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: CallbackCampaignStatus.DRAFT, label: "Draft" },
  { value: CallbackCampaignStatus.SCHEDULED, label: "Scheduled" },
  { value: CallbackCampaignStatus.ACTIVE, label: "Active" },
  { value: CallbackCampaignStatus.COMPLETED, label: "Completed" },
  { value: CallbackCampaignStatus.CANCELLED, label: "Cancelled" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function CampaignsListPage() {
  const searchParams = useSearch({ from: "/care-callbacks/" })
  const navigate = useNavigate({ from: "/care-callbacks/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [addOpen, setAddOpen] = useState(false)
  const [sort, setSort] = useState<SortState>({ field: "period_start", desc: true })
  const canWrite = useCanWrite()
  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  const query = useQuery({
    queryKey: ["care-callback-campaigns", "list"],
    queryFn: () => careCallbacksApi.listCampaigns(),
    staleTime: 30_000,
  })
  const allItems = query.data?.items ?? []
  const items = filterAndSort(allItems, {
    search: searchInput.trim(),
    status: searchParams.status,
    sort,
  })
  const selection = useTableSelection(items)
  const loading = query.isPending
  const error = query.isError ? "Failed to load campaigns." : null
  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : (next as CallbackCampaignStatus)
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
  }
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const hasFilters = Boolean(searchInput) || Boolean(searchParams.status)

  return (
    <PageShell
      icon={Phone}
      breadcrumb="Care · Callback campaigns"
      actions={
        <>
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={() => navigate({ to: "/care-callbacks/worklist" })}
          >
            <Headphones className="size-3.5" />
            My worklist
          </Button>
          {canWrite && (
            <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
              <Plus className="size-3.5" />
              New campaign
            </Button>
          )}
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "client", label: "Client" },
          ]}
        />
        {searchParams.status ? (
          <FilterChip
            label={`Status is ${searchParams.status}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(searchParams.status ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search campaigns…"
        />
      </FilterBar>

      <CampaignFormSheet
        open={addOpen}
        onOpenChange={setAddOpen}
      />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} rows={6} />
          </div>
        ) : error ? (
          <div className="flex flex-1 items-center justify-center">
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => void query.refetch()}>
              <RotateCw className="size-4" />
              {error} Try again
            </Button>
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Phone}
            title={hasFilters ? "No campaigns match your filters" : "No campaigns yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Create a campaign to start a wellbeing follow-up wave."
            }
            action={
              hasFilters || !canWrite ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  New campaign
                </Button>
              )
            }
          />
        ) : (
          <>
            <SelectionBar count={selection.selectedIds.size} onClear={selection.clearSelection} />
            <div className="relative min-h-0 flex-1 overflow-auto">
              <Table className="w-full caption-bottom text-sm">
                <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <Checkbox aria-label="Select all" checked={selection.selectAllState} onCheckedChange={selection.toggleSelectAll} />
                    </TableHead>
                  <TableHead>
                    <SortHeader field="name" sort={sort} onToggle={toggleSort}>
                      Campaign
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                      Status
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="period_start" sort={sort} onToggle={toggleSort}>
                      Window
                    </SortHeader>
                  </TableHead>
                  <TableHead className="text-fg/65">Pool</TableHead>
                  <TableHead className="text-fg/65">Cases</TableHead>
                  <TableHead className="w-16 text-right text-fg/65">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((c) => (
                  <CampaignRow key={c.id} row={c} isSelected={selection.selectedIds.has(c.id)} onToggle={() => selection.toggleSelect(c.id)} />
                ))}
              </TableBody>
            </Table>
            </div>
          </>
        )}
      </div>
    </PageShell>
  )
}

function CampaignRow({ row, isSelected, onToggle }: { row: CallbackCampaign; isSelected: boolean; onToggle: () => void }) {
  const total = row.case_count
  const completionPct = total ? Math.round((row.cases_completed / total) * 100) : 0
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox aria-label={`Select ${row.name}`} checked={isSelected} onCheckedChange={onToggle} />
      </TableCell>
      <TableCell>
        <Link
          to="/care-callbacks/$campaignId"
          params={{ campaignId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <Phone className="size-3" />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium text-fg group-hover:text-primary">
              {row.name}
            </span>
            <span className="block truncate text-xs text-fg/55">
              Sampling: {row.sampling}
              {row.sample_size ? ` (n=${row.sample_size})` : ""}
            </span>
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <CampaignStatusPill status={row.status} />
      </TableCell>
      <TableCell className="text-sm text-fg/75">
        {new Date(row.period_start).toLocaleDateString()}
        <span className="text-fg/40"> – </span>
        {new Date(row.period_end).toLocaleDateString()}
      </TableCell>
      <TableCell className="font-mono text-xs text-fg/75">
        {row.counsellor_user_ids.length}
      </TableCell>
      <TableCell>
        <div className="min-w-32">
          <div className="flex items-center justify-between text-xs text-fg/65">
            <span>
              {row.cases_completed}/{total}
            </span>
            <span className="font-mono">{completionPct}%</span>
          </div>
          <div
            className="mt-1 h-1 w-full overflow-hidden rounded-sm bg-fg/10"
            aria-hidden
          >
            <div
              className="h-full bg-primary"
              style={{ width: `${Math.min(100, completionPct)}%` }}
            />
          </div>
        </div>
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/care-callbacks/$campaignId"
            params={{ campaignId: row.id }}
            aria-label={`Open ${row.name}`}
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button type="button" variant="ghost" size="sm" aria-label={`More actions for ${row.name}`} className="size-7 p-0 text-fg/65"><MoreHorizontal className="size-4" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/care-callbacks/$campaignId" params={{ campaignId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}

export function CampaignStatusPill({ status }: { status: CallbackCampaignStatus }) {
  const tone = statusTone(status)
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[11px] font-medium",
        tone,
      )}
    >
      {status}
    </span>
  )
}

function statusTone(status: CallbackCampaignStatus): string {
  switch (status) {
    case CallbackCampaignStatus.ACTIVE:
      return "border-primary/30 bg-primary/10 text-primary"
    case CallbackCampaignStatus.SCHEDULED:
      return "border-fg/20 bg-bg text-fg"
    case CallbackCampaignStatus.COMPLETED:
      return "border-fg/15 bg-bg text-fg/60"
    case CallbackCampaignStatus.CANCELLED:
      return "border-danger/30 bg-danger-soft text-danger-fg"
    default:
      return "border-fg/15 bg-bg text-fg/65"
  }
}

function IconButton({
  label,
  icon: Icon,
  onClick,
}: {
  label: string
  icon: React.ElementType
  onClick?: () => void
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="size-7 p-0 text-fg/70"
    >
      <Icon className="size-3.5" />
    </Button>
  )
}

function filterAndSort(
  items: CallbackCampaign[],
  opts: {
    search: string
    status?: CallbackCampaignStatus
    sort: SortState
  },
): CallbackCampaign[] {
  let out = items
  if (opts.status) out = out.filter((c) => c.status === opts.status)
  if (opts.search) {
    const q = opts.search.toLowerCase()
    out = out.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.description?.toLowerCase().includes(q) ||
        c.client_id.toLowerCase().includes(q),
    )
  }
  return compareSort(out, opts.sort)
}
