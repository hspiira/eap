import { useState } from "react"

import { createFileRoute, Link } from "@tanstack/react-router"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { useEntityList } from "@/lib/queries"
import type { ServiceSession } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

export const Route = createFileRoute("/service-sessions/")({
  component: ServiceSessionsListPage,
})

const columns = [
  {
    id: "id",
    accessorKey: "id" as keyof ServiceSession,
    header: "Session",
    cell: (row: ServiceSession) => (
      <Link to="/service-sessions/$sessionId" params={{ sessionId: row.id }} className="text-natural hover:underline">
        {row.scheduled_at ? new Date(row.scheduled_at).toLocaleString() : row.id.slice(0, 8)}…
      </Link>
    ),
  },
  { id: "scheduled_at", accessorKey: "scheduled_at" as keyof ServiceSession, header: "Scheduled", cell: (row: ServiceSession) => row.scheduled_at ? new Date(row.scheduled_at).toLocaleString() : "—" },
  { id: "status", accessorKey: "status" as keyof ServiceSession, header: "Status", cell: (row: ServiceSession) => <StatusBadge status={row.status} /> },
]

function ServiceSessionsListPage() {
  const [page, setPage] = useState(1)
  const limit = 20
  const query = useEntityList({
    resource: "service-sessions",
    params: { page, limit },
    listFn: serviceSessionsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Sessions</h1>
        <Link to="/service-sessions/new" className="inline-flex items-center justify-center h-9 px-4 bg-natural text-white font-medium rounded-none hover:bg-natural-dark">Add session</Link>
      </div>
      <DataTable<ServiceSession> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage="No sessions yet." />
    </div>
  )
}
