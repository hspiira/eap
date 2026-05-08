/**
 * Tree-aware diagnosis combobox. Searches `/v1/diagnoses` (or fixture) by code/label
 * and lets the user drill into the hierarchy.
 *
 * Props mirror a controlled input: `value` is the selected diagnosis id; `onChange`
 * fires with `(id, diagnosis)`. The full path is rendered for context.
 */

import { useEffect, useId, useMemo, useRef, useState } from 'react'

import { useQuery } from '@tanstack/react-query'
import { Check, ChevronDown, ChevronRight, Search } from 'lucide-react'

import { diagnosesApi } from '@/api/endpoints/diagnoses'
import { Input } from '@/components/ui/input'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { cn } from '@/lib/utils'
import type { Diagnosis } from '@/types/entities'

export interface DiagnosisSelectorProps {
  value: string | null | undefined
  onChange: (id: string | null, diagnosis: Diagnosis | null) => void
  disabled?: boolean
  placeholder?: string
  /** Show the full path of the selected node next to the trigger button. */
  showPath?: boolean
  /** Restrict to leaves (deepest level codes). Default: false (any node selectable). */
  leavesOnly?: boolean
}

export function DiagnosisSelector({
  value,
  onChange,
  disabled,
  placeholder = 'Select diagnosis',
  showPath = true,
  leavesOnly = false,
}: DiagnosisSelectorProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const debouncedSearch = useDebouncedValue(search.trim(), 200)
  const containerRef = useRef<HTMLDivElement>(null)
  const buttonId = useId()

  useEffect(() => {
    if (!open) return
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  const selectedQuery = useQuery({
    queryKey: ['diagnoses', 'detail', value ?? ''],
    queryFn: () => diagnosesApi.getById(value as string),
    enabled: !!value,
    staleTime: 60_000,
  })

  const rootsQuery = useQuery({
    queryKey: ['diagnoses', 'list', { parent_id: null }],
    queryFn: () => diagnosesApi.list({ parent_id: null, limit: 200 }),
    staleTime: 60_000,
  })

  const searchQuery = useQuery({
    queryKey: ['diagnoses', 'search', debouncedSearch],
    queryFn: () => diagnosesApi.list({ search: debouncedSearch, limit: 50 }),
    enabled: debouncedSearch.length >= 2,
    staleTime: 30_000,
  })

  const isSearching = debouncedSearch.length >= 2

  const handleSelect = (d: Diagnosis) => {
    if (leavesOnly && d.has_children) {
      const next = new Set(expanded)
      if (next.has(d.id)) next.delete(d.id)
      else next.add(d.id)
      setExpanded(next)
      return
    }
    onChange(d.id, d)
    setOpen(false)
    setSearch('')
  }

  const triggerLabel = useMemo(() => {
    if (selectedQuery.data) return selectedQuery.data.code + ' — ' + selectedQuery.data.label
    if (value && selectedQuery.isPending) return 'Loading…'
    return placeholder
  }, [selectedQuery.data, selectedQuery.isPending, value, placeholder])

  return (
    <div ref={containerRef} className="relative">
      <button
        id={buttonId}
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className={cn(
          'flex w-full items-center justify-between gap-2 border border-fg/30 bg-white px-3 py-2 text-left text-sm text-fg rounded-none',
          'focus:outline-none focus:ring-1 focus:ring-natural disabled:opacity-50',
          !value && 'text-fg/60',
        )}
      >
        <span className="min-w-0 truncate">{triggerLabel}</span>
        <ChevronDown className="h-4 w-4 shrink-0 text-fg/60" />
      </button>

      {showPath && selectedQuery.data && (
        <p className="mt-1 text-xs text-fg/60">{selectedQuery.data.path}</p>
      )}

      {open && (
        <div
          className="absolute z-20 mt-1 w-full max-h-80 overflow-auto border border-fg/30 bg-white shadow-lg rounded-none"
          role="listbox"
        >
          <div className="sticky top-0 border-b border-fg/15 bg-white p-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-fg/60" />
              <Input
                placeholder="Search diagnoses..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="rounded-none h-8 pl-8 pr-3 border-fg/20"
                autoFocus
              />
            </div>
          </div>

          {isSearching ? (
            <SearchResults
              data={searchQuery.data?.items ?? []}
              loading={searchQuery.isPending}
              onSelect={handleSelect}
              selectedId={value ?? null}
              leavesOnly={leavesOnly}
            />
          ) : (
            <TreeView
              roots={rootsQuery.data?.items ?? []}
              loadingRoots={rootsQuery.isPending}
              expanded={expanded}
              onToggle={(id) => {
                const next = new Set(expanded)
                if (next.has(id)) next.delete(id)
                else next.add(id)
                setExpanded(next)
              }}
              onSelect={handleSelect}
              selectedId={value ?? null}
              leavesOnly={leavesOnly}
            />
          )}
        </div>
      )}
    </div>
  )
}

function SearchResults({
  data,
  loading,
  onSelect,
  selectedId,
  leavesOnly,
}: {
  data: Diagnosis[]
  loading: boolean
  onSelect: (d: Diagnosis) => void
  selectedId: string | null
  leavesOnly: boolean
}) {
  if (loading) return <p className="p-3 text-sm text-fg/60">Searching…</p>
  if (data.length === 0) return <p className="p-3 text-sm text-fg/60">No matches.</p>

  return (
    <ul className="p-1">
      {data.map((d) => (
        <li key={d.id}>
          <button
            type="button"
            disabled={leavesOnly && d.has_children}
            onClick={() => onSelect(d)}
            className={cn(
              'flex w-full items-start gap-2 px-2 py-1.5 text-left text-sm text-fg rounded-none hover:bg-surface/50 disabled:cursor-not-allowed disabled:opacity-50',
              d.id === selectedId && 'bg-primary/10',
            )}
          >
            <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center">
              {d.id === selectedId ? <Check className="h-4 w-4 text-primary" /> : null}
            </span>
            <span className="min-w-0 flex-1">
              <span className="font-medium text-fg">
                {d.code} <span className="font-normal">— {d.label}</span>
              </span>
              <span className="block text-xs text-fg/60">{d.path}</span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}

function TreeView({
  roots,
  loadingRoots,
  expanded,
  onToggle,
  onSelect,
  selectedId,
  leavesOnly,
}: {
  roots: Diagnosis[]
  loadingRoots: boolean
  expanded: Set<string>
  onToggle: (id: string) => void
  onSelect: (d: Diagnosis) => void
  selectedId: string | null
  leavesOnly: boolean
}) {
  if (loadingRoots) return <p className="p-3 text-sm text-fg/60">Loading…</p>
  if (roots.length === 0) return <p className="p-3 text-sm text-fg/60">No diagnoses available.</p>

  return (
    <ul className="p-1">
      {roots.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          expanded={expanded}
          onToggle={onToggle}
          onSelect={onSelect}
          selectedId={selectedId}
          leavesOnly={leavesOnly}
        />
      ))}
    </ul>
  )
}

function TreeNode({
  node,
  expanded,
  onToggle,
  onSelect,
  selectedId,
  leavesOnly,
}: {
  node: Diagnosis
  expanded: Set<string>
  onToggle: (id: string) => void
  onSelect: (d: Diagnosis) => void
  selectedId: string | null
  leavesOnly: boolean
}) {
  const isExpanded = expanded.has(node.id)
  const childrenQuery = useQuery({
    queryKey: ['diagnoses', 'list', { parent_id: node.id }],
    queryFn: () => diagnosesApi.list({ parent_id: node.id, limit: 200 }),
    enabled: isExpanded && node.has_children,
    staleTime: 60_000,
  })

  const indent = node.level * 12
  const selectable = !(leavesOnly && node.has_children)

  return (
    <li>
      <div className="flex items-stretch">
        {node.has_children ? (
          <button
            type="button"
            onClick={() => onToggle(node.id)}
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
            className="flex h-8 w-6 shrink-0 items-center justify-center text-fg/60 hover:text-fg"
            style={{ marginLeft: indent }}
          >
            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        ) : (
          <span className="h-8 w-6 shrink-0" style={{ marginLeft: indent }} />
        )}
        <button
          type="button"
          disabled={!selectable}
          onClick={() => onSelect(node)}
          className={cn(
            'flex flex-1 items-center gap-2 px-2 py-1 text-left text-sm text-fg rounded-none hover:bg-surface/50 disabled:cursor-not-allowed disabled:text-fg/60',
            node.id === selectedId && 'bg-primary/10',
          )}
        >
          <span className="font-medium">{node.code}</span>
          <span className="text-fg/80">{node.label}</span>
          {node.id === selectedId && <Check className="ml-auto h-4 w-4 text-primary" />}
        </button>
      </div>
      {isExpanded && childrenQuery.data?.items && (
        <ul>
          {childrenQuery.data.items.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              expanded={expanded}
              onToggle={onToggle}
              onSelect={onSelect}
              selectedId={selectedId}
              leavesOnly={leavesOnly}
            />
          ))}
        </ul>
      )}
    </li>
  )
}
