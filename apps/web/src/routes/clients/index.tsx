import { createFileRoute, Link } from "@tanstack/react-router"
import { useMemo, useState } from "react"
import { useList } from "@/hooks/useList"
import { clientsApi } from "@/api/endpoints/clients"
import { ClientsPageHeader, ClientsListToolbar } from "@/components/ClientsPageHeader"
import { ClientsListSkeleton } from "@/components/ClientsPageSkeletons"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
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
      <Link to="/clients/$clientId" params={{ clientId: row.id }} className="text-natural hover:underline font-medium">
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
  const [search, setSearch] = useState("")
  const { items, total, page, limit, setPage, loading, error } = useList({
    listFn: clientsApi.list,
    initialParams: { page: 1, limit: 20 },
  })

  const filteredItems = useMemo(() => {
    if (!search.trim()) return items
    const q = search.trim().toLowerCase()
    return items.filter(
      (c) =>
        c.name?.toLowerCase().includes(q) ||
        c.code?.toLowerCase().includes(q) ||
        c.contact_info?.email?.toLowerCase().includes(q) ||
        c.contact_info?.phone?.includes(q)
    )
  }, [items, search])

  return (
    <ClientsPageHeader
      breadcrumb="Clients"
      toolbar={<ClientsListToolbar searchValue={search} onSearchChange={setSearch} />}
    >
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-3">
        {loading ? (
          <ClientsListSkeleton />
        ) : error ? (
          <div className="border border-[#5A626A]/30 rounded-none bg-white p-4 text-center">
            <p className="text-[#5A626A]">{error}</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="border border-[#5A626A]/20 rounded-none bg-white p-6 text-center">
            <p className="text-[#5A626A] mb-1 text-sm">
              {items.length === 0 ? "No clients yet." : "No clients match your search."}
            </p>
            <p className="text-xs text-[#5A626A]/80 mb-3">Add your first client to get started.</p>
            <Link to="/clients/new">
              <Button className="rounded-none bg-natural text-white hover:bg-natural-dark">Add client</Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="rounded-none border border-[#5A626A]/30 bg-white">
              <DataTable<Client>
                columns={columns}
                data={search.trim() ? filteredItems : items}
                loading={false}
                error={null}
                page={search.trim() ? 1 : page}
                total={search.trim() ? filteredItems.length : total}
                limit={search.trim() ? Math.max(limit, filteredItems.length) : limit}
                onPageChange={setPage}
                emptyMessage=""
              />
            </div>
          </div>
        )}
      </div>
    </ClientsPageHeader>
  )
}
