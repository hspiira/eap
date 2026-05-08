import { useEffect, useRef, useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Check, CheckCircle, Copy, KeyRound, X } from 'lucide-react'
import { z } from 'zod'

import type { TenantCreateResponse } from '@/api/endpoints/tenants'
import { tenantsApi } from '@/api/endpoints/tenants'
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
      <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
          <p className="text-white/70">Register as a new tenant</p>
        </div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-none bg-natural/20 flex items-center justify-center shrink-0">
            <CheckCircle className="w-5 h-5 text-natural" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Tenant created</h2>
            <p className="text-white/70 text-sm">{adminCredentials.name}</p>
          </div>
        </div>
        <p className="text-white/80 text-sm mb-4">Set your admin password, then sign in.</p>
        <dl className="space-y-0 mb-6">
          <div className="flex items-baseline gap-4 py-3 border-b border-white/10">
            <dt className="text-sm text-white/70 shrink-0 w-28">Tenant code</dt>
            <dd className="text-sm font-mono text-white min-w-0">{adminCredentials.code}</dd>
          </div>
          <div className="flex items-baseline gap-4 py-3 border-b border-white/10">
            <dt className="text-sm text-white/70 shrink-0 w-28">Email</dt>
            <dd className="text-sm text-white min-w-0 break-all">{adminCredentials.admin_email}</dd>
          </div>
        </dl>
        <div className="mb-4">
          <span className="text-sm text-white/70">Set-password link</span>
          <div className="mt-1 flex gap-2">
            <input
              readOnly
              value={adminCredentials.set_password_url}
              className="flex-1 px-4 py-2 bg-white/10 border border-white/5 rounded-none text-white font-mono text-xs"
            />
            <button
              type="button"
              onClick={handleCopySetPasswordLink}
              className="px-4 py-2 bg-[#5A626A] hover:bg-[#4a5260] text-white rounded-none transition-colors flex items-center gap-2"
              title={copiedSetPasswordLink ? 'Copied!' : 'Copy link'}
            >
              <Copy className="w-4 h-4" />
              {copiedSetPasswordLink ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>
        <button
          type="button"
          onClick={goToSetPassword}
          className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors flex items-center justify-center gap-2 mb-4"
        >
          <KeyRound className="w-4 h-4" />
          Set your password
        </button>
        <p className="text-white/70 text-sm mt-6 mb-2">After you&apos;ve set your password:</p>
        <button
          type="button"
          onClick={goToLoginFromSuccess}
          className="w-full py-3 bg-[#D0B5B3] hover:bg-[#c0a5a3] text-white font-semibold rounded-none transition-colors"
        >
          Go to Sign in
        </button>
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => setAdminCredentials(null)}
            className="inline-flex items-center gap-2 text-sm text-white/70 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
        </div>
      </div>
    )
  }

  if (adminCredentials) {
    return (
      <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
          <p className="text-white/70">Tenant created</p>
        </div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-none bg-natural/20 flex items-center justify-center shrink-0">
            <CheckCircle className="w-5 h-5 text-natural" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{adminCredentials.name}</h2>
            <p className="text-white/70 text-sm">Code: {adminCredentials.code}</p>
          </div>
        </div>
        <p className="text-white/80 text-sm mb-4">Save these credentials. They cannot be retrieved later.</p>
        <dl className="space-y-2 mb-6">
          <div className="flex items-baseline gap-4 py-2 border-b border-white/10">
            <dt className="text-sm text-white/70 shrink-0 w-28">Admin email</dt>
            <dd className="text-sm text-white break-all">{adminCredentials.admin_email}</dd>
          </div>
          {adminCredentials.admin_password && (
            <div className="flex items-baseline gap-4 py-2 border-b border-white/10">
              <dt className="text-sm text-white/70 shrink-0 w-28">Admin password</dt>
              <dd className="text-sm text-white font-mono">{adminCredentials.admin_password}</dd>
            </div>
          )}
        </dl>
        <button
          type="button"
          onClick={goToLoginFromSuccess}
          className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors"
        >
          Go to Sign in
        </button>
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => setAdminCredentials(null)}
            className="inline-flex items-center gap-2 text-sm text-white/70 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
        </div>
      </div>
    )
  }

  const codeRegister = register('code')

  return (
    <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
        <p className="text-white/70">Register as a new tenant</p>
      </div>

      <form onSubmit={submit} className="space-y-4" noValidate>
        {serverError && (
          <div className="p-3 bg-[#D0B5B3]/20 border border-[#D0B5B3]/30 text-white text-sm">
            {serverError}
          </div>
        )}

        <div>
          <label htmlFor="name" className="block text-white/90 text-sm font-medium mb-1">
            Tenant Name *
          </label>
          <input
            id="name"
            type="text"
            placeholder="Enter tenant name"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
            {...register('name')}
          />
          {formState.errors.name && (
            <p className="mt-1 text-sm text-[#D0B5B3]">{formState.errors.name.message as string}</p>
          )}
        </div>

        <div>
          <label htmlFor="code" className="block text-white/90 text-sm font-medium mb-1">
            Tenant Code *
          </label>
          <div className="relative">
            <input
              id="code"
              type="text"
              placeholder="e.g., acme-corp"
              className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30 pr-10"
              {...codeRegister}
              onChange={(e) => {
                const formatted = formatCode(e.target.value)
                setValue('code', formatted, { shouldValidate: true, shouldTouch: true })
              }}
            />
            {codeValue && codeIsValid && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {codeAvailability.checking ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-transparent rounded-full animate-spin" />
                ) : codeAvailability.available === true ? (
                  <Check size={20} className="text-natural" />
                ) : codeAvailability.available === false ? (
                  <X size={20} className="text-red-400" />
                ) : null}
              </div>
            )}
          </div>
          {formState.errors.code && (
            <p className="mt-1 text-sm text-[#D0B5B3]">{formState.errors.code.message as string}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={
            formState.isSubmitting ||
            !nameValue?.trim() ||
            !codeIsValid ||
            codeAvailability.checking ||
            codeAvailability.available === false
          }
          className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {formState.isSubmitting ? 'Creating tenant...' : 'Create Tenant'}
        </button>
      </form>

      <div className="mt-6 text-center space-y-2">
        <p className="text-white/70 text-sm">
          Already have an account?{' '}
          <Link
            to="/auth/login"
            search={{ tenant_code: undefined, email: undefined, redirect: undefined }}
            className="text-natural hover:underline"
          >
            Sign in
          </Link>
        </p>
        <Link to="/" className="block text-white/80 hover:text-white text-sm">
          ← Back to Home
        </Link>
      </div>
    </div>
  )
}
