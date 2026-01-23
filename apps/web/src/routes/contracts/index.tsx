/**
 * Contracts List Page
 * Displays all contracts within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { contractsApi } from '@/api/endpoints/contracts'
import { clientsApi } from '@/api/endpoints/clients'
import type { Contract } from '@/types/entities'
import type { ContractStatus } from '@/types/enums'
import { Plus } from 'lucide-react'

export const Route = createFileRoute('/contracts/')({
  component: ContractsPage,
})

function ContractsPage() {
  const navigate = useNavigate()
  const { showError } = useToast()
  const [contracts, setContracts] = useState<Contract[]>([])
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [clientFilter, setClientFilter] = useState<string>('')
  const [startDateFilter, setStartDateFilter] = useState<string>('')
  const [endDateFilter, setEndDateFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)

  // Fetch clients for filter
  useEffect(() => {
    const fetchClients = async () => {
      try {
        const response = await clientsApi.list({ limit: 100 })
        setClients(response.items.map(c => ({ id: c.id, name: c.name })))
      } catch (error) {
        console.error('Error fetching clients:', error)
      }
    }
    fetchClients()
  }, [])

  // Fetch contracts (tenant-scoped automatically via API client)
  const fetchContracts = async () => {
    try {
      setLoading(true)
      const params: any = {
        page: currentPage,
        limit: pageSize,
      }

      if (searchValue) {
        params.search = searchValue
      }

      if (statusFilter) {
        params.status = statusFilter
      }

      if (clientFilter) {
        params.client_id = clientFilter
      }

      if (startDateFilter) {
        params.start_date_from = startDateFilter
      }

      if (endDateFilter) {
        params.end_date_to = endDateFilter
      }

      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const response = await contractsApi.list(params)
      setContracts(response.items)
      setTotalItems(response.total)
    } catch (error) {
      showError('Failed to load contracts')
      console.error('Error fetching contracts:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchContracts()
  }, [currentPage, pageSize, searchValue, statusFilter, clientFilter, startDateFilter, endDateFilter, sortBy, sortDirection])

  const handleSort = (columnId: string) => {
    if (sortBy === columnId) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortBy(null)
        setSortDirection(null)
      } else {
        setSortDirection('asc')
      }
    } else {
      setSortBy(columnId)
      setSortDirection('asc')
    }
  }

  const handleRowClick = (contract: Contract) => {
    navigate({ to: `/contracts/${contract.id}` })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Active', label: 'Active' },
    { value: 'Expired', label: 'Expired' },
    { value: 'Terminated', label: 'Terminated' },
    { value: 'Renewed', label: 'Renewed' },
    { value: 'Pending', label: 'Pending' },
    { value: 'Draft', label: 'Draft' },
  ]

  const clientOptions = [
    { value: '', label: 'All Clients' },
    ...clients.map(c => ({ value: c.id, label: c.name })),
  ]

  const columns: Column<Contract>[] = [
    {
      id: 'contract_number',
      header: 'Contract #',
      accessor: 'contract_number',
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-natural hover:text-natural-dark font-medium"
        >
          {value || `#${row.id.slice(0, 8)}`}
        </button>
      ),
    },
    {
      id: 'client_id',
      header: 'Client',
      accessor: 'client_id',
      sortable: true,
      render: (value, row) => {
        const client = clients.find(c => c.id === row.client_id)
        return <span>{client?.name || row.client_id}</span>
      },
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      render: (value) => <StatusBadge status={value as ContractStatus} size="sm" />,
    },
    {
      id: 'start_date',
      header: 'Start Date',
      accessor: 'start_date',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        const date = new Date(value as string)
        return date.toLocaleDateString()
      },
    },
    {
      id: 'end_date',
      header: 'End Date',
      accessor: 'end_date',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        const date = new Date(value as string)
        return date.toLocaleDateString()
      },
    },
    {
      id: 'billing_amount',
      header: 'Amount',
      accessor: 'billing_amount',
      sortable: true,
      render: (value, row) => {
        if (!value) return '-'
        const currency = row.currency || 'USD'
        return <span>{new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value as number)}</span>
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

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-safe">Contracts</h1>
          <button
            onClick={() => navigate({ to: '/contracts/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Create Contract</span>
          </button>
        </div>

        {loading && contracts.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={contracts}
            columns={columns}
            loading={loading}
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
              searchPlaceholder: 'Search contracts by number...',
              statusFilter: {
                value: statusFilter,
                options: statusOptions,
                onChange: (value) => {
                  setStatusFilter(value)
                  setCurrentPage(1)
                },
              },
              dateRangeFilter: {
                startDate: startDateFilter,
                endDate: endDateFilter,
                onStartDateChange: (date) => {
                  setStartDateFilter(date)
                  setCurrentPage(1)
                },
                onEndDateChange: (date) => {
                  setEndDateFilter(date)
                  setCurrentPage(1)
                },
              },
              customFilters: [
                ...(clients.length > 0
                  ? [
                      {
                        id: 'client-filter',
                        label: 'Client',
                        value: clientFilter,
                        options: clientOptions,
                        onChange: (value) => {
                          setClientFilter(value)
                          setCurrentPage(1)
                        },
                      },
                    ]
                  : []),
              ],
              onClearFilters: () => {
                setSearchValue('')
                setStatusFilter('')
                setClientFilter('')
                setStartDateFilter('')
                setEndDateFilter('')
                setCurrentPage(1)
              },
            }}
            emptyMessage="No contracts found"
          />
        )}
      </div>
    </AppLayout>
  )
}
