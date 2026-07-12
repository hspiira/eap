/**
 * Two-level diagnosis combobox.
 *
 * Default view: collapsible type groups (ICD-10 categories) with diagnoses nested
 * within. Search mode (≥2 chars): flat list filtered by code or name across all
 * types. Recently-used codes pinned at the top (up to 5, persisted in localStorage).
 *
 * Props are a controlled input: `value` is the selected diagnosis id; `onChange`
 * fires with (id, diagnosis). Pass null to clear.
 */

import { useEffect, useId, useMemo, useRef, useState } from 'react'

import { useQuery } from '@tanstack/react-query'
import { Check, ChevronDown, ChevronRight, Clock, Search } from 'lucide-react'

import { diagnosesApi } from '@/api/endpoints/diagnoses'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { cn } from '@/lib/utils'
import type { Diagnosis } from '@/types/entities'

const RECENTS_KEY = 'evexia:diagnosis_recents'
const RECENTS_MAX = 5

function readRecents(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENTS_KEY) ?? '[]') as string[]
  } catch {
    return []
  }
}

function pushRecent(id: string): void {
  const existing = readRecents().filter((r) => r !== id)
  const next = [id, ...existing].slice(0, RECENTS_MAX)
  localStorage.setItem(RECENTS_KEY, JSON.stringify(next))
}

export interface DiagnosisSelectorProps {
  value: string | null | undefined
  onChange: (id: string | null, diagnosis: Diagnosis | null) => void
  disabled?: boolean
  placeholder?: string
}

export function DiagnosisSelector({
  value,
  onChange,
  disabled,
  placeholder = 'Select diagnosis',
}: DiagnosisSelectorProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const debouncedSearch = useDebouncedValue(search.trim(), 200)
  const containerRef = useRef<HTMLDivElement>(null)
  const buttonId = useId()

  useEffect(() => {
    if (!open) return
    function onOutside(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onOutside)
    return () => document.removeEventListener('mousedown', onOutside)
  }, [open])

  const treeQuery = useQuery({
    queryKey: ['diagnoses', 'tree'],
    queryFn: () => diagnosesApi.getTree(),
    staleTime: 5 * 60_000,
  })

  const allDiagnoses = useMemo(
    () => (treeQuery.data?.types ?? []).flatMap((t) => t.diagnoses),
    [treeQuery.data],
  )

  const selectedDiagnosis = useMemo(
    () => (value ? allDiagnoses.find((d) => d.id === value) ?? null : null),
    [allDiagnoses, value],
  )

  const recentIds = useMemo(() => (open ? readRecents() : []), [open])
  const recentDiagnoses = useMemo(
    () => recentIds.flatMap((id) => allDiagnoses.filter((d) => d.id === id)),
    [allDiagnoses, recentIds],
  )

  const isSearching = debouncedSearch.length >= 2

  const searchResults = useMemo(() => {
    if (!isSearching) return []
    const q = debouncedSearch.toLowerCase()
    return allDiagnoses.filter(
      (d) => d.code.toLowerCase().includes(q) || d.name.toLowerCase().includes(q),
    )
  }, [isSearching, debouncedSearch, allDiagnoses])

  const handleSelect = (d: Diagnosis) => {
    pushRecent(d.id)
    onChange(d.id, d)
    setOpen(false)
    setSearch('')
  }

  const triggerLabel = useMemo(() => {
    if (selectedDiagnosis) return selectedDiagnosis.code + ' — ' + selectedDiagnosis.name
    if (value && treeQuery.isPending) return 'Loading…'
    return placeholder
  }, [selectedDiagnosis, treeQuery.isPending, value, placeholder])

  return (
    <div ref={containerRef} className="relative">
      <Button
        id={buttonId}
        type="button"
        variant="outline"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className={cn(
          'h-9 w-full justify-between gap-2 rounded-sm border-fg/20 bg-bg px-3 text-left text-sm shadow-sm',
          !value && 'text-fg/60',
        )}
      >
        <span className="min-w-0 truncate">{triggerLabel}</span>
        <ChevronDown className="h-4 w-4 shrink-0 text-fg/60" />
      </Button>

      {open && (
        <div
          className="absolute z-20 mt-1 max-h-80 w-full overflow-auto rounded-sm border border-fg/15 bg-bg shadow-lg"
          role="listbox"
        >
          <div className="sticky top-0 border-b border-fg/10 bg-surface p-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-fg/60" />
              <Input
                placeholder="Search by code or name…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="rounded-none h-8 pl-8 pr-3 border-fg/20"
                autoFocus
              />
            </div>
          </div>

          {isSearching ? (
            <DiagnosisList
              diagnoses={searchResults}
              selectedId={value ?? null}
              onSelect={handleSelect}
              emptyText="No matches."
            />
          ) : (
            <>
              {recentDiagnoses.length > 0 && (
                <section>
                  <p className="flex items-center gap-1.5 px-3 pt-2 pb-1 text-[10px] font-semibold tracking-wide text-fg/45">
                    <Clock className="size-3" aria-hidden />
                    Recently used
                  </p>
                  <DiagnosisList
                    diagnoses={recentDiagnoses}
                    selectedId={value ?? null}
                    onSelect={handleSelect}
                  />
                </section>
              )}
              <TypeGroupList
                types={treeQuery.data?.types ?? []}
                loading={treeQuery.isPending}
                expanded={expanded}
                onToggle={(id) => {
                  setExpanded((prev) => {
                    const next = new Set(prev)
                    if (next.has(id)) next.delete(id)
                    else next.add(id)
                    return next
                  })
                }}
                onSelect={handleSelect}
                selectedId={value ?? null}
              />
            </>
          )}
        </div>
      )}
    </div>
  )
}

function DiagnosisList({
  diagnoses,
  selectedId,
  onSelect,
  emptyText,
}: {
  diagnoses: Diagnosis[]
  selectedId: string | null
  onSelect: (d: Diagnosis) => void
  emptyText?: string
}) {
  if (diagnoses.length === 0 && emptyText)
    return <p className="p-3 text-sm text-fg/60">{emptyText}</p>
  return (
    <ul className="p-1">
      {diagnoses.map((d) => (
        <li key={d.id}>
          <Button
            type="button"
            variant="ghost"
            onClick={() => onSelect(d)}
            className={cn(
              'h-auto w-full items-start justify-start gap-2 rounded-none px-2 py-1.5 text-left text-sm text-fg hover:bg-surface-hover',
              d.id === selectedId && 'bg-primary/10',
            )}
          >
            <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center">
              {d.id === selectedId ? <Check className="h-4 w-4 text-primary" /> : null}
            </span>
            <span className="min-w-0 flex-1">
              <span className="font-medium">{d.code}</span>
              <span className="ml-1 text-fg/80">— {d.name}</span>
            </span>
          </Button>
        </li>
      ))}
    </ul>
  )
}

function TypeGroupList({
  types,
  loading,
  expanded,
  onToggle,
  onSelect,
  selectedId,
}: {
  types: { id: string; name: string; diagnoses: Diagnosis[] }[]
  loading: boolean
  expanded: Set<string>
  onToggle: (id: string) => void
  onSelect: (d: Diagnosis) => void
  selectedId: string | null
}) {
  if (loading) return <p className="p-3 text-sm text-fg/60">Loading…</p>
  if (types.length === 0) return <p className="p-3 text-sm text-fg/60">No diagnoses available.</p>

  return (
    <ul className="p-1">
      {types.map((type) => {
        const isOpen = expanded.has(type.id)
        return (
          <li key={type.id}>
            <Button
              type="button"
              variant="ghost"
              onClick={() => onToggle(type.id)}
              aria-expanded={isOpen}
              className="h-auto w-full justify-start gap-2 rounded-none px-2 py-1.5 text-left text-sm font-medium text-fg/70 hover:bg-surface-hover"
            >
              {isOpen ? (
                <ChevronDown className="h-4 w-4 shrink-0" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0" />
              )}
              {type.name}
            </Button>
            {isOpen && (
              <ul className="border-l border-fg/10 ml-4">
                {type.diagnoses.map((d) => (
                  <li key={d.id}>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => onSelect(d)}
                      className={cn(
                        'h-auto w-full items-start justify-start gap-2 rounded-none px-2 py-1.5 text-left text-sm text-fg hover:bg-surface-hover',
                        d.id === selectedId && 'bg-primary/10',
                      )}
                    >
                      <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center">
                        {d.id === selectedId ? <Check className="h-4 w-4 text-primary" /> : null}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="font-medium">{d.code}</span>
                        <span className="ml-1 text-fg/80">— {d.name}</span>
                      </span>
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </li>
        )
      })}
    </ul>
  )
}
