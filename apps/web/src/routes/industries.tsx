import { useCallback, useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { BarChart3, Download, Plus, RotateCw } from "lucide-react"

import { industriesApi } from "@/api/endpoints/industries"
import { AppLayout } from "@/components/AppLayout"
import { ListToolbar } from "@/components/common/ListToolbar"
import { PageShell } from "@/components/common/PageShell"
import { IndustriesListSkeleton } from "@/components/IndustriesPageSkeletons"
import { IndustryDetailsCard } from "@/components/IndustryDetailsCard"
import { Button } from "@/components/ui/button"
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
]

function IndustriesPage() {
  const { isAuthenticated, isLoading } = useAuthStore()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const limit = 20
  const [searchInput, setSearchInput] = useState("")
  const [levelFilter, setLevelFilter] = useState<string>("all")
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

  const description =
    total > 0
      ? `${total.toLocaleString()} ${total === 1 ? "industry" : "industries"} indexed`
      : "Standard industry taxonomy used to classify clients"

  return (
    <AppLayout>
      <PageShell
        icon={BarChart3}
        breadcrumb="Organization & Clients · Industries"
        title="Industries"
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
            >
              <Plus className="size-4" />
              Add industry
            </Button>
          </>
        }
        toolbar={
          <ListToolbar
            searchValue={searchInput}
            onSearchChange={setSearchInput}
            placeholder="Search industries…"
            filters={
              <Select value={levelFilter} onValueChange={setLevelFilter}>
                <SelectTrigger
                  className="h-9 w-36 rounded-none border-fg/25 bg-surface text-fg [&>svg]:text-fg/60"
                  aria-label="Filter by level"
                >
                  <SelectValue placeholder="All levels" />
                </SelectTrigger>
                <SelectContent className="rounded-none border-fg/25 bg-surface">
                  {LEVEL_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="rounded-none">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            }
          />
        }
      >
        <div className="grid min-h-0 flex-1 grid-cols-12 gap-3 overflow-hidden bg-bg p-3">
          <div className="col-span-12 flex min-w-0 flex-col overflow-hidden lg:col-span-8">
            {loading ? (
              <IndustriesListSkeleton />
            ) : error ? (
              <ErrorBlock message={error} onRetry={refetch} />
            ) : items.length === 0 ? (
              <EmptyBlock hasSearch={Boolean(activeSearch) || levelFilter !== "all"} />
            ) : (
              <>
                <div className="min-h-0 flex-1 overflow-auto border border-fg/15 bg-surface">
                  <Table>
                    <TableHeader className="sticky top-0 z-10 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                      <TableRow className="hover:bg-transparent">
                        <TableHead className="text-fg/70">Name</TableHead>
                        <TableHead className="text-fg/70">Code</TableHead>
                        <TableHead className="text-fg/70">Level</TableHead>
                        <TableHead className="text-fg/70">Parent</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {items.map((row) => (
                        <TableRow
                          key={row.id}
                          onClick={() => setSelectedId(row.id)}
                          className={cn(
                            "cursor-pointer",
                            selectedId === row.id &&
                              "bg-primary/5 hover:bg-primary/5 [&>td]:border-l-0",
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
                            {row.code ?? "—"}
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
                  </Table>
                </div>
                {total > 0 && (
                  <div className="shrink-0 border border-t-0 border-fg/15 bg-surface px-3 py-2">
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
              <div className="border border-fg/15 bg-surface p-4 text-sm text-fg/70">
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

function filterByLevel(items: ReadonlyArray<Industry>, level: string): Industry[] {
  if (level === "all") return [...items]
  if (level === "3") return items.filter((i) => (i.level ?? 0) >= 3)
  const target = Number.parseInt(level, 10)
  return items.filter((i) => (i.level ?? 0) === target)
}

function LevelPill({ level }: { level: number | null }) {
  if (level == null) {
    return <span className="text-fg/40">—</span>
  }
  return (
    <span className="inline-flex items-center border border-fg/20 bg-surface-hover px-1.5 py-0.5 font-mono text-[11px] text-fg/75">
      L{level}
    </span>
  )
}

function DetailsPlaceholder() {
  return (
    <div className="flex flex-1 flex-col justify-center border border-dashed border-fg/20 bg-surface p-5">
      <div className="mx-auto mb-2 grid size-9 place-items-center bg-primary/10">
        <BarChart3 className="size-4 text-primary" />
      </div>
      <h3 className="text-center text-sm font-semibold text-fg">Pick an industry</h3>
      <p className="mt-1 text-center text-xs text-fg/65">
        Select a row to view its hierarchy and edit details.
      </p>
    </div>
  )
}

function ErrorBlock({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center">
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

function EmptyBlock({ hasSearch }: { hasSearch: boolean }) {
  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="max-w-md border border-fg/15 bg-surface p-8 text-center">
        <div className="mx-auto mb-3 grid size-10 place-items-center bg-primary/10">
          <BarChart3 className="size-5 text-primary" />
        </div>
        <h2 className="text-base font-semibold text-fg">
          {hasSearch ? "No industries match your filters" : "No industries yet"}
        </h2>
        <p className="mt-1 text-sm text-fg/65">
          {hasSearch
            ? "Try a different name or clear filters."
            : "Add an industry classification to get started."}
        </p>
      </div>
    </div>
  )
}
