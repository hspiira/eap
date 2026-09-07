import { useCallback, useEffect, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
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
  ScanSearch,
} from "lucide-react"

import { clientTagsApi } from "@/api/endpoints/client-tags"
import {
  type ClientDuplicateCandidate,
  clientsApi,
  type ClientSavedView,
} from "@/api/endpoints/clients"
import { ClientFormSheet } from "@/components/clients/ClientFormSheet"
import { ClientImportDialog } from "@/components/clients/ClientImportDialog"
import { BulkAction } from "@/components/common/BulkAction"
import { ConfirmDialog } from "@/components/common/ConfirmDialog"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView, type ListColumn } from "@/components/common/EntityListView"
import { EntityNameCell } from "@/components/common/EntityNameCell"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { SelectionBar } from "@/components/common/SelectionBar"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ROW_BORDER } from "@/components/common/tableStyles"
import { TierBadge } from "@/components/common/TierBadge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { TableCell, TableRow } from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite, useCurrentRole } from "@/hooks/useCanWrite"
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDateTime, formatDay } from "@/lib/format"
import { useEntityList } from "@/lib/queries"
import { boolParam, enumParam, listSearchSchema } from "@/lib/search-params"
import { useAuthStore } from "@/store/slices/authSlice"
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
  {
    header: <span className="sr-only">Status</span>,
    sortField: "status",
    className: "text-center",
  },
  { header: "Email", className: "text-fg/65" },
  { header: "Phone", className: "text-fg/65" },
  { header: "Employees", className: "text-fg/65 text-center" },
  { header: "Last activity", className: "text-fg/65" },
  { header: "Renewal", className: "text-fg/65" },
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
  const currentUserId = useAuthStore((state) => state.user_id)
  const canArchive = currentRole === TenantRole.ADMIN
  const [editing, setEditing] = useState<Client | null>(null)
  const [archiving, setArchiving] = useState<Client | null>(null)
  const [archiveLoading, setArchiveLoading] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [savedViews, setSavedViews] = useState<ClientSavedView[]>([])
  const [bulkTagId, setBulkTagId] = useState("")
  const [duplicatesOpen, setDuplicatesOpen] = useState(false)
  const [mergeSelection, setMergeSelection] = useState<{
    targetId: string
    targetName: string
    sourceId: string
    sourceName: string
  } | null>(null)
  const [mergeLoading, setMergeLoading] = useState(false)

  const savedViewsQuery = useQuery({
    queryKey: ["client-views"],
    queryFn: clientsApi.listViews,
  })
  const duplicatesQuery = useQuery({
    queryKey: ["client-duplicates"],
    queryFn: clientsApi.scanDuplicates,
    enabled: false,
  })

  useEffect(() => {
    setSavedViews(savedViewsQuery.data?.items ?? [])
  }, [savedViewsQuery.data])

  const saveCurrentView = () => {
    const name = window.prompt("Name this client view")?.trim()
    if (!name) return
    void clientsApi
      .saveView({
        name,
        filters: {
          search: activeSearch ?? null,
          tier: activeTier ?? null,
          archived: includeArchived,
          parent_client_id: activeParentClientId ?? null,
        },
        is_shared: window.confirm("Share this view with other users in your tenant?"),
      })
      .then(() => {
        toast.showSuccess("Client view saved")
        return savedViewsQuery.refetch()
      })
      .catch((err) => toast.showError(normalizeErrorMessage(err, "Could not save this view")))
  }

  const applyView = (view: ClientSavedView) => {
    setSearchInput(view.filters.search ?? "")
    navigate({
      search: (prev) => ({
        ...prev,
        search: view.filters.search ?? undefined,
        tier: view.filters.tier ?? undefined,
        archived: view.filters.archived || undefined,
        parent_client_id: view.filters.parent_client_id ?? undefined,
      }),
      replace: true,
    })
    setPage(1)
  }

  const removeView = (id: string) => {
    void clientsApi
      .deleteView(id)
      .then(() => savedViewsQuery.refetch())
      .catch((err) => toast.showError(normalizeErrorMessage(err, "Could not remove this view")))
  }

  const scanDuplicates = () => {
    setDuplicatesOpen(true)
    void duplicatesQuery.refetch()
  }

  const mergeDuplicate = async () => {
    if (!mergeSelection) return
    setMergeLoading(true)
    try {
      await clientsApi.mergeDuplicate(mergeSelection.targetId, mergeSelection.sourceId)
      toast.showSuccess(`${mergeSelection.sourceName} merged into ${mergeSelection.targetName}`)
      setMergeSelection(null)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["clients"] }),
        duplicatesQuery.refetch(),
      ])
    } catch (err) {
      toast.showError(normalizeErrorMessage(err, "Could not merge these clients"))
    } finally {
      setMergeLoading(false)
    }
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
  const tagsQuery = useQuery({
    queryKey: ["client-tags", "active"],
    queryFn: () => clientTagsApi.list({ limit: 100 }),
    enabled: canWrite,
  })
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
          {canWrite ? (
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
          ) : null}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2"
            onClick={scanDuplicates}
          >
            <ScanSearch className="size-3.5" />
            Find duplicates
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
                {savedViews.some((view) => view.created_by === currentUserId) ? (
                  <>
                    <DropdownMenuSeparator />
                    {savedViews
                      .filter((view) => view.created_by === currentUserId)
                      .map((view) => (
                        <DropdownMenuItem
                          key={`remove-${view.id}`}
                          onSelect={() => removeView(view.id)}
                        >
                          Remove &ldquo;{view.name}&rdquo;
                        </DropdownMenuItem>
                      ))}
                  </>
                ) : null}
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

      <DuplicateScanDialog
        open={duplicatesOpen}
        onOpenChange={setDuplicatesOpen}
        loading={duplicatesQuery.isFetching}
        scanned={duplicatesQuery.data?.scanned ?? 0}
        items={duplicatesQuery.data?.items ?? []}
        onMerge={
          canWrite
            ? (target, source) =>
                setMergeSelection({
                  targetId: target.id,
                  targetName: target.name,
                  sourceId: source.id,
                  sourceName: source.name,
                })
            : undefined
        }
      />

      <ConfirmDialog
        open={mergeSelection !== null}
        onOpenChange={(open) => {
          if (!open) setMergeSelection(null)
        }}
        title="Merge duplicate clients"
        description={
          mergeSelection
            ? `${mergeSelection.sourceName} will be archived and its contacts, contracts, activities, documents, tags, and aliases will move to ${mergeSelection.targetName}.`
            : ""
        }
        confirmLabel="Merge clients"
        destructive
        loading={mergeLoading}
        onConfirm={mergeDuplicate}
      />

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
            {selection.selectedIds.size > 0 ? (
              <>
                <Select value={bulkTagId} onValueChange={setBulkTagId}>
                  <SelectTrigger aria-label="Tag selected clients" className="h-7 w-36 text-xs">
                    <SelectValue placeholder="Choose tag…" />
                  </SelectTrigger>
                  <SelectContent>
                    {(tagsQuery.data?.items ?? []).map((tag) => (
                      <SelectItem key={tag.id} value={tag.id}>
                        {tag.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 px-2.5"
                  disabled={!bulkTagId}
                  onClick={() => {
                    void clientsApi
                      .bulkUpdateTags([...selection.selectedIds], [bulkTagId], "add")
                      .then(() => {
                        toast.showSuccess("Tag applied to selected clients")
                        setBulkTagId("")
                        void queryClient.invalidateQueries({ queryKey: ["client-tags"] })
                      })
                      .catch((err) =>
                        toast.showError(normalizeErrorMessage(err, "Could not apply tag")),
                      )
                  }}
                >
                  Apply tag
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 px-2.5"
                  onClick={() =>
                    void download(
                      clientsApi.exportSelected([...selection.selectedIds]),
                      "selected-clients.csv",
                    )
                  }
                >
                  <Download className="mr-1.5 size-3.5" />
                  Export selected
                </Button>
              </>
            ) : null}
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

function DuplicateScanDialog({
  open,
  onOpenChange,
  loading,
  scanned,
  items,
  onMerge,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  loading: boolean
  scanned: number
  items: ClientDuplicateCandidate[]
  onMerge?: (
    target: ClientDuplicateCandidate["first"],
    source: ClientDuplicateCandidate["second"],
  ) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Possible duplicate clients</DialogTitle>
          <DialogDescription>
            {loading
              ? "Scanning the client list…"
              : `${items.length} possible matches in ${scanned} clients.`}
          </DialogDescription>
        </DialogHeader>
        {!loading && items.length === 0 ? (
          <p className="text-sm text-fg-muted">No likely duplicates found.</p>
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <div key={`${item.first.id}-${item.second.id}`} className="rounded-md border p-3">
                <div className="grid gap-2 sm:grid-cols-[1fr_auto_1fr] sm:items-center">
                  <DuplicateClientCard client={item.first} />
                  <span className="text-center text-xs text-fg-muted">{item.reason}</span>
                  <DuplicateClientCard client={item.second} />
                </div>
                {onMerge ? (
                  <div className="mt-3 flex flex-wrap justify-end gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => onMerge(item.first, item.second)}
                    >
                      Keep {item.first.name}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => onMerge(item.second, item.first)}
                    >
                      Keep {item.second.name}
                    </Button>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

function DuplicateClientCard({ client }: { client: ClientDuplicateCandidate["first"] }) {
  return (
    <div className="min-w-0">
      <p className="truncate text-sm font-medium text-fg">{client.name}</p>
      <p className="text-xs text-fg-muted">
        {client.code}
        {client.contact_email ? ` · ${client.contact_email}` : ""}
      </p>
    </div>
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
  return (
    <TableRow className={`group h-9 cursor-default ${ROW_BORDER}`}>
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
          <EntityNameCell initials={nameInitials(row.name)} name={row.name} />
        </Link>
      </TableCell>
      <TableCell className="text-xs text-fg/70">{row.code}</TableCell>
      <TableCell>
        <TierBadge tier={row.tier} />
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={row.status} iconOnly />
      </TableCell>
      <TableCell className="max-w-[14rem] truncate text-xs text-fg/70">
        {row.contact_info?.email ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/70">
        {row.contact_info?.phone ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
      <TableCell className="text-center text-xs text-fg/70">
        {row.staff_count == null ? "-" : row.staff_count}
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/70">
        {formatDateTime(row.last_activity_at)}
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/70">
        {formatDay(row.next_renewal_date)}
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
