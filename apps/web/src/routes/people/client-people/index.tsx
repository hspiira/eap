/**
 * Roster List Page
 * Employees + Dependents only. PlatformStaff excluded (users). ServiceProvider → /service-providers.
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { CreatePersonModal } from '@/components/forms/CreatePersonModal'
import { personsApi } from '@/api/endpoints/persons'
import { clientsApi } from '@/api/endpoints/clients'
import type { Person } from '@/types/entities'
import { PersonType } from '@/types/enums'
import type { BaseStatus } from '@/types/enums'

const ALLOWED_TYPES: PersonType[] = [PersonType.CLIENT_EMPLOYEE, PersonType.DEPENDENT]

export const Route = createFileRoute('/people/client-people/')({
  component: ClientPeoplePage,
})

function ClientPeoplePage() {
  const navigate = useNavigate()
  const [persons, setPersons] = useState<Person[]>([])
  const [allEmployees, setAllEmployees] = useState<Person[]>([]) // For looking up primary employees
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [personTypeFilter, setPersonTypeFilter] = useState<string>('ClientEmployee')
  const [clientFilter, setClientFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const res = await clientsApi.list({ limit: 100 })
        setClients(res.items.map((c) => ({ id: c.id, name: c.name })))
      } catch (err) {
        console.error('Error fetching clients:', err)
      }
    }
    fetchClients()
  }, [])

  const fetchPersons = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, unknown> = {
        page: currentPage,
        limit: pageSize,
      }
      if (searchValue) params.search = searchValue
      if (statusFilter) params.status = statusFilter
      if (personTypeFilter) params.person_type = personTypeFilter
      if (clientFilter) params.client_id = clientFilter
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const res = await personsApi.list(params)
      const filtered = res.items.filter((p) =>
        ALLOWED_TYPES.includes(p.person_type as PersonType)
      )
      setPersons(filtered)
      setTotalItems(res.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load roster'
      setError(msg)
      console.error('Error fetching roster:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPersons()
  }, [currentPage, pageSize, searchValue, statusFilter, personTypeFilter, clientFilter, sortBy, sortDirection])

  // Fetch all employees when we need to display dependents (for looking up primary employees)
  useEffect(() => {
    const fetchEmployees = async () => {
      // Only fetch if we're showing dependents or all types
      if (personTypeFilter === 'Dependent' || !personTypeFilter) {
        try {
          const params: Record<string, unknown> = {
            person_type: 'ClientEmployee',
            limit: 500, // Get a reasonable number
          }
          if (clientFilter) params.client_id = clientFilter
          const res = await personsApi.list(params)
          setAllEmployees(res.items.filter((p) => p.person_type === 'ClientEmployee'))
        } catch (err) {
          console.error('Error fetching employees for lookup:', err)
          setAllEmployees([])
        }
      } else {
        setAllEmployees([])
      }
    }
    fetchEmployees()
  }, [personTypeFilter, clientFilter])

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

  const personTypeOptions = [
    { value: 'ClientEmployee', label: 'Employee' },
    { value: 'Dependent', label: 'Dependent' },
  ]

  const clientOptions = [
    { value: '', label: 'All Clients' },
    ...clients.map((c) => ({ value: c.id, label: c.name })),
  ]

  const typeLabels: Record<string, string> = {
    ClientEmployee: 'Employee',
    Dependent: 'Dependent',
  }

  const columns: Column<Person>[] = [
    {
      id: 'name',
      header: 'Name',
      accessor: (row) => getFullName(row),
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-primary hover:text-primary-hover font-medium"
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
      render: (value) => <span>{typeLabels[value as string] ?? value}</span>,
    },
    {
      id: 'employee_code',
      header: 'Employee Code',
      accessor: 'employment_info',
      sortable: false,
      render: (value, row) => {
        if (row.person_type !== 'ClientEmployee') return '—'
        const empInfo = value as Person['employment_info']
        return <span className="text-text">{empInfo?.employee_code || '—'}</span>
      },
    },
    {
      id: 'dependent_of',
      header: 'Dependent of',
      accessor: 'dependent_info',
      sortable: false,
      render: (value, row) => {
        if (row.person_type !== 'Dependent') return '—'
        const depInfo = value as Person['dependent_info']
        if (!depInfo?.primary_employee_id) return '—'
        const primary = allEmployees.find((p) => p.id === depInfo.primary_employee_id)
        if (!primary) return <span className="text-text-muted">{depInfo.primary_employee_id.slice(0, 8)}...</span>
        const name = getFullName(primary)
        return (
          <button
            onClick={() => handleRowClick(primary)}
            className="text-left text-primary hover:text-primary-hover font-medium"
          >
            {name}
          </button>
        )
      },
    },
    {
      id: 'relationship',
      header: 'Relationship',
      accessor: 'dependent_info',
      sortable: false,
      render: (value, row) => {
        if (row.person_type !== 'Dependent') return '—'
        const depInfo = value as Person['dependent_info']
        return <span className="text-text">{depInfo?.relationship || '—'}</span>
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
      id: 'client_id',
      header: 'Client',
      accessor: 'client_id',
      sortable: false,
      render: (_, row) => {
        const c = clients.find((x) => x.id === row.client_id)
        return <span>{c?.name ?? row.client_id ?? '—'}</span>
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
          <span className="text-text-muted">—</span>
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
        <DataTable
          data={persons}
          columns={columns}
          loading={loading}
          error={error}
          onRetry={fetchPersons}
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
            searchPlaceholder: 'Search by name...',
            statusFilter: {
              value: statusFilter,
              options: statusOptions,
              onChange: (v) => {
                setStatusFilter(v)
                setCurrentPage(1)
              },
            },
            customFilters: [
              {
                id: 'person-type-filter',
                label: 'Type',
                value: personTypeFilter,
                options: personTypeOptions,
                onChange: (v) => {
                  setPersonTypeFilter(v)
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
                      onChange: (v: string) => {
                        setClientFilter(v)
                        setCurrentPage(1)
                      },
                    },
                  ]
                : []),
            ],
            onClearFilters: () => {
              setSearchValue('')
              setStatusFilter('')
              setPersonTypeFilter('ClientEmployee')
              setClientFilter('')
              setCurrentPage(1)
            },
            createAction: {
              onClick: () => setCreateModalOpen(true),
              label: 'Add person',
            },
          }}
          emptyMessage="No people in roster"
        />
      </div>

      <CreatePersonModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreated={() => fetchPersons()}
      />
    </AppLayout>
  )
}
