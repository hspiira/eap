/**
 * Edit Tenant Page
 * Form to edit tenant information
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { tenantsApi } from '@/api/endpoints/tenants'
import type { Tenant } from '@/types/entities'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/tenants/$tenantId/edit')({
  component: EditTenantPage,
})

function EditTenantPage() {
  const { tenantId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [formData, setFormData] = useState({
    name: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const fetchTenant = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await tenantsApi.getById(tenantId)
        setTenant(data)
        setFormData({
          name: data.name,
        })
      } catch (err: any) {
        setError(err.message || 'Failed to load tenant')
        showError('Failed to load tenant')
      } finally {
        setLoading(false)
      }
    }

    fetchTenant()
  }, [tenantId])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Tenant name is required'
    } else if (formData.name.length > 255) {
      newErrors.name = 'Tenant name must be 255 characters or less'
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
      setSaving(true)
      await tenantsApi.update(tenantId, {
        name: formData.name.trim(),
      })
      showSuccess('Tenant updated successfully')
      navigate({ to: `/tenants/${tenantId}` })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to update tenant'
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
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <AppLayout>
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error || !tenant) {
    return (
      <AppLayout>
        <div className="max-w-2xl mx-auto">
          <ErrorDisplay
            error={error || 'Tenant not found'}
            onRetry={() => window.location.reload()}
          />
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: `/tenants/${tenantId}` })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Tenant</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Edit Tenant</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
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

          <div className="mb-4">
            <label className="block text-safe text-sm font-medium mb-2">
              Tenant Code
            </label>
            <div className="px-4 py-2 bg-calm border border-[0.5px] border-safe text-safe-light">
              {tenant.code || 'N/A'}
            </div>
            <p className="mt-1 text-xs text-safe-light">
              Tenant code cannot be changed after creation
            </p>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50"
            >
              {saving ? (
                <span className="flex items-center justify-center gap-2">
                  <LoadingSpinner size="sm" color="white" />
                  Saving...
                </span>
              ) : (
                'Save Changes'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: `/tenants/${tenantId}` })}
              className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </AppLayout>
  )
}
