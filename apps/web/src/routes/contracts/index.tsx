import { createFileRoute, Link } from "@tanstack/react-router"
import { useList } from "@/hooks/useList"
import { contractsApi } from "@/api/endpoints/contracts"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import type { Contract } from "@/types/entities"

export const Route = createFileRoute("/contracts/")({
  component: ContractsListPage,
})

const columns = [
  {
    id: "contract_number",
    accessorKey: "contract_number" as keyof Contract,
    header: "Number",
    cell: (row: Contract) => (
      <Link to="/contracts/$contractId" params={{ contractId: row.id }} className="text-[#8BA88B] hover:underline">
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
  const { items, total, page, limit, setPage, loading, error } = useList({
    listFn: contractsApi.list,
    initialParams: { page: 1, limit: 20 },
  })

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Contracts</h1>
        <Link to="/contracts/new" className="inline-flex items-center justify-center h-9 px-4 bg-[#8BA88B] text-white font-medium rounded-none hover:bg-[#7a9a7a]">
          Add contract
        </Link>
      </div>
      <DataTable<Contract> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage="No contracts yet." />
    </div>
  )
}
