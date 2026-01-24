/**
 * Service Providers List Page
 * ServiceProvider only. PlatformStaff excluded (users). Client people → /people/client-people.
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { personsApi } from '@/api/endpoints/persons'
import type { Person } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'
import { Plus } from 'lucide-react'

export const Route = createFileRoute('/service-providers/')({
  component: ServiceProvidersPage,
})

function ServiceProvidersPage() {
  const navigate = useNavigate()
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)

  const fetchProviders = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, unknown> = {
        page: currentPage,
        limit: pageSize,
        person_type: 'ServiceProvider',
      }
      if (searchValue) params.search = searchValue
      if (statusFilter) params.status = statusFilter
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const res = await personsApi.list(params)
      setPersons(res.items.filter((p) => p.person_type === 'ServiceProvider'))
      setTotalItems(res.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load service providers'
      setError(msg)
      console.error('Error fetching service providers:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProviders()
  }, [currentPage, pageSize, searchValue, statusFilter, sortBy, sortDirection])

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

  const handleRowClick = (person: Person) => navigate({ to: `/persons/${person.id}` })

  const getFullName = (p: Person) => {
    const parts = [p.first_name]
    if (p.middle_name) parts.push(p.middle_name)
    parts.push(p.last_name)
    return parts.join(' ')
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Active', label: 'Active' },
    { value: 'Inactive', label: 'Inactive' },
    { value: 'Pending', label: 'Pending' },
    { value: 'Archived', label: 'Archived' },
  ]

  const columns: Column<Person>[] = [
    {
      id: 'name',
      header: 'Name',
      accessor: (row) => getFullName(row),
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
      id: 'license_info',
      header: 'License',
      accessor: 'license_info',
      render: (value) => {
        const lic = value as Person['license_info']
        return lic?.license_number ? (
          <span className="text-safe-light text-sm">{lic.license_type ? `${lic.license_type} · ` : ''}{lic.license_number}</span>
        ) : (
          <span className="text-safe-light">—</span>
        )
      },
    },
    {
      id: 'contact_info',
      header: 'Contact',
      accessor: 'contact_info',
      render: (value) => {
        const contact = value as Person['contact_info']
        return contact?.email ? (
          <span>{contact.email}</span>
        ) : contact?.phone ? (
          <span>{contact.phone}</span>
        ) : (
          <span className="text-safe-light">—</span>
        )
      },
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
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-safe">Service providers</h1>
          <button
            onClick={() => navigate({ to: '/service-providers/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Add provider</span>
          </button>
        </div>

        <DataTable
          data={persons}
          columns={columns}
          loading={loading}
          error={error}
          onRetry={fetchProviders}
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
            searchPlaceholder: 'Search providers...',
            statusFilter: {
              value: statusFilter,
              options: statusOptions,
              onChange: (v) => {
                setStatusFilter(v)
                setCurrentPage(1)
              },
            },
            onClearFilters: () => {
              setSearchValue('')
              setStatusFilter('')
              setCurrentPage(1)
            },
          }}
          emptyMessage="No service providers found"
        />
      </div>
    </AppLayout>
  )
}
