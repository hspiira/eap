import { createFileRoute, Link } from "@tanstack/react-router"
import { useList } from "@/hooks/useList"
import { clientTagsApi } from "@/api/endpoints/client-tags"
import { TagsPageHeader } from "@/components/TagsPageHeader"
import { DataTable } from "@/components/common/DataTable"
import { Button } from "@/components/ui/button"
import type { ClientTag } from "@/types/entities"
import { Pencil } from "lucide-react"

export const Route = createFileRoute("/tags/")({
  component: TagsListPage,
})

const columns = [
  {
    id: "name",
    accessorKey: "name" as keyof ClientTag,
    header: "Name",
    cell: (row: ClientTag) => (
      <Link
        to="/tags/$tagId"
        params={{ tagId: row.id }}
        className="text-natural hover:underline"
      >
        {row.name}
      </Link>
    ),
  },
  {
    id: "color",
    accessorKey: "color" as keyof ClientTag,
    header: "Color",
    cell: (row: ClientTag) =>
      row.color ? (
        <span className="flex items-center gap-2">
          <span
            className="inline-block h-4 w-4 border border-[#5A626A]/30"
            style={{ backgroundColor: row.color }}
          />
          <span className="text-[#5A626A]">{row.color}</span>
        </span>
      ) : (
        "—"
      ),
  },
  {
    id: "description",
    accessorKey: "description" as keyof ClientTag,
    header: "Description",
    cell: (row: ClientTag) => (
      <span className="text-[#5A626A] max-w-[240px] truncate block">
        {row.description ?? "—"}
      </span>
    ),
  },
  {
    id: "actions",
    accessorKey: "id" as keyof ClientTag,
    header: "",
    cell: (row: ClientTag) => (
      <Button asChild variant="ghost" size="sm" className="rounded-none h-8 w-8 p-0 text-[#5A626A]">
        <Link to="/tags/$tagId" params={{ tagId: row.id }} aria-label="Edit tag">
          <Pencil className="h-4 w-4" />
        </Link>
      </Button>
    ),
  },
]

function TagsListPage() {
  const { items, total, page, limit, setPage, loading, error } = useList({
    listFn: clientTagsApi.list,
    initialParams: { page: 1, limit: 20 },
  })

  return (
    <TagsPageHeader breadcrumb="Tags">
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
        <DataTable<ClientTag>
          columns={columns}
          data={items}
          loading={loading}
          error={error}
          page={page}
          total={total}
          limit={limit}
          onPageChange={setPage}
          emptyMessage="No tags yet. Create one to organize clients."
        />
      </div>
    </TagsPageHeader>
  )
}
