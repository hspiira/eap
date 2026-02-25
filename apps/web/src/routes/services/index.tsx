/**
 * Services List Page
 * Displays all services within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'
import { useState, useCallback } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { CreateModal } from '@/components/common/CreateModal'
import { CreateServiceForm } from '@/components/forms/CreateServiceForm'
import { useListResource } from '@/hooks/useListResource'
import { servicesApi } from '@/api/endpoints/services'
import type { Service } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'

export const Route = createFileRoute('/services/')({
  beforeLoad: requireAuthBeforeLoad,
  component: ServicesPage,
})

function ServicesPage() {
  const navigate = useNavigate()
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)

  const fetchList = useCallback(
    (params: { page: number; limit: number; search?: string; status?: string; sort_by?: string; sort_desc?: boolean }) =>
      servicesApi.list(params).then((r) => ({ items: r.items, total: r.total })),
    []
  )

  const {
    items: services,
    loading,
    error,
    refetch: fetchServices,
    currentPage,
    setCurrentPage,
    pageSize,
    setPageSize,
    totalItems,
    searchValue,
    setSearchValue,
    statusFilter,
    setStatusFilter,
    sortBy,
    sortDirection,
    handleSort,
    clearFilters,
  } = useListResource<Service>({
    fetchList,
    initialPageSize: 25,
    errorFallback: 'Failed to load services',
  })

  const handleRowClick = (service: Service) => {
    navigate({ to: `/services/${service.id}` })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Active', label: 'Active' },
    { value: 'Inactive', label: 'Inactive' },
    { value: 'Pending', label: 'Pending' },
    { value: 'Archived', label: 'Archived' },
    { value: 'Deleted', label: 'Deleted' },
  ]

  const columns: Column<Service>[] = [
    {
      id: 'name',
      header: 'Service Name',
      accessor: 'name',
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-natural hover:text-natural-dark font-medium"
        >
          {value as string}
        </button>
      ),
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
      sortable: false,
      render: (value) => (
        <span className="text-safe-light text-sm line-clamp-2">
          {value || '-'}
        </span>
      ),
    },
    {
      id: 'service_type',
      header: 'Type',
      accessor: 'service_type',
      sortable: true,
      render: (value) => <span>{value as string || '-'}</span>,
    },
    {
      id: 'category',
      header: 'Category',
      accessor: 'category',
      sortable: true,
      render: (value) => <span>{value || '-'}</span>,
    },
    {
      id: 'duration_minutes',
      header: 'Duration',
      accessor: 'duration_minutes',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        const hours = Math.floor(value as number / 60)
        const minutes = (value as number) % 60
        if (hours > 0) {
          return `${hours}h ${minutes > 0 ? `${minutes}m` : ''}`
        }
        return `${minutes}m`
      },
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      render: (value) => <StatusBadge status={value as BaseStatus} size="sm" />,
    },
    {
      id: 'created_at',
      header: 'Created',
      accessor: 'created_at',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        const date = new Date(value as string)
        return date.toLocaleDateString()
      },
    },
  ]

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {loading && services.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={services}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchServices}
            pagination={{
              currentPage,
              pageSize,
              totalItems,
              onPageChange: setCurrentPage,
              onPageSizeChange: setPageSize,
            }}
            sorting={{
              sortBy,
              sortDirection,
              onSort: handleSort,
            }}
            filters={{
              searchValue,
              onSearchChange: setSearchValue,
              searchPlaceholder: 'Search services by name...',
              statusFilter: {
                value: statusFilter,
                options: statusOptions,
                onChange: setStatusFilter,
              },
              onClearFilters: clearFilters,
              createAction: {
                onClick: () => setCreateModalOpen(true),
                label: 'Create Service',
              },
            }}
            emptyMessage="No services found"
          />
        )}

        <CreateModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Create Service"
          loading={createLoading}
        >
          <CreateServiceForm
            onSuccess={() => {
              setCreateModalOpen(false)
              fetchServices()
            }}
            onCancel={() => setCreateModalOpen(false)}
            onLoadingChange={setCreateLoading}
          />
        </CreateModal>
      </div>
    </AppLayout>
  )
}
