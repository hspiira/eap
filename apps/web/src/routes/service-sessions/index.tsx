import { useEffect, useMemo, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  CalendarClock,
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
  RotateCw,
} from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import {
  type ServiceSessionListParams,
  serviceSessionsApi,
} from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { usersApi } from "@/api/endpoints/users"
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
import { displayName } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import type { Service, ServiceSession } from "@/types/entities"
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

function isRange(value: unknown): value is Exclude<RangeFilter, "all"> {
  return value === "today" || value === "7d" || value === "30d" || value === "past"
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
      range?: Exclude<RangeFilter, "all">
    } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    if (typeof search.service_id === "string" && search.service_id.trim())
      out.service_id = search.service_id
    if (typeof search.person_id === "string" && search.person_id.trim())
      out.person_id = search.person_id
    if (isRange(search.range)) out.range = search.range
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
  const activeRange: RangeFilter = searchParams.range ?? "all"

  // Anchored to the selected range, not to render: `new Date()` inline would mint
  // a new query key on every render and refetch forever.
  const rangeParams = useMemo(() => rangeBounds(activeRange, new Date()), [activeRange])

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

  const handleRangeChange = (next: RangeFilter) => {
    const range = next === "all" ? undefined : next
    navigate({ search: (prev) => ({ ...prev, range }), replace: true })
    setPage(1)
  }

  const { data: servicesData } = useQuery({
    queryKey: ["services", "lookup"],
    queryFn: () => servicesApi.list({ limit: 200 }),
    staleTime: 5 * 60_000,
  })
  const servicesById = useMemo(() => {
    const m = new Map<string, Service>()
    for (const s of servicesData?.items ?? []) m.set(s.id, s)
    return m
  }, [servicesData])

  const { data: activePersonForChip = null } = useQuery({
    queryKey: ["person", activePersonId],
    queryFn: () => personsApi.getById(activePersonId!),
    enabled: !!activePersonId,
    staleTime: 10 * 60_000,
  })

  const query = useEntityList<ServiceSession, ServiceSessionListParams>({
    resource: "service-sessions",
    params: {
      page,
      limit,
      search: activeSearch,
      status: activeStatus,
      service_id: activeServiceId,
      person_id: activePersonId,
      ...rangeParams,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: serviceSessionsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const selection = useTableSelection(items)
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters =
    Boolean(activeSearch) ||
    Boolean(activeStatus) ||
    Boolean(activeServiceId) ||
    Boolean(activePersonId) ||
    activeRange !== "all"

  const activeServiceLabel = activeServiceId
    ? (servicesById.get(activeServiceId)?.name ?? activeServiceId.slice(0, 8))
    : null
  const activePersonLabel = activePersonId
    ? (activePersonForChip ? displayName(activePersonForChip, null) : activePersonId.slice(0, 8))
    : null

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
        {activeServiceLabel ? (
          <FilterChip
            label={`Service: ${activeServiceLabel}`}
            onRemove={clearService}
          />
        ) : null}
        {activePersonLabel ? (
          <FilterChip
            label={`Person: ${activePersonLabel}`}
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
          value={activeRange}
          options={RANGE_OPTIONS}
          onChange={handleRangeChange}
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
                    <SessionRow
                      key={row.id}
                      row={row}
                      servicesById={servicesById}
                      isSelected={selection.selectedIds.has(row.id)}
                      onToggle={() => selection.toggleSelect(row.id)}
                    />
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

function SessionRow({
  row,
  servicesById,
  isSelected,
  onToggle,
}: {
  row: ServiceSession
  servicesById: Map<string, Service>
  isSelected: boolean
  onToggle: () => void
}) {
  const linkedService = servicesById.get(row.service_id) ?? null
  const { data: linkedPerson = null } = useQuery({
    queryKey: ["person", row.person_id],
    queryFn: () => personsApi.getById(row.person_id),
    staleTime: 10 * 60_000,
  })
  const { data: linkedPersonUser = null } = useQuery({
    queryKey: ["user", linkedPerson?.user_id],
    queryFn: () => usersApi.getById(linkedPerson!.user_id!),
    enabled: !!linkedPerson?.user_id,
    staleTime: 10 * 60_000,
  })
  const personLabel = linkedPerson
    ? displayName(linkedPerson, linkedPersonUser)
    : row.person_id.slice(0, 8)
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
          className="text-xs text-fg/75 hover:text-primary"
        >
          {linkedService?.name ?? row.service_id.slice(0, 8)}
        </Link>
      </TableCell>
      <TableCell>
        <Link
          to="/persons/$personId"
          params={{ personId: row.person_id }}
          className="text-xs text-fg/75 hover:text-primary"
        >
          {personLabel}
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

/**
 * Turns the range dropdown into absolute instants for the server to filter on.
 * This used to filter the fetched page in memory, which contradicted the total
 * returned alongside it.
 *
 * The bounds are computed here rather than named to the server ("today") on
 * purpose: "today" means the viewer's calendar day, so the browser is the only
 * thing that knows where it starts and ends. `now` is passed in so the mapping
 * stays a pure function.
 */
function rangeBounds(
  range: RangeFilter,
  now: Date,
): Pick<ServiceSessionListParams, "scheduled_from" | "scheduled_to"> {
  if (range === "all") return {}
  if (range === "past") return { scheduled_to: now.toISOString() }
  if (range === "today") {
    const start = new Date(now)
    start.setHours(0, 0, 0, 0)
    const end = new Date(now)
    end.setHours(23, 59, 59, 999)
    return { scheduled_from: start.toISOString(), scheduled_to: end.toISOString() }
  }
  const days = range === "7d" ? 7 : 30
  return {
    scheduled_from: now.toISOString(),
    scheduled_to: new Date(now.getTime() + days * 86_400_000).toISOString(),
  }
}

function isBackfill(s: ServiceSession): boolean {
  const meta = s.metadata as Record<string, unknown> | null | undefined
  return Boolean(meta && typeof meta === "object" && "backfill" in meta && meta.backfill)
}
