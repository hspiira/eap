import { useEffect, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { ArrowRight, CornerDownLeft, Search } from "lucide-react"

import { MIN_SEARCH_LENGTH, SEARCH_RESULT_LIMIT, searchApi } from "@/api/endpoints/search"
import type { SearchCategoryResult, SearchResultItem } from "@/api/generated"
import {
  countRecords,
  hasCategoryFailure,
  matchesActionQuery,
  RECORD_CATEGORIES,
  type RecordCategory,
  SEARCH_ACTIONS,
  type SearchAction,
} from "@/components/search/search-registry"
import {
  CommandDialog,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEnabledNavItems } from "@/hooks/useNavigation"
import { isComingSoon, matchesNavQuery, type NavItem } from "@/lib/navigation"
import { globalSearchQueryKey, onGlobalSearchToggle } from "@/lib/search-state"
import { useAuthStore } from "@/store/slices/authSlice"
import { useTenantStore } from "@/store/slices/tenantSlice"

const DEBOUNCE_MS = 250

const STATUS_ROW = "px-4 py-3 text-xs text-fg-muted"

/**
 * Rank within the returned page: an exact label or identifier match, then a
 * prefix match, then any other supported match. The page itself is selected
 * name-ascending by the API, so this orders what came back rather than
 * claiming relevance ranking across the whole dataset.
 */
function matchRank(item: SearchResultItem, needle: string): number {
  const label = item.label.toLowerCase()
  const secondary = (item.secondary ?? "").toLowerCase()
  if (label === needle || secondary === needle) return 0
  if (label.startsWith(needle) || secondary.startsWith(needle)) return 1
  return 2
}

function orderByMatch(items: SearchResultItem[], query: string): SearchResultItem[] {
  const needle = query.trim().toLowerCase()
  return [...items].sort((a, b) => matchRank(a, needle) - matchRank(b, needle))
}

/** Open state, the Cmd/Ctrl+K binding, and the header launcher's signal. */
function useSearchDialog() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setOpen((v) => !v)
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])

  useEffect(() => onGlobalSearchToggle(() => setOpen((v) => !v)), [])

  // Reopening starts from a clean slate rather than the previous search.
  const change = (next: boolean) => {
    setOpen(next)
    if (!next) setQuery("")
  }

  return { open, setOpen: change, query, setQuery }
}

/**
 * Record results for the debounced query. Keyed by identity and tenant, so a
 * different session never reads these rows; the abort signal is consumed, so
 * TanStack Query cancels a request the next keystroke supersedes. There is no
 * placeholder data, which is what keeps a previous query's results from
 * appearing beneath a newer one.
 */
function useRecordSearch(query: string, open: boolean) {
  const userId = useAuthStore((s) => s.user_id)
  const tenantId = useTenantStore((s) => s.currentTenant?.id ?? null)
  const enabled = open && query.length >= MIN_SEARCH_LENGTH

  return useQuery({
    queryKey: globalSearchQueryKey({ userId, tenantId }, query, SEARCH_RESULT_LIMIT),
    queryFn: ({ signal }) => searchApi.global({ q: query, limit: SEARCH_RESULT_LIMIT }, { signal }),
    enabled,
    retry: false,
    staleTime: 30_000,
    gcTime: 60_000,
  })
}

function ResultRow({
  icon: Icon,
  label,
  secondary,
  onSelect,
  value,
}: {
  icon: React.ElementType
  label: string
  secondary?: string | null
  onSelect: () => void
  value: string
}) {
  return (
    <CommandItem value={value} onSelect={onSelect}>
      <Icon className="text-fg-muted" />
      <span className="min-w-0 flex-1 truncate">{label}</span>
      {secondary ? <span className="shrink-0 text-xs text-fg-muted">{secondary}</span> : null}
    </CommandItem>
  )
}

function RecordGroup({
  category,
  result,
  query,
  onNavigate,
}: {
  category: RecordCategory
  result: SearchCategoryResult
  query: string
  onNavigate: (to: string, search?: Record<string, unknown>) => void
}) {
  // A failed category says so. Rendering it as "no records" would report a
  // broken request as an established absence.
  if (result.failed) {
    return (
      <CommandGroup heading={category.heading}>
        <p className={STATUS_ROW} role="status">
          {category.failureLabel}. Try again.
        </p>
      </CommandGroup>
    )
  }
  if (result.items.length === 0) return null

  return (
    <CommandGroup heading={category.heading}>
      {orderByMatch(result.items, query).map((item) => (
        <ResultRow
          key={item.id}
          value={`${category.key}:${item.id}`}
          icon={category.icon}
          label={item.label}
          secondary={item.secondary}
          onSelect={() => onNavigate(category.detailTo(item.id))}
        />
      ))}
      {result.has_more ? (
        <CommandItem
          value={`${category.key}:see-all`}
          onSelect={() => onNavigate(category.listTo, { search: query })}
        >
          <ArrowRight className="text-fg-muted" />
          <span className="flex-1">See all {category.heading.toLowerCase()}</span>
        </CommandItem>
      ) : null}
    </CommandGroup>
  )
}

function RecordResults({
  query,
  liveQuery,
  onNavigate,
}: {
  /** Debounced: what has actually been asked for. */
  query: string
  /** What the user has typed right now, which drives the pending state. */
  liveQuery: string
  onNavigate: (to: string, search?: Record<string, unknown>) => void
}) {
  const { data, isFetching, isError } = useRecordSearch(query, true)

  if (liveQuery.length < MIN_SEARCH_LENGTH) return null

  // Distinct from no results: nothing has been established yet. Covers the
  // debounce window too, so a query still settling does not read as empty.
  if (query !== liveQuery || (isFetching && !data)) {
    return (
      <p className={STATUS_ROW} role="status">
        Searching records…
      </p>
    )
  }

  if (isError) {
    return (
      <p className={STATUS_ROW} role="status">
        Records could not be searched. Pages and actions still work.
      </p>
    )
  }

  if (!data) return null

  return (
    <>
      {RECORD_CATEGORIES.map((category) => (
        <RecordGroup
          key={category.key}
          category={category}
          result={data[category.key]}
          query={query}
          onNavigate={onNavigate}
        />
      ))}
      {countRecords(data) === 0 && !hasCategoryFailure(data) ? (
        <p className={STATUS_ROW} role="status">
          No records match “{query}”.
        </p>
      ) : null}
    </>
  )
}

function PagesGroup({ items, onNavigate }: { items: NavItem[]; onNavigate: (to: string) => void }) {
  if (items.length === 0) return null
  return (
    <CommandGroup heading="Pages">
      {items.map((item) => (
        <CommandItem
          key={item.to}
          value={`page:${item.to}`}
          disabled={isComingSoon(item)}
          onSelect={() => onNavigate(item.to)}
        >
          <item.icon className="text-fg-muted" />
          <span className="flex-1">{item.label}</span>
          {isComingSoon(item) ? (
            <span className="shrink-0 text-[10px] font-medium tracking-wide text-fg-subtle">
              Soon
            </span>
          ) : null}
        </CommandItem>
      ))}
    </CommandGroup>
  )
}

function ActionsGroup({
  actions,
  onNavigate,
}: {
  actions: SearchAction[]
  onNavigate: (to: string, search?: Record<string, unknown>) => void
}) {
  if (actions.length === 0) return null
  return (
    <CommandGroup heading="Actions">
      {actions.map((action) => (
        <CommandItem
          key={action.id}
          value={`action:${action.id}`}
          onSelect={() => onNavigate(action.to, action.search)}
        >
          <action.icon className="text-fg-muted" />
          <span className="flex-1">{action.label}</span>
          <CornerDownLeft className="text-fg-subtle" />
        </CommandItem>
      ))}
    </CommandGroup>
  )
}

export function GlobalSearch() {
  const { open, setOpen, query, setQuery } = useSearchDialog()
  const debounced = useDebouncedValue(query.trim(), DEBOUNCE_MS)
  const navigate = useNavigate()
  const nav = useEnabledNavItems()
  const canWrite = useCanWrite()

  const pages = nav.all.filter((item) => matchesNavQuery(item, query))
  const actions = SEARCH_ACTIONS.filter(
    (action) => (canWrite || !action.requiresWrite) && matchesActionQuery(action, query),
  )

  const onNavigate = (to: string, search?: Record<string, unknown>) => {
    setOpen(false)
    void navigate({ to, search } as never)
  }

  const typed = query.trim()
  const nothingLocal = pages.length === 0 && actions.length === 0
  // Only worth saying while records are not being searched; past the floor the
  // record section reports the outcome and a second "no match" line is noise.
  const showLocalEmpty = nothingLocal && typed.length > 0 && typed.length < MIN_SEARCH_LENGTH

  return (
    <CommandDialog
      open={open}
      onOpenChange={setOpen}
      title="Search"
      description="Search clients, practitioners and provider organisations, or jump to a page or a task."
      commandProps={{ shouldFilter: false }}
    >
      <CommandInput
        placeholder="Search clients, practitioners, organisations…"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {/* Records come from the API; pages and actions match locally. cmdk's
            own filter is off so a record matched on a field the label does not
            show is not silently dropped. */}
        <RecordResults query={debounced} liveQuery={typed} onNavigate={onNavigate} />
        {typed.length >= MIN_SEARCH_LENGTH && !nothingLocal ? <CommandSeparator /> : null}
        <PagesGroup items={pages} onNavigate={onNavigate} />
        <ActionsGroup actions={actions} onNavigate={onNavigate} />
        {showLocalEmpty ? (
          <p className={STATUS_ROW} role="status">
            No pages or actions match “{typed}”.
          </p>
        ) : null}
        {query.length === 0 ? (
          <p className="flex items-center gap-1.5 border-t border-border-subtle px-4 py-2 text-[11px] text-fg-subtle">
            <Search className="size-3" aria-hidden />
            Type at least {MIN_SEARCH_LENGTH} characters to search records.
          </p>
        ) : null}
      </CommandList>
    </CommandDialog>
  )
}
