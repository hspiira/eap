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
import { IndustriesListSkeleton } from "@/components/IndustriesPageSkeletons"
import { IndustryDetailsCard } from "@/components/IndustryDetailsCard"
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
import { normalizeErrorMessage } from "@/utils/errorHandler"

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
  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined

  const query = useEntityList({
    resource: "industries",
    params: { page, limit, search: activeSearch },
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

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedIndustry, setSelectedIndustry] = useState<Industry | null>(null)
  const [parentIndustry, setParentIndustry] = useState<Industry | null>(null)
  const [childIndustries, setChildIndustries] = useState<Industry[]>([])
  const [detailsLoading, setDetailsLoading] = useState(false)

  const loadDetails = useCallback(async (id: string) => {
    setDetailsLoading(true)
    try {
      const [industry, children] = await Promise.all([
        industriesApi.getById(id),
        industriesApi.getChildren(id),
      ])
      setSelectedIndustry(industry)
      setChildIndustries(children)
      if (industry.parent_id) {
        try {
          const parent = await industriesApi.getById(industry.parent_id)
          setParentIndustry(parent)
        } catch {
          setParentIndustry(null)
        }
      } else {
        setParentIndustry(null)
      }
    } catch {
      setSelectedIndustry(null)
      setParentIndustry(null)
      setChildIndustries([])
    } finally {
      setDetailsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedId) {
      loadDetails(selectedId)
    } else {
      setSelectedIndustry(null)
      setParentIndustry(null)
      setChildIndustries([])
    }
  }, [selectedId, loadDetails])

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

        <div className="grid min-h-0 flex-1 grid-cols-12 gap-3 overflow-hidden bg-bg p-3">
          <div className="col-span-12 flex min-w-0 flex-col overflow-hidden lg:col-span-8">
            {loading ? (
              <IndustriesListSkeleton />
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
                        <TableHead className="text-fg/65">Name</TableHead>
                        <TableHead className="text-fg/65">Code</TableHead>
                        <TableHead className="text-fg/65">Level</TableHead>
                        <TableHead className="text-fg/65">Parent</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {items.map((row) => (
                        <TableRow
                          key={row.id}
                          onClick={() => setSelectedId(row.id)}
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
                onClose={() => setSelectedId(null)}
                onUpdated={handleIndustryUpdated}
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
