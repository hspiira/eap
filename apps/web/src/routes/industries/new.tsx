/**
 * Create Industry Page
 * Industry creation form with optional parent selection
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { industriesApi } from '@/api/endpoints/industries'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/industries/new')({
  component: CreateIndustryPage,
})

function CreateIndustryPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [industries, setIndustries] = useState<Array<{ id: string; name: string; code?: string | null }>>([])
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    parent_id: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const load = async () => {
      try {
        const res = await industriesApi.list({ limit: 500 })
        setIndustries(res.items.map((i) => ({ id: i.id, name: i.name, code: i.code })))
      } catch (err) {
        console.error('Error fetching industries:', err)
      }
    }
    load()
  }, [])

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
      await industriesApi.create({
        name: formData.name.trim(),
        code: formData.code.trim() || null,
        parent_id: formData.parent_id || null,
      })
      showSuccess('Industry created')
      navigate({ to: '/industries' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create industry'
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

  const parentOptions = [
    { value: '', label: 'None (root industry)' },
    ...industries.map((i) => ({
      value: i.id,
      label: i.code ? `${i.name} (${i.code})` : i.name,
    })),
  ]

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/industries' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Industries</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Add Industry</h1>

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
            placeholder="Industry name"
          />

          <FormField
            label="Code"
            name="code"
            value={formData.code}
            onChange={(e) => setFormData((p) => ({ ...p, code: e.target.value }))}
            placeholder="Optional code (e.g. NAICS)"
          />

          <Select
            label="Parent industry"
            name="parent_id"
            value={formData.parent_id}
            onChange={(v) => setFormData((p) => ({ ...p, parent_id: v as string }))}
            options={parentOptions}
            placeholder="Select parent (optional)"
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
                'Create Industry'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/industries' })}
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
