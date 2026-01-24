/**
 * Activities List Page
 * Client interaction log with filters (type, date range, client) and search
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { activitiesApi } from '@/api/endpoints/activities'
import { clientsApi } from '@/api/endpoints/clients'
import type { Activity } from '@/types/entities'
import { Plus, Calendar, Phone, Mail, Users, FileText } from 'lucide-react'

export const Route = createFileRoute('/activities/')({
  component: ActivitiesPage,
})

const typeIcons: Record<string, typeof Phone> = {
  CALL: Phone,
  EMAIL: Mail,
  MEETING: Users,
  NOTE: FileText,
}

function ActivitiesPage() {
  const navigate = useNavigate()
  const [activities, setActivities] = useState<Activity[]>([])
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [clientFilter, setClientFilter] = useState<string>('')
  const [startDateFilter, setStartDateFilter] = useState<string>('')
  const [endDateFilter, setEndDateFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await clientsApi.list({ limit: 100 })
        setClients(res.items.map((c) => ({ id: c.id, name: c.name })))
      } catch (err) {
        console.error('Error fetching clients:', err)
      }
    }
    load()
  }, [])

  const fetchActivities = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, unknown> = {
        page: currentPage,
        limit: pageSize,
      }
      if (searchValue) params.search = searchValue
      if (typeFilter) params.activity_type = typeFilter
      if (clientFilter) params.client_id = clientFilter
      if (startDateFilter) params.date_from = startDateFilter
      if (endDateFilter) params.date_to = endDateFilter
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const res = await activitiesApi.list(params)
      setActivities(res.items)
      setTotalItems(res.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load activities'
      setError(msg)
      console.error('Error fetching activities:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchActivities()
  }, [currentPage, pageSize, searchValue, typeFilter, clientFilter, startDateFilter, endDateFilter, sortBy, sortDirection])

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

  const handleRowClick = (a: Activity) => navigate({ to: `/activities/${a.id}` })

  const typeOptions = [
    { value: '', label: 'All Types' },
    { value: 'CALL', label: 'Call' },
    { value: 'EMAIL', label: 'Email' },
    { value: 'MEETING', label: 'Meeting' },
    { value: 'NOTE', label: 'Note' },
  ]

  const clientOptions = [
    { value: '', label: 'All Clients' },
    ...clients.map((c) => ({ value: c.id, label: c.name })),
  ]

  const columns: Column<Activity>[] = [
    {
      id: 'occurred_at',
      header: 'Date',
      accessor: 'occurred_at',
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
      id: 'activity_type',
      header: 'Type',
      accessor: 'activity_type',
      sortable: true,
      render: (value) => {
        const Icon = typeIcons[(value as string) || 'NOTE'] ?? FileText
        return (
          <span className="flex items-center gap-2">
            <Icon size={16} />
            {(value as string) || '-'}
          </span>
        )
      },
    },
    {
      id: 'client_id',
      header: 'Client',
      accessor: 'client_id',
      sortable: true,
      render: (_, row) => {
        const c = clients.find((x) => x.id === row.client_id)
        return <span>{c?.name ?? row.client_id}</span>
      },
    },
    {
      id: 'title',
      header: 'Title',
      accessor: 'title',
      sortable: false,
      render: (value) => (
        <span className="text-safe-light text-sm line-clamp-2">{(value as string) || '-'}</span>
      ),
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
      sortable: false,
      render: (value) => (
        <span className="text-safe-light text-sm line-clamp-2">{(value as string) || '-'}</span>
      ),
    },
    {
      id: 'created_at',
      header: 'Created',
      accessor: 'created_at',
      sortable: true,
      render: (v) => (v ? new Date(v as string).toLocaleDateString() : '-'),
    },
  ]

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-safe">Activities</h1>
          <button
            onClick={() => navigate({ to: '/activities/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Log Activity</span>
          </button>
        </div>

        {loading && activities.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={activities}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchActivities}
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
              searchPlaceholder: 'Search activities...',
              dateRangeFilter: {
                startDate: startDateFilter,
                endDate: endDateFilter,
                onStartDateChange: (d) => {
                  setStartDateFilter(d)
                  setCurrentPage(1)
                },
                onEndDateChange: (d) => {
                  setEndDateFilter(d)
                  setCurrentPage(1)
                },
              },
              customFilters: [
                {
                  id: 'type-filter',
                  label: 'Type',
                  value: typeFilter,
                  options: typeOptions,
                  onChange: (v) => {
                    setTypeFilter(v)
                    setCurrentPage(1)
                  },
                },
                {
                  id: 'client-filter',
                  label: 'Client',
                  value: clientFilter,
                  options: clientOptions,
                  onChange: (v) => {
                    setClientFilter(v)
                    setCurrentPage(1)
                  },
                },
              ],
              onClearFilters: () => {
                setSearchValue('')
                setTypeFilter('')
                setClientFilter('')
                setStartDateFilter('')
                setEndDateFilter('')
                setCurrentPage(1)
              },
            }}
            emptyMessage="No activities found"
          />
        )}
      </div>
    </AppLayout>
  )
}
