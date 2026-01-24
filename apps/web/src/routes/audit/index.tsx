/**
 * Audit Logs List Page
 * Read-only audit log with DataTable, advanced filters (action, resource, user, date range), search
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { auditApi, type AuditListParams } from '@/api/endpoints/audit'
import { usersApi } from '@/api/endpoints/users'
import type { AuditLog } from '@/types/entities'
import { Calendar, User, FileText } from 'lucide-react'

export const Route = createFileRoute('/audit/')({
  component: AuditPage,
})

const ACTION_OPTIONS = [
  { value: '', label: 'All Actions' },
  { value: 'CREATE', label: 'Create' },
  { value: 'UPDATE', label: 'Update' },
  { value: 'DELETE', label: 'Delete' },
  { value: 'LOGIN', label: 'Login' },
  { value: 'LOGOUT', label: 'Logout' },
  { value: 'APPROVE', label: 'Approve' },
  { value: 'REJECT', label: 'Reject' },
  { value: 'LIST', label: 'List' },
  { value: 'VIEW', label: 'View' },
  { value: 'EXPORT', label: 'Export' },
  { value: 'IMPORT', label: 'Import' },
]

const RESOURCE_OPTIONS = [
  { value: '', label: 'All Resources' },
  { value: 'Person', label: 'Person' },
  { value: 'Client', label: 'Client' },
  { value: 'Contract', label: 'Contract' },
  { value: 'Service', label: 'Service' },
  { value: 'User', label: 'User' },
  { value: 'Document', label: 'Document' },
  { value: 'Contact', label: 'Contact' },
  { value: 'Activity', label: 'Activity' },
  { value: 'Industry', label: 'Industry' },
  { value: 'ClientTag', label: 'Client Tag' },
]

function AuditPage() {
  const navigate = useNavigate()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [users, setUsers] = useState<Array<{ id: string; email: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [actionFilter, setActionFilter] = useState('')
  const [resourceFilter, setResourceFilter] = useState('')
  const [userFilter, setUserFilter] = useState('')
  const [startDateFilter, setStartDateFilter] = useState('')
  const [endDateFilter, setEndDateFilter] = useState('')
  const [sortBy, setSortBy] = useState<string | null>('created_at')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>('desc')

  useEffect(() => {
    const load = async () => {
      try {
        const res = await usersApi.list({ limit: 200 })
        setUsers(res.items.map((u) => ({ id: u.id, email: u.email })))
      } catch (err) {
        console.error('Error fetching users:', err)
      }
    }
    load()
  }, [])

  const fetchLogs = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: AuditListParams = {
        page: currentPage,
        limit: pageSize,
      }
      if (searchValue) params.search = searchValue
      if (actionFilter) params.action_type = actionFilter
      if (resourceFilter) params.resource_type = resourceFilter
      if (userFilter) params.user_id = userFilter
      if (startDateFilter) params.date_from = startDateFilter
      if (endDateFilter) params.date_to = endDateFilter
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const res = await auditApi.list(params)
      setLogs(res.items)
      setTotalItems(res.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load audit logs'
      setError(msg)
      console.error('Error fetching audit logs:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [
    currentPage,
    pageSize,
    searchValue,
    actionFilter,
    resourceFilter,
    userFilter,
    startDateFilter,
    endDateFilter,
    sortBy,
    sortDirection,
  ])

  const handleSort = (columnId: string) => {
    if (sortBy === columnId) {
      if (sortDirection === 'asc') setSortDirection('desc')
      else if (sortDirection === 'desc') {
        setSortBy(null)
        setSortDirection(null)
      } else setSortDirection('asc')
    } else {
      setSortBy(columnId)
      setSortDirection('desc')
    }
  }

  const handleRowClick = (log: AuditLog) => navigate({ to: `/audit/${log.id}` })

  const userOptions = [
    { value: '', label: 'All Users' },
    ...users.map((u) => ({ value: u.id, label: u.email })),
  ]

  const columns: Column<AuditLog>[] = [
    {
      id: 'created_at',
      header: 'Time',
      accessor: 'created_at',
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-natural hover:text-natural-dark font-medium flex items-center gap-2"
        >
          <Calendar size={16} />
          {value ? new Date(value as string).toLocaleString() : '—'}
        </button>
      ),
    },
    {
      id: 'action_type',
      header: 'Action',
      accessor: 'action_type',
      sortable: true,
      render: (value) => (
        <span className="font-medium text-safe">{(value as string) || '—'}</span>
      ),
    },
    {
      id: 'resource_type',
      header: 'Resource',
      accessor: 'resource_type',
      sortable: true,
      render: (value) => (
        <span className="flex items-center gap-1">
          <FileText size={14} className="text-safe-light" />
          {(value as string) || '—'}
        </span>
      ),
    },
    {
      id: 'resource_id',
      header: 'Resource ID',
      accessor: 'resource_id',
      sortable: false,
      render: (value, row) => (
        <button
          onClick={() => navigate({ to: `/audit/entity/${row.resource_type}/${row.resource_id}` })}
          className="text-natural hover:text-natural-dark text-sm truncate max-w-[140px] block"
          title={value as string}
        >
          {(value as string) || '—'}
        </button>
      ),
    },
    {
      id: 'user_id',
      header: 'User',
      accessor: 'user_id',
      sortable: true,
      render: (value) => {
        const u = users.find((x) => x.id === value)
        return (
          <span className="flex items-center gap-1 text-safe-light text-sm">
            <User size={14} />
            {u?.email ?? (value as string) ?? '—'}
          </span>
        )
      },
    },
    {
      id: 'ip_address',
      header: 'IP',
      accessor: 'ip_address',
      sortable: false,
      render: (value) => (
        <span className="text-safe-light text-sm font-mono">{(value as string) || '—'}</span>
      ),
    },
  ]

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {loading && logs.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={logs}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchLogs}
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
              searchPlaceholder: 'Search audit logs...',
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
                  id: 'action-filter',
                  label: 'Action',
                  value: actionFilter,
                  options: ACTION_OPTIONS,
                  onChange: (v) => {
                    setActionFilter(v)
                    setCurrentPage(1)
                  },
                },
                {
                  id: 'resource-filter',
                  label: 'Resource',
                  value: resourceFilter,
                  options: RESOURCE_OPTIONS,
                  onChange: (v) => {
                    setResourceFilter(v)
                    setCurrentPage(1)
                  },
                },
                {
                  id: 'user-filter',
                  label: 'User',
                  value: userFilter,
                  options: userOptions,
                  onChange: (v) => {
                    setUserFilter(v)
                    setCurrentPage(1)
                  },
                },
              ],
              onClearFilters: () => {
                setSearchValue('')
                setActionFilter('')
                setResourceFilter('')
                setUserFilter('')
                setStartDateFilter('')
                setEndDateFilter('')
                setCurrentPage(1)
              },
            }}
            emptyMessage="No audit logs found"
          />
        )}
      </div>
    </AppLayout>
  )
}
