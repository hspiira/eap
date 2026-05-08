import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { z } from 'zod'

import { useApiForm } from '@/hooks/useApiForm'
import { useRedirectIfAuthenticated } from '@/hooks/useRedirectIfAuthenticated'
import { authActions } from '@/lib/auth-store'

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

function LoginPage() {
  const navigate = useNavigate()
  const search = Route.useSearch()
  const redirectTo = search.redirect ?? '/'
  const isAuthenticated = useRedirectIfAuthenticated(redirectTo)

  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof loginSchema>>({
    schema: loginSchema,
    defaultValues: {
      tenant_code: search.tenant_code ?? '',
      email: search.email ?? '',
      password: '',
    },
    errorToast: false,
    onSubmit: async (values) => {
      authActions.clearError()
      await authActions.login(values)
      navigate({ to: redirectTo, search: {} })
    },
  })

  if (isAuthenticated) return null

  return (
    <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
        <p className="text-white/70">Sign in to your account</p>
      </div>

      <form onSubmit={submit} className="space-y-4" noValidate>
        {serverError && (
          <div className="p-3 bg-[#D0B5B3]/20 border border-[#D0B5B3]/30 text-white text-sm">
            {serverError}
          </div>
        )}

        <div>
          <label htmlFor="tenant_code" className="block text-white/90 text-sm font-medium mb-1">
            Tenant Code *
          </label>
          <input
            id="tenant_code"
            type="text"
            placeholder="Enter tenant code"
            autoComplete="organization"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
            {...register('tenant_code', {
              setValueAs: (v) => (typeof v === 'string' ? v.toLowerCase() : v),
            })}
          />
          {formState.errors.tenant_code && (
            <p className="mt-1 text-sm text-[#D0B5B3]">{formState.errors.tenant_code.message as string}</p>
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
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
            {...register('email')}
          />
          {formState.errors.email && (
            <p className="mt-1 text-sm text-[#D0B5B3]">{formState.errors.email.message as string}</p>
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
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
            {...register('password')}
          />
          {formState.errors.password && (
            <p className="mt-1 text-sm text-[#D0B5B3]">{formState.errors.password.message as string}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={formState.isSubmitting}
          className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {formState.isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <div className="mt-6 text-center space-y-2">
        <p className="text-white/70 text-sm">
          Don&apos;t have an account?{' '}
          <Link to="/auth/signup" className="text-natural hover:underline">
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
