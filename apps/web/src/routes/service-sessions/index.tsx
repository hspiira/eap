import { createFileRoute, Link } from "@tanstack/react-router"
import { useList } from "@/hooks/useList"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import type { ServiceSession } from "@/types/entities"

export const Route = createFileRoute("/service-sessions/")({
  component: ServiceSessionsListPage,
})

const columns = [
  {
    id: "id",
    accessorKey: "id" as keyof ServiceSession,
    header: "Session",
    cell: (row: ServiceSession) => (
      <Link to="/service-sessions/$sessionId" params={{ sessionId: row.id }} className="text-[#8BA88B] hover:underline">
        {row.scheduled_at ? new Date(row.scheduled_at).toLocaleString() : row.id.slice(0, 8)}…
      </Link>
    ),
  },
  { id: "scheduled_at", accessorKey: "scheduled_at" as keyof ServiceSession, header: "Scheduled", cell: (row: ServiceSession) => row.scheduled_at ? new Date(row.scheduled_at).toLocaleString() : "—" },
  { id: "status", accessorKey: "status" as keyof ServiceSession, header: "Status", cell: (row: ServiceSession) => <StatusBadge status={row.status} /> },
]

function ServiceSessionsListPage() {
  const { items, total, page, limit, setPage, loading, error } = useList({ listFn: serviceSessionsApi.list, initialParams: { page: 1, limit: 20 } })
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Sessions</h1>
        <Link to="/service-sessions/new" className="inline-flex items-center justify-center h-9 px-4 bg-[#8BA88B] text-white font-medium rounded-none hover:bg-[#7a9a7a]">Add session</Link>
      </div>
      <DataTable<ServiceSession> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage="No sessions yet." />
    </div>
  )
}
