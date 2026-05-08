import { useState } from "react"

import { createFileRoute, Link } from "@tanstack/react-router"

import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { useEntityList } from "@/lib/queries"
import type { ServiceAssignment } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

export const Route = createFileRoute("/service-assignments/")({
  component: ServiceAssignmentsListPage,
})

const columns = [
  {
    id: "id",
    accessorKey: "id" as keyof ServiceAssignment,
    header: "Assignment",
    cell: (row: ServiceAssignment) => (
      <Link to="/service-assignments/$assignmentId" params={{ assignmentId: row.id }} className="text-primary hover:underline">
        {row.id.slice(0, 8)}…
      </Link>
    ),
  },
  { id: "contract_id", accessorKey: "contract_id" as keyof ServiceAssignment, header: "Contract ID" },
  { id: "service_id", accessorKey: "service_id" as keyof ServiceAssignment, header: "Service ID" },
  { id: "status", accessorKey: "status" as keyof ServiceAssignment, header: "Status", cell: (row: ServiceAssignment) => <StatusBadge status={row.status} /> },
]

function ServiceAssignmentsListPage() {
  const [page, setPage] = useState(1)
  const limit = 20
  const query = useEntityList({
    resource: "service-assignments",
    params: { page, limit },
    listFn: serviceAssignmentsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-fg">Service Assignments</h1>
        <Link to="/service-assignments/new" className="inline-flex items-center justify-center h-9 px-4 bg-primary text-white font-medium rounded-none hover:bg-primary">Add assignment</Link>
      </div>
      <DataTable<ServiceAssignment> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage="No assignments yet." />
    </div>
  )
}
