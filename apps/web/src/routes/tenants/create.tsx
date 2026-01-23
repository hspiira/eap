/**
 * Create Tenant Page
 * Public page for creating a new tenant (no authentication required)
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useTenant } from '@/contexts/TenantContext'
import { FormField } from '@/components/common/FormField'
import { AdminPasswordDisplay } from '@/components/common/AdminPasswordDisplay'
import type { ApiError } from '@/api/types'
import type { TenantCreateResponse } from '@/api/endpoints/tenants'

export const Route = createFileRoute('/tenants/create')({
  component: CreateTenantPage,
})

function CreateTenantPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [errors, setErrors] = useState<{ 
    name?: string
    email?: string
    phone?: string
    general?: string
  }>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [adminCredentials, setAdminCredentials] = useState<TenantCreateResponse | null>(null)
  const { createTenant } = useTenant()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})
    setIsSubmitting(true)

    try {
      const response = await createTenant({
        name,
        contact_info: {
          email: email || undefined,
          phone: phone || undefined,
        },
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
            email?: string
            phone?: string
          })
        } else {
          setErrors({ general: apiError.message || 'Failed to create tenant. Please try again.' })
        }
      } else {
        setErrors({ general: 'An unexpected error occurred. Please try again.' })
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleContinue = () => {
    setAdminCredentials(null)
    // Redirect to login page
    navigate({ to: '/auth/login', search: {} })
  }

  return (
    <>
      <div className="min-h-screen bg-calm flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="bg-white p-8 rounded-none">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-safe mb-2">Evexía</h1>
              <p className="text-safe-light">Create a new tenant</p>
            </div>

            <form onSubmit={handleSubmit}>
              {errors.general && (
                <div className="mb-4 p-3 bg-nurturing-light border-[0.5px] border-nurturing text-safe">
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

              <FormField
                label="Contact Email"
                name="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={errors.email}
                placeholder="Enter contact email (optional)"
                autoComplete="email"
              />

              <FormField
                label="Contact Phone"
                name="phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                error={errors.phone}
                placeholder="Enter contact phone (optional)"
                autoComplete="tel"
              />

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating tenant...' : 'Create Tenant'}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-safe-light text-sm mb-2">
                Already have an account?{' '}
                <a
                  href="/auth/login"
                  className="text-natural hover:text-natural-dark transition-colors"
                >
                  Sign in
                </a>
              </p>
              <a
                href="/"
                className="text-safe hover:text-natural text-sm transition-colors"
              >
                ← Back to Home
              </a>
            </div>
          </div>
        </div>
      </div>

      {adminCredentials && (
        <AdminPasswordDisplay
          email={adminCredentials.admin_email}
          password={adminCredentials.admin_password}
          onClose={handleContinue}
        />
      )}
    </>
  )
}
