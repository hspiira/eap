import * as React from "react"
import { useState } from "react"

import { clientsApi } from "@/api/endpoints/clients"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { nameInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import type { ListParams, PaginatedResponse } from "@/types/api"
import type { Client } from "@/types/entities"

/** Search-and-select over a paginated resource. */
export function EntityPicker<T extends { id: string }, P extends ListParams = ListParams>({
  resource,
  listFn,
  value,
  onChange,
  placeholder,
  emptyPrompt,
  emptyNoMatch,
  renderRow,
  renderSelected,
  params,
  filter,
}: {
  resource: string
  listFn: (params: P) => Promise<PaginatedResponse<T>>
  value: string
  onChange: (id: string) => void
  placeholder: string
  /** Shown before the user has typed. */
  emptyPrompt: string
  /** Shown when a search returns nothing. */
  emptyNoMatch: string
  renderRow: (item: T) => React.ReactNode
  renderSelected: (item: T) => React.ReactNode
  /** Merged into the list query, e.g. a person_type narrowing. */
  params?: Omit<P, keyof ListParams> & Partial<ListParams>
  /** Last-resort client-side narrowing for resources the API can't filter. */
  filter?: (item: T) => boolean
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<T, P>({
    resource,
    params: { page: 1, limit: 8, search: debounced || undefined, ...params } as P,
    listFn,
  })
  const all = list.data?.items ?? []
  const items = filter ? all.filter(filter) : all
  const selected = items.find((i) => i.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        {renderSelected(selected)}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onChange("")}
          className="shrink-0 text-xs text-fg/65"
        >
          Change
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-1.5">
      <Input
        placeholder={placeholder}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="max-h-48 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">
            {debounced ? emptyNoMatch : emptyPrompt}
          </p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {items.map((item) => (
              <li key={item.id}>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => onChange(item.id)}
                  className="flex h-auto w-full items-center gap-2.5 px-3 py-2 text-left"
                >
                  {renderRow(item)}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

/** Avatar + primary/secondary line — the shape every picker row uses. */
export function PickerRow({
  initials,
  primary,
  secondary,
  size = "sm",
}: {
  initials: string
  primary: string
  secondary?: string | null
  size?: "sm" | "md"
}) {
  return (
    <>
      <span
        aria-hidden
        className={`grid ${size === "md" ? "size-7" : "size-6"} shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary`}
      >
        {initials}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-fg">{primary}</span>
        {secondary ? (
          <span className="block truncate font-mono text-[11px] text-fg/55">
            {secondary}
          </span>
        ) : null}
      </span>
    </>
  )
}

/** Client search-and-select. Was copy-pasted into five form sheets. */
export function ClientPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  return (
    <EntityPicker<Client>
      resource="clients"
      listFn={clientsApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search clients by name or code…"
      emptyPrompt="Start typing to search clients."
      emptyNoMatch="No clients match."
      renderSelected={(c) => (
        <PickerRow initials={nameInitials(c.name)} primary={c.name} secondary={c.code} size="md" />
      )}
      renderRow={(c) => (
        <PickerRow initials={nameInitials(c.name)} primary={c.name} secondary={c.code} />
      )}
    />
  )
}
