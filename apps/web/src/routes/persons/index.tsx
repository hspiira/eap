import { useEffect, useMemo, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
  Users,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { personsApi } from "@/api/endpoints/persons"
import { usersApi } from "@/api/endpoints/users"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
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
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { PERSON_TYPE_LABELS,PersonFormSheet } from "@/components/PersonFormSheet"
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
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { displayName, personInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import type { Client, Person } from "@/types/entities"
import { BaseStatus, PersonType } from "@/types/enums"

function isType(value: unknown): value is PersonType {
  return (
    value === PersonType.CLIENT_EMPLOYEE ||
    value === PersonType.DEPENDENT ||
    value === PersonType.SERVICE_PROVIDER ||
    value === PersonType.PLATFORM_STAFF
  )
}

function isStatus(value: unknown): value is BaseStatus {
  return STATUS_VALUES.includes(value as BaseStatus)
}

export const Route = createFileRoute("/persons/")({
  component: PersonsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: {
      new?: boolean
      search?: string
      type?: PersonType
      client_id?: string
      status?: BaseStatus
    } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isType(search.type)) out.type = search.type
    if (typeof search.client_id === "string" && search.client_id.trim()) {
      out.client_id = search.client_id
    }
    if (isStatus(search.status)) out.status = search.status
    return out
  },
})

const TYPE_OPTIONS = [
  { value: "all", label: "All roles" },
  { value: PersonType.CLIENT_EMPLOYEE, label: PERSON_TYPE_LABELS[PersonType.CLIENT_EMPLOYEE] },
  { value: PersonType.DEPENDENT, label: PERSON_TYPE_LABELS[PersonType.DEPENDENT] },
  { value: PersonType.SERVICE_PROVIDER, label: PERSON_TYPE_LABELS[PersonType.SERVICE_PROVIDER] },
  { value: PersonType.PLATFORM_STAFF, label: PERSON_TYPE_LABELS[PersonType.PLATFORM_STAFF] },
] as const

const STATUS_VALUES: ReadonlyArray<BaseStatus> = [
  BaseStatus.ACTIVE,
  BaseStatus.INACTIVE,
  BaseStatus.ARCHIVED,
]

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: BaseStatus.ACTIVE, label: "Active" },
  { value: BaseStatus.INACTIVE, label: "Inactive" },
  { value: BaseStatus.ARCHIVED, label: "Archived" },
] as const

type TypeFilter = (typeof TYPE_OPTIONS)[number]["value"]
type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function PersonsListPage() {
  const searchParams = useSearch({ from: "/persons/" })
  const navigate = useNavigate({ from: "/persons/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const limit = 20

  const toggleSort = (field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }

  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined
  const activeType = searchParams.type
  const activeClientId = searchParams.client_id
  const activeStatus = searchParams.status

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

  const handleTypeChange = (next: TypeFilter) => {
    const type = next === "all" ? undefined : next
    navigate({ search: (prev) => ({ ...prev, type }), replace: true })
    setPage(1)
  }

  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : next
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
    setPage(1)
  }

  const clearClient = () => {
    navigate({ search: (prev) => ({ ...prev, client_id: undefined }), replace: true })
    setPage(1)
  }

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup"],
    queryFn: () => clientsApi.list({ limit: 500 }),
    staleTime: 5 * 60_000,
  })
  const clientsById = useMemo(() => {
    const m = new Map<string, Client>()
    for (const c of clientsData?.items ?? []) m.set(c.id, c)
    return m
  }, [clientsData])

  const query = useEntityList({
    resource: "persons",
    params: {
      page,
      limit,
      search: activeSearch,
      person_type: activeType,
      client_id: activeClientId,
      status: activeStatus,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: personsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters =
    Boolean(activeSearch) ||
    Boolean(activeType) ||
    Boolean(activeClientId) ||
    Boolean(activeStatus)

  return (
    <PageShell
      icon={Users}
      breadcrumb="People · Persons"
      actions={
        <>
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
            <Plus className="size-3.5" />
            Add person
          </Button>
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "type", label: "Role" },
            { id: "status", label: "Status" },
            { id: "client", label: "Client" },
          ]}
        />
        {activeType ? (
          <FilterChip
            label={`Role is ${PERSON_TYPE_LABELS[activeType]}`}
            onRemove={() => handleTypeChange("all")}
          />
        ) : null}
        {activeClientId ? (
          <FilterChip
            label={`Client: ${clientsById.get(activeClientId)?.name ?? activeClientId.slice(0, 8)}`}
            onRemove={clearClient}
          />
        ) : null}
        {activeStatus ? (
          <FilterChip
            label={`Status is ${activeStatus}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        <FilterTrigger
          label="All roles"
          value={(activeType ?? "all") as TypeFilter}
          options={TYPE_OPTIONS}
          onChange={handleTypeChange}
        />
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
          placeholder="Search persons…"
        />
      </FilterBar>

      <PersonFormSheet
        open={addOpen}
        onOpenChange={setAddOpen}
        clientId={activeClientId}
        lockType={
          activeType === PersonType.PLATFORM_STAFF || activeType === PersonType.SERVICE_PROVIDER
            ? activeType
            : undefined
        }
      />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={6} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void query.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Users}
            title={hasFilters ? "No persons match your filters" : "No persons yet"}
            description={
              hasFilters
                ? "Try a different name, role, or clear filters."
                : "Add your first person — employee, dependent, provider, or staff."
            }
            action={
              hasFilters ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  Add person
                </Button>
              )
            }
          />
        ) : (
          <>
            <div className="relative min-h-0 flex-1 overflow-auto">
              <Table className="w-full caption-bottom text-sm">
                <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <Checkbox aria-label="Select all" />
                    </TableHead>
                    <TableHead>
                      <SortHeader field="last_name" sort={sort} onToggle={toggleSort}>
                        Name
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="person_type" sort={sort} onToggle={toggleSort}>
                        Role
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="client_id" sort={sort} onToggle={toggleSort}>
                        Client
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        Status
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Account</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <PersonRow
                      key={row.id}
                      row={row}
                      clientsById={clientsById}
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

function PersonRow({
  row,
  clientsById,
}: {
  row: Person
  clientsById: Map<string, Client>
}) {
  const { data: linkedUser = null } = useQuery({
    queryKey: ["user", row.user_id],
    queryFn: () => usersApi.getById(row.user_id!),
    enabled: !!row.user_id,
    staleTime: 10 * 60_000,
  })
  const linkedClient = row.employment_info?.client_id
    ? (clientsById.get(row.employment_info.client_id) ?? null)
    : null
  const fullName = displayName(row, linkedUser)

  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox aria-label={`Select ${fullName}`} onClick={(e) => e.stopPropagation()} />
      </TableCell>
      <TableCell>
        <Link
          to="/persons/$personId"
          params={{ personId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            {personInitials(row, linkedUser)}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium text-fg group-hover:text-primary">
              {fullName}
            </span>
            {row.employment_info?.role ? (
              <span className="block truncate text-xs text-fg/55">
                {row.employment_info.role}
                {row.employment_info.department ? ` · ${row.employment_info.department}` : ""}
              </span>
            ) : null}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <span className="inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[11px] font-medium text-fg/75">
          {PERSON_TYPE_LABELS[row.person_type]}
        </span>
      </TableCell>
      <TableCell>
        {linkedClient ? (
          <Link
            to="/clients/$clientId"
            params={{ clientId: linkedClient.id }}
            className="text-xs text-fg/70 hover:text-primary"
          >
            {linkedClient.name}
          </Link>
        ) : row.employment_info?.client_id ? (
          <Link
            to="/clients/$clientId"
            params={{ clientId: row.employment_info.client_id }}
            className="font-mono text-xs text-fg/40 hover:text-primary"
          >
            {row.employment_info.client_id.slice(0, 8)}
          </Link>
        ) : (
          <span className="text-fg/40">—</span>
        )}
      </TableCell>
      <TableCell>
        <StatusBadge status={row.status} />
      </TableCell>
      <TableCell>
        {linkedUser ? (
          <Link
            to="/users/$userId"
            params={{ userId: linkedUser.id }}
            className="max-w-35 truncate text-xs text-fg/70 hover:text-primary"
          >
            {linkedUser.email}
          </Link>
        ) : row.user_id ? (
          <span className="font-mono text-xs text-fg/40">{row.user_id.slice(0, 8)}</span>
        ) : (
          <span className="text-fg/40">—</span>
        )}
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/persons/$personId"
            params={{ personId: row.id }}
            aria-label={`Open ${fullName}`}
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button type="button" variant="ghost" size="sm" aria-label={`More actions for ${fullName}`} className="size-7 p-0 text-fg/65"><MoreHorizontal className="size-4" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/persons/$personId" params={{ personId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              {row.employment_info?.client_id ? (
                <DropdownMenuItem asChild>
                  <Link to="/clients/$clientId" params={{ clientId: row.employment_info.client_id }}>
                    View client
                  </Link>
                </DropdownMenuItem>
              ) : null}
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive focus:text-destructive">
                Archive
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}

