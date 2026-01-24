/**
 * Industries List Page
 * Hierarchical industry tree with search and filters
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect, useMemo } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { IndustryTree } from '@/components/common/IndustryTree'
import { TableFilters } from '@/components/common/TableFilters'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { industriesApi } from '@/api/endpoints/industries'
import type { Industry } from '@/types/entities'
import { Plus } from 'lucide-react'

export const Route = createFileRoute('/industries/')({
  component: IndustriesPage,
})

function IndustriesPage() {
  const navigate = useNavigate()
  const [industries, setIndustries] = useState<Industry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchValue, setSearchValue] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const fetchIndustries = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await industriesApi.list({ limit: 500 })
      setIndustries(res.items)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load industries'
      setError(msg)
      console.error('Error fetching industries:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIndustries()
  }, [])

  const filtered = useMemo(() => {
    if (!searchValue.trim()) return industries
    const q = searchValue.trim().toLowerCase()
    const matches = industries.filter(
      (i) =>
        (i.name ?? '').toLowerCase().includes(q) ||
        (i.code ?? '').toLowerCase().includes(q)
    )
    const ancestorIds = new Set<string>()
    for (const m of matches) {
      let pid: string | null | undefined = m.parent_id
      while (pid) {
        ancestorIds.add(pid)
        const parent = industries.find((i) => i.id === pid)
        pid = parent?.parent_id
      }
    }
    return industries.filter(
      (i) => matches.some((m) => m.id === i.id) || ancestorIds.has(i.id)
    )
  }, [industries, searchValue])

  const handleSelect = (industry: Industry) => {
    setSelectedId(industry.id)
    navigate({ to: `/industries/${industry.id}` })
  }

  const hasActiveFilters = !!searchValue.trim()

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-safe">Industries</h1>
          <button
            onClick={() => navigate({ to: '/industries/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Add Industry</span>
          </button>
        </div>

        <TableFilters
          searchValue={searchValue}
          onSearchChange={(v) => setSearchValue(v)}
          searchPlaceholder="Search by name or code..."
          onClearFilters={() => {
            setSearchValue('')
          }}
          className="mb-4"
        />

        {loading ? (
          <div className="flex items-center justify-center p-12 border border-[0.5px] border-safe bg-calm">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <div className="border border-[0.5px] border-safe bg-calm px-4 py-12 text-center">
            <p className="text-nurturing font-medium mb-2">Error loading industries</p>
            <p className="text-safe-light text-sm mb-4">{error}</p>
            <button
              onClick={fetchIndustries}
              className="px-4 py-2 bg-natural hover:bg-natural-dark text-white text-sm rounded-none"
            >
              Retry
            </button>
          </div>
        ) : (
          <IndustryTree
            industries={filtered}
            onSelect={handleSelect}
            selectedId={selectedId}
            emptyMessage={hasActiveFilters ? 'No industries match your search' : 'No industries yet'}
          />
        )}
      </div>
    </AppLayout>
  )
}
