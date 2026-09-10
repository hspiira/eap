import * as React from "react"
import { useState } from "react"

import { clientsApi } from "@/api/endpoints/clients"
import { industriesApi } from "@/api/endpoints/industries"
import { type MemberListParams, membersApi } from "@/api/endpoints/members"
import { personsApi } from "@/api/endpoints/persons"
import { type ProviderListParams, providersApi } from "@/api/endpoints/providers"
import { servicesApi } from "@/api/endpoints/services"
import { usersApi } from "@/api/endpoints/users"
import { CATEGORY_LABELS } from "@/components/ServiceFormSheet"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { displayName, memberLabel, nameInitials, personInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import type { ListParams, PaginatedResponse } from "@/types/api"
import type { Client, Industry, Member, Person, Provider, Service, User } from "@/types/entities"
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
  staleTime,
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
  /** Longer for slow-changing lookups (e.g. industries, services categories). */
  staleTime?: number
}) {
  const [query, setQuery] = useState("")
  // A combobox, not a permanently open list: eight rows of every picker at
  // once made a form three screens tall before anything was chosen.
  const [open, setOpen] = useState(false)
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<T, P>({
    resource,
    params: { page: 1, limit: 8, search: debounced || undefined, ...params } as P,
    listFn,
    staleTime,
  })
  const all = list.data?.items ?? []
  const items = filter ? all.filter(filter) : all
  const selected =
    selectedItem?.id === value ? selectedItem : items.find((item) => item.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-1.5">
        {renderSelected(selected)}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => {
            onChange("")
            setQuery("")
          }}
          className="shrink-0 text-xs text-fg/65"
        >
          Change
        </Button>
      </div>
    )
  }

  return (
    <div className="relative">
      <Input
        role="combobox"
        aria-expanded={open}
        placeholder={placeholder}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setOpen(false)
        }}
      />
      {open ? (
        <div className="absolute z-50 mt-1 max-h-56 w-full overflow-y-auto rounded-sm border border-fg/15 bg-bg shadow-md">
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
                    // Mousedown, not click: the input blurs first otherwise,
                    // the list unmounts, and the click lands on nothing.
                    onMouseDown={(e) => {
                      e.preventDefault()
                      onChange(item.id)
                      setOpen(false)
                    }}
                    className="flex h-auto w-full items-center gap-2.5 px-3 py-1.5 text-left"
                  >
                    {renderRow(item)}
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
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
export function IndustryPicker({
  value,
  onChange,
  selected,
  filter,
}: {
  value: string
  onChange: (id: string) => void
  selected?: Industry | null
  /** e.g. exclude the industry being edited so it cannot be its own parent. */
  filter?: (industry: Industry) => boolean
}) {
  return (
    <EntityPicker<Industry>
      resource="industries"
      listFn={industriesApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search industries by name…"
      emptyPrompt="Start typing to search industries."
      emptyNoMatch="No industries match."
      staleTime={5 * 60_000}
      renderSelected={(i) => (
        <PickerRow initials={nameInitials(i.name)} primary={i.name} secondary={i.code} size="md" />
      )}
      renderRow={(i) => (
        <PickerRow initials={nameInitials(i.name)} primary={i.name} secondary={i.code} />
      )}
      selectedItem={selected}
      filter={filter}
    />
  )
}

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
      staleTime={5 * 60_000}
      renderSelected={(s) => (
        <PickerRow
          initials="SV"
          primary={s.name}
          secondary={s.category ? CATEGORY_LABELS[s.category] : "-"}
          size="md"
        />
      )}
      renderRow={(s) => (
        <PickerRow
          initials="SV"
          primary={s.name}
          secondary={s.category ? CATEGORY_LABELS[s.category] : "-"}
        />
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

export function UserPicker({
  value,
  onChange,
  selected,
}: {
  value: string
  onChange: (id: string) => void
  selected?: User | null
}) {
  return (
    <EntityPicker<User>
      resource="users"
      listFn={usersApi.list}
      value={value}
      onChange={onChange}
      selectedItem={selected}
      placeholder="Search users by email…"
      emptyPrompt="Search for an existing user account."
      emptyNoMatch="No user accounts match."
      renderSelected={(user) => (
        <PickerRow
          initials={nameInitials(user.display_name || user.email)}
          primary={user.display_name || user.email}
          secondary={user.display_name ? user.email : user.status}
          size="md"
        />
      )}
      renderRow={(user) => (
        <PickerRow
          initials={nameInitials(user.display_name || user.email)}
          primary={user.display_name || user.email}
          secondary={user.display_name ? user.email : user.status}
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
    <EntityPicker<Provider, ProviderListParams>
      resource="providers"
      listFn={providersApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search practitioners…"
      emptyPrompt="Start typing to search practitioners."
      emptyNoMatch="No practitioners match."
      renderSelected={(p) => (
        <PickerRow
          initials="PR"
          primary={p.display_name}
          secondary={`${p.provider_profile.tier} · ${p.provider_profile.region}`}
          size="md"
        />
      )}
      renderRow={(p) => (
        <PickerRow
          initials="PR"
          primary={p.display_name}
          secondary={`${p.provider_profile.tier} · ${p.provider_profile.region}`}
        />
      )}
    />
  )
}
