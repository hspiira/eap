import { useEffect, useMemo, useState } from "react"

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
import { normalizeErrorMessage } from "@/utils/errorHandler"
export const Route = createFileRoute("/clients/")({
  component: ClientsListPage,
  validateSearch: (search: Record<string, unknown>) => ({
    new: search.new === "1" || search.new === true,
    search: typeof search.search === "string" && search.search.trim() ? search.search : undefined,
  }),
})

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

  useEffect(() => {
    if (searchParams.new) setAddModalOpen(true)
  }, [searchParams.new])

  useEffect(() => {
    if (activeSearch !== searchParams.search) {
      navigate({ search: (prev) => ({ ...prev, search: activeSearch }), replace: true })
      setPage(1)
    }
  }, [activeSearch, navigate, searchParams.search])

  const query = useEntityList({
    resource: "clients",
    params: { page, limit, search: activeSearch },
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
            <div className="flex flex-nowrap items-center gap-2 border-b border-[#5A626A]/20 bg-white px-3 py-2 shrink-0">
              <div className="relative flex-1 min-w-0 max-w-md">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#5A626A]/70" />
                <Input
                  placeholder="Search clients..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  className="rounded-none h-9 pl-8 pr-3 border-[#5A626A]/30 bg-white text-[#5A626A] placeholder:text-[#5A626A]/60"
                />
              </div>
              <Button
                variant="secondary"
                size="sm"
                className="rounded-none h-9 gap-1.5 border-[#5A626A]/30 text-[#5A626A] bg-white hover:bg-[#E6E0D7]/50"
              >
                <Filter className="h-4 w-4" />
                Filter
              </Button>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="rounded-none h-9 w-[180px] gap-1.5 border-[#5A626A]/30 bg-white text-[#5A626A] [&>svg]:text-[#5A626A]">
                  <Calendar className="h-4 w-4 shrink-0" />
                  <SelectValue placeholder="Last 12 hours" />
                </SelectTrigger>
                <SelectContent className="rounded-none border-[#5A626A]/30 bg-white">
                  {TIME_RANGE_OPTIONS.map((opt) => (
                    <SelectItem
                      key={opt.value}
                      value={opt.value}
                      className="rounded-none focus:bg-[#E6E0D7]/50 focus:text-[#5A626A]"
                    >
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="secondary"
                size="sm"
                className="rounded-none h-9 gap-1.5 border-[#5A626A]/30 text-[#5A626A] bg-white hover:bg-[#E6E0D7]/50"
              >
                <ListFilter className="h-4 w-4" />
                Queries
              </Button>
              <div className="flex-1 min-w-2" />
              <Button
                variant="secondary"
                size="sm"
                className="rounded-none h-9 gap-1.5 border-[#5A626A]/30 text-[#5A626A] bg-white hover:bg-[#E6E0D7]/50"
                onClick={() => refetch?.()}
              >
                <RotateCw className="h-4 w-4" />
                Refresh
              </Button>
              <Button
                variant="secondary"
                size="sm"
                className="rounded-none h-9 gap-1.5 border-[#5A626A]/30 text-[#5A626A] bg-[#E6E0D7]/50 hover:bg-[#E0DAD2]"
              >
                <Download className="h-4 w-4" />
                Download
              </Button>
              <Button
                size="sm"
                className="rounded-none h-9 gap-1.5 bg-natural text-white hover:bg-natural-dark"
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
                <div className="rounded-none border border-[#5A626A]/20 bg-white p-6 text-center">
                  <p className="text-[#5A626A]">{error}</p>
                </div>
              ) : displayItems.length === 0 ? (
                <div className="rounded-none border border-[#5A626A]/20 bg-white p-8 text-center">
                  <p className="text-[#5A626A]">
                    {items.length === 0 ? "No clients yet." : "No clients match your search."}
                  </p>
                  <Button
                    size="sm"
                    className="mt-3 rounded-none bg-natural text-white hover:bg-natural-dark"
                    onClick={() => setAddModalOpen(true)}
                  >
                    Add client
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="rounded-none border border-[#5A626A]/20 bg-white overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-[#5A626A]/15 hover:bg-transparent [&>th]:h-9 [&>th]:py-2 [&>th]:px-3 [&>th]:text-xs [&>th]:font-medium [&>th]:uppercase [&>th]:text-[#5A626A] [&>th]:bg-[#E6E0D7]/30">
                          <TableHead>Name</TableHead>
                          <TableHead>Code</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Contact</TableHead>
                          <TableHead>Operation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {displayItems.map((row) => (
                          <TableRow
                            key={row.id}
                            className="border-[#5A626A]/10 hover:bg-[#E6E0D7]/20 [&>td]:py-2 [&>td]:px-3 [&>td]:text-sm [&>td]:text-[#5A626A]"
                          >
                            <TableCell>
                              <Link
                                to="/clients/$clientId"
                                params={{ clientId: row.id }}
                                className="text-[#5A626A] hover:text-natural hover:underline"
                              >
                                {row.name}
                              </Link>
                            </TableCell>
                            <TableCell>{row.code}</TableCell>
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
                                className="inline-flex items-center justify-center text-[#5A626A] hover:text-natural"
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

                  {showPagination && total > 0 && (
                    <Pagination
                      page={paginationPage}
                      total={paginationTotal}
                      limit={paginationLimit}
                      onPageChange={setPage}
                    />
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
