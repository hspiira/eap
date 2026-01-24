/**
 * Contacts List Page
 * Displays all contacts within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { contactsApi } from '@/api/endpoints/contacts'
import { clientsApi } from '@/api/endpoints/clients'
import type { Contact } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'
import { Plus, UserCircle, Star } from 'lucide-react'

export const Route = createFileRoute('/contacts/')({
  component: ContactsPage,
})

function ContactsPage() {
  const navigate = useNavigate()
  const [contacts, setContacts] = useState<Contact[]>([])
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [clientFilter, setClientFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const response = await clientsApi.list({ limit: 100 })
        setClients(response.items.map((c) => ({ id: c.id, name: c.name })))
      } catch (err) {
        console.error('Error fetching clients:', err)
      }
    }
    fetchClients()
  }, [])

  const fetchContacts = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, unknown> = {
        page: currentPage,
        limit: pageSize,
      }
      if (searchValue) params.search = searchValue
      if (statusFilter) params.status = statusFilter
      if (clientFilter) params.client_id = clientFilter
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const response = await contactsApi.list(params)
      setContacts(response.items)
      setTotalItems(response.total)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load contacts'
      setError(message)
      console.error('Error fetching contacts:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchContacts()
  }, [currentPage, pageSize, searchValue, statusFilter, clientFilter, sortBy, sortDirection])

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

  const handleRowClick = (contact: Contact) => {
    navigate({ to: `/contacts/${contact.id}` })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Active', label: 'Active' },
    { value: 'Inactive', label: 'Inactive' },
    { value: 'Pending', label: 'Pending' },
    { value: 'Archived', label: 'Archived' },
    { value: 'Deleted', label: 'Deleted' },
  ]

  const clientOptions = [
    { value: '', label: 'All Clients' },
    ...clients.map((c) => ({ value: c.id, label: c.name })),
  ]

  const columns: Column<Contact>[] = [
    {
      id: 'name',
      header: 'Name',
      accessor: 'first_name',
      sortable: true,
      render: (_, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-natural hover:text-natural-dark font-medium flex items-center gap-2"
        >
          <UserCircle size={16} />
          {`${row.first_name} ${row.last_name}`.trim()}
          {row.is_primary && (
            <Star size={14} className="text-natural" fill="currentColor" title="Primary contact" />
          )}
        </button>
      ),
    },
    {
      id: 'client_id',
      header: 'Client',
      accessor: 'client_id',
      sortable: true,
      render: (value, row) => {
        const client = clients.find((c) => c.id === row.client_id)
        return <span>{client?.name ?? (value as string)}</span>
      },
    },
    {
      id: 'title',
      header: 'Title',
      accessor: 'title',
      sortable: true,
      render: (value) => <span className="text-safe-light text-sm">{(value as string) || '-'}</span>,
    },
    {
      id: 'contact_info',
      header: 'Email',
      accessor: 'contact_info',
      sortable: false,
      render: (value) => (
        <span className="text-safe-light text-sm">
          {value && typeof value === 'object' && 'email' in value && (value as { email?: string }).email
            ? (value as { email?: string }).email
            : '-'}
        </span>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      render: (value) => <StatusBadge status={(value as BaseStatus) ?? 'Active'} size="sm" />,
    },
    {
      id: 'created_at',
      header: 'Created',
      accessor: 'created_at',
      sortable: true,
      render: (value) =>
        value ? new Date(value as string).toLocaleDateString() : '-',
    },
  ]

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-safe">Contacts</h1>
          <button
            onClick={() => navigate({ to: '/contacts/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Create Contact</span>
          </button>
        </div>

        {loading && contacts.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={contacts}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchContacts}
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
              onSearchChange: (v) => {
                setSearchValue(v)
                setCurrentPage(1)
              },
              searchPlaceholder: 'Search contacts by name...',
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
                setStatusFilter('')
                setClientFilter('')
                setCurrentPage(1)
              },
            }}
            emptyMessage="No contacts found"
          />
        )}
      </div>
    </AppLayout>
  )
}
