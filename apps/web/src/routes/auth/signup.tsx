/**
 * Signup Page - Tenant Creation
 * Creates a new tenant and returns admin credentials
 */

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState, useEffect, useRef } from 'react'
import { useTenant } from '@/hooks/useTenant'
import { tenantsApi } from '@/api/endpoints/tenants'
import { FormField } from '@/components/common/FormField'
import { AdminPasswordDisplay } from '@/components/common/AdminPasswordDisplay'
import type { ApiError } from '@/api/types'
import type { TenantCreateResponse } from '@/api/endpoints/tenants'
import { Check, X } from 'lucide-react'

export const Route = createFileRoute('/auth/signup')({
  component: SignupPage,
})

function SignupPage() {
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [codeAvailability, setCodeAvailability] = useState<{
    checking: boolean
    available: boolean | null
  }>({ checking: false, available: null })
  const [errors, setErrors] = useState<{ 
    name?: string
    code?: string
    general?: string
  }>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [adminCredentials, setAdminCredentials] = useState<TenantCreateResponse | null>(null)
  const { createTenant } = useTenant()
  const navigate = useNavigate()
  const checkTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Validate tenant code format: ^[a-z0-9]+(-[a-z0-9]+)*$
  const validateCode = (value: string): boolean => {
    if (value.length < 3 || value.length > 15) return false
    const pattern = /^[a-z0-9]+(-[a-z0-9]+)*$/
    return pattern.test(value)
  }

  // Check code availability with debouncing
  useEffect(() => {
    // Clear previous timeout
    if (checkTimeoutRef.current) {
      clearTimeout(checkTimeoutRef.current)
    }

    // Reset availability if code is empty or invalid
    if (!code.trim() || !validateCode(code)) {
      setCodeAvailability({ checking: false, available: null })
      return
    }

    // Set checking state
    setCodeAvailability({ checking: true, available: null })

    // Debounce the check (wait 500ms after user stops typing)
    checkTimeoutRef.current = setTimeout(async () => {
      try {
        const result = await tenantsApi.checkCode(code.trim())
        setCodeAvailability({ checking: false, available: result.available })
        
        if (!result.available) {
          setErrors({ 
            ...errors, 
            code: 'A tenant with this code already exists. Please choose a different code.' 
          })
        } else {
          // Clear code error if available
          if (errors.code) {
            setErrors({ ...errors, code: undefined })
          }
        }
      } catch (error) {
        // If endpoint doesn't exist or fails, don't block submission
        // The backend will validate on submit
        setCodeAvailability({ checking: false, available: null })
      }
    }, 500)

    return () => {
      if (checkTimeoutRef.current) {
        clearTimeout(checkTimeoutRef.current)
      }
    }
  }, [code])

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '')
    // Remove leading/trailing hyphens
    const cleaned = value.replace(/^-+|-+$/g, '')
    setCode(cleaned)
    
    // Clear code error when user types
    if (errors.code) {
      setErrors({ ...errors, code: undefined })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    // Client-side validation
    if (!name.trim()) {
      setErrors({ name: 'Tenant name is required' })
      return
    }

    if (name.length > 255) {
      setErrors({ name: 'Tenant name must be 255 characters or less' })
      return
    }

    if (!code.trim()) {
      setErrors({ code: 'Tenant code is required' })
      return
    }

    if (!validateCode(code)) {
      setErrors({ 
        code: 'Code must be 3-15 characters, lowercase alphanumeric with optional hyphens (e.g., acme-corp, test123)' 
      })
      return
    }

    setIsSubmitting(true)

    try {
      const response = await createTenant({
        name: name.trim(),
        code: code.trim(),
        // subscription_tier defaults to "Free" on backend
        // settings will be configured in tenant settings later
      })
      
      // Show admin credentials
      setAdminCredentials(response)
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        
        // Handle field-specific errors
        if (apiError.fieldErrors) {
          setErrors(apiError.fieldErrors as { 
            name?: string
            code?: string
          })
        } else {
          // Handle 409 Conflict (duplicate code)
          if (apiError.status === 409) {
            setErrors({ 
              code: 'A tenant with this code already exists. Please choose a different code.' 
            })
          } else {
            setErrors({ general: apiError.message || 'Failed to create tenant. Please try again.' })
          }
        }
      } else {
        setErrors({ general: 'An unexpected error occurred. Please try again.' })
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLoginNow = () => {
    if (adminCredentials) {
      // Navigate to login with pre-filled tenant code and email
      navigate({ 
        to: '/auth/login',
        search: {
          tenant_code: adminCredentials.code,
          email: adminCredentials.admin_email,
        }
      })
    }
  }

  const handleDownloadCredentials = () => {
    if (!adminCredentials) return

    const content = `Evexía - Tenant Admin Credentials

Tenant: ${adminCredentials.name}
Code: ${adminCredentials.code}

IMPORTANT: Save these credentials securely. They cannot be retrieved later.

Admin Email: ${adminCredentials.admin_email}
Admin Password: ${adminCredentials.admin_password}

Generated: ${new Date().toISOString()}
`

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `evexia-${adminCredentials.code}-credentials.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5 [&_label]:text-white/90 [&_input]:bg-white/10 [&_input]:border [&_input]:border-white/5 [&_input]:text-white [&_input::placeholder]:text-white/50 [&_input]:focus-visible:ring-white/20 [&_p.text-danger]:text-nurturing-light">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
              <p className="text-white/70">Register as a new tenant</p>
            </div>

            <form onSubmit={handleSubmit}>
              {errors.general && (
                <div className="mb-4 p-3 bg-nurturing/20 border border-nurturing/30 text-white">
                  {errors.general}
                </div>
              )}

              <FormField
                label="Tenant Name"
                name="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                error={errors.name}
                required
                placeholder="Enter tenant name"
              />

              <div className="mb-4">
                <label
                  htmlFor="code"
                  className="block text-white/90 text-sm font-medium mb-2"
                >
                  Tenant Code
                  <span className="text-danger ml-1">*</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    id="code"
                    name="code"
                    value={code}
                    onChange={handleCodeChange}
                    required
                    placeholder="e.g., acme-corp"
                    className="w-full px-4 py-2 bg-white/10 backdrop-blur-sm border border-white/5 rounded-none focus:outline-none focus:ring-1 focus:ring-white/20 text-white placeholder:text-white/50 pr-10"
                  />
                  {code && validateCode(code) && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      {codeAvailability.checking ? (
                        <div className="w-5 h-5 border-2 border-safe/30 border-t-transparent rounded-full animate-spin"></div>
                      ) : codeAvailability.available === true ? (
                        <Check size={20} className="text-natural" />
                      ) : codeAvailability.available === false ? (
                        <X size={20} className="text-danger" />
                      ) : null}
                    </div>
                  )}
                </div>
                {errors.code && (
                  <p className="mt-1 text-sm text-nurturing-light">{errors.code}</p>
                )}
                {code && !validateCode(code) && code.length > 0 && !errors.code && (
                  <p className="mt-1 text-sm text-nurturing-light">
                    Code must be 3-15 characters, lowercase alphanumeric with optional hyphens
                  </p>
                )}
                {code && validateCode(code) && codeAvailability.available === true && !errors.code && (
                  <p className="mt-1 text-sm text-natural">✓ This code is available</p>
                )}
              </div>

              <button
                type="submit"
                disabled={
                  isSubmitting || 
                  !name.trim() || 
                  !code.trim() || 
                  !validateCode(code) ||
                  codeAvailability.checking ||
                  codeAvailability.available === false
                }
                className="w-full py-3 bg-primary hover:bg-primary-hover text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating tenant...' : 'Create Tenant'}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-white/70 text-sm mb-2">
                Already have an account?{' '}
                <Link
                  to="/auth/login"
                  search={{ tenant_code: '', email: '' }}
                  className="text-natural hover:text-natural-light transition-colors"
                >
                  Sign in
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

      {adminCredentials && (
        <AdminPasswordDisplay
          tenant={adminCredentials}
          onLogin={handleLoginNow}
          onDownload={handleDownloadCredentials}
          onClose={() => setAdminCredentials(null)}
        />
      )}
    </>
  )
}
