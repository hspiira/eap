/**
 * Login Page
 */

import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { FormField } from '@/components/common/FormField'
import type { ApiError } from '@/api/types'

export const Route = createFileRoute('/auth/login')({
  component: LoginPage,
  validateSearch: (search: Record<string, unknown>): {
    tenant_code?: string
    email?: string
  } => {
    return {
      tenant_code: search.tenant_code as string | undefined,
      email: search.email as string | undefined,
    }
  },
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
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white p-8 rounded-none border border-[0.5px] border-safe/30">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-safe mb-2">Evexía</h1>
            <p className="text-safe-light">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit}>
            {errors.general && (
              <div className="mb-4 p-3 bg-nurturing-light border-[0.5px] border-nurturing text-safe">
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
              className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-safe-light text-sm mb-2">
              Don't have an account?{' '}
              <Link
                to="/auth/signup"
                className="text-natural hover:text-natural-dark transition-colors"
              >
                Sign up
              </Link>
            </p>
            <Link
              to="/"
              className="text-safe hover:text-natural text-sm transition-colors"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
