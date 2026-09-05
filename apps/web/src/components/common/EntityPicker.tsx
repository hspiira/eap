import * as React from "react"
import { useState } from "react"

import { clientsApi } from "@/api/endpoints/clients"
import { type MemberListParams, membersApi } from "@/api/endpoints/members"
import { personsApi } from "@/api/endpoints/persons"
import { providersApi } from "@/api/endpoints/providers"
import { servicesApi } from "@/api/endpoints/services"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { displayName, memberLabel, nameInitials, personInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import type { ListParams, PaginatedResponse } from "@/types/api"
import type { Client, Member, Person, Provider, Service } from "@/types/entities"
import { getStatusLabel } from "@/utils/statusColors"

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
  selectedItem,
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
  /** Optional resolved value for records not present in the first search page. */
  selectedItem?: T | null
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
  const selected =
    selectedItem?.id === value ? selectedItem : items.find((item) => item.id === value)

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
      <Input placeholder={placeholder} value={query} onChange={(e) => setQuery(e.target.value)} />
      <div className="max-h-48 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg-muted">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg-muted">
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

/** Avatar + primary/secondary line: the shape every picker row uses. */
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
        className={`grid ${size === "md" ? "size-7" : "size-6"} shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary`}
      >
        {initials}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-fg">{primary}</span>
        {secondary ? (
          <span className="block truncate text-[11px] text-fg-muted">{secondary}</span>
        ) : null}
      </span>
    </>
  )
}

/** Client search-and-select. Was copy-pasted into five form sheets. */
export function ClientPicker({
  value,
  onChange,
  selected,
}: {
  value: string
  onChange: (id: string) => void
  selected?: Client | null
}) {
  return (
    <EntityPicker<Client>
      resource="clients"
      listFn={clientsApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search clients by name…"
      emptyPrompt="Start typing to search clients."
      emptyNoMatch="No clients match."
      renderSelected={(c) => (
        <PickerRow initials={nameInitials(c.name)} primary={c.name} size="md" />
      )}
      renderRow={(c) => <PickerRow initials={nameInitials(c.name)} primary={c.name} />}
      selectedItem={selected}
    />
  )
}

/** Service search-and-select. Was copy-pasted into two form sheets. */
export function ServicePicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  return (
    <EntityPicker<Service>
      resource="services"
      listFn={servicesApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search services by name…"
      emptyPrompt="Start typing to search services."
      emptyNoMatch="No services match."
      renderSelected={(s) => (
        <PickerRow
          initials="SV"
          primary={s.name}
          secondary={s.service_type ?? s.category ?? "-"}
          size="md"
        />
      )}
      renderRow={(s) => (
        <PickerRow initials="SV" primary={s.name} secondary={s.service_type ?? s.category ?? "-"} />
      )}
    />
  )
}

/** Person search-and-select. Was copy-pasted into form sheets that assign a session or service to someone. */
export function MemberPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  return (
    <EntityPicker<Member, MemberListParams>
      resource="members"
      listFn={membersApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search members…"
      emptyPrompt="Search by name or company member ID."
      emptyNoMatch="No members match."
      renderSelected={(member) => (
        <PickerRow
          initials={nameInitials(memberLabel(member))}
          primary={memberLabel(member)}
          secondary={member.relation}
          size="md"
        />
      )}
      renderRow={(member) => (
        <PickerRow
          initials={nameInitials(memberLabel(member))}
          primary={memberLabel(member)}
          secondary={member.relation}
        />
      )}
    />
  )
}

export function PersonPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  return (
    <EntityPicker<Person>
      resource="persons"
      listFn={personsApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search persons…"
      emptyPrompt="Start typing to search persons."
      emptyNoMatch="No persons match."
      renderSelected={(p) => (
        <PickerRow
          initials={personInitials(p)}
          primary={displayName(p)}
          secondary={getStatusLabel(p.person_type)}
          size="md"
        />
      )}
      renderRow={(p) => (
        <PickerRow
          initials={personInitials(p)}
          primary={displayName(p)}
          secondary={getStatusLabel(p.person_type)}
        />
      )}
    />
  )
}

/** Provider search-and-select. Was copy-pasted into two form sheets. */
export function ProviderPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  return (
    <EntityPicker<Provider>
      resource="providers"
      listFn={providersApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search providers…"
      emptyPrompt="Start typing to search providers."
      emptyNoMatch="No providers match."
      renderSelected={(p) => (
        <PickerRow
          initials="PR"
          primary={p.id}
          secondary={`${p.provider_profile.tier} · ${p.provider_profile.region}`}
          size="md"
        />
      )}
      renderRow={(p) => (
        <PickerRow
          initials="PR"
          primary={p.id}
          secondary={`${p.provider_profile.tier} · ${p.provider_profile.region}`}
        />
      )}
    />
  )
}
