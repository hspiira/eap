import { createFileRoute, Link } from "@tanstack/react-router"

import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { useList } from "@/hooks/useList"
import type { ServiceAssignment } from "@/types/entities"

export const Route = createFileRoute("/service-assignments/")({
  component: ServiceAssignmentsListPage,
})

const columns = [
  {
    id: "id",
    accessorKey: "id" as keyof ServiceAssignment,
    header: "Assignment",
    cell: (row: ServiceAssignment) => (
      <Link to="/service-assignments/$assignmentId" params={{ assignmentId: row.id }} className="text-natural hover:underline">
        {row.id.slice(0, 8)}…
      </Link>
    ),
  },
  { id: "contract_id", accessorKey: "contract_id" as keyof ServiceAssignment, header: "Contract ID" },
  { id: "service_id", accessorKey: "service_id" as keyof ServiceAssignment, header: "Service ID" },
  { id: "status", accessorKey: "status" as keyof ServiceAssignment, header: "Status", cell: (row: ServiceAssignment) => <StatusBadge status={row.status} /> },
]

function ServiceAssignmentsListPage() {
  const { items, total, page, limit, setPage, loading, error } = useList({ listFn: serviceAssignmentsApi.list, initialParams: { page: 1, limit: 20 } })
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Service Assignments</h1>
        <Link to="/service-assignments/new" className="inline-flex items-center justify-center h-9 px-4 bg-natural text-white font-medium rounded-none hover:bg-natural-dark">Add assignment</Link>
      </div>
      <DataTable<ServiceAssignment> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage="No assignments yet." />
    </div>
  )
}
