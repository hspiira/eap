import { useEffect, useState } from "react"

import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  BadgeCheck,
  Download,
  ExternalLink,
  KeyRound,
  MoreHorizontal,
  Plus,
  RotateCw,
  ShieldCheck,
  ShieldOff,
  UserCog,
} from "lucide-react"

import { usersApi } from "@/api/endpoints/users"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Pagination } from "@/components/ui/pagination"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { UserFormSheet } from "@/components/UserFormSheet"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import type { User } from "@/types/entities"
import { AuthProvider, UserStatus } from "@/types/enums"

function isStatus(value: unknown): value is UserStatus {
  return (
    value === UserStatus.ACTIVE ||
    value === UserStatus.SUSPENDED ||
    value === UserStatus.BANNED ||
    value === UserStatus.TERMINATED ||
    value === UserStatus.PENDING_VERIFICATION ||
    value === UserStatus.INACTIVE
  )
}

export const Route = createFileRoute("/users/")({
  component: UsersListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { new?: boolean; search?: string; status?: UserStatus } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: UserStatus.ACTIVE, label: "Active" },
  { value: UserStatus.PENDING_VERIFICATION, label: "Pending verification" },
  { value: UserStatus.SUSPENDED, label: "Suspended" },
  { value: UserStatus.INACTIVE, label: "Inactive" },
  { value: UserStatus.BANNED, label: "Banned" },
  { value: UserStatus.TERMINATED, label: "Terminated" },
] as const

const SECURITY_OPTIONS = [
  { value: "all", label: "Any security" },
  { value: "verified", label: "Email verified" },
  { value: "unverified", label: "Unverified email" },
  { value: "2fa-on", label: "2FA enabled" },
  { value: "2fa-off", label: "2FA disabled" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]
type SecurityFilter = (typeof SECURITY_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function UsersListPage() {
  const searchParams = useSearch({ from: "/users/" })
  const navigate = useNavigate({ from: "/users/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [security, setSecurity] = useState<SecurityFilter>("all")
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const limit = 20
  const toggleSort = (field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }

  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined
  const activeStatus = searchParams.status

  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  useEffect(() => {
    if (activeSearch !== searchParams.search) {
      navigate({ search: (prev) => ({ ...prev, search: activeSearch }), replace: true })
      setPage(1)
    }
  }, [activeSearch, navigate, searchParams.search])

  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : next
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
    setPage(1)
  }

  const query = useEntityList({
    resource: "users",
    params: {
      page,
      limit,
      search: activeSearch,
      status: activeStatus,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: usersApi.list,
  })
  const allItems = query.data?.items ?? []
  const items = filterBySecurity(allItems, security)
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters = Boolean(activeSearch) || Boolean(activeStatus) || security !== "all"

  return (
    <PageShell
      icon={UserCog}
      breadcrumb="People · Platform Users"
      actions={
        <>
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
            <Plus className="size-3.5" />
            Add user
          </Button>
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "security", label: "Security" },
          ]}
        />
        {activeStatus ? (
          <FilterChip
            label={`Status is ${activeStatus}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(activeStatus ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <FilterTrigger
          icon={ShieldCheck}
          label="Security"
          value={security}
          options={SECURITY_OPTIONS}
          onChange={setSecurity}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search users…"
        />
      </FilterBar>

      <UserFormSheet open={addOpen} onOpenChange={setAddOpen} />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void query.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={UserCog}
            title={hasFilters ? "No users match your filters" : "No users yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Add the first platform user to get started."
            }
            action={
              hasFilters ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  Add user
                </Button>
              )
            }
          />
        ) : (
          <>
            <div className="relative min-h-0 flex-1 overflow-auto">
              <Table className="w-full caption-bottom text-sm">
                <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <Checkbox aria-label="Select all" />
                    </TableHead>
                    <TableHead>
                      <SortHeader field="email" sort={sort} onToggle={toggleSort}>
                        Email
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        Status
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Email verified</TableHead>
                    <TableHead className="text-fg/65">2FA</TableHead>
                    <TableHead className="text-fg/65">Sign-in</TableHead>
                    <TableHead>
                      <SortHeader field="last_login_at" sort={sort} onToggle={toggleSort}>
                        Last login
                      </SortHeader>
                    </TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <UserRow key={row.id} row={row} />
                  ))}
                </TableBody>
              </Table>
            </div>
            {total > 0 && (
              <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                <Pagination page={page} total={total} limit={limit} onPageChange={setPage} />
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  )
}

function UserRow({ row }: { row: User }) {
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox aria-label={`Select ${row.email}`} onClick={(e) => e.stopPropagation()} />
      </TableCell>
      <TableCell>
        <Link
          to="/users/$userId"
          params={{ userId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <UserCog className="size-3" />
          </span>
          <span className="text-sm font-medium text-fg group-hover:text-primary">
            {row.email}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <StatusBadge status={row.status} />
      </TableCell>
      <TableCell>
        {row.is_email_verified ? (
          <span className="inline-flex items-center gap-1 text-xs text-fg">
            <BadgeCheck className="size-3 text-primary" /> Verified
          </span>
        ) : (
          <span className="text-xs text-fg/55">Unverified</span>
        )}
      </TableCell>
      <TableCell>
        {row.is_two_factor_enabled ? (
          <span className="inline-flex items-center gap-1 text-xs text-fg">
            <ShieldCheck className="size-3 text-primary" /> On
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-xs text-fg/55">
            <ShieldOff className="size-3" /> Off
          </span>
        )}
      </TableCell>
      <TableCell>
        {row.auth_provider === AuthProvider.AZURE_AD ? (
          <span className="inline-flex items-center gap-1 text-xs text-fg">
            <KeyRound className="size-3 text-primary" /> Microsoft
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-xs text-fg/55">
            <KeyRound className="size-3" /> Password
          </span>
        )}
      </TableCell>
      <TableCell className="text-sm text-fg/75">
        {row.last_login_at ? new Date(row.last_login_at).toLocaleDateString() : "—"}
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/users/$userId"
            params={{ userId: row.id }}
            aria-label={`Open ${row.email}`}
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button type="button" variant="ghost" size="sm" aria-label={`More actions for ${row.email}`} className="size-7 p-0 text-fg/65"><MoreHorizontal className="size-4" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/users/$userId" params={{ userId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive focus:text-destructive">
                Suspend
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center px-6 py-10">
      <div className="flex max-w-sm flex-col items-center text-center">
        <p className="text-sm text-danger-fg">{message}</p>
        <Button variant="outline" size="sm" className="mt-4 gap-1.5" onClick={onRetry}>
          <RotateCw className="size-4" />
          Try again
        </Button>
      </div>
    </div>
  )
}

function IconButton({
  label,
  icon: Icon,
  onClick,
}: {
  label: string
  icon: React.ElementType
  onClick?: () => void
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="size-7 p-0 text-fg/70"
    >
      <Icon className="size-3.5" />
    </Button>
  )
}

function filterBySecurity(items: User[], filter: SecurityFilter): User[] {
  switch (filter) {
    case "verified":
      return items.filter((u) => u.is_email_verified)
    case "unverified":
      return items.filter((u) => !u.is_email_verified)
    case "2fa-on":
      return items.filter((u) => u.is_two_factor_enabled)
    case "2fa-off":
      return items.filter((u) => !u.is_two_factor_enabled)
    default:
      return items
  }
}
