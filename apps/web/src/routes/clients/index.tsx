import { createFileRoute, Link } from "@tanstack/react-router"
import { useList } from "@/hooks/useList"
import { clientsApi } from "@/api/endpoints/clients"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import type { Client } from "@/types/entities"

export const Route = createFileRoute("/clients/")({
  component: ClientsListPage,
})

const columns = [
  {
    id: "name",
    accessorKey: "name" as keyof Client,
    header: "Name",
    cell: (row: Client) => (
      <Link to="/clients/$clientId" params={{ clientId: row.id }} className="text-[#8BA88B] hover:underline">
        {row.name}
      </Link>
    ),
  },
  { id: "code", accessorKey: "code" as keyof Client, header: "Code" },
  {
    id: "status",
    accessorKey: "status" as keyof Client,
    header: "Status",
    cell: (row: Client) => <StatusBadge status={row.status} />,
  },
  {
    id: "contact",
    accessorKey: "contact_info" as keyof Client,
    header: "Contact",
    cell: (row: Client) => row.contact_info?.email ?? row.contact_info?.phone ?? "—",
  },
]

function ClientsListPage() {
  const { items, total, page, limit, setPage, loading, error } = useList({
    listFn: clientsApi.list,
    initialParams: { page: 1, limit: 20 },
  })

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Clients</h1>
        <Link
          to="/clients/new"
          className="inline-flex items-center justify-center h-9 px-4 bg-[#8BA88B] text-white font-medium rounded-none hover:bg-[#7a9a7a]"
        >
          Add client
        </Link>
      </div>
      <DataTable<Client>
        columns={columns}
        data={items}
        loading={loading}
        error={error}
        page={page}
        total={total}
        limit={limit}
        onPageChange={setPage}
        emptyMessage="No clients yet."
      />
    </div>
  )
}
