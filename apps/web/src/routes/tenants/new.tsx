/**
 * Create Tenant Page
 * Form to create a new tenant
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { tenantsApi } from '@/api/endpoints/tenants'
import { AdminPasswordDisplay } from '@/components/common/AdminPasswordDisplay'
import type { TenantCreateResponse } from '@/api/endpoints/tenants'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/tenants/new')({
  component: CreateTenantPage,
})

function CreateTenantPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [createdTenant, setCreatedTenant] = useState<TenantCreateResponse | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    code: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Tenant name is required'
    } else if (formData.name.length > 255) {
      newErrors.name = 'Tenant name must be 255 characters or less'
    }

    if (!formData.code.trim()) {
      newErrors.code = 'Tenant code is required'
    } else if (formData.code.length < 3 || formData.code.length > 15) {
      newErrors.code = 'Tenant code must be between 3 and 15 characters'
    } else if (!/^[a-z0-9-]+$/.test(formData.code)) {
      newErrors.code = 'Tenant code can only contain lowercase letters, numbers, and hyphens'
    } else if (formData.code.startsWith('-') || formData.code.endsWith('-')) {
      newErrors.code = 'Tenant code cannot start or end with a hyphen'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    try {
      setLoading(true)
      const response = await tenantsApi.create({
        name: formData.name.trim(),
        code: formData.code.toLowerCase().trim(),
      })
      setCreatedTenant(response)
      showSuccess('Tenant created successfully')
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create tenant'
      showError(errorMessage)
      if (error.details) {
        const fieldErrors: Record<string, string> = {}
        error.details.forEach((detail: any) => {
          if (detail.field) {
            fieldErrors[detail.field] = detail.message
          }
        })
        setErrors(fieldErrors)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCloseAdminPassword = () => {
    setCreatedTenant(null)
    navigate({ to: '/tenants' })
  }

  const handleLogin = () => {
    if (createdTenant) {
      navigate({
        to: '/auth/login',
        search: {
          tenant_code: createdTenant.code,
          email: createdTenant.admin_email,
        },
      })
    }
  }

  const handleDownload = () => {
    if (createdTenant) {
      const content = `Tenant Credentials\n\nTenant: ${createdTenant.name}\nCode: ${createdTenant.code}\n\nAdmin Email: ${createdTenant.admin_email}\nAdmin Password: ${createdTenant.admin_password}\n\nCreated: ${new Date().toISOString()}\n\n⚠️ IMPORTANT: Save these credentials securely. They cannot be retrieved later.`
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tenant-${createdTenant.code}-credentials.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/tenants' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Tenants</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Create New Tenant</h1>

        <form onSubmit={handleSubmit} className="bg-white border border-[0.5px] border-safe p-6">
          <FormField
            label="Tenant Name"
            name="name"
            value={formData.name}
            onChange={(e) => {
              setFormData({ ...formData, name: e.target.value })
              if (errors.name) setErrors({ ...errors, name: '' })
            }}
            error={errors.name}
            required
            placeholder="Enter tenant name"
          />

          <FormField
            label="Tenant Code"
            name="code"
            value={formData.code}
            onChange={(e) => {
              const value = e.target.value.toLowerCase()
              setFormData({ ...formData, code: value })
              if (errors.code) setErrors({ ...errors, code: '' })
            }}
            error={errors.code}
            required
            placeholder="e.g., acme-corp"
          />

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <LoadingSpinner size="sm" color="white" />
                  Creating...
                </span>
              ) : (
                'Create Tenant'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/tenants' })}
              className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      {createdTenant && (
        <AdminPasswordDisplay
          tenant={createdTenant}
          onLogin={handleLogin}
          onDownload={handleDownload}
          onClose={handleCloseAdminPassword}
        />
      )}
    </AppLayout>
  )
}
