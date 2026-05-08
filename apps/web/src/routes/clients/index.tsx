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
import { ClientForm } from "@/components/ClientForm"
import { ClientsListSkeleton } from "@/components/ClientsPageSkeletons"
import { ListToolbar } from "@/components/common/ListToolbar"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { TierBadge } from "@/components/common/TierBadge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogCloseButton,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Pagination } from "@/components/ui/pagination"
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

const TIER_FILTER_OPTIONS: Array<{ value: "all" | ClientTier; label: string }> = [
  { value: "all", label: "All tiers" },
  { value: ClientTier.A, label: "Tier A" },
  { value: ClientTier.B, label: "Tier B" },
  { value: ClientTier.C, label: "Tier C" },
]

const TIME_RANGE_OPTIONS = [
  { value: "12h", label: "Last 12 hours" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "all", label: "All time" },
]

function ClientsListPage() {
  const searchParams = useSearch({ from: "/clients/" })
  const navigate = useNavigate({ from: "/clients/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [timeRange, setTimeRange] = useState("12h")
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [page, setPage] = useState(1)
  const limit = 20
  const queryClient = useQueryClient()

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

  const handleTierChange = (next: string) => {
    const tier = isTier(next) ? next : undefined
    navigate({ search: (prev) => ({ ...prev, tier }), replace: true })
    setPage(1)
  }

  const query = useEntityList({
    resource: "clients",
    params: { page, limit, search: activeSearch, tier: activeTier },
    listFn: clientsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const refetch = () => queryClient.invalidateQueries({ queryKey: ["clients", "list"] })

  const description =
    total > 0
      ? `${total.toLocaleString()} ${total === 1 ? "client" : "clients"} on file`
      : "Manage corporate clients, billing entities, and tiering"

  return (
    <PageShell
      icon={Building2}
      breadcrumb="Organization & Clients · Clients"
      title="Clients"
      description={description}
      actions={
        <>
          <Button
            variant="outline"
            size="sm"
            className="rounded-none gap-1.5"
            onClick={refetch}
          >
            <RotateCw className="size-4" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" className="rounded-none gap-1.5">
            <Download className="size-4" />
            Export
          </Button>
          <Button
            size="sm"
            className="rounded-none gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={() => setAddModalOpen(true)}
          >
            <Plus className="size-4" />
            Add client
          </Button>
        </>
      }
      toolbar={
        <ListToolbar
          searchValue={searchInput}
          onSearchChange={setSearchInput}
          placeholder="Search clients by name or code…"
          filters={
            <>
              <Select value={activeTier ?? "all"} onValueChange={handleTierChange}>
                <SelectTrigger
                  className="h-9 w-32 rounded-none border-fg/25 bg-surface text-fg [&>svg]:text-fg/60"
                  aria-label="Filter by tier"
                >
                  <SelectValue placeholder="All tiers" />
                </SelectTrigger>
                <SelectContent className="rounded-none border-fg/25 bg-surface">
                  {TIER_FILTER_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="rounded-none">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="h-9 w-44 gap-1.5 rounded-none border-fg/25 bg-surface text-fg [&>svg]:text-fg/60">
                  <Calendar className="size-4" />
                  <SelectValue placeholder="Last 12 hours" />
                </SelectTrigger>
                <SelectContent className="rounded-none border-fg/25 bg-surface">
                  {TIME_RANGE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="rounded-none">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      }
    >
      <Dialog open={addModalOpen} onOpenChange={setAddModalOpen}>
        <DialogContent className="rounded-none">
          <DialogCloseButton />
          <DialogHeader>
            <DialogTitle>Add client</DialogTitle>
            <DialogDescription>Create a new client record.</DialogDescription>
          </DialogHeader>
          <div className="px-6 pb-6">
            <ClientForm
              onSuccess={() => setAddModalOpen(false)}
              onCancel={() => setAddModalOpen(false)}
            />
          </div>
        </DialogContent>
      </Dialog>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <ClientsListSkeleton />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={refetch} />
        ) : items.length === 0 ? (
          <EmptyState
            hasSearch={Boolean(activeSearch)}
            onAdd={() => setAddModalOpen(true)}
          />
        ) : (
          <>
            <div className="min-h-0 flex-1 overflow-auto">
              <ClientsTable items={items} />
            </div>
            {total > 0 && (
              <div className="shrink-0 border-t border-fg/10 bg-surface px-5 py-2.5">
                <Pagination page={page} total={total} limit={limit} onPageChange={setPage} />
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  )
}

function ClientsTable({ items }: { items: ReadonlyArray<Client> }) {
  return (
    <Table>
      <TableHeader className="sticky top-0 z-10 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
        <TableRow className="hover:bg-transparent">
          <TableHead className="w-10 px-5">
            <input
              type="checkbox"
              aria-label="Select all"
              className="size-3.5 cursor-pointer accent-primary"
            />
          </TableHead>
          <TableHead className="text-fg/70">Client</TableHead>
          <TableHead className="text-fg/70">Code</TableHead>
          <TableHead className="text-fg/70">Tier</TableHead>
          <TableHead className="text-fg/70">Status</TableHead>
          <TableHead className="text-fg/70">Contact</TableHead>
          <TableHead className="w-16 text-right text-fg/70">
            <span className="sr-only">Actions</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((row) => (
          <ClientRow key={row.id} row={row} />
        ))}
      </TableBody>
    </Table>
  )
}

function ClientRow({ row }: { row: Client }) {
  const contactPrimary = row.contact_info?.email ?? row.contact_info?.phone ?? null
  const contactSecondary =
    row.contact_info?.email && row.contact_info?.phone ? row.contact_info?.phone : null

  return (
    <TableRow className="group cursor-default">
      <TableCell className="px-5">
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
            className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-xs font-semibold text-primary"
          >
            {initial(row.name)}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium text-fg group-hover:text-primary">
              {row.name}
            </span>
            <span className="block truncate text-xs text-fg/55">
              {row.code}
            </span>
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
            className="grid size-7 place-items-center rounded-none text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label={`More actions for ${row.name}`}
                className="grid size-7 place-items-center rounded-none text-fg/65 hover:bg-surface-hover hover:text-fg"
              >
                <MoreHorizontal className="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="rounded-none">
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

function EmptyState({ hasSearch, onAdd }: { hasSearch: boolean; onAdd: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center p-10">
      <div className="max-w-md border border-fg/15 bg-surface p-8 text-center">
        <div className="mx-auto mb-3 grid size-10 place-items-center bg-primary/10">
          <Building2 className="size-5 text-primary" />
        </div>
        <h2 className="text-base font-semibold text-fg">
          {hasSearch ? "No clients match your search" : "No clients yet"}
        </h2>
        <p className="mt-1 text-sm text-fg/65">
          {hasSearch
            ? "Try a different name or code, or clear filters."
            : "Add your first corporate client to get started."}
        </p>
        {!hasSearch && (
          <Button
            size="sm"
            className="mt-4 rounded-none bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={onAdd}
          >
            <Plus className="size-4" />
            Add client
          </Button>
        )}
      </div>
    </div>
  )
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center p-10">
      <div className="max-w-md border border-danger/30 bg-danger-soft p-6 text-center">
        <p className="text-sm text-danger-fg">{message}</p>
        <Button
          variant="outline"
          size="sm"
          className="mt-4 rounded-none gap-1.5"
          onClick={onRetry}
        >
          <RotateCw className="size-4" />
          Try again
        </Button>
      </div>
    </div>
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
