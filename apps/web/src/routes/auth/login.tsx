/**
 * Login Page
 */

import { createFileRoute, Link } from '@tanstack/react-router'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { FormField } from '@/components/common/FormField'
import type { ApiError } from '@/api/types'

export const Route = createFileRoute('/auth/login')({
  component: LoginPage,
  validateSearch: (search: Record<string, unknown>): {
    tenant_code?: string
    email?: string
  } => ({
    tenant_code: typeof search.tenant_code === 'string' ? search.tenant_code : undefined,
    email: typeof search.email === 'string' ? search.email : undefined,
  }),
})

function LoginPage() {
  const search = Route.useSearch()
  const [email, setEmail] = useState(search.email || '')
  const [password, setPassword] = useState('')
  const [tenantCode, setTenantCode] = useState(search.tenant_code || '')
  const [errors, setErrors] = useState<{ email?: string; password?: string; tenant_code?: string; general?: string }>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})
    setIsSubmitting(true)

    try {
      await login({ 
        email, 
        password,
        tenant_code: tenantCode
      })
      // Navigation handled by AuthContext
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        
        // Handle field-specific errors
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

  return (
    <div className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
      <video
        autoPlay
        loop
        muted
        playsInline
        className="fixed inset-0 w-full h-full object-cover z-0"
        aria-hidden
      >
        <source src="/videos/wellness.webm" type="video/webm" />
      </video>
      <div className="relative z-10 w-full max-w-md">
        <div className="bg-surface/80 backdrop-blur-xl p-8 rounded-none border border-[0.5px] border-white/10">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-text mb-2">Evexía</h1>
            <p className="text-text-muted">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit}>
            {errors.general && (
              <div className="mb-4 p-3 bg-nurturing-light border-[0.5px] border-nurturing text-text">
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
            <p className="text-text-muted text-sm mb-2">
              Don't have an account?{' '}
              <Link
                to="/auth/signup"
                className="text-primary hover:text-primary-hover transition-colors"
              >
                Sign up
              </Link>
            </p>
            <Link
              to="/"
              className="text-text hover:text-primary text-sm transition-colors"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
