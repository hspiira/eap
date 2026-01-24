/**
 * Create Industry Form
 * Used inside CreateModal on industries list page
 */

import { useState, useEffect } from 'react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { industriesApi } from '@/api/endpoints/industries'

export interface CreateIndustryFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateIndustryForm({ onSuccess, onCancel, onLoadingChange }: CreateIndustryFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [industries, setIndustries] = useState<Array<{ id: string; name: string; code?: string | null }>>([])
  const [formData, setFormData] = useState({ name: '', code: '', parent_id: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const load = async () => {
      try {
        const res = await industriesApi.list({ limit: 500 })
        setIndustries(res.items.map((i) => ({ id: i.id, name: i.name, code: i.code })))
      } catch (e) {
        console.error(e)
      }
    }
    load()
  }, [])

  const setLoadingState = (v: boolean) => { setLoading(v); onLoadingChange?.(v) }

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
      await industriesApi.create({
        name: formData.name.trim(),
        code: formData.code.trim() || null,
        parent_id: formData.parent_id || null,
      })
      showSuccess('Industry created')
      onSuccess()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create industry'
      showError(msg)
      if (err && typeof err === 'object' && 'details' in err && Array.isArray((err as { details: unknown[] }).details)) {
        const m: Record<string, string> = {}
        ;(err as { details: Array<{ field?: string; message?: string }> }).details.forEach((d) => { if (d.field) m[d.field] = d.message ?? '' })
        setErrors(m)
      }
    } finally {
      setLoadingState(false)
    }
  }

  const parentOptions = [{ value: '', label: 'None (root industry)' }, ...industries.map((i) => ({ value: i.id, label: i.code ? `${i.name} (${i.code})` : i.name }))]

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormField label="Name" name="name" value={formData.name} onChange={(e) => { setFormData((p) => ({ ...p, name: e.target.value })); if (errors.name) setErrors((e) => ({ ...e, name: '' })) }} error={errors.name} required placeholder="Industry name" />
      <FormField label="Code" name="code" value={formData.code} onChange={(e) => setFormData((p) => ({ ...p, code: e.target.value }))} placeholder="Optional (e.g. NAICS)" />
      <Select label="Parent industry" name="parent_id" value={formData.parent_id} onChange={(v) => setFormData((p) => ({ ...p, parent_id: v as string }))} options={parentOptions} placeholder="Optional" />

      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Creating...</span> : 'Create Industry'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
