import { useEffect, useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { z } from 'zod'

import { FormField } from '@/components/common/FormField'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useApiForm } from '@/hooks/useApiForm'
import { useRedirectIfAuthenticated } from '@/hooks/useRedirectIfAuthenticated'
import { authActions } from '@/lib/auth-store'
import { getLockoutSecondsRemaining, isAccountLocked } from '@/lib/errors'

function safeRedirectPath(raw: unknown): string | undefined {
  const s = typeof raw === 'string' ? raw.trim() : ''
  if (!s || !s.startsWith('/') || s.startsWith('//')) return undefined
  if (s === '/auth/login' || s === '/auth/signup' || s === '/auth/set-password') return undefined
  return s
}

export const Route = createFileRoute('/auth/login')({
  component: LoginPage,
  validateSearch: (search: Record<string, unknown>) => ({
    tenant_code: typeof search.tenant_code === 'string' ? search.tenant_code : undefined,
    email: typeof search.email === 'string' ? search.email : undefined,
    redirect: safeRedirectPath(search.redirect),
  }),
})

const loginSchema = z.object({
  tenant_code: z.string().trim().min(1, 'Tenant code is required'),
  email: z.email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

const DEFAULT_LOCKOUT_SECONDS = 60

function formatLockoutCountdown(seconds: number): string {
  if (seconds <= 0) return ''
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m > 0) return `${m}m ${s.toString().padStart(2, '0')}s`
  return `${s}s`
}

function LoginPage() {
  const navigate = useNavigate()
  const search = Route.useSearch()
  const redirectTo = search.redirect ?? '/'
  const isAuthenticated = useRedirectIfAuthenticated(redirectTo)

  const [lockoutUntil, setLockoutUntil] = useState<number | null>(null)
  const [now, setNow] = useState(() => Date.now())

  const lockoutSecondsLeft = lockoutUntil
    ? Math.max(0, Math.ceil((lockoutUntil - now) / 1000))
    : 0
  const isLocked = lockoutSecondsLeft > 0

  useEffect(() => {
    if (!lockoutUntil) return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [lockoutUntil])

  useEffect(() => {
    if (lockoutUntil && Date.now() >= lockoutUntil) setLockoutUntil(null)
  }, [now, lockoutUntil])

  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof loginSchema>>({
    schema: loginSchema,
    defaultValues: {
      tenant_code: search.tenant_code ?? '',
      email: search.email ?? '',
      password: '',
    },
    errorToast: false,
    onSubmit: async (values) => {
      if (isLocked) return
      authActions.clearError()
      try {
        await authActions.login(values)
        navigate({ to: redirectTo, search: {} })
      } catch (err) {
        if (isAccountLocked(err)) {
          const seconds = getLockoutSecondsRemaining(err) ?? DEFAULT_LOCKOUT_SECONDS
          setLockoutUntil(Date.now() + seconds * 1000)
        }
        throw err
      }
    },
  })

  if (isAuthenticated) return null

  const submitDisabled = formState.isSubmitting || isLocked

  return (
    <div className="bg-surface text-fg p-8 rounded-sm border border-border-strong shadow-lg">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
        <p className="text-fg-muted">Sign in to your account</p>
      </div>

      <form onSubmit={submit} className="space-y-4" noValidate>
        {isLocked ? (
          <div
            className="p-3 bg-danger-soft border border-danger/30 text-danger-fg text-sm rounded-sm"
            role="alert"
            aria-live="polite"
          >
            <p className="font-semibold">Account temporarily locked</p>
            <p className="mt-1">
              Too many failed attempts. Try again in {formatLockoutCountdown(lockoutSecondsLeft)}.
            </p>
          </div>
        ) : serverError ? (
          <div className="p-3 bg-danger-soft border border-danger/30 text-danger-fg text-sm rounded-sm">
            {serverError}
          </div>
        ) : null}

        <FormField
          label="Tenant code"
          required
          error={formState.errors.tenant_code?.message}
          htmlFor="tenant_code"
        >
          <Input
            id="tenant_code"
            type="text"
            placeholder="Enter tenant code"
            autoComplete="organization"
            disabled={isLocked}
            {...register('tenant_code', {
              setValueAs: (v) => (typeof v === 'string' ? v.toLowerCase() : v),
            })}
          />
        </FormField>

        <FormField
          label="Email"
          required
          error={formState.errors.email?.message}
          htmlFor="email"
        >
          <Input
            id="email"
            type="email"
            placeholder="Enter your email"
            autoComplete="email"
            disabled={isLocked}
            {...register('email')}
          />
        </FormField>

        <FormField
          label="Password"
          required
          error={formState.errors.password?.message}
          htmlFor="password"
        >
          <Input
            id="password"
            type="password"
            placeholder="Enter your password"
            autoComplete="current-password"
            disabled={isLocked}
            {...register('password')}
          />
        </FormField>

        <Button
          type="submit"
          disabled={submitDisabled}
          className="w-full"
        >
          {isLocked
            ? `Locked — ${formatLockoutCountdown(lockoutSecondsLeft)}`
            : formState.isSubmitting
              ? 'Signing in...'
              : 'Sign in'}
        </Button>
      </form>

      <div className="mt-6 text-center space-y-2">
        <p className="text-fg-muted text-sm">
          Don&apos;t have an account?{' '}
          <Link to="/auth/signup" className="text-primary hover:underline font-medium">
            Sign up
          </Link>
        </p>
        <Link to="/" className="block text-fg-muted hover:text-fg text-sm">
          ← Back to Home
        </Link>
      </div>
    </div>
  )
}
