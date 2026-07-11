import { useEffect, useState } from 'react'

import { createFileRoute, Link } from '@tanstack/react-router'
import { z } from 'zod'

import { authApi } from '@/api/endpoints/auth'
import { FormField } from '@/components/common/FormField'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useApiForm } from '@/hooks/useApiForm'
import { useRedirectIfAuthenticated } from '@/hooks/useRedirectIfAuthenticated'

export const Route = createFileRoute('/auth/sso')({
  component: SsoPage,
  validateSearch: (search: Record<string, unknown>) => ({
    tenant_code: typeof search.tenant_code === 'string' ? search.tenant_code : undefined,
    redirect: typeof search.redirect === 'string' ? search.redirect : undefined,
  }),
})

const ssoSchema = z.object({
  tenant_code: z.string().trim().min(1, 'Tenant code is required'),
})

function SsoPage() {
  const search = Route.useSearch()
  const isAuthenticated = useRedirectIfAuthenticated(search.redirect ?? '/')
  const azureEnabled = authApi.isAzureSsoEnabled()
  const [launched, setLaunched] = useState(false)

  const { register, formState, submit } = useApiForm<z.infer<typeof ssoSchema>>({
    schema: ssoSchema,
    defaultValues: { tenant_code: search.tenant_code ?? '' },
    errorToast: false,
    onSubmit: async (_values) => {
      const url = authApi.azureLoginUrl()
      setLaunched(true)
      window.location.href = url
    },
  })

  useEffect(() => {
    if (search.tenant_code && azureEnabled && !launched) {
      const url = authApi.azureLoginUrl()
      setLaunched(true)
      window.location.href = url
    }
  }, [search.tenant_code, azureEnabled, launched])

  if (isAuthenticated) return null

  if (!azureEnabled) {
    return (
      <div className="rounded-sm p-8 bg-white/3">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
          <p className="text-fg-muted">SSO not configured</p>
        </div>
        <p className="text-sm text-fg-muted text-center mb-6">
          Microsoft SSO has not been enabled for this deployment. Contact your administrator.
        </p>
        <Link
          to="/auth/login"
          search={{ tenant_code: search.tenant_code, email: undefined, redirect: search.redirect }}
          className="block w-full py-3 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-sm transition-colors text-center text-sm"
        >
          Back to sign in
        </Link>
      </div>
    )
  }

  if (search.tenant_code) {
    return (
      <div className="rounded-sm p-8 bg-white/3">
        <div className="text-center">
          <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
          <p className="text-fg-muted">Redirecting to Microsoft…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-sm p-8 bg-white/3">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
        <p className="text-fg-muted">Sign in with Microsoft</p>
      </div>

      <form onSubmit={submit} className="space-y-4" noValidate>
        <FormField
          label="Tenant code"
          required
          error={formState.errors.tenant_code?.message}
          htmlFor="sso-tenant-code"
        >
          <Input
            id="sso-tenant-code"
            type="text"
            placeholder="Enter tenant code"
            autoComplete="organization"
            {...register('tenant_code', {
              setValueAs: (v) => (typeof v === 'string' ? v.toLowerCase() : v),
            })}
          />
        </FormField>

        <Button type="submit" disabled={formState.isSubmitting} className="w-full h-11 gap-3">
          <img src="/microsoft-logo.svg" alt="" aria-hidden="true" width={18} height={18} />
          Continue with Microsoft
        </Button>
      </form>

      <div className="mt-5 text-center">
        <Link
          to="/auth/login"
          search={{ tenant_code: undefined, email: undefined, redirect: search.redirect }}
          className="text-sm text-fg-muted hover:text-primary"
        >
          Sign in with email instead
        </Link>
      </div>
    </div>
  )
}
