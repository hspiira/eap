import { useCallback, useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { BarChart3, Download, Plus, RotateCw } from "lucide-react"

import { industriesApi } from "@/api/endpoints/industries"
import { AppLayout } from "@/components/AppLayout"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import {
  nextSort,
  SortHeader,
  type SortState,
} from "@/components/common/SortHeader"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { IndustryDetailsCard } from "@/components/IndustryDetailsCard"
import { IndustryFormSheet } from "@/components/IndustryFormSheet"
import { Button } from "@/components/ui/button"
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
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/slices/authSlice"
import type { Industry } from "@/types/entities"
import { normalizeErrorMessage } from "@/lib/errors"

export const Route = createFileRoute("/industries")({
  component: IndustriesPage,
})

const LEVEL_OPTIONS = [
  { value: "all", label: "All levels" },
  { value: "0", label: "Top level" },
  { value: "1", label: "Level 1" },
  { value: "2", label: "Level 2" },
  { value: "3", label: "Level 3+" },
] as const

type LevelFilter = (typeof LEVEL_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function IndustriesPage() {
  const { isAuthenticated, isLoading } = useAuthStore()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const limit = 20
  const [searchInput, setSearchInput] = useState("")
  const [levelFilter, setLevelFilter] = useState<LevelFilter>("all")
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
  const allItems = query.data?.items ?? []
  const items = filterByLevel(allItems, levelFilter)
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const refetch = useCallback(
    () => queryClient.invalidateQueries({ queryKey: ["industries", "list"] }),
    [queryClient],
  )

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
   * Navigates to a specific industry: makes its row visible in the table by
   * resetting filters/search to the target's name (so it lands on page 1)
   * unless it's already in the visible items, then highlights + scrolls.
   */
  const navigateToIndustry = useCallback(
    (id: string, hint?: Industry) => {
      const visibleItems = query.data?.items ?? []
      const inVisible = visibleItems.some((i) => i.id === id)
      if (!inVisible && hint) {
        setSearchInput(hint.code ?? hint.name)
        setLevelFilter("all")
        setPage(1)
      }
      selectIndustry(id, hint)
    },
    [query.data?.items, selectIndustry],
  )

  const loadDetails = useCallback(
    async (id: string, rowHint?: Industry | null) => {
      setDetailsLoading(true)
      // Render immediately from the row payload while the network catches up.
      if (rowHint) setSelectedIndustry(rowHint)
      try {
        const [industry, children] = await Promise.all([
          industriesApi.getById(id),
          industriesApi.getChildren(id),
        ])
        // Some endpoints drop parent_id from /industries/:id even when it
        // exists on the list payload; fall back to the row hint.
        const merged: Industry = {
          ...industry,
          parent_id: industry.parent_id ?? rowHint?.parent_id ?? null,
        }
        setSelectedIndustry(merged)
        setChildIndustries(children)
        if (merged.parent_id) {
          try {
            const parent = await industriesApi.getById(merged.parent_id)
            setParentIndustry(parent)
          } catch {
            setParentIndustry(null)
          }
        } else {
          setParentIndustry(null)
        }
      } catch {
        if (!rowHint) setSelectedIndustry(null)
        setParentIndustry(null)
        setChildIndustries([])
      } finally {
        setDetailsLoading(false)
      }
    },
    [],
  )

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

  const handleIndustryUpdated = useCallback(
    (updated: Industry) => {
      setSelectedIndustry(updated)
      refetch()
    },
    [refetch],
  )

  if (isLoading) return <div className="p-8 text-fg">Loading…</div>
  if (!isAuthenticated) return null

  const levelChip = LEVEL_OPTIONS.find((o) => o.value === levelFilter)
  const hasFilters = Boolean(activeSearch) || levelFilter !== "all"

  return (
    <AppLayout>
      <PageShell
        icon={BarChart3}
        breadcrumb="Organization & Clients · Industries"
        actions={
          <>
            <IconButton label="Refresh" onClick={refetch} icon={RotateCw} />
            <IconButton label="Export" icon={Download} />
            <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
            <Button
              size="sm"
              className="h-7 gap-1.5 px-2.5"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="size-3.5" />
              Add industry
            </Button>
          </>
        }
      >
        <FilterBar>
          <FilterButton
            options={[
              { id: "level", label: "Level" },
              { id: "parent", label: "Parent" },
              { id: "code", label: "Code" },
            ]}
          />
          {levelFilter !== "all" && levelChip ? (
            <FilterChip
              label={levelChip.label}
              onRemove={() => setLevelFilter("all")}
            />
          ) : null}
          <FilterTrigger
            label="All levels"
            value={levelFilter}
            options={LEVEL_OPTIONS}
            onChange={setLevelFilter}
          />
          <div className="ml-auto" />
          <FilterSearch
            value={searchInput}
            onChange={setSearchInput}
            placeholder="Search industries…"
          />
        </FilterBar>

        <IndustryFormSheet
          open={createOpen}
          onOpenChange={setCreateOpen}
          onSaved={() => refetch()}
        />

        <div className="grid min-h-0 flex-1 grid-cols-12 gap-3 overflow-hidden bg-bg p-3">
          <div className="col-span-12 flex min-w-0 flex-col overflow-hidden lg:col-span-8">
            {loading ? (
              <TableSkeleton cols={3} headers={["Name","Code","Level"]} withPagination />
            ) : error ? (
              <ErrorBlock message={error} onRetry={refetch} />
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
                  <table className="w-full caption-bottom text-sm">
                    <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
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
                        <TableHead>
                          <SortHeader field="level" sort={sort} onToggle={toggleSort}>
                            Level
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
                          <TableCell className="font-mono text-xs text-fg/65">
                            {row.code ?? <span className="text-fg/40">—</span>}
                          </TableCell>
                          <TableCell>
                            <LevelPill level={row.level ?? null} />
                          </TableCell>
                          <TableCell className="text-sm text-fg/65">
                            {row.parent_id ? (
                              <span className="font-mono text-xs">{row.parent_id.slice(0, 8)}</span>
                            ) : (
                              <span className="text-fg/40">—</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </table>
                </div>
                {total > 0 && (
                  <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                    <Pagination
                      page={page}
                      total={total}
                      limit={limit}
                      onPageChange={setPage}
                    />
                  </div>
                )}
              </>
            )}
          </div>

          <div className="col-span-12 flex min-w-0 flex-col lg:col-span-4">
            {selectedId && detailsLoading ? (
              <div className="border border-fg/10 bg-surface p-4 text-sm text-fg/70">
                Loading…
              </div>
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
    </AppLayout>
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

function filterByLevel(items: ReadonlyArray<Industry>, level: LevelFilter): Industry[] {
  if (level === "all") return [...items]
  if (level === "3") return items.filter((i) => (i.level ?? 0) >= 3)
  const target = Number.parseInt(level, 10)
  return items.filter((i) => (i.level ?? 0) === target)
}

function LevelPill({ level }: { level: number | null }) {
  if (level == null) return <span className="text-fg/40">—</span>
  return (
    <span className="inline-flex items-center border border-fg/15 bg-surface-hover px-1.5 py-0.5 font-mono text-[11px] text-fg/75">
      L{level}
    </span>
  )
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
        <Button
          variant="outline"
          size="sm"
          className="mt-4 gap-1.5"
          onClick={onRetry}
        >
          <RotateCw className="size-4" />
          Try again
        </Button>
      </div>
    </div>
  )
}
