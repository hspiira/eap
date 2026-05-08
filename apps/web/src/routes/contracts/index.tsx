import { useState } from "react"

import { createFileRoute, Link } from "@tanstack/react-router"

import { contractsApi } from "@/api/endpoints/contracts"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { useEntityList } from "@/lib/queries"
import type { Contract } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

export const Route = createFileRoute("/contracts/")({
  component: ContractsListPage,
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
  const [page, setPage] = useState(1)
  const limit = 20
  const query = useEntityList({
    resource: "contracts",
    params: { page, limit },
    listFn: contractsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Contracts</h1>
        <Link to="/contracts/new" className="inline-flex items-center justify-center h-9 px-4 bg-natural text-white font-medium rounded-none hover:bg-natural-dark">
          Add contract
        </Link>
      </div>
      <DataTable<Contract> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage="No contracts yet." />
    </div>
  )
}
