import { useEffect, useRef, useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Check, CheckCircle, Copy, KeyRound, X } from 'lucide-react'
import { z } from 'zod'

import type { TenantCreateResponse } from '@/api/endpoints/tenants'
import { tenantsApi } from '@/api/endpoints/tenants'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useApiForm } from '@/hooks/useApiForm'
import { isConflict } from '@/lib/errors'
import { tenantActions } from '@/lib/tenant-actions'
import { ApiError } from '@/types/api'

export const Route = createFileRoute('/auth/signup')({
  component: SignupPage,
})

const tenantCodeRegex = /^[a-z0-9]+(-[a-z0-9]+)*$/

const tenantCreateSchema = z.object({
  name: z.string().trim().min(1, 'Tenant name is required'),
  code: z
    .string()
    .trim()
    .min(3, 'Code must be 3-15 characters')
    .max(15, 'Code must be 3-15 characters')
    .regex(tenantCodeRegex, 'Lowercase alphanumeric with optional hyphens'),
})

function formatCode(raw: string): string {
  return raw
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '')
    .replace(/^-+|-+$/g, '')
}

function SignupPage() {
  const navigate = useNavigate()
  const [adminCredentials, setAdminCredentials] = useState<TenantCreateResponse | null>(null)
  const [copiedSetPasswordLink, setCopiedSetPasswordLink] = useState(false)
  const [codeAvailability, setCodeAvailability] = useState<{
    checking: boolean
    available: boolean | null
  }>({ checking: false, available: null })

  const form = useApiForm<z.infer<typeof tenantCreateSchema>>({
    schema: tenantCreateSchema,
    defaultValues: { name: '', code: '' },
    errorToast: false,
    formOptions: { mode: 'onTouched' },
    onSubmit: async (values) => {
      try {
        const response = await tenantActions.createTenant(values)
        setAdminCredentials(response)
      } catch (err) {
        if (isConflict(err) && !err.fieldErrors) {
          throw new ApiError(err.message, err.code, err.status, {
            code: 'A tenant with this code already exists. Please choose a different code.',
          })
        }
        throw err
      }
    },
  })

  const { register, watch, setValue, formState, submit, serverError } = form
  const codeValue = watch('code')
  const nameValue = watch('name')
  const codeIsValid = tenantCodeRegex.test(codeValue ?? '') && (codeValue?.length ?? 0) >= 3 && (codeValue?.length ?? 0) <= 15

  const checkTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(() => {
    if (checkTimeoutRef.current) clearTimeout(checkTimeoutRef.current)
    if (!codeIsValid) {
      setCodeAvailability({ checking: false, available: null })
      return
    }
    setCodeAvailability({ checking: true, available: null })
    checkTimeoutRef.current = setTimeout(async () => {
      try {
        const result = await tenantsApi.checkCode(codeValue.trim())
        setCodeAvailability({ checking: false, available: result.available })
      } catch {
        setCodeAvailability({ checking: false, available: null })
      }
    }, 500)
    return () => {
      if (checkTimeoutRef.current) clearTimeout(checkTimeoutRef.current)
    }
  }, [codeValue, codeIsValid])

  const goToSetPassword = () => {
    if (!adminCredentials?.set_password_url) return
    try {
      const url = new URL(adminCredentials.set_password_url, window.location.origin)
      const token = url.searchParams.get('token') ?? ''
      if (token) {
        navigate({ to: '/auth/set-password', search: { token, tenant_code: adminCredentials.code } })
      } else {
        window.location.href = adminCredentials.set_password_url
      }
    } catch {
      window.location.href = adminCredentials.set_password_url
    }
  }

  const handleCopySetPasswordLink = () => {
    if (!adminCredentials?.set_password_url) return
    void navigator.clipboard.writeText(adminCredentials.set_password_url).then(() => {
      setCopiedSetPasswordLink(true)
      setTimeout(() => setCopiedSetPasswordLink(false), 2000)
    })
  }

  const goToLoginFromSuccess = () => {
    if (adminCredentials) {
      navigate({
        to: '/auth/login',
        search: {
          tenant_code: adminCredentials.code,
          email: adminCredentials.admin_email,
          redirect: undefined,
        },
      })
    }
  }

  if (adminCredentials?.set_password_url) {
    return (
      <div className="bg-surface text-fg p-8 rounded-sm border border-border-strong shadow-lg">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
          <p className="text-fg-muted">Register as a new tenant</p>
        </div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-sm bg-brand-soft flex items-center justify-center shrink-0">
            <CheckCircle className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-fg">Tenant created</h2>
            <p className="text-fg-muted text-sm">{adminCredentials.name}</p>
          </div>
        </div>
        <p className="text-fg-muted text-sm mb-4">Set your admin password, then sign in.</p>
        <dl className="space-y-0 mb-6">
          <div className="flex items-baseline gap-4 py-3 border-b border-border-strong">
            <dt className="text-sm text-fg-muted shrink-0 w-28">Tenant code</dt>
            <dd className="text-sm font-mono text-fg min-w-0">{adminCredentials.code}</dd>
          </div>
          <div className="flex items-baseline gap-4 py-3 border-b border-border-strong">
            <dt className="text-sm text-fg-muted shrink-0 w-28">Email</dt>
            <dd className="text-sm text-fg min-w-0 break-all">{adminCredentials.admin_email}</dd>
          </div>
        </dl>
        <div className="mb-4">
          <span className="text-sm text-fg-muted">Set-password link</span>
          <div className="mt-1 flex gap-2">
            <Input
              readOnly
              value={adminCredentials.set_password_url}
              className="flex-1 font-mono text-xs"
            />
            <Button
              type="button"
              variant="secondary"
              onClick={handleCopySetPasswordLink}
              title={copiedSetPasswordLink ? 'Copied!' : 'Copy link'}
              className="gap-2"
            >
              <Copy className="w-4 h-4" />
              {copiedSetPasswordLink ? 'Copied!' : 'Copy'}
            </Button>
          </div>
        </div>
        <Button type="button" onClick={goToSetPassword} className="w-full mb-4 gap-2">
          <KeyRound className="w-4 h-4" />
          Set your password
        </Button>
        <p className="text-fg-muted text-sm mt-6 mb-2">After you&apos;ve set your password:</p>
        <Button type="button" variant="outline" onClick={goToLoginFromSuccess} className="w-full">
          Go to Sign in
        </Button>
        <div className="mt-6 text-center">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setAdminCredentials(null)}
            className="h-auto gap-2 p-0 text-sm text-fg-muted hover:text-fg"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
        </div>
      </div>
    )
  }

  if (adminCredentials) {
    return (
      <div className="bg-surface text-fg p-8 rounded-sm border border-border-strong shadow-lg">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
          <p className="text-fg-muted">Tenant created</p>
        </div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-sm bg-brand-soft flex items-center justify-center shrink-0">
            <CheckCircle className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-fg">{adminCredentials.name}</h2>
            <p className="text-fg-muted text-sm">Code: {adminCredentials.code}</p>
          </div>
        </div>
        <p className="text-fg-muted text-sm mb-4">Save these credentials. They cannot be retrieved later.</p>
        <dl className="space-y-2 mb-6">
          <div className="flex items-baseline gap-4 py-2 border-b border-border-strong">
            <dt className="text-sm text-fg-muted shrink-0 w-28">Admin email</dt>
            <dd className="text-sm text-fg break-all">{adminCredentials.admin_email}</dd>
          </div>
          {adminCredentials.admin_password && (
            <div className="flex items-baseline gap-4 py-2 border-b border-border-strong">
              <dt className="text-sm text-fg-muted shrink-0 w-28">Admin password</dt>
              <dd className="text-sm text-fg font-mono">{adminCredentials.admin_password}</dd>
            </div>
          )}
        </dl>
        <Button type="button" onClick={goToLoginFromSuccess} className="w-full">
          Go to Sign in
        </Button>
        <div className="mt-6 text-center">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setAdminCredentials(null)}
            className="h-auto gap-2 p-0 text-sm text-fg-muted hover:text-fg"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
        </div>
      </div>
    )
  }

  const codeRegister = register('code')

  return (
    <div className="bg-surface text-fg p-8 rounded-sm border border-border-strong shadow-lg">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
        <p className="text-fg-muted">Register as a new tenant</p>
      </div>

      <form onSubmit={submit} className="space-y-4" noValidate>
        {serverError && (
          <div className="p-3 bg-danger-soft border border-danger/30 text-danger-fg text-sm rounded-sm">
            {serverError}
          </div>
        )}

        <div>
          <label htmlFor="name" className="block text-fg text-sm font-medium mb-1">
            Tenant Name *
          </label>
          <Input
            id="name"
            type="text"
            placeholder="Enter tenant name"
            {...register('name')}
          />
          {formState.errors.name && (
            <p className="mt-1 text-sm text-danger">{formState.errors.name.message as string}</p>
          )}
        </div>

        <div>
          <label htmlFor="code" className="block text-fg text-sm font-medium mb-1">
            Tenant Code *
          </label>
          <div className="relative">
            <Input
              id="code"
              type="text"
              placeholder="e.g., acme-corp"
              className="pr-10"
              {...codeRegister}
              onChange={(e) => {
                const formatted = formatCode(e.target.value)
                setValue('code', formatted, { shouldValidate: true, shouldTouch: true })
              }}
            />
            {codeValue && codeIsValid && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {codeAvailability.checking ? (
                  <div className="w-5 h-5 border-2 border-fg-subtle border-t-transparent rounded-full animate-spin" />
                ) : codeAvailability.available === true ? (
                  <Check size={20} className="text-success" />
                ) : codeAvailability.available === false ? (
                  <X size={20} className="text-danger" />
                ) : null}
              </div>
            )}
          </div>
          {formState.errors.code && (
            <p className="mt-1 text-sm text-danger">{formState.errors.code.message as string}</p>
          )}
        </div>

        <Button
          type="submit"
          disabled={
            formState.isSubmitting ||
            !nameValue?.trim() ||
            !codeIsValid ||
            codeAvailability.checking ||
            codeAvailability.available === false
          }
          className="w-full"
        >
          {formState.isSubmitting ? 'Creating tenant...' : 'Create Tenant'}
        </Button>
      </form>

      <div className="mt-6 text-center space-y-2">
        <p className="text-fg-muted text-sm">
          Already have an account?{' '}
          <Link
            to="/auth/login"
            search={{ tenant_code: undefined, email: undefined, redirect: undefined }}
            className="text-primary hover:underline font-medium"
          >
            Sign in
          </Link>
        </p>
        <Link to="/" className="block text-fg-muted hover:text-fg text-sm">
          ← Back to Home
        </Link>
      </div>
    </div>
  )
}
