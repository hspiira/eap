/**
 * Persons List Page
 * Displays all persons within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { personsApi } from '@/api/endpoints/persons'
import { clientsApi } from '@/api/endpoints/clients'
import type { Person } from '@/types/entities'
import type { BaseStatus, PersonType } from '@/types/enums'
import { Plus } from 'lucide-react'

export const Route = createFileRoute('/persons/')({
  component: PersonsPage,
})

function PersonsPage() {
  const navigate = useNavigate()
  const { showError } = useToast()
  const [persons, setPersons] = useState<Person[]>([])
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [personTypeFilter, setPersonTypeFilter] = useState<string>('')
  const [clientFilter, setClientFilter] = useState<string>('')
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

  // Fetch persons (tenant-scoped automatically via API client)
  const fetchPersons = async () => {
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

      if (personTypeFilter) {
        params.person_type = personTypeFilter
      }

      if (clientFilter) {
        params.client_id = clientFilter
      }

      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const response = await personsApi.list(params)
      setPersons(response.items)
      setTotalItems(response.total)
    } catch (error) {
      showError('Failed to load persons')
      console.error('Error fetching persons:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPersons()
  }, [currentPage, pageSize, searchValue, statusFilter, personTypeFilter, clientFilter, sortBy, sortDirection])

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

  const handleRowClick = (person: Person) => {
    navigate({ to: `/persons/${person.id}` })
  }

  const getFullName = (person: Person) => {
    const parts = [person.first_name]
    if (person.middle_name) parts.push(person.middle_name)
    parts.push(person.last_name)
    return parts.join(' ')
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Active', label: 'Active' },
    { value: 'Inactive', label: 'Inactive' },
    { value: 'Pending', label: 'Pending' },
    { value: 'Archived', label: 'Archived' },
  ]

  const personTypeOptions = [
    { value: '', label: 'All Types' },
    { value: 'ClientEmployee', label: 'Client Employee' },
    { value: 'Dependent', label: 'Dependent' },
    { value: 'ServiceProvider', label: 'Service Provider' },
    { value: 'PlatformStaff', label: 'Platform Staff' },
  ]

  const clientOptions = [
    { value: '', label: 'All Clients' },
    ...clients.map(c => ({ value: c.id, label: c.name })),
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
      id: 'person_type',
      header: 'Type',
      accessor: 'person_type',
      sortable: true,
      render: (value) => {
        const type = value as PersonType
        const labels: Record<PersonType, string> = {
          ClientEmployee: 'Employee',
          Dependent: 'Dependent',
          ServiceProvider: 'Provider',
          PlatformStaff: 'Staff',
        }
        return <span>{labels[type] || type}</span>
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

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-safe">Persons</h1>
          <button
            onClick={() => navigate({ to: '/persons/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Create Person</span>
          </button>
        </div>

        {loading && persons.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={persons}
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
              searchPlaceholder: 'Search persons by name...',
              statusFilter: {
                value: statusFilter,
                options: statusOptions,
                onChange: (value) => {
                  setStatusFilter(value)
                  setCurrentPage(1)
                },
              },
              customFilters: [
                {
                  id: 'person-type-filter',
                  label: 'Type',
                  value: personTypeFilter,
                  options: personTypeOptions,
                  onChange: (value) => {
                    setPersonTypeFilter(value)
                    setCurrentPage(1)
                  },
                },
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
                setPersonTypeFilter('')
                setClientFilter('')
                setCurrentPage(1)
              },
            }}
            emptyMessage="No persons found"
          />
        )}
      </div>
    </AppLayout>
  )
}
