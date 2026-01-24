/**
 * Sessions List Page
 * Displays all service sessions within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { CreateModal } from '@/components/common/CreateModal'
import { CreateSessionForm } from '@/components/forms/CreateSessionForm'
import { serviceSessionsApi } from '@/api/endpoints/service-sessions'
import { personsApi } from '@/api/endpoints/persons'
import { servicesApi } from '@/api/endpoints/services'
import type { ServiceSession } from '@/types/entities'
import type { SessionStatus } from '@/types/enums'
import { Calendar } from 'lucide-react'

export const Route = createFileRoute('/sessions/')({
  component: SessionsPage,
})

function SessionsPage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<ServiceSession[]>([])
  const [persons, setPersons] = useState<Array<{ id: string; name: string }>>([])
  const [services, setServices] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [personFilter, setPersonFilter] = useState<string>('')
  const [serviceFilter, setServiceFilter] = useState<string>('')
  const [startDateFilter, setStartDateFilter] = useState<string>('')
  const [endDateFilter, setEndDateFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)

  // Fetch persons and services for filters
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [personsResponse, servicesResponse] = await Promise.all([
          personsApi.list({ limit: 100 }),
          servicesApi.list({ limit: 100 }),
        ])
        setPersons(personsResponse.items.map(p => ({ 
          id: p.id, 
          name: `${p.first_name} ${p.last_name}`.trim() 
        })))
        setServices(servicesResponse.items.map(s => ({ id: s.id, name: s.name })))
      } catch (error) {
        console.error('Error fetching filter data:', error)
      }
    }
    fetchData()
  }, [])

  // Fetch sessions (tenant-scoped automatically via API client)
  const fetchSessions = async () => {
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

      if (personFilter) {
        params.person_id = personFilter
      }

      if (serviceFilter) {
        params.service_id = serviceFilter
      }

      if (startDateFilter) {
        params.date_from = startDateFilter
      }

      if (endDateFilter) {
        params.date_to = endDateFilter
      }

      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const response = await serviceSessionsApi.list(params)
      setSessions(response.items)
      setTotalItems(response.total)
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load sessions'
      setError(errorMessage)
      console.error('Error fetching sessions:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [currentPage, pageSize, searchValue, statusFilter, personFilter, serviceFilter, startDateFilter, endDateFilter, sortBy, sortDirection])

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

  const handleRowClick = (session: ServiceSession) => {
    navigate({ to: `/sessions/${session.id}` })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Scheduled', label: 'Scheduled' },
    { value: 'Rescheduled', label: 'Rescheduled' },
    { value: 'Completed', label: 'Completed' },
    { value: 'Cancelled', label: 'Cancelled' },
    { value: 'No Show', label: 'No Show' },
  ]

  const personOptions = [
    { value: '', label: 'All Persons' },
    ...persons.map(p => ({ value: p.id, label: p.name })),
  ]

  const serviceOptions = [
    { value: '', label: 'All Services' },
    ...services.map(s => ({ value: s.id, label: s.name })),
  ]

  const columns: Column<ServiceSession>[] = [
    {
      id: 'scheduled_at',
      header: 'Scheduled',
      accessor: 'scheduled_at',
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-natural hover:text-natural-dark font-medium flex items-center gap-2"
        >
          <Calendar size={16} />
          {value ? new Date(value as string).toLocaleString() : '-'}
        </button>
      ),
    },
    {
      id: 'person_id',
      header: 'Person',
      accessor: 'person_id',
      sortable: true,
      render: (value, row) => {
        const person = persons.find(p => p.id === row.person_id)
        return <span>{person?.name || row.person_id}</span>
      },
    },
    {
      id: 'service_id',
      header: 'Service',
      accessor: 'service_id',
      sortable: true,
      render: (value, row) => {
        const service = services.find(s => s.id === row.service_id)
        return <span>{service?.name || row.service_id}</span>
      },
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      render: (value) => <StatusBadge status={value as SessionStatus} size="sm" />,
    },
    {
      id: 'location',
      header: 'Location',
      accessor: 'location',
      sortable: false,
      render: (value) => <span className="text-safe-light text-sm">{value || '-'}</span>,
    },
    {
      id: 'completed_at',
      header: 'Completed',
      accessor: 'completed_at',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        return new Date(value as string).toLocaleString()
      },
    },
  ]

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {loading && sessions.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={sessions}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchSessions}
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
              searchPlaceholder: 'Search sessions...',
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
                ...(persons.length > 0
                  ? [
                      {
                        id: 'person-filter',
                        label: 'Person',
                        value: personFilter,
                        options: personOptions,
                        onChange: (value) => {
                          setPersonFilter(value)
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
                        onChange: (value) => {
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
                setPersonFilter('')
                setServiceFilter('')
                setStartDateFilter('')
                setEndDateFilter('')
                setCurrentPage(1)
              },
              createAction: {
                onClick: () => setCreateModalOpen(true),
                label: 'Schedule Session',
              },
            }}
            emptyMessage="No sessions found"
          />
        )}

        <CreateModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Schedule Session"
          loading={createLoading}
        >
          <CreateSessionForm
            onSuccess={() => {
              setCreateModalOpen(false)
              fetchSessions()
            }}
            onCancel={() => setCreateModalOpen(false)}
            onLoadingChange={setCreateLoading}
          />
        </CreateModal>
      </div>
    </AppLayout>
  )
}
