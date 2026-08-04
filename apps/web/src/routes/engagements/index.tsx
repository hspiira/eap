import { useEffect, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  AlertTriangle,
  Briefcase,
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
} from "lucide-react"

import { engagementsApi } from "@/api/endpoints/engagements"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SelectionBar } from "@/components/common/SelectionBar"
import { compareSort, nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { EngagementFormSheet } from "@/components/EngagementFormSheet"
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
import type { Engagement } from "@/types/entities"
import { EngagementStatus, EngagementType } from "@/types/enums"

function isStatus(v: unknown): v is EngagementStatus {
  return (
    v === EngagementStatus.SCOPING ||
    v === EngagementStatus.ACTIVE ||
    v === EngagementStatus.DELIVERED ||
    v === EngagementStatus.CLOSED ||
    v === EngagementStatus.CANCELLED
  )
}

function isType(v: unknown): v is EngagementType {
  return (
    v === EngagementType.POLICY_DRAFT ||
    v === EngagementType.TRAINING ||
    v === EngagementType.ASSESSMENT ||
    v === EngagementType.ADVISORY ||
    v === EngagementType.AUDIT ||
    v === EngagementType.OTHER
  )
}

export const Route = createFileRoute("/engagements/")({
  component: EngagementsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: {
      new?: boolean
      search?: string
      status?: EngagementStatus
      type?: EngagementType
      overdue?: boolean
    } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    if (isType(search.type)) out.type = search.type
    if (search.overdue === "1" || search.overdue === true) out.overdue = true
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: EngagementStatus.SCOPING, label: "Scoping" },
  { value: EngagementStatus.ACTIVE, label: "Active" },
  { value: EngagementStatus.DELIVERED, label: "Delivered" },
  { value: EngagementStatus.CLOSED, label: "Closed" },
  { value: EngagementStatus.CANCELLED, label: "Cancelled" },
] as const

const TYPE_OPTIONS = [
  { value: "all", label: "All types" },
  { value: EngagementType.POLICY_DRAFT, label: "Policy draft" },
  { value: EngagementType.TRAINING, label: "Training" },
  { value: EngagementType.ASSESSMENT, label: "Assessment" },
  { value: EngagementType.ADVISORY, label: "Advisory" },
  { value: EngagementType.AUDIT, label: "Audit" },
  { value: EngagementType.OTHER, label: "Other" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]
type TypeFilter = (typeof TYPE_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function EngagementsListPage() {
  const searchParams = useSearch({ from: "/engagements/" })
  const navigate = useNavigate({ from: "/engagements/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [addOpen, setAddOpen] = useState(false)
  const [sort, setSort] = useState<SortState>({ field: "due_date", desc: false })
  const canWrite = useCanWrite()
  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  const query = useQuery({
    queryKey: ["engagements", "list"],
    queryFn: () => engagementsApi.list(),
    staleTime: 30_000,
  })
  const allItems = query.data?.items ?? []
  const items = filterAndSort(allItems, {
    search: searchInput.trim(),
    status: searchParams.status,
    type: searchParams.type,
    overdueOnly: searchParams.overdue ?? false,
    sort,
  })
  const selection = useTableSelection(items)
  const loading = query.isPending
  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : (next as EngagementStatus)
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
  }
  const handleTypeChange = (next: TypeFilter) => {
    const type = next === "all" ? undefined : (next as EngagementType)
    navigate({ search: (prev) => ({ ...prev, type }), replace: true })
  }
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const overdueCount = allItems.filter((e) => isOverdue(e.due_date, e.status)).length
  const hasFilters =
    Boolean(searchInput) ||
    Boolean(searchParams.status) ||
    Boolean(searchParams.type) ||
    Boolean(searchParams.overdue)

  return (
    <PageShell
      icon={Briefcase}
      breadcrumb="Commercial · Consultancy engagements"
      actions={
        <>
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          {canWrite && (
            <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
              <Plus className="size-3.5" />
              New engagement
            </Button>
          )}
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "type", label: "Type" },
            { id: "client", label: "Client" },
          ]}
        />
        {searchParams.status ? (
          <FilterChip
            label={`Status is ${searchParams.status}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        {searchParams.type ? (
          <FilterChip
            label={`Type is ${searchParams.type}`}
            onRemove={() => handleTypeChange("all")}
          />
        ) : null}
        {searchParams.overdue ? (
          <FilterChip
            label="Overdue"
            onRemove={() =>
              navigate({
                search: (prev) => ({ ...prev, overdue: undefined }),
                replace: true,
              })
            }
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(searchParams.status ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <FilterTrigger
          label="All types"
          value={(searchParams.type ?? "all") as TypeFilter}
          options={TYPE_OPTIONS}
          onChange={handleTypeChange}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() =>
            navigate({
              search: (prev) => ({
                ...prev,
                overdue: searchParams.overdue ? undefined : true,
              }),
              replace: true,
            })
          }
          className={cn(
            "h-8 shrink-0 gap-1.5 rounded-sm border px-2 text-sm",
            searchParams.overdue
              ? "border-amber-500/40 bg-amber-500/10 text-amber-600 hover:bg-amber-500/15"
              : "border-fg/25 bg-bg text-fg/80 hover:bg-surface-hover",
          )}
        >
          <AlertTriangle className="size-3.5" />
          Overdue only
          {overdueCount > 0 ? (
            <span className="font-mono text-[10px] text-fg/55">({overdueCount})</span>
          ) : null}
        </Button>
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search engagements…"
        />
      </FilterBar>

      <EngagementFormSheet
        open={addOpen}
        onOpenChange={setAddOpen}
      />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Briefcase}
            title={hasFilters ? "No engagements match your filters" : "No engagements yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Create a consultancy engagement to track scope, deliverables, and hours."
            }
            action={
              hasFilters || !canWrite ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  New engagement
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
                      Engagement
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                      Status
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="engagement_type" sort={sort} onToggle={toggleSort}>
                      Type
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="due_date" sort={sort} onToggle={toggleSort}>
                      Due
                    </SortHeader>
                  </TableHead>
                  <TableHead className="text-fg/65">Hours</TableHead>
                  <TableHead className="w-16 text-right text-fg/65">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((e) => (
                  <EngagementRow key={e.id} row={e} isSelected={selection.selectedIds.has(e.id)} onToggle={() => selection.toggleSelect(e.id)} />
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

function EngagementRow({ row, isSelected, onToggle }: { row: Engagement; isSelected: boolean; onToggle: () => void }) {
  const overdue = isOverdue(row.due_date, row.status)
  const budgetPct = row.budget_hours
    ? Math.round((row.hours_logged / row.budget_hours) * 100)
    : null
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox aria-label={`Select ${row.name}`} checked={isSelected} onCheckedChange={onToggle} />
      </TableCell>
      <TableCell>
        <Link
          to="/engagements/$engagementId"
          params={{ engagementId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <Briefcase className="size-3" />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium text-fg group-hover:text-primary">
              {row.name}
            </span>
            <span className="block truncate text-xs text-fg/55">
              Started {new Date(row.start_date).toLocaleDateString()}
            </span>
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1.5">
          <EngagementStatusPill status={row.status} />
          {overdue ? (
            <span
              title="Past due date and not yet delivered"
              className="inline-flex items-center gap-1 rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-amber-600"
            >
              <AlertTriangle className="size-3" />
              Overdue
            </span>
          ) : null}
        </div>
      </TableCell>
      <TableCell className="text-xs text-fg/75">{row.engagement_type}</TableCell>
      <TableCell className="text-sm text-fg/75">
        {row.due_date ? new Date(row.due_date).toLocaleDateString() : "—"}
      </TableCell>
      <TableCell>
        <div className="min-w-32">
          <div className="flex items-center justify-between text-xs text-fg/65">
            <span className="font-mono">
              {row.hours_logged.toFixed(1)}
              {row.budget_hours ? `/${row.budget_hours}` : ""}
            </span>
            {budgetPct !== null ? (
              <span
                className={cn(
                  "font-mono",
                  budgetPct > 100 ? "text-amber-600" : "text-fg/55",
                )}
              >
                {budgetPct}%
              </span>
            ) : null}
          </div>
          {budgetPct !== null ? (
            <div
              className="mt-1 h-1 w-full overflow-hidden rounded-sm bg-fg/10"
              aria-hidden
            >
              <div
                className={cn(
                  "h-full",
                  budgetPct > 100 ? "bg-amber-500" : "bg-primary",
                )}
                style={{ width: `${Math.min(100, budgetPct)}%` }}
              />
            </div>
          ) : null}
        </div>
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/engagements/$engagementId"
            params={{ engagementId: row.id }}
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
                <Link
                  to="/engagements/$engagementId"
                  params={{ engagementId: row.id }}
                >
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

export function EngagementStatusPill({ status }: { status: EngagementStatus }) {
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

function statusTone(status: EngagementStatus): string {
  switch (status) {
    case EngagementStatus.ACTIVE:
      return "border-primary/30 bg-primary/10 text-primary"
    case EngagementStatus.SCOPING:
      return "border-fg/20 bg-bg text-fg"
    case EngagementStatus.DELIVERED:
      return "border-amber-500/40 bg-amber-500/10 text-amber-600"
    case EngagementStatus.CLOSED:
      return "border-fg/15 bg-bg text-fg/60"
    case EngagementStatus.CANCELLED:
      return "border-danger/30 bg-danger-soft text-danger-fg"
    default:
      return "border-fg/15 bg-bg text-fg/65"
  }
}

export function isOverdue(
  due: string | null | undefined,
  status: EngagementStatus,
): boolean {
  if (!due) return false
  if (status === EngagementStatus.DELIVERED || status === EngagementStatus.CLOSED) return false
  if (status === EngagementStatus.CANCELLED) return false
  return Date.parse(due) < Date.now()
}

function filterAndSort(
  items: Engagement[],
  opts: {
    search: string
    status?: EngagementStatus
    type?: EngagementType
    overdueOnly: boolean
    sort: SortState
  },
): Engagement[] {
  let out = items
  if (opts.status) out = out.filter((e) => e.status === opts.status)
  if (opts.type) out = out.filter((e) => e.engagement_type === opts.type)
  if (opts.overdueOnly) out = out.filter((e) => isOverdue(e.due_date, e.status))
  if (opts.search) {
    const q = opts.search.toLowerCase()
    out = out.filter(
      (e) =>
        e.name.toLowerCase().includes(q) ||
        e.description?.toLowerCase().includes(q) ||
        e.client_id.toLowerCase().includes(q),
    )
  }
  return compareSort(out, opts.sort)
}
