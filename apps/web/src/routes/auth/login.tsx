import { useEffect,useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'

import type { ApiError } from '@/api/types'
import { useRedirectIfAuthenticated } from '@/hooks/useRedirectIfAuthenticated'
import { authActions } from '@/lib/auth-store'
import { useAuthStore } from '@/store/slices/authSlice'
import { normalizeErrorMessage } from '@/utils/errorHandler'

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

function LoginPage() {
  const navigate = useNavigate()
  const search = Route.useSearch()
  const redirectTo = search.redirect ?? '/'
  const isAuthenticated = useRedirectIfAuthenticated(redirectTo)

  const [email, setEmail] = useState(search.email || '')
  const [password, setPassword] = useState('')
  const [tenantCode, setTenantCode] = useState(search.tenant_code || '')
  const [errors, setErrors] = useState<{ email?: string; password?: string; tenant_code?: string; general?: string }>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const authError = useAuthStore((s) => s.error)

  useEffect(() => {
    if (authError) setErrors((e) => ({ ...e, general: authError }))
  }, [authError])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})
    setIsSubmitting(true)
    authActions.clearError()

    try {
      await authActions.login({
        email,
        password,
        tenant_code: tenantCode,
      })
      navigate({ to: redirectTo, search: {} })
    } catch (error: unknown) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        if (apiError.fieldErrors) {
          setErrors(apiError.fieldErrors as { email?: string; password?: string; tenant_code?: string })
        } else {
          setErrors({ general: apiError.message || 'Login failed. Please try again.' })
        }
      } else {
        setErrors({
          general: normalizeErrorMessage(error, 'Login failed. Please try again.'),
        })
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isAuthenticated) return null

  return (
    <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
        <p className="text-white/70">Sign in to your account</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {errors.general && (
          <div className="p-3 bg-[#D0B5B3]/20 border border-[#D0B5B3]/30 text-white text-sm">
            {errors.general}
          </div>
        )}

        <div>
          <label htmlFor="tenant_code" className="block text-white/90 text-sm font-medium mb-1">
            Tenant Code *
          </label>
          <input
            id="tenant_code"
            name="tenant_code"
            type="text"
            value={tenantCode}
            onChange={(e) => setTenantCode(e.target.value.toLowerCase())}
            required
            placeholder="Enter tenant code"
            autoComplete="organization"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
          />
          {errors.tenant_code && <p className="mt-1 text-sm text-[#D0B5B3]">{errors.tenant_code}</p>}
        </div>

        <div>
          <label htmlFor="email" className="block text-white/90 text-sm font-medium mb-1">
            Email *
          </label>
          <input
            id="email"
            name="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Enter your email"
            autoComplete="email"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
          />
          {errors.email && <p className="mt-1 text-sm text-[#D0B5B3]">{errors.email}</p>}
        </div>

        <div>
          <label htmlFor="password" className="block text-white/90 text-sm font-medium mb-1">
            Password *
          </label>
          <input
            id="password"
            name="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="Enter your password"
            autoComplete="current-password"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
          />
          {errors.password && <p className="mt-1 text-sm text-[#D0B5B3]">{errors.password}</p>}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Signing in...' : 'Sign in'}
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
