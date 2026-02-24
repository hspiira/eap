/**
 * Login Page
 */

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { authActions } from '@/lib/auth-store'
import { useRedirectIfAuthenticated } from '@/hooks/useRedirectIfAuthenticated'
import { useAuthStore } from '@/store/slices/authSlice'
import { FormField } from '@/components/common/FormField'
import type { ApiError } from '@/api/types'

function safeRedirectPath(raw: unknown): string | undefined {
  const s = typeof raw === 'string' ? raw.trim() : ''
  if (!s || !s.startsWith('/') || s.startsWith('//')) return undefined
  if (s === '/auth/login' || s === '/auth/signup') return undefined
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
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        if (apiError.fieldErrors) {
          setErrors(apiError.fieldErrors as { email?: string; password?: string; tenant_code?: string })
        } else {
          setErrors({ general: apiError.message || 'Login failed. Please try again.' })
        }
      } else {
        setErrors({ general: 'An unexpected error occurred. Please try again.' })
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isAuthenticated) return null

  return (
    <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5 [&_label]:text-white/90 [&_input]:bg-white/10 [&_input]:border [&_input]:border-white/5 [&_input]:text-white [&_input::placeholder]:text-white/50 [&_input]:focus-visible:ring-white/20 [&_p.text-danger]:text-nurturing-light">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
            <p className="text-white/70">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit}>
            {errors.general && (
              <div className="mb-4 p-3 bg-nurturing/20 border border-nurturing/30 text-white">
                {errors.general}
              </div>
            )}

            <FormField
              label="Tenant Code"
              name="tenant_code"
              type="text"
              value={tenantCode}
              onChange={(e) => setTenantCode(e.target.value.toLowerCase())}
              error={errors.tenant_code}
              required
              placeholder="Enter tenant code"
              autoComplete="organization"
            />

            <FormField
              label="Email"
              name="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              required
              placeholder="Enter your email"
              autoComplete="email"
            />

            <FormField
              label="Password"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              required
              placeholder="Enter your password"
              autoComplete="current-password"
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 bg-primary hover:bg-primary-hover text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-white/70 text-sm mb-2">
              Don't have an account?{' '}
              <Link
                to="/auth/signup"
                className="text-natural hover:text-natural-light transition-colors"
              >
                Sign up
              </Link>
            </p>
            <Link
              to="/"
              className="text-white/80 hover:text-white text-sm transition-colors"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
  )
}
