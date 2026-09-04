import { useCallback, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Bookmark,
  Building2,
  Download,
  ExternalLink,
  FileDown,
  FileUp,
  MoreHorizontal,
  Plus,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { ClientFormSheet } from "@/components/ClientFormSheet"
import { ClientImportDialog } from "@/components/ClientImportDialog"
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
import { useCanWrite, useCurrentRole } from "@/hooks/useCanWrite"
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import { boolParam, enumParam, listSearchSchema } from "@/lib/search-params"
import { type ClientSavedView, clientViewsStorage } from "@/lib/storage"
import type { Client } from "@/types/entities"
import { ClientTier, TenantRole } from "@/types/enums"

export const Route = createFileRoute("/clients/")({
  component: ClientsListPage,
  validateSearch: listSearchSchema({
    tier: enumParam(ClientTier),
    archived: boolParam(),
    parent_client_id: (v) => (typeof v === "string" && v.trim() ? v : undefined),
  }),
})

const TIER_OPTIONS = [
  { value: "all", label: "All tiers" },
  { value: ClientTier.A, label: "Tier A" },
  { value: ClientTier.B, label: "Tier B" },
  { value: ClientTier.C, label: "Tier C" },
] as const

type TierFilter = (typeof TIER_OPTIONS)[number]["value"]

const ARCHIVED_OPTIONS = [
  { value: "active", label: "Active only" },
  { value: "with-archived", label: "Include archived" },
] as const

type ArchivedFilter = (typeof ARCHIVED_OPTIONS)[number]["value"]

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
  const activeParentClientId = searchParams.parent_client_id
  const includeArchived = searchParams.archived === true
  const queryClient = useQueryClient()
  const toast = useToast()
  const canWrite = useCanWrite()
  const currentRole = useCurrentRole()
  const canArchive = currentRole === TenantRole.ADMIN
  const [editing, setEditing] = useState<Client | null>(null)
  const [archiving, setArchiving] = useState<Client | null>(null)
  const [archiveLoading, setArchiveLoading] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [savedViews, setSavedViews] = useState<ClientSavedView[]>(() => clientViewsStorage.read())

  const saveCurrentView = () => {
    const name = window.prompt("Name this client view")?.trim()
    if (!name) return
    const view: ClientSavedView = {
      id: `${Date.now()}`,
      name,
      search: activeSearch,
      tier: activeTier,
      archived: includeArchived,
      parent_client_id: activeParentClientId,
    }
    const next = [...savedViews.filter((item) => item.name !== name), view]
    setSavedViews(next)
    clientViewsStorage.write(next)
    toast.showSuccess("Client view saved")
  }

  const applyView = (view: ClientSavedView) => {
    setSearchInput(view.search ?? "")
    navigate({
      search: (prev) => ({
        ...prev,
        search: view.search,
        tier: view.tier as ClientTier | undefined,
        archived: view.archived || undefined,
        parent_client_id: view.parent_client_id,
      }),
      replace: true,
    })
    setPage(1)
  }

  const removeView = (id: string) => {
    const next = savedViews.filter((view) => view.id !== id)
    setSavedViews(next)
    clientViewsStorage.write(next)
  }

  const download = useCallback(
    async (blobPromise: Promise<Blob>, filename: string) => {
      try {
        const blob = await blobPromise
        const url = URL.createObjectURL(blob)
        const anchor = document.createElement("a")
        anchor.href = url
        anchor.download = filename
        anchor.click()
        URL.revokeObjectURL(url)
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Could not download file"))
      }
    },
    [toast],
  )

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

  const handleArchivedChange = (next: ArchivedFilter) =>
    setFilter("archived", next === "with-archived" ? "1" : undefined)

  const query = useEntityList({
    resource: "clients",
    params: {
      page,
      limit,
      search: activeSearch,
      tier: activeTier,
      parent_client_id: activeParentClientId,
      include_archived: includeArchived || undefined,
      ...sortParams,
    },
    listFn: clientsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const selection = useTableSelection(items)
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters =
    Boolean(activeSearch) || Boolean(activeTier) || Boolean(activeParentClientId) || includeArchived

  return (
    <PageShell
      icon={Building2}
      trail={[{ label: "Organization & Clients" }]}
      title="Clients"
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2"
            onClick={saveCurrentView}
          >
            <Bookmark className="size-3.5" />
            Save view
          </Button>
          {savedViews.length > 0 ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button type="button" variant="ghost" size="sm" className="h-7 px-2">
                  Views
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {savedViews.map((view) => (
                  <DropdownMenuItem key={view.id} onSelect={() => applyView(view)}>
                    {view.name}
                  </DropdownMenuItem>
                ))}
                <DropdownMenuSeparator />
                {savedViews.map((view) => (
                  <DropdownMenuItem key={`remove-${view.id}`} onSelect={() => removeView(view.id)}>
                    Remove &ldquo;{view.name}&rdquo;
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          ) : null}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2"
            onClick={() =>
              void download(clientsApi.getImportTemplate(), "clients-import-template.csv")
            }
          >
            <FileDown className="size-3.5" />
            Template
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2"
            onClick={() =>
              void download(
                clientsApi.exportCsv({
                  search: activeSearch,
                  tier: activeTier,
                  include_archived: includeArchived,
                  sort_by: sort.field,
                  sort_desc: sort.field ? sort.desc : undefined,
                }),
                "clients.csv",
              )
            }
          >
            <Download className="size-3.5" />
            Export
          </Button>
          {canWrite ? (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 gap-1.5 px-2"
                onClick={() => setImportOpen(true)}
              >
                <FileUp className="size-3.5" />
                Import
              </Button>
              <Button
                size="sm"
                className="h-7 gap-1.5 px-2.5"
                onClick={() => setAddModalOpen(true)}
              >
                <Plus className="size-3.5" />
                Add client
              </Button>
            </>
          ) : null}
        </>
      }
    >
      <FilterBar>
        {activeParentClientId ? (
          <FilterChip
            label={`Child clients of ${activeParentClientId.slice(0, 8)}`}
            onRemove={() => setFilter("parent_client_id", undefined)}
          />
        ) : null}
        {activeTier ? (
          <FilterChip label={`Tier is ${activeTier}`} onRemove={() => handleTierChange("all")} />
        ) : null}
        <FilterTrigger
          label="All tiers"
          value={(activeTier ?? "all") as TierFilter}
          options={TIER_OPTIONS}
          onChange={handleTierChange}
        />
        <FilterTrigger
          label="Active only"
          value={includeArchived ? "with-archived" : "active"}
          options={ARCHIVED_OPTIONS}
          onChange={handleArchivedChange}
        />
        <div className="ml-auto" />
        <FilterSearch value={searchInput} onChange={setSearchInput} placeholder="Search clients…" />
      </FilterBar>

      <ClientImportDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        onImported={() => void queryClient.invalidateQueries({ queryKey: ["clients"] })}
      />

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
            onEdit={canWrite ? () => setEditing(row) : undefined}
            onArchive={canArchive ? () => setArchiving(row) : undefined}
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
              hasFilters || !canWrite ? null : (
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
            {canArchive ? (
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
            ) : null}
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
  onEdit?: () => void
  onArchive?: () => void
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
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
          >
            {nameInitials(row.name)}
          </span>
          <span className="text-sm font-medium text-fg group-hover:text-primary">{row.name}</span>
        </Link>
      </TableCell>
      <TableCell className="text-xs text-fg/70">{row.code}</TableCell>
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
              {onEdit ? <DropdownMenuItem onSelect={onEdit}>Edit</DropdownMenuItem> : null}
              {onArchive ? (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onSelect={onArchive}
                    className="text-destructive focus:text-destructive"
                  >
                    Archive
                  </DropdownMenuItem>
                </>
              ) : null}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}
