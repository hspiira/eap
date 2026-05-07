import { createFileRoute, Link } from "@tanstack/react-router"

import { servicesApi } from "@/api/endpoints/services"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { useList } from "@/hooks/useList"
import type { Service } from "@/types/entities"

export const Route = createFileRoute("/services/")({
  component: ServicesListPage,
})

const columns = [
  {
    id: "name",
    accessorKey: "name" as keyof Service,
    header: "Name",
    cell: (row: Service) => (
      <Link to="/services/$serviceId" params={{ serviceId: row.id }} className="text-natural hover:underline">{row.name}</Link>
    ),
  },
  { id: "description", accessorKey: "description" as keyof Service, header: "Description", cell: (row: Service) => (row.description ?? "—") },
  { id: "status", accessorKey: "status" as keyof Service, header: "Status", cell: (row: Service) => <StatusBadge status={row.status} /> },
]

function ServicesListPage() {
  const { items, total, page, limit, setPage, loading, error } = useList({ listFn: servicesApi.list, initialParams: { page: 1, limit: 20 } })
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Services</h1>
        <Link to="/services/new" className="inline-flex items-center justify-center h-9 px-4 bg-natural text-white font-medium rounded-none hover:bg-natural-dark">Add service</Link>
      </div>
      <DataTable<Service> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage="No services yet." />
    </div>
  )
}
