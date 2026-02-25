import { createFileRoute, Link } from "@tanstack/react-router"
import { useList } from "@/hooks/useList"
import { usersApi } from "@/api/endpoints/users"
import { DataTable } from "@/components/common/DataTable"
import { StatusBadge } from "@/components/common/StatusBadge"
import type { User } from "@/types/entities"

export const Route = createFileRoute("/users/")({
  component: UsersListPage,
})

const columns = [
  {
    id: "email",
    accessorKey: "email" as keyof User,
    header: "Email",
    cell: (row: User) => (
      <Link to="/users/$userId" params={{ userId: row.id }} className="text-[#8BA88B] hover:underline">
        {row.email}
      </Link>
    ),
  },
  {
    id: "status",
    accessorKey: "status" as keyof User,
    header: "Status",
    cell: (row: User) => <StatusBadge status={row.status} />,
  },
  {
    id: "verified",
    accessorKey: "is_email_verified" as keyof User,
    header: "Email verified",
    cell: (row: User) => (row.is_email_verified ? "Yes" : "No"),
  },
  {
    id: "2fa",
    accessorKey: "is_two_factor_enabled" as keyof User,
    header: "2FA",
    cell: (row: User) => (row.is_two_factor_enabled ? "On" : "Off"),
  },
]

function UsersListPage() {
  const { items, total, page, limit, setPage, loading, error } = useList({
    listFn: usersApi.list,
    initialParams: { page: 1, limit: 20 },
  })

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#5A626A]">Users</h1>
        <Link
          to="/users/new"
          className="inline-flex items-center justify-center h-9 px-4 bg-[#8BA88B] text-white font-medium rounded-none hover:bg-[#7a9a7a]"
        >
          Add user
        </Link>
      </div>
      <DataTable<User>
        columns={columns}
        data={items}
        loading={loading}
        error={error}
        page={page}
        total={total}
        limit={limit}
        onPageChange={setPage}
        emptyMessage="No users yet."
      />
    </div>
  )
}
