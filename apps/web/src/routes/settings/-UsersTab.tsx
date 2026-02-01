import { useState, useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { CreateModal } from '@/components/common/CreateModal'
import { CreateUserForm } from '@/components/forms/CreateUserForm'
import { usersApi } from '@/api/endpoints/users'
import type { User } from '@/types/entities'
import type { UserStatus } from '@/types/enums'

export function UsersTab() {
  const navigate = useNavigate()
  const [users, setUsers] = useState<User[]>([])
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

  const fetchUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, unknown> = {
        page: currentPage,
        limit: pageSize,
      }
      if (searchValue) params.search = searchValue
      if (statusFilter) params.status = statusFilter
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }
      const response = await usersApi.list(params)
      setUsers(response.items)
      setTotalItems(response.total)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load users'
      setError(msg)
      console.error('Error fetching users:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [currentPage, pageSize, searchValue, statusFilter, sortBy, sortDirection])

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

  const handleRowClick = (user: User) => {
    navigate({ to: `/users/${user.id}` })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Active', label: 'Active' },
    { value: 'Suspended', label: 'Suspended' },
    { value: 'Banned', label: 'Banned' },
    { value: 'Terminated', label: 'Terminated' },
    { value: 'Pending Verification', label: 'Pending Verification' },
    { value: 'Inactive', label: 'Inactive' },
  ]

  const columns: Column<User>[] = [
    {
      id: 'email',
      header: 'Email',
      accessor: 'email',
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-primary hover:text-primary-dark font-medium"
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
      render: (value) => <StatusBadge status={value as UserStatus} size="sm" />,
    },
    {
      id: 'is_email_verified',
      header: 'Email Verified',
      accessor: 'is_email_verified',
      sortable: true,
      render: (value) => (
        <span className={value ? 'text-primary' : 'text-text-light'}>
          {value ? 'Yes' : 'No'}
        </span>
      ),
    },
    {
      id: 'is_two_factor_enabled',
      header: '2FA',
      accessor: 'is_two_factor_enabled',
      sortable: true,
      render: (value) => (
        <span className={value ? 'text-primary' : 'text-text-light'}>
          {value ? 'Enabled' : 'Disabled'}
        </span>
      ),
    },
    {
      id: 'last_login_at',
      header: 'Last Login',
      accessor: 'last_login_at',
      sortable: true,
      render: (value) => {
        if (!value) return <span className="text-text-light">Never</span>
        const date = new Date(value as string)
        return date.toLocaleDateString()
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
    <div className="space-y-0">
      <h2 className="text-sm font-semibold text-text mb-1.5">Users</h2>
      <p className="text-xs text-text-light mb-2">Users in your organization.</p>
      <DataTable
        data={users}
        columns={columns}
        loading={loading}
        error={error}
        onRetry={fetchUsers}
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
          searchPlaceholder: 'Search users by email...',
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
            label: 'Create User',
          },
        }}
        emptyMessage="No users found"
      />

      <CreateModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create User"
        loading={createLoading}
      >
        <CreateUserForm
          onSuccess={() => {
            setCreateModalOpen(false)
            fetchUsers()
          }}
          onCancel={() => setCreateModalOpen(false)}
          onLoadingChange={setCreateLoading}
        />
      </CreateModal>
    </div>
  )
}
