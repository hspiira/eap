/**
 * Create Client Tag Page
 * Tag creation form
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { clientTagsApi } from '@/api/endpoints/client-tags'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/client-tags/new')({
  component: CreateClientTagPage,
})

function CreateClientTagPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    color: '',
    description: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

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
      setLoading(true)
      await clientTagsApi.create({
        name: formData.name.trim(),
        color: formData.color.trim() || null,
        description: formData.description.trim() || null,
      })
      showSuccess('Tag created')
      navigate({ to: '/client-tags' })
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
      setLoading(false)
    }
  }

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/client-tags' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Tags</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Add Tag</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
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

          <div className="mb-4">
            <label htmlFor="color" className="block text-safe text-sm font-medium mb-2">
              Color
            </label>
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
                'Create Tag'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/client-tags' })}
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
