import { useCallback, useEffect, useState } from "react"

import { createFileRoute } from "@tanstack/react-router"
import { BarChart3, Download, Plus, RotateCw } from "lucide-react"

import { industriesApi } from "@/api/endpoints/industries"
import { AuthedLayout } from "@/components/common/AuthedLayout"
import { EmptyState } from "@/components/common/EmptyState"
import { FilterBar, FilterSearch } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { IndustryDetailsCard } from "@/components/IndustryDetailsCard"
import { IndustryFormSheet } from "@/components/IndustryFormSheet"
import { Button } from "@/components/ui/button"
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
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import { cn } from "@/lib/utils"
import type { Industry } from "@/types/entities"

export const Route = createFileRoute("/industries")({
  component: IndustriesPage,
})

const ROW_BORDER = "border-fg/8"

function IndustriesPage() {
  const [page, setPage] = useState(1)
  const limit = 20
  const [searchInput, setSearchInput] = useState("")
  const [createOpen, setCreateOpen] = useState(false)
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })

  const toggleSort = (field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }
  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined

  const query = useEntityList({
    resource: "industries",
    params: {
      page,
      limit,
      search: activeSearch,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: industriesApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const [selected, setSelected] = useState<{ id: string; hint: Industry | null } | null>(null)
  const selectedId = selected?.id ?? null
  const [selectedIndustry, setSelectedIndustry] = useState<Industry | null>(null)
  const [parentIndustry, setParentIndustry] = useState<Industry | null>(null)
  const [childIndustries, setChildIndustries] = useState<Industry[]>([])
  const [detailsLoading, setDetailsLoading] = useState(false)

  const selectIndustry = useCallback((id: string | null, hint?: Industry | null) => {
    if (id == null) setSelected(null)
    else setSelected({ id, hint: hint ?? null })
  }, [])

  /**
   * Go to a row wherever it is: select it, and page the table to it.
   *
   * This used to put the target's code in the search box, which the server
   * matches against the name only, so following a child left the table empty
   * and the row it was pointing at unreachable. Paging there costs a scan, but
   * it lands on the row rather than on a search that cannot match.
   */
  const navigateToIndustry = useCallback(
    (id: string, hint?: Industry) => {
      selectIndustry(id, hint)
      if ((query.data?.items ?? []).some((i) => i.id === id)) return
      void pageOf(id, sort, limit).then((target) => {
        if (target == null) return
        // The row's position is its position in the unfiltered list.
        setSearchInput("")
        setPage(target)
      })
    },
    [query.data?.items, selectIndustry, sort],
  )

  const loadDetails = useCallback(async (id: string, rowHint?: Industry | null) => {
    setDetailsLoading(true)
    // Render immediately from the row payload while the network catches up.
    if (rowHint) setSelectedIndustry(rowHint)
    try {
      const [industry, children] = await Promise.all([
        industriesApi.getById(id),
        industriesApi.getChildren(id),
      ])
      const merged: Industry = {
        ...industry,
        parent_industry_id: industry.parent_industry_id ?? rowHint?.parent_industry_id ?? null,
      }
      setSelectedIndustry(merged)
      setChildIndustries(children)
      if (merged.parent_industry_id) {
        try {
          const parent = await industriesApi.getById(merged.parent_industry_id)
          setParentIndustry(parent)
        } catch (_err) {
          setParentIndustry(null)
        }
      } else {
        setParentIndustry(null)
      }
    } catch (_err) {
      if (!rowHint) setSelectedIndustry(null)
      setParentIndustry(null)
      setChildIndustries([])
    } finally {
      setDetailsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!selected) {
      setSelectedIndustry(null)
      setParentIndustry(null)
      setChildIndustries([])
      return
    }
    loadDetails(selected.id, selected.hint)
  }, [selected, loadDetails])

  // Scroll the selected row into view whenever it appears in the visible list
  // (e.g. after navigating from the detail tree to a different page).
  useEffect(() => {
    if (!selectedId) return
    const id = window.requestAnimationFrame(() => {
      const el = document.querySelector<HTMLElement>(`[data-row-id="${selectedId}"]`)
      el?.scrollIntoView({ block: "nearest", behavior: "smooth" })
    })
    return () => window.cancelAnimationFrame(id)
  }, [selectedId, items])

  const handleIndustryUpdated = useCallback((updated: Industry) => {
    setSelectedIndustry(updated)
  }, [])

  const hasFilters = Boolean(activeSearch)

  return (
    <AuthedLayout>
      <PageShell
        icon={BarChart3}
        breadcrumb="Organization & Clients · Industries"
        actions={
          <>
            <IconButton label="Export" icon={Download} />
            <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
            <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setCreateOpen(true)}>
              <Plus className="size-3.5" />
              Add industry
            </Button>
          </>
        }
      >
        <FilterBar>
          <div className="ml-auto" />
          <FilterSearch
            value={searchInput}
            onChange={setSearchInput}
            placeholder="Search industries…"
          />
        </FilterBar>

        <IndustryFormSheet open={createOpen} onOpenChange={setCreateOpen} />

        <div className="grid min-h-0 flex-1 grid-cols-12 gap-3 overflow-hidden bg-bg p-3">
          <div className="col-span-12 flex min-w-0 flex-col overflow-hidden lg:col-span-8">
            {loading ? (
              <TableSkeleton cols={3} headers={["Name", "Code", "Parent"]} withPagination />
            ) : error ? (
              <ErrorBlock message={error} onRetry={() => void query.refetch()} />
            ) : items.length === 0 ? (
              <EmptyState
                icon={BarChart3}
                title={hasFilters ? "No industries match your filters" : "No industries yet"}
                description={
                  hasFilters
                    ? "Try a different name or clear filters."
                    : "Add an industry classification to get started."
                }
              />
            ) : (
              <>
                <div className="relative min-h-0 flex-1 overflow-auto bg-surface">
                  <Table className="w-full caption-bottom text-sm" scrollable={false}>
                    <TableHeader className={STICKY_TABLE_HEAD}>
                      <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                        <TableHead>
                          <SortHeader field="name" sort={sort} onToggle={toggleSort}>
                            Name
                          </SortHeader>
                        </TableHead>
                        <TableHead>
                          <SortHeader field="code" sort={sort} onToggle={toggleSort}>
                            Code
                          </SortHeader>
                        </TableHead>
                        <TableHead className="text-fg/65">Parent</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {items.map((row) => (
                        <TableRow
                          key={row.id}
                          data-row-id={row.id}
                          onClick={() => selectIndustry(row.id, row)}
                          className={cn(
                            "cursor-pointer",
                            ROW_BORDER,
                            selectedId === row.id && "bg-primary/5 hover:bg-primary/5",
                          )}
                        >
                          <TableCell>
                            <span
                              className={cn(
                                "block max-w-[36ch] truncate font-medium",
                                selectedId === row.id ? "text-primary" : "text-fg",
                              )}
                            >
                              {row.name}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-fg/65">
                            {row.code ?? <span className="text-fg-subtle">-</span>}
                          </TableCell>
                          <TableCell className="text-sm text-fg/65">
                            {row.parent_industry_id ? (
                              <span className="text-xs font-mono">
                                {row.parent_industry_id.slice(0, 8)}
                              </span>
                            ) : (
                              <span className="text-fg-subtle">-</span>
                            )}
                          </TableCell>
                        </TableRow>
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

          <div className="col-span-12 flex min-w-0 flex-col lg:col-span-4">
            {selectedId && detailsLoading ? (
              <div className="border border-fg/10 bg-surface p-4 text-sm text-fg/70">Loading…</div>
            ) : selectedIndustry ? (
              <IndustryDetailsCard
                industry={selectedIndustry}
                parent={parentIndustry}
                children={childIndustries}
                onClose={() => selectIndustry(null)}
                onUpdated={handleIndustryUpdated}
                onSelectIndustry={navigateToIndustry}
              />
            ) : (
              <DetailsPlaceholder />
            )}
          </div>
        </div>
      </PageShell>
    </AuthedLayout>
  )
}

/**
 * Which page a row sits on, in the order the table is paging through.
 *
 * The list endpoint has no "where is this row" call, so this walks it in
 * hundreds under the same sort and divides the position by the page size.
 * A few hundred rows is one or two requests, and only on a click.
 */
async function pageOf(id: string, sort: SortState, limit: number): Promise<number | null> {
  const SCAN = 100
  for (let page = 1; ; page++) {
    const result = await industriesApi.list({
      page,
      limit: SCAN,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    })
    const index = result.items.findIndex((row) => row.id === id)
    if (index >= 0) return Math.floor(((page - 1) * SCAN + index) / limit) + 1
    if (!result.has_more || result.items.length === 0) return null
  }
}

function DetailsPlaceholder() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-1 text-center">
      <div className="mb-2 grid size-9 place-items-center bg-primary/10">
        <BarChart3 className="size-4 text-primary" />
      </div>
      <h3 className="text-sm font-semibold text-fg">Pick an industry</h3>
      <p className="max-w-[24ch] text-xs text-fg/60">
        Select a row to view its hierarchy and edit details.
      </p>
    </div>
  )
}

function ErrorBlock({ message, onRetry }: { message: string; onRetry: () => void }) {
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
