import { useMemo } from 'react'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { LogOut, User as UserIcon } from 'lucide-react'
import { z } from 'zod'

import { usersApi } from '@/api/endpoints/users'
import { AppLayout } from '@/components/AppLayout'
import { FormField } from '@/components/common/FormField'
import { PageShell } from '@/components/common/PageShell'
import { DetailSkeleton } from '@/components/common/PageSkeletons'
import { RequireAuth } from '@/components/common/RequireAuth'
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
import { useAuthStore } from '@/store/slices/authSlice'
import type { User } from '@/types/entities'
import { Language } from '@/types/enums'

export const Route = createFileRoute('/me')({
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

function MeBody() {
  const userId = useAuthStore((s) => s.user_id)

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
  return (
    <section className="rounded-sm border border-border-subtle bg-surface p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-wider text-fg-subtle">Signed in as</p>
          <p className="text-base font-semibold text-fg">{user.email}</p>
          <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-1 text-sm text-fg-muted sm:grid-cols-2">
            <div className="flex gap-2">
              <dt className="text-fg-subtle">User ID</dt>
              <dd className="font-mono text-xs">{user.id}</dd>
            </div>
            {user.status ? (
              <div className="flex gap-2">
                <dt className="text-fg-subtle">Status</dt>
                <dd>{user.status}</dd>
              </div>
            ) : null}
          </dl>
        </div>

        <Button type="button" variant="outline" onClick={onLogout}>
          <LogOut className="size-4" aria-hidden="true" />
          Sign out
        </Button>
      </div>
    </section>
  )
}
