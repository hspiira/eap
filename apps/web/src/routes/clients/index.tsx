import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Calendar,
  Download,
  ExternalLink,
  Filter,
  ListFilter,
  Plus,
  RotateCw,
  Search,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { ClientForm } from "@/components/ClientForm"
import { ClientsPageHeader } from "@/components/ClientsPageHeader"
import { ClientsListSkeleton } from "@/components/ClientsPageSkeletons"
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
import { Input } from "@/components/ui/input"
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

  return (
    <ClientsPageHeader breadcrumb="Clients">
      <div className="content-area-scroll flex-1 min-h-0 flex flex-col overflow-hidden">
        {loading ? (
          <div className="p-4 overflow-auto">
            <ClientsListSkeleton />
          </div>
        ) : (
          <>
            <div className="flex flex-nowrap items-center gap-2 border-b border-fg/20 bg-white px-3 py-2 shrink-0">
              <div className="relative flex-1 min-w-0 max-w-md">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-fg/70" />
                <Input
                  placeholder="Search clients..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  className="rounded-none h-9 pl-8 pr-3 border-fg/30 bg-white text-fg placeholder:text-fg/60"
                />
              </div>
              <Button
                variant="secondary"
                size="sm"
                className="rounded-none h-9 gap-1.5 border-fg/30 text-fg bg-white hover:bg-surface/50"
              >
                <Filter className="h-4 w-4" />
                Filter
              </Button>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="rounded-none h-9 w-45 gap-1.5 border-fg/30 bg-white text-fg [&>svg]:text-fg">
                  <Calendar className="h-4 w-4 shrink-0" />
                  <SelectValue placeholder="Last 12 hours" />
                </SelectTrigger>
                <SelectContent className="rounded-none border-fg/30 bg-white">
                  {TIME_RANGE_OPTIONS.map((opt) => (
                    <SelectItem
                      key={opt.value}
                      value={opt.value}
                      className="rounded-none focus:bg-surface/50 focus:text-fg"
                    >
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={activeTier ?? "all"} onValueChange={handleTierChange}>
                <SelectTrigger
                  className="rounded-none h-9 w-35 gap-1.5 border-fg/30 bg-white text-fg [&>svg]:text-fg"
                  aria-label="Filter by tier"
                >
                  <SelectValue placeholder="All tiers" />
                </SelectTrigger>
                <SelectContent className="rounded-none border-fg/30 bg-white">
                  {TIER_FILTER_OPTIONS.map((opt) => (
                    <SelectItem
                      key={opt.value}
                      value={opt.value}
                      className="rounded-none focus:bg-surface/50 focus:text-fg"
                    >
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="secondary"
                size="sm"
                className="rounded-none h-9 gap-1.5 border-fg/30 text-fg bg-white hover:bg-surface/50"
              >
                <ListFilter className="h-4 w-4" />
                Queries
              </Button>
              <div className="flex-1 min-w-2" />
              <Button
                variant="secondary"
                size="sm"
                className="rounded-none h-9 gap-1.5 border-fg/30 text-fg bg-white hover:bg-surface/50"
                onClick={() => refetch?.()}
              >
                <RotateCw className="h-4 w-4" />
                Refresh
              </Button>
              <Button
                variant="secondary"
                size="sm"
                className="rounded-none h-9 gap-1.5 border-fg/30 text-fg bg-surface/50 hover:bg-surface-hover"
              >
                <Download className="h-4 w-4" />
                Download
              </Button>
              <Button
                size="sm"
                className="rounded-none h-9 gap-1.5 bg-primary text-white hover:bg-primary"
                onClick={() => setAddModalOpen(true)}
              >
                <Plus className="h-4 w-4" />
                Add client
              </Button>
            </div>

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

            <div className="flex-1 min-h-0 overflow-auto p-4">
              {error ? (
                <div className="rounded-none border border-fg/20 bg-white p-6 text-center">
                  <p className="text-fg">{error}</p>
                </div>
              ) : items.length === 0 ? (
                <div className="rounded-none border border-fg/20 bg-white p-8 text-center">
                  <p className="text-fg">
                    {activeSearch ? "No clients match your search." : "No clients yet."}
                  </p>
                  <Button
                    size="sm"
                    className="mt-3 rounded-none bg-primary text-white hover:bg-primary"
                    onClick={() => setAddModalOpen(true)}
                  >
                    Add client
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="rounded-none border border-fg/20 bg-white overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-fg/15 hover:bg-transparent [&>th]:h-9 [&>th]:py-2 [&>th]:px-3 [&>th]:text-xs [&>th]:font-medium [&>th]:uppercase [&>th]:text-fg [&>th]:bg-surface/30">
                          <TableHead>Name</TableHead>
                          <TableHead>Code</TableHead>
                          <TableHead>Tier</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Contact</TableHead>
                          <TableHead>Operation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {items.map((row) => (
                          <TableRow
                            key={row.id}
                            className="border-fg/10 hover:bg-surface/20 [&>td]:py-2 [&>td]:px-3 [&>td]:text-sm [&>td]:text-fg"
                          >
                            <TableCell>
                              <Link
                                to="/clients/$clientId"
                                params={{ clientId: row.id }}
                                className="text-fg hover:text-primary hover:underline"
                              >
                                {row.name}
                              </Link>
                            </TableCell>
                            <TableCell>{row.code}</TableCell>
                            <TableCell>
                              <TierBadge tier={row.tier} />
                            </TableCell>
                            <TableCell>
                              <StatusBadge status={row.status} />
                            </TableCell>
                            <TableCell>
                              {row.contact_info?.email ?? row.contact_info?.phone ?? "—"}
                            </TableCell>
                            <TableCell>
                              <Link
                                to="/clients/$clientId"
                                params={{ clientId: row.id }}
                                className="inline-flex items-center justify-center text-fg hover:text-primary"
                                aria-label="View client"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </Link>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  {total > 0 && (
                    <Pagination page={page} total={total} limit={limit} onPageChange={setPage} />
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </ClientsPageHeader>
  )
}
