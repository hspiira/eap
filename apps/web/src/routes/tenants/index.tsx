import { useEffect, useState } from 'react'

import { createFileRoute, Link, useNavigate, useSearch } from '@tanstack/react-router'
import {
  ExternalLink,
  KeyRound,
  Plus,
  RotateCw,
  ShieldCheck,
} from 'lucide-react'

import { tenantsApi } from '@/api/endpoints/tenants'
import { AppLayout } from '@/components/AppLayout'
import { EmptyState } from '@/components/common/EmptyState'
import {
  FilterBar,
  FilterSearch,
  FilterTrigger,
} from '@/components/common/FilterBar'
import { PageShell } from '@/components/common/PageShell'
import { TableSkeleton } from '@/components/common/PageSkeletons'
import { RequirePlatformAdmin } from '@/components/common/RequirePlatformAdmin'
import { StatusBadge } from '@/components/common/StatusBadge'
import { TenantFormSheet } from '@/components/TenantFormSheet'
import { Button } from '@/components/ui/button'
import { Pagination } from '@/components/ui/pagination'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { normalizeErrorMessage } from '@/lib/errors'
import { useEntityList } from '@/lib/queries'
import type { Tenant } from '@/types/entities'
import { TenantStatus } from '@/types/enums'

function isStatus(v: unknown): v is TenantStatus {
  return (
    v === TenantStatus.ACTIVE ||
    v === TenantStatus.SUSPENDED ||
    v === TenantStatus.TERMINATED ||
    v === TenantStatus.ARCHIVED
  )
}

export const Route = createFileRoute('/tenants/')({
  component: TenantsListPage,
  validateSearch: (search: Record<string, unknown>) => ({
    new: search.new === '1' || search.new === true || undefined,
    search:
      typeof search.search === 'string' && search.search.trim()
        ? search.search
        : undefined,
    status: isStatus(search.status) ? search.status : undefined,
  }),
})

const STATUS_OPTIONS = [
  { value: 'all', label: 'All statuses' },
  { value: TenantStatus.ACTIVE, label: 'Active' },
  { value: TenantStatus.SUSPENDED, label: 'Suspended' },
  { value: TenantStatus.ARCHIVED, label: 'Archived' },
  { value: TenantStatus.TERMINATED, label: 'Terminated' },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]['value']

function TenantsListPage() {
  return (
    <RequirePlatformAdmin>
      <TenantsListBody />
    </RequirePlatformAdmin>
  )
}

function TenantsListBody() {
  const searchParams = useSearch({ from: '/tenants/' })
  const navigate = useNavigate({ from: '/tenants/' })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? '')
  const [page, setPage] = useState(1)
  const [addOpen, setAddOpen] = useState(false)
  const limit = 20

  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined
  const activeStatus = searchParams.status

  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  const params = {
    limit,
    offset: (page - 1) * limit,
    search: activeSearch,
    status: activeStatus,
  }

  const { data, isLoading, isError, error, refetch, isFetching } = useEntityList({
    resource: 'tenants',
    params,
    listFn: (p) => tenantsApi.list(p),
  })

  const rows = (data?.items ?? []) as Tenant[]
  const total = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / limit))

  function setStatus(next: StatusFilter) {
    navigate({
      search: (prev) => ({
        ...prev,
        status: next === 'all' ? undefined : (next as TenantStatus),
      }),
      replace: true,
    })
    setPage(1)
  }

  function clearAll() {
    setSearchInput('')
    navigate({
      search: () => ({ new: undefined, search: undefined, status: undefined }),
      replace: true,
    })
    setPage(1)
  }

  const filtersActive = Boolean(activeSearch || activeStatus)

  return (
    <AppLayout>
      <PageShell
        icon={ShieldCheck}
        breadcrumb="Tenants"
        actions={
          <Button type="button" size="sm" onClick={() => setAddOpen(true)}>
            <Plus className="size-3.5" /> New tenant
          </Button>
        }
      >
        <div className="flex flex-1 flex-col gap-3 p-4">
          <FilterBar>
            <FilterSearch
              value={searchInput}
              onChange={setSearchInput}
              placeholder="Search by name or code…"
            />
            <FilterTrigger
              label="Status"
              value={activeStatus ?? 'all'}
              options={STATUS_OPTIONS}
              onChange={(v) => setStatus(v as StatusFilter)}
            />
            {filtersActive ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={clearAll}
              >
                Clear
              </Button>
            ) : null}
            <div className="ml-auto flex items-center gap-1.5">
              <span className="text-xs text-fg/65">
                {total} {total === 1 ? 'tenant' : 'tenants'}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => refetch()}
                disabled={isFetching}
                aria-label="Refresh"
                className="size-7 p-0"
              >
                <RotateCw className={`size-3.5 ${isFetching ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </FilterBar>

          {isError ? (
            <EmptyState
              title="Could not load tenants"
              description={normalizeErrorMessage(error, 'Unknown error')}
              action={<Button onClick={() => refetch()}>Retry</Button>}
            />
          ) : isLoading ? (
            <TableSkeleton cols={6} rows={8} />
          ) : rows.length === 0 ? (
            <EmptyState
              icon={ShieldCheck}
              title={filtersActive ? 'No tenants match those filters' : 'No tenants yet'}
              description={
                filtersActive
                  ? 'Try clearing filters or adjusting your search.'
                  : 'Create the first tenant to onboard an employer.'
              }
              action={
                <Button onClick={() => setAddOpen(true)}>
                  <Plus className="size-3.5" /> New tenant
                </Button>
              }
            />
          ) : (
            <>
              <div className="overflow-x-auto rounded-sm border border-fg/10">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Code</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Tier</TableHead>
                      <TableHead>SSO</TableHead>
                      <TableHead className="w-12" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((row) => (
                      <TenantRow key={row.id} tenant={row} />
                    ))}
                  </TableBody>
                </Table>
              </div>

              {totalPages > 1 ? (
                <Pagination
                  page={page}
                  total={total}
                  limit={limit}
                  onPageChange={setPage}
                />
              ) : null}
            </>
          )}
        </div>
      </PageShell>

      <TenantFormSheet
        open={addOpen}
        onOpenChange={setAddOpen}
        onSaved={(t) => {
          setAddOpen(false)
          navigate({ to: '/tenants/$tenantId', params: { tenantId: t.id } })
        }}
      />
    </AppLayout>
  )
}

function TenantRow({ tenant }: { tenant: Tenant }) {
  return (
    <TableRow className="group">
      <TableCell className="font-medium text-fg">
        <Link
          to="/tenants/$tenantId"
          params={{ tenantId: tenant.id }}
          className="hover:underline"
        >
          {tenant.name}
        </Link>
      </TableCell>
      <TableCell className="font-mono text-xs text-fg/75">
        {tenant.code ?? '—'}
      </TableCell>
      <TableCell>
        <StatusBadge status={tenant.status} />
      </TableCell>
      <TableCell className="text-sm text-fg/75">
        {tenant.subscription_tier ?? '—'}
      </TableCell>
      <TableCell>
        {tenant.azure_sso_enabled ? (
          <span className="inline-flex items-center gap-1 text-xs text-fg">
            <KeyRound className="size-3 text-primary" /> Azure
          </span>
        ) : (
          <span className="text-xs text-fg/55">—</span>
        )}
      </TableCell>
      <TableCell className="text-right">
        <Link
          to="/tenants/$tenantId"
          params={{ tenantId: tenant.id }}
          aria-label={`Open ${tenant.name}`}
          className="grid size-7 place-items-center rounded-sm text-fg/65 opacity-0 transition-opacity hover:bg-surface-hover hover:text-fg group-hover:opacity-100 focus-within:opacity-100"
        >
          <ExternalLink className="size-3.5" />
        </Link>
      </TableCell>
    </TableRow>
  )
}
