/**
 * Service Assignments List Page
 * Displays all service assignments within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { serviceAssignmentsApi } from '@/api/endpoints/service-assignments'
import { contractsApi } from '@/api/endpoints/contracts'
import { servicesApi } from '@/api/endpoints/services'
import type { ServiceAssignment } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'
import { Plus } from 'lucide-react'

export const Route = createFileRoute('/service-assignments/')({
  component: ServiceAssignmentsPage,
})

function ServiceAssignmentsPage() {
  const navigate = useNavigate()
  const [assignments, setAssignments] = useState<ServiceAssignment[]>([])
  const [contracts, setContracts] = useState<Array<{ id: string; name: string }>>([])
  const [services, setServices] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [contractFilter, setContractFilter] = useState<string>('')
  const [serviceFilter, setServiceFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)

  // Fetch contracts and services for filters
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [contractsResponse, servicesResponse] = await Promise.all([
          contractsApi.list({ limit: 100 }),
          servicesApi.list({ limit: 100 }),
        ])
        setContracts(contractsResponse.items.map(c => ({ 
          id: c.id, 
          name: c.contract_number || `Contract #${c.id.slice(0, 8)}` 
        })))
        setServices(servicesResponse.items.map(s => ({ id: s.id, name: s.name })))
      } catch (error) {
        console.error('Error fetching filter data:', error)
      }
    }
    fetchData()
  }, [])

  // Fetch assignments (tenant-scoped automatically via API client)
  const fetchAssignments = async () => {
    try {
      setLoading(true)
      setError(null)
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

      if (contractFilter) {
        params.contract_id = contractFilter
      }

      if (serviceFilter) {
        params.service_id = serviceFilter
      }

      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const response = await serviceAssignmentsApi.list(params)
      setAssignments(response.items)
      setTotalItems(response.total)
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load service assignments'
      setError(errorMessage)
      console.error('Error fetching assignments:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAssignments()
  }, [currentPage, pageSize, searchValue, statusFilter, contractFilter, serviceFilter, sortBy, sortDirection])

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

  const handleRowClick = (assignment: ServiceAssignment) => {
    navigate({ to: `/service-assignments/${assignment.id}` })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Active', label: 'Active' },
    { value: 'Inactive', label: 'Inactive' },
    { value: 'Pending', label: 'Pending' },
    { value: 'Archived', label: 'Archived' },
    { value: 'Deleted', label: 'Deleted' },
  ]

  const contractOptions = [
    { value: '', label: 'All Contracts' },
    ...contracts.map(c => ({ value: c.id, label: c.name })),
  ]

  const serviceOptions = [
    { value: '', label: 'All Services' },
    ...services.map(s => ({ value: s.id, label: s.name })),
  ]

  const columns: Column<ServiceAssignment>[] = [
    {
      id: 'contract_id',
      header: 'Contract',
      accessor: 'contract_id',
      sortable: true,
      render: (_value, row) => {
        const contract = contracts.find(c => c.id === row.contract_id)
        return (
          <button
            onClick={() => handleRowClick(row)}
            className="text-left text-natural hover:text-natural-dark font-medium"
          >
            {contract?.name || row.contract_id}
          </button>
        )
      },
    },
    {
      id: 'service_id',
      header: 'Service',
      accessor: 'service_id',
      sortable: true,
      render: (_value, row) => {
        const service = services.find(s => s.id === row.service_id)
        return <span>{service?.name || row.service_id}</span>
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
      id: 'start_date',
      header: 'Start Date',
      accessor: 'start_date',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        return new Date(value as string).toLocaleDateString()
      },
    },
    {
      id: 'end_date',
      header: 'End Date',
      accessor: 'end_date',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        return new Date(value as string).toLocaleDateString()
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
          <h1 className="text-3xl font-bold text-safe">Service Assignments</h1>
          <button
            onClick={() => navigate({ to: '/service-assignments/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Create Assignment</span>
          </button>
        </div>

        {loading && assignments.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={assignments}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchAssignments}
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
              searchPlaceholder: 'Search assignments...',
              statusFilter: {
                value: statusFilter,
                options: statusOptions,
                onChange: (value) => {
                  setStatusFilter(value)
                  setCurrentPage(1)
                },
              },
              customFilters: [
                ...(contracts.length > 0
                  ? [
                      {
                        id: 'contract-filter',
                        label: 'Contract',
                        value: contractFilter,
                        options: contractOptions,
                        onChange: (value: string) => {
                          setContractFilter(value)
                          setCurrentPage(1)
                        },
                      },
                    ]
                  : []),
                ...(services.length > 0
                  ? [
                      {
                        id: 'service-filter',
                        label: 'Service',
                        value: serviceFilter,
                        options: serviceOptions,
                        onChange: (value: string) => {
                          setServiceFilter(value)
                          setCurrentPage(1)
                        },
                      },
                    ]
                  : []),
              ],
              onClearFilters: () => {
                setSearchValue('')
                setStatusFilter('')
                setContractFilter('')
                setServiceFilter('')
                setCurrentPage(1)
              },
            }}
            emptyMessage="No service assignments found"
          />
        )}
      </div>
    </AppLayout>
  )
}
