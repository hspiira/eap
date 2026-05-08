import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  Download,
  ExternalLink,
  MoreHorizontal,
  Pencil,
  Plus,
  RotateCw,
  Tag,
} from "lucide-react"

import { clientTagsApi } from "@/api/endpoints/client-tags"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterSearch,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
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
import type { ClientTag } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

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
  const queryClient = useQueryClient()

  useEffect(() => {
    setPage(1)
  }, [activeSearch])

  const query = useEntityList({
    resource: "client-tags",
    params: { page, limit, search: activeSearch },
    listFn: clientTagsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const refetch = () => queryClient.invalidateQueries({ queryKey: ["client-tags", "list"] })

  return (
    <PageShell
      icon={Tag}
      breadcrumb="Organization & Clients · Tags"
      actions={
        <>
          <IconButton label="Refresh" onClick={refetch} icon={RotateCw} />
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            asChild
            size="sm"
            className="h-7 gap-1.5 rounded-none bg-primary px-2.5 text-primary-foreground hover:bg-primary/90"
          >
            <Link to="/tags/new">
              <Plus className="size-3.5" />
              New tag
            </Link>
          </Button>
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "color", label: "Color" },
            { id: "name", label: "Name" },
          ]}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search tags…"
        />
      </FilterBar>

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5 text-sm text-fg/65">Loading…</div>
        ) : error ? (
          <ErrorState message={error} onRetry={refetch} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Tag}
            title={activeSearch ? "No tags match your search" : "No tags yet"}
            description={
              activeSearch
                ? "Try a different name."
                : "Create a tag to start organising clients."
            }
            action={
              activeSearch ? null : (
                <Button
                  asChild
                  size="sm"
                  className="rounded-none gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  <Link to="/tags/new">
                    <Plus className="size-4" />
                    New tag
                  </Link>
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
                    <TableHead className="text-fg/65">Tag</TableHead>
                    <TableHead className="text-fg/65">Color</TableHead>
                    <TableHead className="text-fg/65">Description</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <TagRow key={row.id} row={row} />
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
      className="grid size-7 place-items-center rounded-none text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
    >
      <Icon className="size-3.5" />
    </button>
  )
}

function TagRow({ row }: { row: ClientTag }) {
  const swatch = row.color ?? null
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
          to="/tags/$tagId"
          params={{ tagId: row.id }}
          className="inline-flex items-center gap-2"
        >
          <span
            aria-hidden
            className="block size-2.5 shrink-0 border border-fg/20"
            style={swatch ? { backgroundColor: swatch } : undefined}
          />
          <span className="text-sm font-medium text-fg group-hover:text-primary">
            {row.name}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        {swatch ? (
          <span className="inline-flex items-center gap-2">
            <span
              className="block size-3.5 border border-fg/20"
              style={{ backgroundColor: swatch }}
              aria-hidden
            />
            <span className="font-mono text-xs uppercase text-fg/65">{swatch}</span>
          </span>
        ) : (
          <span className="text-fg/40">—</span>
        )}
      </TableCell>
      <TableCell>
        <span className="block max-w-[60ch] truncate text-sm text-fg/75">
          {row.description ?? <span className="text-fg/40">—</span>}
        </span>
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/tags/$tagId"
            params={{ tagId: row.id }}
            aria-label={`Edit ${row.name}`}
            className="grid size-7 place-items-center rounded-none text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <Pencil className="size-3.5" />
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
                <Link to="/tags/$tagId" params={{ tagId: row.id }} className="gap-2">
                  <ExternalLink className="size-3.5" />
                  Open
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

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center px-6 py-10">
      <div className="flex max-w-sm flex-col items-center text-center">
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
