import { useEffect, useMemo, useState } from "react"

import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  CalendarClock,
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
  RotateCw,
} from "lucide-react"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
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
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ServiceSessionFormSheet } from "@/components/ServiceSessionFormSheet"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Pagination } from "@/components/ui/pagination"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useTableSelection } from "@/hooks/useTableSelection"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import type { ServiceSession } from "@/types/entities"
import { SessionStatus } from "@/types/enums"

function isStatus(value: unknown): value is SessionStatus {
  return (
    value === SessionStatus.SCHEDULED ||
    value === SessionStatus.RESCHEDULED ||
    value === SessionStatus.COMPLETED ||
    value === SessionStatus.CANCELLED ||
    value === SessionStatus.NO_SHOW
  )
}

export const Route = createFileRoute("/service-sessions/")({
  component: ServiceSessionsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: {
      new?: boolean
      search?: string
      status?: SessionStatus
      service_id?: string
      person_id?: string
    } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    if (typeof search.service_id === "string" && search.service_id.trim())
      out.service_id = search.service_id
    if (typeof search.person_id === "string" && search.person_id.trim())
      out.person_id = search.person_id
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: SessionStatus.SCHEDULED, label: "Scheduled" },
  { value: SessionStatus.RESCHEDULED, label: "Rescheduled" },
  { value: SessionStatus.COMPLETED, label: "Completed" },
  { value: SessionStatus.CANCELLED, label: "Cancelled" },
  { value: SessionStatus.NO_SHOW, label: "No show" },
] as const

const RANGE_OPTIONS = [
  { value: "all", label: "All time" },
  { value: "today", label: "Today" },
  { value: "7d", label: "Next 7 days" },
  { value: "30d", label: "Next 30 days" },
  { value: "past", label: "Past sessions" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]
type RangeFilter = (typeof RANGE_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function ServiceSessionsListPage() {
  const searchParams = useSearch({ from: "/service-sessions/" })
  const navigate = useNavigate({ from: "/service-sessions/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [range, setRange] = useState<RangeFilter>("all")
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SortState>({ field: "scheduled_at", desc: true })
  const canWrite = useCanWrite()
  const limit = 20
  const toggleSort = (field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }

  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined
  const activeStatus = searchParams.status
  const activeServiceId = searchParams.service_id
  const activePersonId = searchParams.person_id

  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  useEffect(() => {
    if (activeSearch !== searchParams.search) {
      navigate({ search: (prev) => ({ ...prev, search: activeSearch }), replace: true })
      setPage(1)
    }
  }, [activeSearch, navigate, searchParams.search])

  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : next
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
    setPage(1)
  }

  const clearService = () =>
    navigate({ search: (prev) => ({ ...prev, service_id: undefined }), replace: true })
  const clearPerson = () =>
    navigate({ search: (prev) => ({ ...prev, person_id: undefined }), replace: true })

  const query = useEntityList({
    resource: "service-sessions",
    params: {
      page,
      limit,
      search: activeSearch,
      status: activeStatus,
      service_id: activeServiceId,
      person_id: activePersonId,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: serviceSessionsApi.list,
  })
  const allItems = query.data?.items ?? []
  const items = useMemo(() => filterByRange(allItems, range), [allItems, range])
  const total = query.data?.total ?? 0
  const selection = useTableSelection(items)
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters =
    Boolean(activeSearch) ||
    Boolean(activeStatus) ||
    Boolean(activeServiceId) ||
    Boolean(activePersonId) ||
    range !== "all"

  return (
    <PageShell
      icon={CalendarClock}
      breadcrumb="Delivery · Sessions"
      actions={
        <>
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          {canWrite && (
            <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
              <Plus className="size-3.5" />
              Schedule session
            </Button>
          )}
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "range", label: "Date range" },
            { id: "service", label: "Service" },
            { id: "person", label: "Person" },
          ]}
        />
        {activeStatus ? (
          <FilterChip
            label={`Status is ${activeStatus}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        {activeServiceId ? (
          <FilterChip
            label={`Service ${activeServiceId.slice(0, 8)}`}
            onRemove={clearService}
          />
        ) : null}
        {activePersonId ? (
          <FilterChip
            label={`Person ${activePersonId.slice(0, 8)}`}
            onRemove={clearPerson}
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(activeStatus ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <FilterTrigger
          icon={CalendarClock}
          label="All time"
          value={range}
          options={RANGE_OPTIONS}
          onChange={setRange}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search sessions…"
        />
      </FilterBar>

      <ServiceSessionFormSheet
        open={addOpen}
        onOpenChange={setAddOpen}
        serviceId={activeServiceId}
        personId={activePersonId}
      />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void query.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title={hasFilters ? "No sessions match your filters" : "No sessions yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Schedule a session to start delivering care against a contract."
            }
            action={
              hasFilters || !canWrite ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  Schedule session
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
                      <SortHeader field="scheduled_at" sort={sort} onToggle={toggleSort}>
                        Scheduled
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="service_id" sort={sort} onToggle={toggleSort}>
                        Service
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="person_id" sort={sort} onToggle={toggleSort}>
                        Person
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        Status
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Location</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <SessionRow key={row.id} row={row} isSelected={selection.selectedIds.has(row.id)} onToggle={() => selection.toggleSelect(row.id)} />
                  ))}
                </TableBody>
              </Table>
            </div>
            {total > 0 && (
              <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                <Pagination page={page} total={total} limit={limit} onPageChange={setPage} />
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  )
}

function SessionRow({ row, isSelected, onToggle }: { row: ServiceSession; isSelected: boolean; onToggle: () => void }) {
  const scheduled = new Date(row.scheduled_at)
  const dateLabel = scheduled.toLocaleDateString()
  const timeLabel = scheduled.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox aria-label={`Select session ${row.id}`} checked={isSelected} onCheckedChange={onToggle} />
      </TableCell>
      <TableCell>
        <Link
          to="/service-sessions/$sessionId"
          params={{ sessionId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <CalendarClock className="size-3" />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium text-fg group-hover:text-primary">
              {dateLabel}
            </span>
            <span className="block truncate font-mono text-xs text-fg/55">{timeLabel}</span>
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <Link
          to="/services/$serviceId"
          params={{ serviceId: row.service_id }}
          className="font-mono text-xs text-fg/75 hover:text-primary"
        >
          {row.service_id.slice(0, 8)}
        </Link>
      </TableCell>
      <TableCell>
        <Link
          to="/persons/$personId"
          params={{ personId: row.person_id }}
          className="font-mono text-xs text-fg/75 hover:text-primary"
        >
          {row.person_id.slice(0, 8)}
        </Link>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1.5">
          <StatusBadge status={row.status} />
          {isBackfill(row) ? (
            <span
              title="Logged after the fact"
              className="inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1 py-0.5 text-[10px] font-medium tracking-wide text-fg/65"
            >
              Backfilled
            </span>
          ) : null}
        </div>
      </TableCell>
      <TableCell className="text-sm text-fg/75">
        {row.location ?? <span className="text-fg/40">—</span>}
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/service-sessions/$sessionId"
            params={{ sessionId: row.id }}
            aria-label="Open session"
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
                aria-label="More actions"
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/service-sessions/$sessionId" params={{ sessionId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/persons/$personId" params={{ personId: row.person_id }}>
                  View person
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/services/$serviceId" params={{ serviceId: row.service_id }}>
                  View service
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive focus:text-destructive">
                Cancel
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center px-6 py-10">
      <div className="flex max-w-sm flex-col items-center text-center">
        <p className="text-sm text-danger-fg">{message}</p>
        <Button variant="outline" size="sm" className="mt-4 gap-1.5" onClick={onRetry}>
          <RotateCw className="size-4" />
          Try again
        </Button>
      </div>
    </div>
  )
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

function filterByRange(items: ServiceSession[], range: RangeFilter): ServiceSession[] {
  if (range === "all") return items
  const now = new Date()
  if (range === "past") {
    return items.filter((s) => new Date(s.scheduled_at) < now)
  }
  if (range === "today") {
    const start = new Date(now)
    start.setHours(0, 0, 0, 0)
    const end = new Date(now)
    end.setHours(23, 59, 59, 999)
    return items.filter((s) => {
      const t = new Date(s.scheduled_at).getTime()
      return t >= start.getTime() && t <= end.getTime()
    })
  }
  const days = range === "7d" ? 7 : 30
  const horizon = new Date(now.getTime() + days * 86_400_000)
  return items.filter((s) => {
    const t = new Date(s.scheduled_at).getTime()
    return t >= now.getTime() && t <= horizon.getTime()
  })
}

function isBackfill(s: ServiceSession): boolean {
  const meta = s.metadata as Record<string, unknown> | null | undefined
  return Boolean(meta && typeof meta === "object" && "backfill" in meta && meta.backfill)
}
