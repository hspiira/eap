/**
 * KPIs List Page
 * Displays all KPIs within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { kpisApi } from '@/api/endpoints/kpis'
import type { KPI } from '@/types/entities'
import { Plus, Target } from 'lucide-react'

export const Route = createFileRoute('/kpis/')({
  component: KPIsPage,
})

function KPIsPage() {
  const navigate = useNavigate()

  const [kpis, setKpis] = useState<KPI[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)

  // Fetch KPIs (tenant-scoped automatically via API client)
  const fetchKPIs = async () => {
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

      if (categoryFilter) {
        params.category = categoryFilter
      }

      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const response = await kpisApi.list(params)
      setKpis(response.items)
      setTotalItems(response.total)
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load KPIs'
      setError(errorMessage)
      console.error('Error fetching KPIs:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchKPIs()
  }, [currentPage, pageSize, searchValue, categoryFilter, sortBy, sortDirection])

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

  const handleRowClick = (kpi: KPI) => {
    navigate({ to: `/kpis/${kpi.id}` })
  }

  const categoryOptions = [
    { value: '', label: 'All Categories' },
    { value: 'Utilization', label: 'Utilization' },
    { value: 'Satisfaction', label: 'Satisfaction' },
    { value: 'Outcome', label: 'Outcome' },
    { value: 'Operational', label: 'Operational' },
  ]

  const formatValue = (value: number | null | undefined, unit: string) => {
    if (value === null || value === undefined) return '-'
    switch (unit) {
      case 'Percentage':
        return `${value}%`
      case 'Currency':
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
      case 'Time':
        return `${value} min`
      default:
        return value.toString()
    }
  }

  const getProgressPercentage = (current: number | null | undefined, target: number | null | undefined) => {
    if (!current || !target || target === 0) return null
    return Math.min((current / target) * 100, 100)
  }

  const columns: Column<KPI>[] = [
    {
      id: 'name',
      header: 'KPI Name',
      accessor: 'name',
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-natural hover:text-natural-dark font-medium flex items-center gap-2"
        >
          <Target size={16} />
          {value as string}
        </button>
      ),
    },
    {
      id: 'category',
      header: 'Category',
      accessor: 'category',
      sortable: true,
      render: (value) => <span>{value as string}</span>,
    },
    {
      id: 'measurement_unit',
      header: 'Unit',
      accessor: 'measurement_unit',
      sortable: true,
      render: (value) => <span className="text-safe-light text-sm">{value as string}</span>,
    },
    {
      id: 'target_value',
      header: 'Target',
      accessor: 'target_value',
      sortable: true,
      render: (value, row) => (
        <span>{formatValue(value as number, row.measurement_unit)}</span>
      ),
    },
    {
      id: 'current_value',
      header: 'Current',
      accessor: 'current_value',
      sortable: true,
      render: (value, row) => {
        const current = value as number | null | undefined
        const target = row.target_value
        const progress = getProgressPercentage(current, target)
        
        return (
          <div className="flex items-center gap-2">
            <span>{formatValue(current, row.measurement_unit)}</span>
            {progress !== null && (
              <div className="w-16 h-2 bg-safe-light rounded-full overflow-hidden">
                <div
                  className={`h-full ${
                    progress >= 100 ? 'bg-natural' : progress >= 75 ? 'bg-safe' : 'bg-nurturing'
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            )}
          </div>
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
          <h1 className="text-3xl font-bold text-safe">KPIs</h1>
          <button
            onClick={() => navigate({ to: '/kpis/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Create KPI</span>
          </button>
        </div>

        {loading && kpis.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={kpis}
            columns={columns}
            loading={loading}
            error={error}
            onRetry={fetchKPIs}
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
              searchPlaceholder: 'Search KPIs by name...',
              customFilters: [
                {
                  id: 'category-filter',
                  label: 'Category',
                  value: categoryFilter,
                  options: categoryOptions,
                  onChange: (value) => {
                    setCategoryFilter(value)
                    setCurrentPage(1)
                  },
                },
              ],
              onClearFilters: () => {
                setSearchValue('')
                setCategoryFilter('')
                setCurrentPage(1)
              },
            }}
            emptyMessage="No KPIs found"
          />
        )}
      </div>
    </AppLayout>
  )
}
