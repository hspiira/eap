import { useEffect, useState } from "react"

import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { Search } from "lucide-react"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Input } from "@/components/ui/input"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { ServiceSession } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

export const Route = createFileRoute("/service-sessions/")({
  component: ServiceSessionsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { search?: string } = {}
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    return out
  },
})

const columns = [
  {
    id: "id",
    accessorKey: "id" as keyof ServiceSession,
    header: "Session",
    cell: (row: ServiceSession) => (
      <Link to="/service-sessions/$sessionId" params={{ sessionId: row.id }} className="text-primary hover:underline">
        {row.scheduled_at ? new Date(row.scheduled_at).toLocaleString() : row.id.slice(0, 8)}…
      </Link>
    ),
  },
  { id: "scheduled_at", accessorKey: "scheduled_at" as keyof ServiceSession, header: "Scheduled", cell: (row: ServiceSession) => row.scheduled_at ? new Date(row.scheduled_at).toLocaleString() : "—" },
  { id: "status", accessorKey: "status" as keyof ServiceSession, header: "Status", cell: (row: ServiceSession) => <StatusBadge status={row.status} /> },
]

function ServiceSessionsListPage() {
  const searchParams = useSearch({ from: "/service-sessions/" })
  const navigate = useNavigate({ from: "/service-sessions/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [page, setPage] = useState(1)
  const limit = 20

  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined

  useEffect(() => {
    if (activeSearch !== searchParams.search) {
      navigate({ search: (prev) => ({ ...prev, search: activeSearch }), replace: true })
      setPage(1)
    }
  }, [activeSearch, navigate, searchParams.search])

  const query = useEntityList({
    resource: "service-sessions",
    params: { page, limit, search: activeSearch },
    listFn: serviceSessionsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-xl font-semibold text-fg">Sessions</h1>
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-fg/70" />
          <Input
            placeholder="Search sessions..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="rounded-none h-9 pl-8 pr-3 border-fg/30"
          />
        </div>
        <Link to="/service-sessions/new" className="inline-flex items-center justify-center h-9 px-4 bg-primary text-white font-medium rounded-none hover:bg-primary">Add session</Link>
      </div>
      <DataTable<ServiceSession> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage={activeSearch ? "No sessions match your search." : "No sessions yet."} />
    </div>
  )
}
