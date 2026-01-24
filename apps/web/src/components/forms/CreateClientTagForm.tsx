/**
 * Create Client Tag Form
 * Used inside CreateModal on client-tags list page
 */

import { useState } from 'react'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { clientTagsApi } from '@/api/endpoints/client-tags'

export interface CreateClientTagFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateClientTagForm({ onSuccess, onCancel, onLoadingChange }: CreateClientTagFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({ name: '', color: '', description: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const setLoadingState = (v: boolean) => {
    setLoading(v)
    onLoadingChange?.(v)
  }

  const validate = () => {
    const next: Record<string, string> = {}
    if (!formData.name.trim()) next.name = 'Name is required'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    try {
      setLoadingState(true)
      await clientTagsApi.create({
        name: formData.name.trim(),
        color: formData.color.trim() || null,
        description: formData.description.trim() || null,
      })
      showSuccess('Tag created')
      onSuccess()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create tag'
      showError(msg)
      if (err && typeof err === 'object' && 'details' in err && Array.isArray((err as { details: unknown[] }).details)) {
        const map: Record<string, string> = {}
        ;(err as { details: Array<{ field?: string; message?: string }> }).details.forEach((d) => {
          if (d.field) map[d.field] = d.message ?? ''
        })
        setErrors(map)
      }
    } finally {
      setLoadingState(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormField
        label="Name"
        name="name"
        value={formData.name}
        onChange={(e) => {
          setFormData((p) => ({ ...p, name: e.target.value }))
          if (errors.name) setErrors((e) => ({ ...e, name: '' }))
        }}
        error={errors.name}
        required
        placeholder="Tag name"
      />
      <div>
        <label htmlFor="color" className="block text-safe text-sm font-medium mb-2">Color</label>
        <div className="flex gap-2 items-center">
          <input
            id="color"
            type="color"
            value={formData.color || '#94a3b8'}
            onChange={(e) => setFormData((p) => ({ ...p, color: e.target.value }))}
            className="w-10 h-10 rounded-none border border-[0.5px] border-safe cursor-pointer bg-calm"
          />
          <input
            type="text"
            value={formData.color}
            onChange={(e) => setFormData((p) => ({ ...p, color: e.target.value }))}
            placeholder="#hex or CSS color"
            className="flex-1 px-4 py-2 bg-calm border border-[0.5px] border-safe rounded-none focus:outline-none focus:border-natural text-safe"
          />
        </div>
      </div>
      <FormField
        label="Description"
        name="description"
        type="textarea"
        value={formData.description}
        onChange={(e) => setFormData((p) => ({ ...p, description: e.target.value }))}
        rows={3}
        placeholder="Optional description"
      />
      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Creating...</span> : 'Create Tag'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
