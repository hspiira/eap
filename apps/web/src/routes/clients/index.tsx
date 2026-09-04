import { useCallback, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { Building2, ExternalLink, MoreHorizontal, Plus } from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { ClientFormSheet } from "@/components/ClientFormSheet"
import { BulkAction } from "@/components/common/BulkAction"
import { ConfirmDialog } from "@/components/common/ConfirmDialog"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView, type ListColumn } from "@/components/common/EntityListView"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { SelectionBar } from "@/components/common/SelectionBar"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ROW_BORDER } from "@/components/common/tableStyles"
import { TierBadge } from "@/components/common/TierBadge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { TableCell, TableRow } from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import { enumParam, listSearchSchema } from "@/lib/search-params"
import type { Client } from "@/types/entities"
import { ClientTier } from "@/types/enums"

export const Route = createFileRoute("/clients/")({
  component: ClientsListPage,
  validateSearch: listSearchSchema({ tier: enumParam(ClientTier) }),
})

const TIER_OPTIONS = [
  { value: "all", label: "All tiers" },
  { value: ClientTier.A, label: "Tier A" },
  { value: ClientTier.B, label: "Tier B" },
  { value: ClientTier.C, label: "Tier C" },
] as const

type TierFilter = (typeof TIER_OPTIONS)[number]["value"]

const COLUMNS: ListColumn[] = [
  { header: "Client", sortField: "name" },
  { header: "Code", sortField: "code" },
  { header: "Tier", sortField: "tier" },
  { header: "Status", sortField: "status" },
  { header: "Contact", className: "text-fg/65" },
]

function ClientsListPage() {
  const searchParams = useSearch({ from: "/clients/" })
  const navigate = useNavigate({ from: "/clients/" })
  const {
    searchInput,
    setSearchInput,
    activeSearch,
    addOpen: addModalOpen,
    setAddOpen: setAddModalOpen,
    page,
    setPage,
    limit,
    sort,
    toggleSort,
    setFilter,
    sortParams,
  } = useListPage({ searchParams, navigate })
  const activeTier = searchParams.tier
  const queryClient = useQueryClient()
  const toast = useToast()
  const [editing, setEditing] = useState<Client | null>(null)
  const [archiving, setArchiving] = useState<Client | null>(null)
  const [archiveLoading, setArchiveLoading] = useState(false)

  const handleArchive = useCallback(async () => {
    if (!archiving) return
    setArchiveLoading(true)
    try {
      await clientsApi.archive(archiving.id)
      await queryClient.invalidateQueries({ queryKey: ["clients"] })
      toast.showSuccess(`${archiving.name} archived`)
    } catch (err) {
      toast.showError(normalizeErrorMessage(err, "Could not archive this client"))
    } finally {
      setArchiveLoading(false)
    }
  }, [archiving, queryClient, toast])

  const handleTierChange = (next: TierFilter) =>
    setFilter("tier", next === "all" ? undefined : next)

  const query = useEntityList({
    resource: "clients",
    params: {
      page,
      limit,
      search: activeSearch,
      tier: activeTier,
      ...sortParams,
    },
    listFn: clientsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const selection = useTableSelection(items)
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters = Boolean(activeSearch) || Boolean(activeTier)

  return (
    <PageShell
      icon={Building2}
      trail={[{ label: "Organization & Clients" }]}
      title="Clients"
      actions={
        <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddModalOpen(true)}>
          <Plus className="size-3.5" />
          Add client
        </Button>
      }
    >
      <FilterBar>
        {activeTier ? (
          <FilterChip label={`Tier is ${activeTier}`} onRemove={() => handleTierChange("all")} />
        ) : null}
        <FilterTrigger
          label="All tiers"
          value={(activeTier ?? "all") as TierFilter}
          options={TIER_OPTIONS}
          onChange={handleTierChange}
        />
        <div className="ml-auto" />
        <FilterSearch value={searchInput} onChange={setSearchInput} placeholder="Search clients…" />
      </FilterBar>

      <ClientFormSheet open={addModalOpen} onOpenChange={setAddModalOpen} />

      <ClientFormSheet
        open={editing !== null}
        onOpenChange={(open) => {
          if (!open) setEditing(null)
        }}
        client={editing}
        onSaved={() => {
          void queryClient.invalidateQueries({ queryKey: ["clients"] })
          setEditing(null)
        }}
      />

      <ConfirmDialog
        open={archiving !== null}
        onOpenChange={(open) => {
          if (!open) setArchiving(null)
        }}
        title="Archive client"
        description={
          archiving
            ? `${archiving.name} will be hidden from the active list. You can restore it later.`
            : ""
        }
        confirmLabel="Archive"
        destructive
        loading={archiveLoading}
        onConfirm={handleArchive}
      />

      <EntityListView
        columns={COLUMNS}
        items={items}
        rowKey={(row) => row.id}
        renderRow={(row) => (
          <ClientRow
            row={row}
            isSelected={selection.selectedIds.has(row.id)}
            onToggle={() => selection.toggleSelect(row.id)}
            onEdit={() => setEditing(row)}
            onArchive={() => setArchiving(row)}
          />
        )}
        loading={loading}
        error={error}
        onRetry={() => void query.refetch()}
        empty={
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
        }
        sort={sort}
        onToggleSort={toggleSort}
        page={page}
        total={total}
        limit={limit}
        onPageChange={setPage}
        selectAllState={selection.selectAllState}
        onToggleSelectAll={selection.toggleSelectAll}
        toolbar={
          <SelectionBar count={selection.selectedIds.size} onClear={selection.clearSelection}>
            <BulkAction
              ids={selection.selectedIds}
              label="Archive"
              confirmTitle="Archive clients"
              confirmDescription={(n) =>
                `${n} ${n === 1 ? "client" : "clients"} will be hidden from the active list. You can restore them later.`
              }
              destructive
              labelFor={(id) => items.find((i) => i.id === id)?.name ?? id}
              action={clientsApi.archive}
              invalidateKey={["clients"]}
              verb="archived"
              noun="client"
              onDone={selection.clearSelection}
            />
          </SelectionBar>
        }
      />
    </PageShell>
  )
}

function ClientRow({
  row,
  isSelected,
  onToggle,
  onEdit,
  onArchive,
}: {
  row: Client
  isSelected: boolean
  onToggle: () => void
  onEdit: () => void
  onArchive: () => void
}) {
  const contactPrimary = row.contact_info?.email ?? row.contact_info?.phone ?? null
  const contactSecondary =
    row.contact_info?.email && row.contact_info?.phone ? row.contact_info?.phone : null

  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox
          aria-label={`Select ${row.name}`}
          checked={isSelected}
          onCheckedChange={onToggle}
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
            {nameInitials(row.name)}
          </span>
          <span className="text-sm font-medium text-fg group-hover:text-primary">{row.name}</span>
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
              <span className="block truncate text-xs text-fg-muted">{contactSecondary}</span>
            ) : null}
          </span>
        ) : (
          <span className="text-fg-subtle">-</span>
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
                <Link to="/clients/$clientId" params={{ clientId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={onEdit}>Edit</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onSelect={onArchive}
                className="text-destructive focus:text-destructive"
              >
                Archive
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}
