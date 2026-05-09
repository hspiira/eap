import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
  RotateCw,
  Users,
} from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { PERSON_TYPE_LABELS,PersonFormSheet } from "@/components/PersonFormSheet"
import { PersonsListSkeleton } from "@/components/PersonsPageSkeletons"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Pagination } from "@/components/ui/pagination"
import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { Person } from "@/types/entities"
import { PersonType } from "@/types/enums"
import { normalizeErrorMessage } from "@/utils/errorHandler"

function isType(value: unknown): value is PersonType {
  return (
    value === PersonType.CLIENT_EMPLOYEE ||
    value === PersonType.DEPENDENT ||
    value === PersonType.SERVICE_PROVIDER ||
    value === PersonType.PLATFORM_STAFF
  )
}

export const Route = createFileRoute("/persons/")({
  component: PersonsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: {
      new?: boolean
      search?: string
      type?: PersonType
      client_id?: string
    } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isType(search.type)) out.type = search.type
    if (typeof search.client_id === "string" && search.client_id.trim()) {
      out.client_id = search.client_id
    }
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

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: "Active", label: "Active" },
  { value: "Inactive", label: "Inactive" },
  { value: "Archived", label: "Archived" },
] as const

type TypeFilter = (typeof TYPE_OPTIONS)[number]["value"]
type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function PersonsListPage() {
  const searchParams = useSearch({ from: "/persons/" })
  const navigate = useNavigate({ from: "/persons/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const limit = 20
  const queryClient = useQueryClient()

  const toggleSort = (field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }

  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined
  const activeType = searchParams.type
  const activeClientId = searchParams.client_id

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

  const clearClient = () => {
    navigate({ search: (prev) => ({ ...prev, client_id: undefined }), replace: true })
    setPage(1)
  }

  const query = useEntityList({
    resource: "persons",
    params: {
      page,
      limit,
      search: activeSearch,
      person_type: activeType,
      client_id: activeClientId,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: personsApi.list,
  })
  const allItems = query.data?.items ?? []
  const items =
    statusFilter === "all"
      ? allItems
      : allItems.filter((p) => p.status === statusFilter)
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const refetch = () => queryClient.invalidateQueries({ queryKey: ["persons", "list"] })
  const hasFilters =
    Boolean(activeSearch) ||
    Boolean(activeType) ||
    Boolean(activeClientId) ||
    statusFilter !== "all"

  return (
    <PageShell
      icon={Users}
      breadcrumb="People · Persons"
      actions={
        <>
          <IconButton label="Refresh" onClick={refetch} icon={RotateCw} />
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
            label={`Client ${activeClientId.slice(0, 8)}`}
            onRemove={clearClient}
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
          value={statusFilter}
          options={STATUS_OPTIONS}
          onChange={setStatusFilter}
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
        onSaved={() => refetch()}
      />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <PersonsListSkeleton />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={refetch} />
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
              <table className="w-full caption-bottom text-sm">
                <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <input
                        type="checkbox"
                        aria-label="Select all"
                        className="size-3.5 cursor-pointer accent-primary"
                      />
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
                    <TableHead className="text-fg/65">Contact</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <PersonRow key={row.id} row={row} />
                  ))}
                </TableBody>
              </table>
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

function PersonRow({ row }: { row: Person }) {
  const fullName = `${row.first_name} ${row.last_name}`.trim()
  const contactPrimary = row.contact_info?.email ?? row.contact_info?.mobile ?? row.contact_info?.phone ?? null
  const contactSecondary =
    row.contact_info?.email && (row.contact_info?.mobile ?? row.contact_info?.phone)
      ? row.contact_info.mobile ?? row.contact_info.phone
      : null

  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <input
          type="checkbox"
          aria-label={`Select ${fullName}`}
          onClick={(e) => e.stopPropagation()}
          className="size-3.5 cursor-pointer accent-primary"
        />
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
            {personInitial(row)}
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
        {row.client_id ? (
          <Link
            to="/clients/$clientId"
            params={{ clientId: row.client_id }}
            className="font-mono text-xs text-fg/70 hover:text-primary"
          >
            {row.client_id.slice(0, 8)}
          </Link>
        ) : (
          <span className="text-fg/40">—</span>
        )}
      </TableCell>
      <TableCell>
        <StatusBadge status={row.status} />
      </TableCell>
      <TableCell>
        {contactPrimary ? (
          <span className="block min-w-0">
            <span className="block truncate text-sm text-fg">{contactPrimary}</span>
            {contactSecondary ? (
              <span className="block truncate text-xs text-fg/55">{contactSecondary}</span>
            ) : null}
          </span>
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
              <button
                type="button"
                aria-label={`More actions for ${fullName}`}
                className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
              >
                <MoreHorizontal className="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/persons/$personId" params={{ personId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              {row.client_id ? (
                <DropdownMenuItem asChild>
                  <Link to="/clients/$clientId" params={{ clientId: row.client_id }}>
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
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
    >
      <Icon className="size-3.5" />
    </button>
  )
}

function personInitial(p: Person): string {
  const f = p.first_name?.[0] ?? ""
  const l = p.last_name?.[0] ?? ""
  return (f + l).toUpperCase() || "·"
}
