import { useState, useEffect, useCallback, useMemo } from 'react'
import { IndustryTree } from '@/components/common/IndustryTree'
import { IndustryDetailPanel } from '@/components/common/IndustryDetailPanel'
import { TableFilters } from '@/components/common/TableFilters'
import { Pagination } from '@/components/common/Pagination'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { CreateModal } from '@/components/common/CreateModal'
import { CreateIndustryForm } from '@/components/forms/CreateIndustryForm'
import { useTenant } from '@/hooks/useTenant'
import { industriesApi } from '@/api/endpoints/industries'
import type { Industry } from '@/types/entities'

const PAGE_SIZE = 15

export function IndustriesTab() {
  const { currentTenant, isLoading: tenantLoading } = useTenant()
  const [industries, setIndustries] = useState<Industry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchValue, setSearchValue] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)

  const [detailIndustry, setDetailIndustry] = useState<Industry | null>(null)
  const [detailChildren, setDetailChildren] = useState<Industry[]>([])
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  const fetchIndustries = useCallback(async () => {
    if (!currentTenant) return
    try {
      setLoading(true)
      setError(null)
      const res = await industriesApi.list({
        tenant_id: currentTenant.id,
        page: 1,
        limit: 100,
      })
      setIndustries(res.items)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load industries'
      setError(msg)
      console.error('Error fetching industries:', err)
    } finally {
      setLoading(false)
    }
  }, [currentTenant])

  const fetchDetail = useCallback(async (id: string) => {
    try {
      setDetailLoading(true)
      setDetailError(null)
      const [data, childList] = await Promise.all([
        industriesApi.getById(id),
        industriesApi.getChildren(id).catch(() => []),
      ])
      setDetailIndustry(data)
      setDetailChildren(childList)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load industry'
      setDetailError(msg)
      setDetailIndustry(null)
      setDetailChildren([])
    } finally {
      setDetailLoading(false)
    }
  }, [])

  useEffect(() => {
    if (tenantLoading) {
      setLoading(true)
      return
    }
    if (!currentTenant) {
      setLoading(false)
      setIndustries([])
      setError(null)
      return
    }
    fetchIndustries()
  }, [tenantLoading, currentTenant, fetchIndustries])

  useEffect(() => {
    if (!selectedId) {
      setDetailIndustry(null)
      setDetailChildren([])
      setDetailError(null)
      setDetailLoading(false)
      return
    }
    fetchDetail(selectedId)
  }, [selectedId, fetchDetail])

  const handleSelect = (industry: Industry) => {
    setSelectedId(industry.id)
  }

  const handleSelectParent = (id: string) => {
    setSelectedId(id)
  }

  const handleSelectChild = (id: string) => {
    setSelectedId(id)
  }

  const filtered = useMemo(() => {
    if (!searchValue.trim()) return industries
    const q = searchValue.trim().toLowerCase()
    const matches = industries.filter(
      (i) =>
        (i.name ?? '').toLowerCase().includes(q) ||
        (i.code ?? '').toLowerCase().includes(q),
    )
    const ancestorIds = new Set<string>()
    for (const m of matches) {
      let pid: string | null | undefined = m.parent_id
      while (pid) {
        ancestorIds.add(pid)
        const parent = industries.find((i) => i.id === pid)
        pid = parent?.parent_id
      }
    }
    return industries.filter(
      (i) => matches.some((m) => m.id === i.id) || ancestorIds.has(i.id),
    )
  }, [industries, searchValue])

  const roots = useMemo(() => {
    return filtered.filter((i) => !i.parent_id)
  }, [filtered])

  const totalRoots = roots.length
  const totalPages = Math.max(1, Math.ceil(totalRoots / PAGE_SIZE))
  const safePage = Math.min(Math.max(1, currentPage), totalPages)
  const rootOffset = (safePage - 1) * PAGE_SIZE

  const handleSearchChange = (v: string) => {
    setSearchValue(v)
    setCurrentPage(1)
  }

  const hasActiveFilters = !!searchValue.trim()
  const emptyMessage = !currentTenant
    ? 'Select a tenant to view industries'
    : hasActiveFilters
      ? 'No industries match your search'
      : 'No industries yet'

  return (
    <div className="space-y-0">
      <TableFilters
        searchValue={searchValue}
        onSearchChange={handleSearchChange}
        searchPlaceholder="Search by name or code..."
        onClearFilters={() => {
          setSearchValue('')
          setCurrentPage(1)
        }}
        createAction={{
          onClick: () => setCreateModalOpen(true),
          label: 'Add Industry',
        }}
        className="mb-4"
      />

      <CreateModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Add Industry"
        loading={createLoading}
      >
        <CreateIndustryForm
          onSuccess={() => {
            setCreateModalOpen(false)
            fetchIndustries()
          }}
          onCancel={() => setCreateModalOpen(false)}
          onLoadingChange={setCreateLoading}
        />
      </CreateModal>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 flex flex-col min-h-0">
          {loading ? (
            <div className="flex items-center justify-center p-12 border border-[0.5px] border-safe/30 bg-white">
              <LoadingSpinner size="lg" />
            </div>
          ) : error ? (
            <div className="border border-[0.5px] border-safe/30 bg-white px-4 py-12 text-center">
              <p className="text-danger font-medium mb-2">Error loading industries</p>
              <p className="text-safe-light text-sm mb-4">{error}</p>
              <button
                onClick={fetchIndustries}
                className="px-4 py-2 bg-natural hover:bg-natural-dark text-white text-sm rounded-none"
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              <div className="border border-[0.5px] border-safe/30 bg-white flex-1 min-h-[200px] overflow-auto">
                <IndustryTree
                  industries={filtered}
                  onSelect={handleSelect}
                  selectedId={selectedId}
                  emptyMessage={emptyMessage}
                  rootOffset={rootOffset}
                  rootLimit={PAGE_SIZE}
                />
              </div>
              {totalRoots > 0 && (
                <Pagination
                  currentPage={safePage}
                  totalPages={totalPages}
                  pageSize={PAGE_SIZE}
                  totalItems={totalRoots}
                  onPageChange={setCurrentPage}
                  onPageSizeChange={() => {}}
                  pageSizeOptions={[PAGE_SIZE]}
                  showPageSizeSelector={false}
                  infoPosition="below"
                  className="mt-2"
                />
              )}
            </>
          )}
        </div>

        <div className="lg:col-span-2 min-h-[280px]">
          <IndustryDetailPanel
            industry={detailIndustry}
            children={detailChildren}
            loading={detailLoading}
            error={detailError}
            onSelectParent={handleSelectParent}
            onSelectChild={handleSelectChild}
            onRetry={() => selectedId && fetchDetail(selectedId)}
          />
        </div>
      </div>
    </div>
  )
}
