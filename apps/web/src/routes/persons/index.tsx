import { useEffect, useState } from "react"

import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { Search } from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Input } from "@/components/ui/input"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { Person } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

export const Route = createFileRoute("/persons/")({
  component: PersonsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { search?: string } = {}
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    return out
  },
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
  const searchParams = useSearch({ from: "/persons/" })
  const navigate = useNavigate({ from: "/persons/" })
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
    resource: "persons",
    params: { page, limit, search: activeSearch },
    listFn: personsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-xl font-semibold text-[#5A626A]">Persons</h1>
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#5A626A]/70" />
          <Input
            placeholder="Search persons..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="rounded-none h-9 pl-8 pr-3 border-[#5A626A]/30"
          />
        </div>
        <Link to="/persons/new" className="inline-flex items-center justify-center h-9 px-4 bg-natural text-white font-medium rounded-none hover:bg-natural-dark">Add person</Link>
      </div>
      <DataTable<Person> columns={columns} data={items} loading={loading} error={error} page={page} total={total} limit={limit} onPageChange={setPage} emptyMessage={activeSearch ? "No persons match your search." : "No persons yet."} />
    </div>
  )
}
