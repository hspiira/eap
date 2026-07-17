import { useMemo } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, Link, useNavigate, useSearch } from '@tanstack/react-router'
import { AlertCircle, ArrowLeft, Building2, Inbox, LogOut, User as UserIcon } from 'lucide-react'
import { z } from 'zod'

import { usersApi } from '@/api/endpoints/users'
import { AppLayout } from '@/components/AppLayout'
import { AtRiskPage } from '@/components/AtRiskPage'
import { FormField } from '@/components/common/FormField'
import { PageShell } from '@/components/common/PageShell'
import { DetailSkeleton } from '@/components/common/PageSkeletons'
import { RequireAuth } from '@/components/common/RequireAuth'
import { StatusBadge } from '@/components/common/StatusBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/contexts/ToastContext'
import { useApiForm } from '@/hooks/useApiForm'
import { authActions } from '@/lib/auth-store'
import { InboxPage } from '@/routes/inbox'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'
import type { User } from '@/types/entities'
import { Language } from '@/types/enums'

type MeView = 'inbox' | 'at-risk'

export const Route = createFileRoute('/me')({
  validateSearch: (search: Record<string, unknown>): { view?: MeView } => {
    const v = search.view
    return v === 'inbox' || v === 'at-risk' ? { view: v } : {}
  },
  component: MePage,
})

const preferencesSchema = z.object({
  preferred_language: z.nativeEnum(Language),
  timezone: z.string().trim().min(1, 'Timezone is required'),
})

type PreferencesValues = z.infer<typeof preferencesSchema>

const LANGUAGES: ReadonlyArray<{ value: Language; label: string }> = [
  { value: Language.EN, label: 'English' },
  { value: Language.ES, label: 'Español' },
  { value: Language.FR, label: 'Français' },
  { value: Language.DE, label: 'Deutsch' },
  { value: Language.IT, label: 'Italiano' },
  { value: Language.PT, label: 'Português' },
  { value: Language.ZH, label: '中文' },
  { value: Language.JA, label: '日本語' },
  { value: Language.KO, label: '한국어' },
]

function MePage() {
  return (
    <RequireAuth redirectAfterLogin="/me">
      <MeBody />
    </RequireAuth>
  )
}

const VIEW_META: Record<MeView, { label: string; icon: React.ElementType; component: React.ComponentType }> = {
  'inbox': { label: 'Inbox', icon: Inbox, component: InboxPage },
  'at-risk': { label: 'At Risk', icon: AlertCircle, component: AtRiskPage },
}

function MeBody() {
  const userId = useAuthStore((s) => s.user_id)
  const { view } = useSearch({ from: '/me' })

  if (view) {
    const meta = VIEW_META[view]
    const Content = meta.component
    return (
      <AppLayout>
        <PageShell
          icon={meta.icon}
          breadcrumb={
            <span className="flex items-center gap-1">
              <Link to="/me" className="hover:text-fg transition-colors">Profile</Link>
              <span className="text-fg/40">·</span>
              {meta.label}
            </span>
          }
          actions={
            <Button
              asChild
              variant="ghost"
              size="sm"
              className="h-7 gap-1 px-2 text-xs text-fg/70"
            >
              <Link to="/me">
                <ArrowLeft className="size-3" />
                Back
              </Link>
            </Button>
          }
        >
          <Content />
        </PageShell>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <PageShell icon={UserIcon} breadcrumb="Profile">
        <div className="mx-auto w-full max-w-3xl space-y-8 px-6 py-8">
          {userId ? <ProfileBody userId={userId} /> : <DetailSkeleton />}
        </div>
      </PageShell>
    </AppLayout>
  )
}

interface ProfileBodyProps {
  userId: string
}

function ProfileBody({ userId }: ProfileBodyProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => usersApi.getById(userId),
    staleTime: 60_000,
  })

  const updatePrefs = useMutation({
    mutationFn: (values: PreferencesValues) =>
      usersApi.updatePreferences(userId, {
        preferred_language: values.preferred_language,
        timezone: values.timezone,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['user', userId], updated)
      toast.showSuccess('Preferences saved')
    },
  })

  const defaults = useMemo<PreferencesValues>(
    () => ({
      preferred_language:
        (user?.preferred_language as Language | undefined) ?? Language.EN,
      timezone: user?.timezone ?? 'UTC',
    }),
    [user?.preferred_language, user?.timezone],
  )

  const { register, formState, submit, setValue, watch, serverError } =
    useApiForm<PreferencesValues>({
      schema: preferencesSchema,
      defaultValues: defaults,
      onSubmit: async (values) => {
        await updatePrefs.mutateAsync(values)
      },
      formOptions: { values: defaults },
    })

  async function handleLogout() {
    await authActions.logout()
    navigate({
      to: '/auth/login',
      search: { tenant_code: undefined, email: undefined, redirect: undefined },
      replace: true,
    })
  }

  if (isLoading || !user) return <DetailSkeleton />

  const currentLanguage = watch('preferred_language')

  return (
    <div className="space-y-8">
      <AccountSummary user={user} onLogout={handleLogout} />
      <TenantSummary />
      <PreviewLinks />

      <section className="space-y-4">
        <header>
          <h2 className="text-lg font-semibold text-fg">Preferences</h2>
          <p className="text-sm text-fg-muted">
            Update your language and timezone — applies to all dates and times shown to you.
          </p>
        </header>

        <form onSubmit={submit} className="space-y-4" noValidate>
          {serverError ? (
            <div className="p-3 bg-danger-soft border border-danger/30 text-danger-fg text-sm rounded-sm">
              {serverError}
            </div>
          ) : null}

          <FormField
            label="Language"
            error={formState.errors.preferred_language?.message}
            htmlFor="preferred_language"
          >
            <Select
              value={currentLanguage}
              onValueChange={(value) =>
                setValue('preferred_language', value as Language, {
                  shouldDirty: true,
                  shouldValidate: true,
                })
              }
            >
              <SelectTrigger id="preferred_language">
                <SelectValue placeholder="Choose a language" />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((l) => (
                  <SelectItem key={l.value} value={l.value}>
                    {l.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField
            label="Timezone"
            error={formState.errors.timezone?.message}
            htmlFor="timezone"
          >
            <Input
              id="timezone"
              type="text"
              placeholder="e.g. Africa/Kampala"
              autoComplete="off"
              {...register('timezone')}
            />
          </FormField>

          <div className="flex justify-end">
            <Button
              type="submit"
              disabled={formState.isSubmitting || !formState.isDirty}
            >
              {formState.isSubmitting ? 'Saving…' : 'Save preferences'}
            </Button>
          </div>
        </form>
      </section>
    </div>
  )
}

interface AccountSummaryProps {
  user: User
  onLogout: () => void
}

function AccountSummary({ user, onLogout }: AccountSummaryProps) {
  const initial = user.email.charAt(0).toUpperCase()
  return (
    <section className="rounded-sm border border-border-subtle bg-surface p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <span
            className="grid size-12 shrink-0 place-items-center rounded-sm bg-primary/10 font-mono text-lg font-semibold text-primary"
            aria-hidden
          >
            {initial}
          </span>
          <div className="space-y-0.5">
            <p className="text-base font-semibold text-fg">{user.email}</p>
            <div className="flex flex-wrap items-center gap-2 text-sm text-fg-muted">
              {user.role ? (
                <span className="inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[11px] font-medium text-fg/75">
                  {user.role}
                </span>
              ) : null}
              {user.status ? <StatusBadge status={user.status} /> : null}
            </div>
            <p className="font-mono text-xs text-fg-subtle">{user.id}</p>
          </div>
        </div>

        <Button type="button" variant="outline" onClick={onLogout}>
          <LogOut className="size-4" aria-hidden="true" />
          Sign out
        </Button>
      </div>
    </section>
  )
}

function PreviewLinks() {
  const items: Array<{ view: MeView; label: string; description: string; icon: React.ElementType }> = [
    {
      view: 'inbox',
      label: 'Inbox',
      description: 'Notification inbox — placeholder, not yet wired to real data.',
      icon: Inbox,
    },
    {
      view: 'at-risk',
      label: 'At Risk',
      description: 'PHQ-9 / no-show driven at-risk list — placeholder, ships in Phase 3.',
      icon: AlertCircle,
    },
  ]
  return (
    <section className="space-y-3">
      <header>
        <h2 className="text-sm font-semibold text-fg">Preview pages</h2>
        <p className="text-xs text-fg-muted">
          Work-in-progress screens — not yet linked from the main nav.
        </p>
      </header>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map(({ view, label, description, icon: Icon }) => (
          <Link
            key={view}
            to="/me"
            search={{ view }}
            className="flex items-start gap-3 rounded-sm border border-border-subtle bg-surface p-4 transition-colors hover:bg-surface-hover"
          >
            <Icon className="mt-0.5 size-4 shrink-0 text-fg-subtle" aria-hidden />
            <div className="min-w-0">
              <p className="text-sm font-medium text-fg">{label}</p>
              <p className="mt-0.5 text-xs text-fg-muted">{description}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}

function TenantSummary() {
  const tenant = useTenantStore((s) => s.currentTenant)
  if (!tenant) return null
  return (
    <section className="rounded-sm border border-border-subtle bg-surface p-6">
      <div className="mb-4 flex items-center gap-2">
        <Building2 className="size-4 text-fg-subtle" aria-hidden />
        <h2 className="text-sm font-semibold text-fg">Workspace</h2>
      </div>
      <dl className="grid grid-cols-1 gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs font-medium text-fg-subtle">Name</dt>
          <dd className="mt-0.5 text-fg">{tenant.name}</dd>
        </div>
        {tenant.code ? (
          <div>
            <dt className="text-xs font-medium text-fg-subtle">Code</dt>
            <dd className="mt-0.5 font-mono text-xs text-fg">{tenant.code}</dd>
          </div>
        ) : null}
        {tenant.subscription_tier ? (
          <div>
            <dt className="text-xs font-medium text-fg-subtle">Plan</dt>
            <dd className="mt-0.5 text-fg">{tenant.subscription_tier}</dd>
          </div>
        ) : null}
        <div>
          <dt className="text-xs font-medium text-fg-subtle">Status</dt>
          <dd className="mt-0.5"><StatusBadge status={tenant.status} /></dd>
        </div>
      </dl>
    </section>
  )
}
