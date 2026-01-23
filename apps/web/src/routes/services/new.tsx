/**
 * Create Service Page
 * Form to create a new service with group settings configuration
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { servicesApi } from '@/api/endpoints/services'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/services/new')({
  component: CreateServicePage,
})

function CreateServicePage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    service_type: '',
    category: '',
    duration_minutes: '',
    allow_group_sessions: false,
    min_group_size: '',
    max_group_size: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Service name is required'
    }

    if (formData.duration_minutes) {
      const duration = parseInt(formData.duration_minutes)
      if (isNaN(duration) || duration < 1) {
        newErrors.duration_minutes = 'Duration must be a positive number'
      }
    }

    if (formData.allow_group_sessions) {
      if (formData.min_group_size) {
        const minSize = parseInt(formData.min_group_size)
        if (isNaN(minSize) || minSize < 1) {
          newErrors.min_group_size = 'Minimum group size must be a positive number'
        }
      }

      if (formData.max_group_size) {
        const maxSize = parseInt(formData.max_group_size)
        if (isNaN(maxSize) || maxSize < 1) {
          newErrors.max_group_size = 'Maximum group size must be a positive number'
        }
      }

      if (formData.min_group_size && formData.max_group_size) {
        const minSize = parseInt(formData.min_group_size)
        const maxSize = parseInt(formData.max_group_size)
        if (minSize > maxSize) {
          newErrors.max_group_size = 'Maximum group size must be greater than or equal to minimum group size'
        }
      }
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
      const serviceData: any = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        service_type: formData.service_type.trim() || null,
        category: formData.category.trim() || null,
        duration_minutes: formData.duration_minutes ? parseInt(formData.duration_minutes) : null,
      }

      // Add group settings if group sessions are enabled
      if (formData.allow_group_sessions) {
        serviceData.group_settings = {
          allow_group_sessions: true,
          min_group_size: formData.min_group_size ? parseInt(formData.min_group_size) : null,
          max_group_size: formData.max_group_size ? parseInt(formData.max_group_size) : null,
        }
      } else {
        serviceData.group_settings = null
      }

      await servicesApi.create(serviceData)
      showSuccess('Service created successfully')
      navigate({ to: '/services' })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create service'
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

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/services' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Services</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Create New Service</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Service Information</h2>

          <FormField
            label="Service Name"
            name="name"
            value={formData.name}
            onChange={(e) => {
              setFormData({ ...formData, name: e.target.value })
              if (errors.name) setErrors({ ...errors, name: '' })
            }}
            error={errors.name}
            required
            placeholder="Enter service name"
          />

          <FormField
            label="Description"
            name="description"
            type="textarea"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Enter service description (optional)"
            rows={4}
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="Service Type"
              name="service_type"
              value={formData.service_type}
              onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
              placeholder="e.g., Counseling, Therapy (optional)"
            />

            <FormField
              label="Category"
              name="category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              placeholder="e.g., Mental Health, Wellness (optional)"
            />
          </div>

          <FormField
            label="Duration (minutes)"
            name="duration_minutes"
            type="number"
            min="1"
            value={formData.duration_minutes}
            onChange={(e) => {
              setFormData({ ...formData, duration_minutes: e.target.value })
              if (errors.duration_minutes) setErrors({ ...errors, duration_minutes: '' })
            }}
            error={errors.duration_minutes}
            placeholder="e.g., 60 for 1 hour"
          />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Group Settings</h2>

          <div className="mb-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.allow_group_sessions}
                onChange={(e) => setFormData({ ...formData, allow_group_sessions: e.target.checked })}
                className="w-4 h-4 text-natural focus:ring-natural border-safe"
              />
              <span className="text-safe">Allow group sessions</span>
            </label>
            <p className="text-sm text-safe-light mt-1 ml-6">
              Enable this to allow multiple participants in a single session
            </p>
          </div>

          {formData.allow_group_sessions && (
            <div className="grid grid-cols-2 gap-4 ml-6">
              <FormField
                label="Minimum Group Size"
                name="min_group_size"
                type="number"
                min="1"
                value={formData.min_group_size}
                onChange={(e) => {
                  setFormData({ ...formData, min_group_size: e.target.value })
                  if (errors.min_group_size) setErrors({ ...errors, min_group_size: '' })
                }}
                error={errors.min_group_size}
                placeholder="Optional"
              />

              <FormField
                label="Maximum Group Size"
                name="max_group_size"
                type="number"
                min="1"
                value={formData.max_group_size}
                onChange={(e) => {
                  setFormData({ ...formData, max_group_size: e.target.value })
                  if (errors.max_group_size) setErrors({ ...errors, max_group_size: '' })
                }}
                error={errors.max_group_size}
                placeholder="Optional"
              />
            </div>
          )}

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
                'Create Service'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/services' })}
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
