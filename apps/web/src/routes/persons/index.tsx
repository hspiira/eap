import { useState } from "react"

import { createFileRoute, Link } from "@tanstack/react-router"

import { personsApi } from "@/api/endpoints/persons"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { useEntityList } from "@/lib/queries"
import type { Person } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

export const Route = createFileRoute("/persons/")({
  component: PersonsListPage,
})

const columns = [
  {
    id: "name",
    accessorKey: "first_name" as keyof Person,
    header: "Name",
    cell: (row: Person) => (
      <Link to="/persons/$personId" params={{ personId: row.id }} className="text-natural hover:underline">
        {row.first_name} {row.last_name}
      </Link>
    ),
  },
  { id: "person_type", accessorKey: "person_type" as keyof Person, header: "Type" },
  { id: "status", accessorKey: "status" as keyof Person, header: "Status", cell: (row: Person) => <StatusBadge status={row.status} /> },
]

function PersonsListPage() {
  const [page, setPage] = useState(1)
  const limit = 20
  const query = useEntityList({
    resource: "persons",
    params: { page, limit },
    listFn: personsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Persons</h1>
        <Link to="/persons/new" className="inline-flex items-center justify-center h-9 px-4 bg-natural text-white font-medium rounded-none hover:bg-natural-dark">Add person</Link>
      </div>
      <DataTable<Person> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage="No persons yet." />
    </div>
  )
}
