import { useEffect, useState } from "react"

import { createFileRoute, Link } from "@tanstack/react-router"
import { Download, ExternalLink, MoreHorizontal, Plus, SquarePen, Tag } from "lucide-react"

import { clientTagsApi } from "@/api/endpoints/client-tags"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { FilterBar, FilterSearch } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { InfiniteScrollSentinel } from "@/components/common/InfiniteScrollSentinel"
import { PagedTableBody } from "@/components/common/PagedTableBody"
import { PageShell } from "@/components/common/PageShell"
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { TagFormSheet } from "@/components/TagFormSheet"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Pagination } from "@/components/ui/pagination"
import { Table, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useVisiblePage } from "@/hooks/useVisiblePage"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityListPages } from "@/lib/queries"
import type { ClientTag } from "@/types/entities"

export const Route = createFileRoute("/tags/")({
  component: TagsListPage,
})

const ROW_BORDER = "border-fg/8"

function TagsListPage() {
  const [page, setPage] = useState(1)
  const limit = 20
  const [searchInput, setSearchInput] = useState("")
  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined
  const [creatingTag, setCreatingTag] = useState(false)
  const [editingTag, setEditingTag] = useState<ClientTag | null>(null)
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })

  const toggleSort = (field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }

  useEffect(() => {
    setPage(1)
  }, [activeSearch])

  const [visiblePage, setVisiblePage] = useVisiblePage(page)

  const query = useEntityListPages({
    resource: "client-tags",
    params: {
      page,
      limit,
      search: activeSearch,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: clientTagsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const sheetOpen = creatingTag || Boolean(editingTag)
  const handleSheetOpenChange = (open: boolean) => {
    if (!open) {
      setCreatingTag(false)
      setEditingTag(null)
    }
  }

  return (
    <PageShell
      icon={Tag}
      breadcrumb="Organization & Clients · Tags"
      actions={
        <>
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setCreatingTag(true)}>
            <Plus className="size-3.5" />
            New tag
          </Button>
        </>
      }
    >
      <FilterBar>
        <div className="ml-auto" />
        <FilterSearch value={searchInput} onChange={setSearchInput} placeholder="Search tags…" />
      </FilterBar>

      <TagFormSheet open={sheetOpen} onOpenChange={handleSheetOpenChange} tag={editingTag} />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5 text-sm text-fg/65">Loading…</div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void query.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Tag}
            title={activeSearch ? "No tags match your search" : "No tags yet"}
            description={
              activeSearch ? "Try a different name." : "Create a tag to start organising clients."
            }
            action={
              activeSearch ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setCreatingTag(true)}>
                  <Plus className="size-4" />
                  New tag
                </Button>
              )
            }
          />
        ) : (
          <>
            <div
              className="relative min-h-0 flex-1 overflow-auto"
              data-scroll-restoration-id="list"
            >
              <Table className="w-full caption-bottom text-sm" scrollable={false}>
                <TableHeader className={STICKY_TABLE_HEAD}>
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead>
                      <SortHeader field="name" sort={sort} onToggle={toggleSort}>
                        Tag
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="color" sort={sort} onToggle={toggleSort}>
                        Color
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Description</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <PagedTableBody
                  items={items}
                  anchorPage={page}
                  limit={limit}
                  rowKey={(row) => row.id}
                  renderRow={(row) => <TagRow row={row} onEdit={() => setEditingTag(row)} />}
                  onVisiblePageChange={setVisiblePage}
                />
              </Table>
              <InfiniteScrollSentinel
                onLoadMore={query.loadMore}
                hasMore={query.hasMore}
                loadingMore={query.loadingMore}
              />
            </div>
            {total > 0 && (
              <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                <Pagination
                  page={visiblePage}
                  total={total}
                  limit={limit}
                  shownCount={items.length}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  )
}

function TagRow({ row, onEdit }: { row: ClientTag; onEdit: () => void }) {
  const swatch = row.color ?? null
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell>
        <Button
          type="button"
          variant="ghost"
          onClick={onEdit}
          className="h-auto gap-2 p-0 text-left hover:bg-transparent"
        >
          <span
            aria-hidden
            className="block size-2.5 shrink-0 border border-fg/20"
            style={swatch ? { backgroundColor: swatch } : undefined}
          />
          <span className="text-sm font-medium text-fg group-hover:text-primary">{row.name}</span>
        </Button>
      </TableCell>
      <TableCell>
        {swatch ? (
          <span className="inline-flex items-center gap-2">
            <span
              className="block size-3.5 border border-fg/20"
              style={{ backgroundColor: swatch }}
              aria-hidden
            />
            <span className="text-xs text-fg/65">{swatch}</span>
          </span>
        ) : (
          <span className="text-fg-subtle">-</span>
        )}
      </TableCell>
      <TableCell>
        <span className="block max-w-[60ch] truncate text-sm text-fg/75">
          {row.description ?? <span className="text-fg-subtle">-</span>}
        </span>
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onEdit}
            aria-label={`Edit ${row.name}`}
            className="size-7 p-0 text-fg/65"
          >
            <SquarePen className="size-3.5" />
          </Button>
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
              <DropdownMenuItem onSelect={onEdit} className="gap-2">
                <SquarePen className="size-3.5" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/tags/$tagId" params={{ tagId: row.id }} className="gap-2">
                  <ExternalLink className="size-3.5" />
                  Open page
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive focus:text-destructive">
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}
