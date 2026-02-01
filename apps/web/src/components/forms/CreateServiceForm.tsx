/**
 * Create Service Form
 * Used inside CreateModal on services list page
 */

import { useState } from 'react'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { servicesApi } from '@/api/endpoints/services'

export interface CreateServiceFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateServiceForm({ onSuccess, onCancel, onLoadingChange }: CreateServiceFormProps) {
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

  const setLoadingState = (v: boolean) => { setLoading(v); onLoadingChange?.(v) }

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.name.trim()) next.name = 'Service name is required'
    if (formData.duration_minutes) {
      const n = parseInt(formData.duration_minutes)
      if (isNaN(n) || n < 1) next.duration_minutes = 'Duration must be a positive number'
    }
    if (formData.allow_group_sessions) {
      if (formData.min_group_size) {
        const n = parseInt(formData.min_group_size)
        if (isNaN(n) || n < 1) next.min_group_size = 'Min group size must be a positive number'
      }
      if (formData.max_group_size) {
        const n = parseInt(formData.max_group_size)
        if (isNaN(n) || n < 1) next.max_group_size = 'Max group size must be a positive number'
      }
      if (formData.min_group_size && formData.max_group_size) {
        const min = parseInt(formData.min_group_size)
        const max = parseInt(formData.max_group_size)
        if (min > max) next.max_group_size = 'Max must be >= min'
      }
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return
    try {
      setLoadingState(true)
      const data: any = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        service_type: formData.service_type.trim() || null,
        category: formData.category.trim() || null,
        duration_minutes: formData.duration_minutes ? parseInt(formData.duration_minutes) : null,
      }
      if (formData.allow_group_sessions) {
        data.group_settings = {
          allow_group_sessions: true,
          min_group_size: formData.min_group_size ? parseInt(formData.min_group_size) : null,
          max_group_size: formData.max_group_size ? parseInt(formData.max_group_size) : null,
        }
      } else {
        data.group_settings = null
      }
      await servicesApi.create(data)
      showSuccess('Service created successfully')
      onSuccess()
    } catch (err: any) {
      showError(err.message || 'Failed to create service')
      if (err.details) {
        const map: Record<string, string> = {}
        err.details.forEach((d: any) => { if (d.field) map[d.field] = d.message })
        setErrors(map)
      }
    } finally {
      setLoadingState(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-sm font-semibold text-safe">Service Information</h3>
      <FormField label="Service Name" name="name" value={formData.name} onChange={(e) => { setFormData({ ...formData, name: e.target.value }); if (errors.name) setErrors({ ...errors, name: '' }) }} error={errors.name} required placeholder="Enter service name" />
      <FormField label="Description" name="description" type="textarea" rows={4} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} placeholder="Optional" />
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Service Type" name="service_type" value={formData.service_type} onChange={(e) => setFormData({ ...formData, service_type: e.target.value })} placeholder="e.g. Counseling (optional)" />
        <FormField label="Category" name="category" value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value })} placeholder="e.g. Mental Health (optional)" />
      </div>
      <FormField label="Duration (minutes)" name="duration_minutes" type="number" min={1} value={formData.duration_minutes} onChange={(e) => { setFormData({ ...formData, duration_minutes: e.target.value }); if (errors.duration_minutes) setErrors({ ...errors, duration_minutes: '' }) }} error={errors.duration_minutes} placeholder="e.g. 60" />

      <h3 className="text-sm font-semibold text-safe mt-4">Group Settings</h3>
      <label className="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" checked={formData.allow_group_sessions} onChange={(e) => setFormData({ ...formData, allow_group_sessions: e.target.checked })} className="w-4 h-4 text-natural focus:ring-natural border-safe rounded-full" />
        <span className="text-safe text-sm">Allow group sessions</span>
      </label>
      {formData.allow_group_sessions && (
        <div className="grid grid-cols-2 gap-4 pl-6">
          <FormField label="Min Group Size" name="min_group_size" type="number" min={1} value={formData.min_group_size} onChange={(e) => { setFormData({ ...formData, min_group_size: e.target.value }); if (errors.min_group_size) setErrors({ ...errors, min_group_size: '' }) }} error={errors.min_group_size} placeholder="Optional" />
          <FormField label="Max Group Size" name="max_group_size" type="number" min={1} value={formData.max_group_size} onChange={(e) => { setFormData({ ...formData, max_group_size: e.target.value }); if (errors.max_group_size) setErrors({ ...errors, max_group_size: '' }) }} error={errors.max_group_size} placeholder="Optional" />
        </div>
      )}

      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Creating...</span> : 'Create Service'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
