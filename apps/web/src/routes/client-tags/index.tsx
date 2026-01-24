/**
 * Client Tags List Page
 * Tag list with DataTable, filter and search
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { CreateModal } from '@/components/common/CreateModal'
import { CreateClientTagForm } from '@/components/forms/CreateClientTagForm'
import { clientTagsApi } from '@/api/endpoints/client-tags'
import type { ClientTag } from '@/types/entities'
import { Tag } from 'lucide-react'

export const Route = createFileRoute('/client-tags/')({
  component: ClientTagsPage,
})

function ClientTagsPage() {
  const navigate = useNavigate()
  const [tags, setTags] = useState<ClientTag[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)

  const fetchTags = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, unknown> = {
        page: currentPage,
        limit: pageSize,
      }
      if (searchValue) params.search = searchValue
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const res = await clientTagsApi.list(params)
      setTags(res.items)
      setTotalItems(res.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load tags'
      setError(msg)
      console.error('Error fetching tags:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTags()
  }, [currentPage, pageSize, searchValue, sortBy, sortDirection])

  const handleSort = (columnId: string) => {
    if (sortBy === columnId) {
      if (sortDirection === 'asc') setSortDirection('desc')
      else if (sortDirection === 'desc') {
        setSortBy(null)
        setSortDirection(null)
      } else setSortDirection('asc')
    } else {
      setSortBy(columnId)
      setSortDirection('asc')
    }
  }

  const handleRowClick = (tag: ClientTag) => navigate({ to: `/client-tags/${tag.id}` })

  const columns: Column<ClientTag>[] = [
    {
      id: 'name',
      header: 'Name',
      accessor: 'name',
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-natural hover:text-natural-dark font-medium flex items-center gap-2"
        >
          <span
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: row.color ?? '#94a3b8' }}
            aria-hidden
          />
          <Tag size={16} />
          {(value as string) ?? '-'}
        </button>
      ),
    },
    {
      id: 'color',
      header: 'Color',
      accessor: 'color',
      sortable: false,
      render: (value) =>
        value ? (
          <span className="flex items-center gap-2">
            <span
              className="w-4 h-4 rounded-full border border-[0.5px] border-safe"
              style={{ backgroundColor: value as string }}
            />
            <span className="text-safe-light text-sm">{value as string}</span>
          </span>
        ) : (
          <span className="text-safe-light">—</span>
        ),
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
      sortable: false,
      render: (value) => (
        <span className="text-safe-light text-sm line-clamp-2">{(value as string) || '—'}</span>
      ),
    },
    {
      id: 'created_at',
      header: 'Created',
      accessor: 'created_at',
      sortable: true,
      render: (v) => (v ? new Date(v as string).toLocaleDateString() : '—'),
    },
  ]

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {loading && tags.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={tags}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchTags}
            pagination={{
              currentPage,
              pageSize,
              totalItems,
              onPageChange: setCurrentPage,
              onPageSizeChange: (size) => {
                setPageSize(size)
                setCurrentPage(1)
              },
            }}
            sorting={{ sortBy, sortDirection, onSort: handleSort }}
            filters={{
              searchValue,
              onSearchChange: (v) => {
                setSearchValue(v)
                setCurrentPage(1)
              },
              searchPlaceholder: 'Search tags...',
              onClearFilters: () => {
                setSearchValue('')
                setCurrentPage(1)
              },
              createAction: {
                onClick: () => setCreateModalOpen(true),
                label: 'Add Tag',
              },
            }}
            emptyMessage="No tags found"
          />
        )}

        <CreateModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Add Tag"
          loading={createLoading}
        >
          <CreateClientTagForm
            onSuccess={() => {
              setCreateModalOpen(false)
              fetchTags()
            }}
            onCancel={() => setCreateModalOpen(false)}
            onLoadingChange={setCreateLoading}
          />
        </CreateModal>
      </div>
    </AppLayout>
  )
}
