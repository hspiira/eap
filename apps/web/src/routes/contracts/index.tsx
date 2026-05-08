import { useEffect, useState } from "react"

import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { Search } from "lucide-react"

import { contractsApi } from "@/api/endpoints/contracts"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Input } from "@/components/ui/input"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { Contract } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

export const Route = createFileRoute("/contracts/")({
  component: ContractsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { search?: string } = {}
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    return out
  },
})

const columns = [
  {
    id: "contract_number",
    accessorKey: "contract_number" as keyof Contract,
    header: "Number",
    cell: (row: Contract) => (
      <Link to="/contracts/$contractId" params={{ contractId: row.id }} className="text-natural hover:underline">
        {row.contract_number ?? row.id.slice(0, 8)}
      </Link>
    ),
  },
  { id: "client_id", accessorKey: "client_id" as keyof Contract, header: "Client ID" },
  {
    id: "status",
    accessorKey: "status" as keyof Contract,
    header: "Status",
    cell: (row: Contract) => <StatusBadge status={row.status} />,
  },
  { id: "start_date", accessorKey: "start_date" as keyof Contract, header: "Start" },
  { id: "end_date", accessorKey: "end_date" as keyof Contract, header: "End" },
]

function ContractsListPage() {
  const searchParams = useSearch({ from: "/contracts/" })
  const navigate = useNavigate({ from: "/contracts/" })
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
    resource: "contracts",
    params: { page, limit, search: activeSearch },
    listFn: contractsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-xl font-semibold text-[#5A626A]">Contracts</h1>
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#5A626A]/70" />
          <Input
            placeholder="Search contracts..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="rounded-none h-9 pl-8 pr-3 border-[#5A626A]/30"
          />
        </div>
        <Link to="/contracts/new" className="inline-flex items-center justify-center h-9 px-4 bg-natural text-white font-medium rounded-none hover:bg-natural-dark">
          Add contract
        </Link>
      </div>
      <DataTable<Contract> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage={activeSearch ? "No contracts match your search." : "No contracts yet."} />
    </div>
  )
}
