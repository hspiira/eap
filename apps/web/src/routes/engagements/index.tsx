import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  AlertTriangle,
  Briefcase,
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
} from "lucide-react"

import { type EngagementListParams, engagementsApi } from "@/api/endpoints/engagements"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView } from "@/components/common/EntityListView"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { ROW_BORDER } from "@/components/common/tableStyles"
import { EngagementFormSheet } from "@/components/EngagementFormSheet"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { TableCell, TableRow } from "@/components/ui/table"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useListPage } from "@/hooks/useListPage"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import { useEntityList } from "@/lib/queries"
import { enumOptions, enumParam, listSearchSchema } from "@/lib/search-params"
import { cn } from "@/lib/utils"
import type { Engagement, EngagementStatusValue } from "@/types/entities"
import { engagementHours } from "@/types/entities"
import { EngagementStatus } from "@/types/enums"

export const Route = createFileRoute("/engagements/")({
  component: EngagementsListPage,
  validateSearch: listSearchSchema({ status: enumParam(EngagementStatus) }),
})

const STATUS_OPTIONS = enumOptions(EngagementStatus, "All statuses")

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const COLUMNS = [
  { header: "Engagement", sortField: "name" },
  { header: "Status", sortField: "status" },
  { header: "Window", sortField: "period_start" },
  { header: "Due", sortField: "period_end" },
  { header: "Hours", className: "text-fg/65" },
]

function EngagementsListPage() {
  const searchParams = useSearch({ from: "/engagements/" })
  const navigate = useNavigate({ from: "/engagements/" })
  const {
    searchInput,
    setSearchInput,
    activeSearch,
    addOpen,
    setAddOpen,
    page,
    setPage,
    limit,
    sort,
    toggleSort,
    setFilter,
    sortParams,
  } = useListPage({ searchParams, navigate, initialSort: { field: "period_end", desc: false } })
  const canWrite = useCanWrite()

  const activeStatus = searchParams.status
  const handleStatusChange = (next: StatusFilter) =>
    setFilter("status", next === "all" ? undefined : next)

  const query = useEntityList<Engagement, EngagementListParams>({
    resource: "engagements",
    params: { page, limit, search: activeSearch, status: activeStatus, ...sortParams },
    listFn: engagementsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters = Boolean(activeSearch) || Boolean(activeStatus)

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
        {activeStatus ? (
          <FilterChip
            label={`Status is ${activeStatus}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(activeStatus ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search engagements…"
        />
      </FilterBar>

      <EngagementFormSheet open={addOpen} onOpenChange={setAddOpen} />

      <EntityListView
        columns={COLUMNS}
        items={items}
        rowKey={(row) => row.id}
        renderRow={(row) => <EngagementRow row={row} />}
        loading={query.isPending}
        error={error}
        onRetry={() => void query.refetch()}
        selectable={false}
        empty={
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
        }
        sort={sort}
        onToggleSort={toggleSort}
        page={page}
        total={total}
        limit={limit}
        onPageChange={setPage}
      />
    </PageShell>
  )
}

function EngagementRow({ row }: { row: Engagement }) {
  const overdue = isOverdue(row.period_end, row.status)
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
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
            {row.description ? (
              <span className="block truncate text-xs text-fg-muted">{row.description}</span>
            ) : null}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1.5">
          <EngagementStatusPill status={row.status} />
          {overdue ? (
            <span
              title="Past the end of the agreed period and not yet delivered"
              className="inline-flex items-center gap-1 rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-amber-600"
            >
              <AlertTriangle className="size-3" />
              Overdue
            </span>
          ) : null}
        </div>
      </TableCell>
      <TableCell className="text-sm text-fg/75">{formatDate(row.period_start)}</TableCell>
      <TableCell className="text-sm text-fg/75">{formatDate(row.period_end)}</TableCell>
      <TableCell className="tabular-nums text-xs text-fg/75">
        {engagementHours(row).toFixed(1)}
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
              <Button
                type="button"
                variant="ghost"
                size="sm"
                aria-label={`More actions for ${row.name}`}
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/engagements/$engagementId" params={{ engagementId: row.id }}>
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

export function EngagementStatusPill({ status }: { status: EngagementStatusValue }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[11px] font-medium",
        statusTone(status),
      )}
    >
      {status}
    </span>
  )
}

function statusTone(status: EngagementStatusValue): string {
  switch (status) {
    case EngagementStatus.ACTIVE:
      return "border-primary/30 bg-primary/10 text-primary"
    case EngagementStatus.DRAFT:
      return "border-fg/20 bg-bg text-fg"
    case EngagementStatus.DELIVERED:
      return "border-amber-500/40 bg-amber-500/10 text-amber-600"
    case EngagementStatus.CLOSED:
      return "border-fg/15 bg-bg text-fg/60"
    case EngagementStatus.INVOICED:
      return "border-primary/20 bg-primary/5 text-primary"
    default:
      return "border-fg/15 bg-bg text-fg/65"
  }
}

/** Past the agreed period end, with the work not yet delivered. */
export function isOverdue(
  periodEnd: string | null | undefined,
  status: EngagementStatusValue,
): boolean {
  if (!periodEnd) return false
  if (status !== EngagementStatus.DRAFT && status !== EngagementStatus.ACTIVE) return false
  return Date.parse(periodEnd) < Date.now()
}
