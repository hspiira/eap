import { useCallback, useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import { industriesApi } from "@/api/endpoints/industries"
import { AppLayout } from "@/components/AppLayout"
import { DataTable } from "@/components/common/DataTable"
import { IndustriesPageHeader } from "@/components/IndustriesPageHeader"
import { IndustriesListSkeleton } from "@/components/IndustriesPageSkeletons"
import { IndustryDetailsCard } from "@/components/IndustryDetailsCard"
import { useEntityList } from "@/lib/queries"
import { useAuthStore } from "@/store/slices/authSlice"
import type { Industry } from "@/types/entities"
import { normalizeErrorMessage } from "@/utils/errorHandler"

export const Route = createFileRoute("/industries")({
  component: IndustriesPage,
})

const columns = [
  { id: "name", accessorKey: "name" as keyof Industry, header: "Name" },
  { id: "code", accessorKey: "code" as keyof Industry, header: "Code" },
  {
    id: "level",
    accessorKey: "level" as keyof Industry,
    header: "Level",
    cell: (row: Industry) => (row.level != null ? String(row.level) : "—"),
  },
]

function IndustriesPage() {
  const { isAuthenticated, isLoading } = useAuthStore()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const limit = 20
  const query = useEntityList({
    resource: "industries",
    params: { page, limit },
    listFn: industriesApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const refetch = useCallback(
    () => queryClient.invalidateQueries({ queryKey: ["industries", "list"] }),
    [queryClient],
  )

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedIndustry, setSelectedIndustry] = useState<Industry | null>(null)
  const [parentIndustry, setParentIndustry] = useState<Industry | null>(null)
  const [childIndustries, setChildIndustries] = useState<Industry[]>([])
  const [detailsLoading, setDetailsLoading] = useState(false)

  const loadDetails = useCallback(async (id: string) => {
    setDetailsLoading(true)
    try {
      const [industry, children] = await Promise.all([
        industriesApi.getById(id),
        industriesApi.getChildren(id),
      ])
      setSelectedIndustry(industry)
      setChildIndustries(children)
      if (industry.parent_id) {
        try {
          const parent = await industriesApi.getById(industry.parent_id)
          setParentIndustry(parent)
        } catch {
          setParentIndustry(null)
        }
      } else {
        setParentIndustry(null)
      }
    } catch {
      setSelectedIndustry(null)
      setParentIndustry(null)
      setChildIndustries([])
    } finally {
      setDetailsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedId) {
      loadDetails(selectedId)
    } else {
      setSelectedIndustry(null)
      setParentIndustry(null)
      setChildIndustries([])
    }
  }, [selectedId, loadDetails])

  const handleIndustryUpdated = useCallback(
    (updated: Industry) => {
      setSelectedIndustry(updated)
      refetch()
    },
    [refetch]
  )

  if (isLoading) return <div className="p-8 text-ink">Loading…</div>
  if (!isAuthenticated) return null

  return (
    <AppLayout>
      <IndustriesPageHeader breadcrumb="Industries">
        <div className="content-area-scroll flex-1 min-h-0 grid grid-cols-12 gap-3 p-3 overflow-hidden">
          <div className="col-span-8 min-w-0 flex flex-col overflow-hidden">
            {loading ? (
              <IndustriesListSkeleton />
            ) : (
              <DataTable<Industry>
                columns={columns}
                data={items}
                loading={false}
                error={error}
                page={page}
                total={total}
                limit={limit}
                onPageChange={setPage}
                emptyMessage="No industries yet."
                getRowId={(row) => row.id}
                onRowClick={(row) => setSelectedId(row.id)}
                selectedId={selectedId}
              />
            )}
          </div>
          <div className="col-span-4 min-w-0 flex flex-col min-h-0">
            {selectedId && detailsLoading ? (
              <div className="border border-border/25 bg-white p-4 text-sm text-ink/70 rounded-none">
                Loading…
              </div>
            ) : selectedIndustry ? (
              <IndustryDetailsCard
                industry={selectedIndustry}
                parent={parentIndustry}
                children={childIndustries}
                onClose={() => setSelectedId(null)}
                onUpdated={handleIndustryUpdated}
              />
            ) : (
              <div className="border border-border/25 bg-white p-4 flex flex-col justify-center flex-1 min-h-[120px] rounded-none">
                <h3 className="text-sm font-semibold text-ink mb-2">Hey, Let&apos;s Start Now!</h3>
                <p className="text-sm text-ink/80">
                  Select an industry from the list to view its details, hierarchy, and edit it.
                </p>
              </div>
            )}
          </div>
        </div>
      </IndustriesPageHeader>
    </AppLayout>
  )
}
