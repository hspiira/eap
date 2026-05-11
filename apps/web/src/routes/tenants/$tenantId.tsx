import { useState } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import {
  AlertTriangle,
  Archive,
  ArrowLeft,
  KeyRound,
  Pencil,
  Play,
  Power,
  RotateCcw,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import { z } from 'zod'

import { tenantsApi } from '@/api/endpoints/tenants'
import { AppLayout } from '@/components/AppLayout'
import { FormField } from '@/components/common/FormField'
import { PageShell } from '@/components/common/PageShell'
import { DetailSkeleton } from '@/components/common/PageSkeletons'
import { RequirePlatformAdmin } from '@/components/common/RequirePlatformAdmin'
import { StatusBadge } from '@/components/common/StatusBadge'
import { TenantFormSheet } from '@/components/TenantFormSheet'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useToast } from '@/contexts/ToastContext'
import { normalizeErrorMessage } from '@/lib/errors'
import type { Tenant } from '@/types/entities'
import { TenantStatus } from '@/types/enums'

export const Route = createFileRoute('/tenants/$tenantId')({
  component: TenantDetailPage,
})

function TenantDetailPage() {
  return (
    <RequirePlatformAdmin>
      <TenantDetailBody />
    </RequirePlatformAdmin>
  )
}

function TenantDetailBody() {
  const { tenantId } = Route.useParams()
  const [editOpen, setEditOpen] = useState(false)

  const { data: tenant, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['tenants', 'detail', tenantId],
    queryFn: () => tenantsApi.getById(tenantId),
  })

  return (
    <AppLayout>
      <PageShell
        icon={ShieldCheck}
        breadcrumb={
          <>
            <Link
              to="/tenants"
              search={{ new: undefined, search: undefined, status: undefined }}
              className="hover:underline"
            >
              Tenants
            </Link>
            <span className="mx-1 text-fg/40">/</span>
            {tenant?.name ?? tenantId}
          </>
        }
        actions={
          tenant ? (
            <Button type="button" variant="outline" size="sm" onClick={() => setEditOpen(true)}>
              <Pencil className="size-3.5" /> Edit name
            </Button>
          ) : null
        }
      >
        <div className="flex flex-1 flex-col gap-6 p-6">
          {isError ? (
            <ErrorBanner message={normalizeErrorMessage(error, 'Could not load tenant')} onRetry={() => refetch()} />
          ) : isLoading || !tenant ? (
            <DetailSkeleton />
          ) : (
            <>
              <OverviewCard tenant={tenant} />
              <AzureSsoCard tenant={tenant} />
              <LifecycleCard tenant={tenant} />
            </>
          )}
        </div>
      </PageShell>

      {tenant ? (
        <TenantFormSheet
          open={editOpen}
          onOpenChange={setEditOpen}
          tenant={tenant}
          onSaved={() => setEditOpen(false)}
        />
      ) : null}
    </AppLayout>
  )
}

function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex items-center gap-3 rounded-sm border border-danger/30 bg-danger-soft p-4 text-danger-fg">
      <AlertTriangle className="size-5 shrink-0" />
      <p className="flex-1 text-sm">{message}</p>
      <Button size="sm" variant="outline" onClick={onRetry}>
        Retry
      </Button>
    </div>
  )
}

function OverviewCard({ tenant }: { tenant: Tenant }) {
  return (
    <section className="rounded-sm border border-border-subtle bg-surface p-6">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-fg">{tenant.name}</h2>
          <p className="font-mono text-xs text-fg-muted">{tenant.code}</p>
        </div>
        <StatusBadge status={tenant.status} />
      </header>
      <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
        <Field label="ID" value={<span className="font-mono text-xs">{tenant.id}</span>} />
        <Field label="Subscription" value={tenant.subscription_tier ?? '—'} />
        <Field label="Max users" value={String(tenant.settings?.max_users ?? '—')} />
        <Field label="Max clients" value={String(tenant.settings?.max_clients ?? '—')} />
        <Field label="Custom branding" value={tenant.settings?.custom_branding ? 'Enabled' : 'Disabled'} />
        <Field
          label="Created"
          value={tenant.created_at ? new Date(tenant.created_at).toLocaleString() : '—'}
        />
      </dl>
    </section>
  )
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col">
      <dt className="text-xs uppercase tracking-wider text-fg-subtle">{label}</dt>
      <dd className="text-fg">{value}</dd>
    </div>
  )
}

const ssoSchema = z.object({
  azure_tenant_id: z
    .string()
    .trim()
    .min(8, 'Looks too short to be an Azure tenant ID')
    .max(64),
  enabled: z.boolean(),
})

type SsoValues = z.infer<typeof ssoSchema>

function AzureSsoCard({ tenant }: { tenant: Tenant }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [tid, setTid] = useState(tenant.azure_tenant_id ?? '')
  const [enabled, setEnabled] = useState(tenant.azure_sso_enabled ?? false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (values: SsoValues) =>
      tenantsApi.updateAzureSso(tenant.id, {
        azure_tenant_id: values.azure_tenant_id || null,
        enabled: values.enabled,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['tenants', 'detail', tenant.id], updated)
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
      toast.showSuccess('Azure SSO config saved')
      setErrorMsg(null)
    },
    onError: (err) => {
      const msg = normalizeErrorMessage(err, 'Could not save Azure SSO config')
      setErrorMsg(msg)
      toast.showError(msg)
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const result = ssoSchema.safeParse({ azure_tenant_id: tid.trim(), enabled })
    if (!result.success) {
      setErrorMsg(result.error.issues[0]?.message ?? 'Invalid input')
      return
    }
    setErrorMsg(null)
    mutation.mutate(result.data)
  }

  const dirty = tid.trim() !== (tenant.azure_tenant_id ?? '') || enabled !== (tenant.azure_sso_enabled ?? false)

  return (
    <section className="rounded-sm border border-border-subtle bg-surface p-6">
      <header className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-fg">
            <KeyRound className="size-4 text-primary" />
            Azure AD SSO
          </h2>
          <p className="mt-1 text-sm text-fg-muted">
            Wire this tenant to a Microsoft Entra ID directory. Users with matching emails
            can then sign in via "Continue with Microsoft".
          </p>
        </div>
      </header>

      <form onSubmit={handleSubmit} className="space-y-4">
        {errorMsg ? (
          <div className="rounded-sm border border-danger/30 bg-danger-soft p-3 text-sm text-danger-fg">
            {errorMsg}
          </div>
        ) : null}

        <FormField
          label="Azure directory (tenant) ID"
          description="The tid claim Microsoft sends in the id_token. Found in Azure → Microsoft Entra ID → Overview."
          htmlFor="azure-tenant-id"
        >
          <Input
            id="azure-tenant-id"
            placeholder="00000000-0000-0000-0000-000000000000"
            className="font-mono"
            value={tid}
            onChange={(e) => setTid(e.target.value)}
            spellCheck={false}
          />
        </FormField>

        <div className="flex items-center gap-2">
          <Checkbox
            id="azure-enabled"
            checked={enabled}
            onCheckedChange={(v) => setEnabled(v === true)}
          />
          <label htmlFor="azure-enabled" className="text-sm text-fg">
            Enable Microsoft sign-in for this tenant
          </label>
        </div>

        <div className="flex justify-end">
          <Button type="submit" disabled={!dirty || mutation.isPending}>
            {mutation.isPending ? 'Saving…' : 'Save SSO config'}
          </Button>
        </div>
      </form>
    </section>
  )
}

function LifecycleCard({ tenant }: { tenant: Tenant }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const navigate = useNavigate()
  const [reasonDialog, setReasonDialog] = useState<null | 'suspend' | 'terminate'>(null)
  const [reason, setReason] = useState('')

  function refresh(updated: Tenant) {
    queryClient.setQueryData(['tenants', 'detail', tenant.id], updated)
    queryClient.invalidateQueries({ queryKey: ['tenants'] })
  }

  const activate = useMutation({
    mutationFn: () => tenantsApi.activate(tenant.id),
    onSuccess: (t) => {
      refresh(t)
      toast.showSuccess('Tenant activated')
    },
    onError: (e) => toast.showError(normalizeErrorMessage(e, 'Action failed')),
  })

  const archive = useMutation({
    mutationFn: () => tenantsApi.archive(tenant.id),
    onSuccess: (t) => {
      refresh(t)
      toast.showSuccess('Tenant archived')
    },
    onError: (e) => toast.showError(normalizeErrorMessage(e, 'Action failed')),
  })

  const restore = useMutation({
    mutationFn: () => tenantsApi.restore(tenant.id),
    onSuccess: (t) => {
      refresh(t)
      toast.showSuccess('Tenant restored')
    },
    onError: (e) => toast.showError(normalizeErrorMessage(e, 'Action failed')),
  })

  const suspendOrTerminate = useMutation({
    mutationFn: ({ kind, reason }: { kind: 'suspend' | 'terminate'; reason: string }) =>
      kind === 'suspend'
        ? tenantsApi.suspend(tenant.id, reason)
        : tenantsApi.terminate(tenant.id, reason),
    onSuccess: (t, vars) => {
      refresh(t)
      toast.showSuccess(`Tenant ${vars.kind === 'suspend' ? 'suspended' : 'terminated'}`)
      setReasonDialog(null)
      setReason('')
      if (vars.kind === 'terminate') {
        navigate({
          to: '/tenants',
          search: { new: undefined, search: undefined, status: undefined },
        })
      }
    },
    onError: (e) => toast.showError(normalizeErrorMessage(e, 'Action failed')),
  })

  const isTerminated = tenant.status === TenantStatus.TERMINATED
  const isActive = tenant.status === TenantStatus.ACTIVE
  const isSuspended = tenant.status === TenantStatus.SUSPENDED
  const isArchived = tenant.status === TenantStatus.ARCHIVED

  return (
    <section className="rounded-sm border border-border-subtle bg-surface p-6">
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-fg">Lifecycle</h2>
        <p className="text-sm text-fg-muted">
          Move the tenant through activation, suspension, archive, or termination.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {!isActive && !isTerminated ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => activate.mutate()}
            disabled={activate.isPending}
          >
            <Play className="size-3.5" /> Activate
          </Button>
        ) : null}

        {isActive ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setReasonDialog('suspend')}
          >
            <Power className="size-3.5" /> Suspend
          </Button>
        ) : null}

        {!isArchived && !isTerminated ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => archive.mutate()}
            disabled={archive.isPending}
          >
            <Archive className="size-3.5" /> Archive
          </Button>
        ) : null}

        {(isArchived || isSuspended) && !isTerminated ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => restore.mutate()}
            disabled={restore.isPending}
          >
            <RotateCcw className="size-3.5" /> Restore
          </Button>
        ) : null}

        {!isTerminated ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setReasonDialog('terminate')}
            className="text-destructive hover:bg-destructive/10 hover:text-destructive"
          >
            <Trash2 className="size-3.5" /> Terminate
          </Button>
        ) : null}

        <Button asChild variant="ghost" size="sm" className="ml-auto">
          <Link to="/tenants" search={{ new: undefined, search: undefined, status: undefined }}>
            <ArrowLeft className="size-3.5" /> Back to list
          </Link>
        </Button>
      </div>

      <Dialog
        open={reasonDialog !== null}
        onOpenChange={(open) => {
          if (!open) {
            setReasonDialog(null)
            setReason('')
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {reasonDialog === 'suspend' ? 'Suspend tenant' : 'Terminate tenant'}
            </DialogTitle>
            <DialogDescription>
              {reasonDialog === 'suspend'
                ? 'Suspending pauses the tenant — users cannot sign in until reactivated.'
                : 'Terminating is permanent. The tenant cannot be restored after termination.'}
            </DialogDescription>
          </DialogHeader>
          <FormField label="Reason" htmlFor="reason" required>
            <Input
              id="reason"
              placeholder="e.g. billing overdue 90 days"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              autoFocus
            />
          </FormField>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setReasonDialog(null)
                setReason('')
              }}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => {
                if (!reason.trim() || !reasonDialog) return
                suspendOrTerminate.mutate({ kind: reasonDialog, reason: reason.trim() })
              }}
              disabled={!reason.trim() || suspendOrTerminate.isPending}
            >
              {suspendOrTerminate.isPending ? 'Submitting…' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  )
}
