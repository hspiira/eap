import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Building2,
  Calendar,
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
  RotateCw,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { ClientFormSheet } from "@/components/ClientFormSheet"
import { ClientsListSkeleton } from "@/components/ClientsPageSkeletons"
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
import { TierBadge } from "@/components/common/TierBadge"
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
import type { Client } from "@/types/entities"
import { ClientTier } from "@/types/enums"
import { normalizeErrorMessage } from "@/utils/errorHandler"

function isTier(value: unknown): value is ClientTier {
  return value === ClientTier.A || value === ClientTier.B || value === ClientTier.C
}

export const Route = createFileRoute("/clients/")({
  component: ClientsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { new?: boolean; search?: string; tier?: ClientTier } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isTier(search.tier)) out.tier = search.tier
    return out
  },
})

const TIER_OPTIONS = [
  { value: "all", label: "All tiers" },
  { value: ClientTier.A, label: "Tier A" },
  { value: ClientTier.B, label: "Tier B" },
  { value: ClientTier.C, label: "Tier C" },
] as const

const TIME_RANGE_OPTIONS = [
  { value: "12h", label: "Last 12 hours" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "all", label: "All time" },
] as const

type TierFilter = (typeof TIER_OPTIONS)[number]["value"]
type TimeRange = (typeof TIME_RANGE_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function ClientsListPage() {
  const searchParams = useSearch({ from: "/clients/" })
  const navigate = useNavigate({ from: "/clients/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [timeRange, setTimeRange] = useState<TimeRange>("12h")
  const [addModalOpen, setAddModalOpen] = useState(false)
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
  const activeTier = searchParams.tier

  useEffect(() => {
    if (searchParams.new) setAddModalOpen(true)
  }, [searchParams.new])

  useEffect(() => {
    if (activeSearch !== searchParams.search) {
      navigate({ search: (prev) => ({ ...prev, search: activeSearch }), replace: true })
      setPage(1)
    }
  }, [activeSearch, navigate, searchParams.search])

  const handleTierChange = (next: TierFilter) => {
    const tier = next === "all" ? undefined : next
    navigate({ search: (prev) => ({ ...prev, tier }), replace: true })
    setPage(1)
  }

  const query = useEntityList({
    resource: "clients",
    params: {
      page,
      limit,
      search: activeSearch,
      tier: activeTier,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: clientsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const refetch = () => queryClient.invalidateQueries({ queryKey: ["clients", "list"] })
  const hasFilters = Boolean(activeSearch) || Boolean(activeTier)

  return (
    <PageShell
      icon={Building2}
      breadcrumb="Organization & Clients · Clients"
      actions={
        <>
          <IconButton label="Refresh" onClick={refetch} icon={RotateCw} />
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            size="sm"
            className="h-7 gap-1.5 px-2.5"
            onClick={() => setAddModalOpen(true)}
          >
            <Plus className="size-3.5" />
            Add client
          </Button>
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "tier", label: "Tier" },
            { id: "status", label: "Status" },
            { id: "industry", label: "Industry" },
            { id: "tag", label: "Tag" },
          ]}
        />
        {activeTier ? (
          <FilterChip
            label={`Tier is ${activeTier}`}
            onRemove={() => handleTierChange("all")}
          />
        ) : null}
        <FilterTrigger
          label="All tiers"
          value={(activeTier ?? "all") as TierFilter}
          options={TIER_OPTIONS}
          onChange={handleTierChange}
        />
        <FilterTrigger
          icon={Calendar}
          label="Time range"
          value={timeRange}
          options={TIME_RANGE_OPTIONS}
          onChange={setTimeRange}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search clients…"
        />
      </FilterBar>

      <ClientFormSheet
        open={addModalOpen}
        onOpenChange={setAddModalOpen}
        onSaved={() => refetch()}
      />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <ClientsListSkeleton />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={refetch} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Building2}
            title={hasFilters ? "No clients match your filters" : "No clients yet"}
            description={
              hasFilters
                ? "Try a different name or clear filters."
                : "Add your first corporate client to get started."
            }
            action={
              hasFilters ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddModalOpen(true)}>
                  <Plus className="size-4" />
                  Add client
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
                      <SortHeader field="name" sort={sort} onToggle={toggleSort}>
                        Client
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="code" sort={sort} onToggle={toggleSort}>
                        Code
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="tier" sort={sort} onToggle={toggleSort}>
                        Tier
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
                    <ClientRow key={row.id} row={row} />
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

function ClientRow({ row }: { row: Client }) {
  const contactPrimary = row.contact_info?.email ?? row.contact_info?.phone ?? null
  const contactSecondary =
    row.contact_info?.email && row.contact_info?.phone ? row.contact_info?.phone : null

  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <input
          type="checkbox"
          aria-label={`Select ${row.name}`}
          onClick={(e) => e.stopPropagation()}
          className="size-3.5 cursor-pointer accent-primary"
        />
      </TableCell>
      <TableCell>
        <Link
          to="/clients/$clientId"
          params={{ clientId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            {initial(row.name)}
          </span>
          <span className="text-sm font-medium text-fg group-hover:text-primary">
            {row.name}
          </span>
        </Link>
      </TableCell>
      <TableCell className="font-mono text-xs text-fg/70">{row.code}</TableCell>
      <TableCell>
        <TierBadge tier={row.tier} />
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
            to="/clients/$clientId"
            params={{ clientId: row.id }}
            aria-label={`Open ${row.name}`}
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label={`More actions for ${row.name}`}
                className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
              >
                <MoreHorizontal className="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/clients/$clientId" params={{ clientId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem>Edit</DropdownMenuItem>
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

function initial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return trimmed.slice(0, 2).toUpperCase()
}
