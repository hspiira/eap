/**
 * Clients List Page
 * Displays all clients within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect, useCallback } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { CreateModal } from '@/components/common/CreateModal'
import { CreateClientForm } from '@/components/forms/CreateClientForm'
import { useTenant } from '@/hooks/useTenant'
import { clientsApi } from '@/api/endpoints/clients'
import { industriesApi } from '@/api/endpoints/industries'
import type { Client, Industry } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'

export const Route = createFileRoute('/clients/')({
  component: ClientsPage,
})

function ClientsPage() {
  const navigate = useNavigate()
  const { currentTenant, isLoading: tenantLoading } = useTenant()
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [industries, setIndustries] = useState<Industry[]>([])
  const [industriesMap, setIndustriesMap] = useState<Map<string, Industry>>(new Map())

  const fetchClients = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, unknown> = {
        page: currentPage,
        limit: pageSize,
      }
      if (currentTenant) params.tenant_id = currentTenant.id
      if (searchValue) params.search = searchValue
      if (statusFilter) params.status = statusFilter
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }
      const response = await clientsApi.list(params)
      const items = Array.isArray(response?.items)
        ? response.items
        : Array.isArray((response as { data?: unknown[] })?.data)
          ? (response as { data: unknown[] }).data
          : []
      const total = typeof response?.total === 'number' ? response.total : items.length
      setClients(items as Client[])
      setTotalItems(total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load clients'
      setError(msg)
      console.error('Error fetching clients:', err)
    } finally {
      setLoading(false)
    }
  }, [currentPage, pageSize, searchValue, statusFilter, sortBy, sortDirection, currentTenant])

  useEffect(() => {
    if (tenantLoading) {
      setLoading(true)
      return
    }
    if (!currentTenant) {
      setLoading(false)
      setClients([])
      setTotalItems(0)
      setError(null)
      return
    }
    fetchClients()
  }, [tenantLoading, currentTenant, fetchClients])

  // Fetch industries for lookup
  useEffect(() => {
    const fetchIndustries = async () => {
      if (!currentTenant) {
        setIndustries([])
        setIndustriesMap(new Map())
        return
      }
      try {
        const res = await industriesApi.list({
          tenant_id: currentTenant.id,
          page: 1,
          limit: 500,
        })
        const industriesList = res.items || []
        setIndustries(industriesList)
        // Create a map for quick lookup
        const map = new Map<string, Industry>()
        industriesList.forEach((ind) => {
          map.set(ind.id, ind)
        })
        setIndustriesMap(map)
      } catch (err) {
        console.error('Error fetching industries:', err)
      }
    }
    if (!tenantLoading && currentTenant) {
      fetchIndustries()
    }
  }, [tenantLoading, currentTenant])

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

  const handleRowClick = (client: Client) => {
    navigate({ to: `/clients/${client.id}` })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Active', label: 'Active' },
    { value: 'Inactive', label: 'Inactive' },
    { value: 'Pending', label: 'Pending' },
    { value: 'Archived', label: 'Archived' },
  ]

  const columns: Column<Client>[] = [
    {
      id: 'name',
      header: 'Name',
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
      id: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      render: (value) => <StatusBadge status={value as BaseStatus} size="sm" />,
    },
    {
      id: 'industry_id',
      header: 'Industry',
      accessor: 'industry_id',
      sortable: true,
      render: (value) => {
        if (!value) return <span className="text-safe-light">-</span>
        const industry = industriesMap.get(value as string)
        return industry ? (
          <span className="text-safe">{industry.name}</span>
        ) : (
          <span className="text-safe-light">-</span>
        )
      },
    },
    {
      id: 'contact_info',
      header: 'Contact',
      accessor: 'contact_info',
      render: (value) => {
        const contact = value as Client['contact_info']
        return contact?.email ? (
          <span>{contact.email}</span>
        ) : contact?.phone ? (
          <span>{contact.phone}</span>
        ) : (
          <span className="text-safe-light">-</span>
        )
      },
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

  if (!tenantLoading && !currentTenant) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <div className="p-6 bg-white border border-[0.5px] border-safe/30 text-safe">
            <p className="font-medium">No organization selected</p>
            <p className="text-sm text-safe-light mt-1">
              Log in with a tenant code to view clients, or create a tenant first.
            </p>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {loading && clients.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={clients}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchClients}
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
            sorting={{
              sortBy,
              sortDirection,
              onSort: handleSort,
            }}
            filters={{
              searchValue,
              onSearchChange: (value) => {
                setSearchValue(value)
                setCurrentPage(1)
              },
              searchPlaceholder: 'Search clients by name...',
              statusFilter: {
                value: statusFilter,
                options: statusOptions,
                onChange: (value) => {
                  setStatusFilter(value)
                  setCurrentPage(1)
                },
              },
              onClearFilters: () => {
                setSearchValue('')
                setStatusFilter('')
                setCurrentPage(1)
              },
              createAction: {
                onClick: () => setCreateModalOpen(true),
                label: 'Create Client',
              },
            }}
            emptyMessage="No clients found"
          />
        )}

        <CreateModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Create Client"
          loading={createLoading}
        >
          <CreateClientForm
            onSuccess={() => {
              setCreateModalOpen(false)
              fetchClients()
            }}
            onCancel={() => setCreateModalOpen(false)}
            onLoadingChange={setCreateLoading}
          />
        </CreateModal>
      </div>
    </AppLayout>
  )
}
