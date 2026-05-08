import { useEffect, useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { z } from 'zod'

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
  email: z.string().trim().min(1, 'Email is required').email('Invalid email address'),
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
    <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
        <p className="text-white/70">Sign in to your account</p>
      </div>

      <form onSubmit={submit} className="space-y-4" noValidate>
        {isLocked ? (
          <div
            className="p-3 bg-danger-soft/20 border border-danger-soft/30 text-white text-sm"
            role="alert"
            aria-live="polite"
          >
            <p className="font-semibold">Account temporarily locked</p>
            <p className="mt-1 text-white/80">
              Too many failed attempts. Try again in {formatLockoutCountdown(lockoutSecondsLeft)}.
            </p>
          </div>
        ) : serverError ? (
          <div className="p-3 bg-danger-soft/20 border border-danger-soft/30 text-white text-sm">
            {serverError}
          </div>
        ) : null}

        <div>
          <label htmlFor="tenant_code" className="block text-white/90 text-sm font-medium mb-1">
            Tenant Code *
          </label>
          <input
            id="tenant_code"
            type="text"
            placeholder="Enter tenant code"
            autoComplete="organization"
            disabled={isLocked}
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30 disabled:opacity-50"
            {...register('tenant_code', {
              setValueAs: (v) => (typeof v === 'string' ? v.toLowerCase() : v),
            })}
          />
          {formState.errors.tenant_code && (
            <p className="mt-1 text-sm text-danger-soft">{formState.errors.tenant_code.message as string}</p>
          )}
        </div>

        <div>
          <label htmlFor="email" className="block text-white/90 text-sm font-medium mb-1">
            Email *
          </label>
          <input
            id="email"
            type="email"
            placeholder="Enter your email"
            autoComplete="email"
            disabled={isLocked}
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30 disabled:opacity-50"
            {...register('email')}
          />
          {formState.errors.email && (
            <p className="mt-1 text-sm text-danger-soft">{formState.errors.email.message as string}</p>
          )}
        </div>

        <div>
          <label htmlFor="password" className="block text-white/90 text-sm font-medium mb-1">
            Password *
          </label>
          <input
            id="password"
            type="password"
            placeholder="Enter your password"
            autoComplete="current-password"
            disabled={isLocked}
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30 disabled:opacity-50"
            {...register('password')}
          />
          {formState.errors.password && (
            <p className="mt-1 text-sm text-danger-soft">{formState.errors.password.message as string}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={submitDisabled}
          className="w-full py-3 bg-primary hover:bg-primary text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLocked
            ? `Locked — ${formatLockoutCountdown(lockoutSecondsLeft)}`
            : formState.isSubmitting
              ? 'Signing in...'
              : 'Sign in'}
        </button>
      </form>

      <div className="mt-6 text-center space-y-2">
        <p className="text-white/70 text-sm">
          Don&apos;t have an account?{' '}
          <Link to="/auth/signup" className="text-primary hover:underline">
            Sign up
          </Link>
        </p>
        <Link to="/" className="block text-white/80 hover:text-white text-sm">
          ← Back to Home
        </Link>
      </div>
    </div>
  )
}
