/**
 * Create Activity Form
 * Used inside CreateModal on activities list page
 */

import { useState, useEffect } from 'react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { activitiesApi } from '@/api/endpoints/activities'
import { clientsApi } from '@/api/endpoints/clients'
import { ActivityType } from '@/types/enums'

const typeOptions = [
  { value: '', label: 'Select type (required)' },
  { value: ActivityType.CALL, label: 'Call' },
  { value: ActivityType.EMAIL, label: 'Email' },
  { value: ActivityType.MEETING, label: 'Meeting' },
  { value: ActivityType.NOTE, label: 'Note' },
]

export interface CreateActivityFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
  /** Pre-fill client and hide selector (e.g. when opened from client detail) */
  initialClientId?: string
}

export function CreateActivityForm({
  onSuccess,
  onCancel,
  onLoadingChange,
  initialClientId,
}: CreateActivityFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({
    client_id: initialClientId ?? '',
    activity_type: '' as ActivityType | '',
    title: '',
    description: '',
    occurred_at: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const load = async () => {
      try {
        const res = await clientsApi.list({ limit: 100 })
        setClients(res.items.map((c) => ({ id: c.id, name: c.name })))
      } catch (e) {
        console.error(e)
      }
    }
    load()
  }, [])

  useEffect(() => {
    if (initialClientId) setFormData((p) => ({ ...p, client_id: initialClientId }))
  }, [initialClientId])

  const setLoadingState = (v: boolean) => { setLoading(v); onLoadingChange?.(v) }

  const validate = () => {
    const next: Record<string, string> = {}
    if (!formData.client_id) next.client_id = 'Client is required'
    if (!formData.activity_type) next.activity_type = 'Type is required'
    if (!formData.occurred_at) next.occurred_at = 'Date & time is required'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    try {
      setLoadingState(true)
      await activitiesApi.create({
        client_id: formData.client_id,
        activity_type: formData.activity_type as ActivityType,
        title: formData.title.trim() || null,
        description: formData.description.trim() || null,
        occurred_at: new Date(formData.occurred_at).toISOString(),
      })
      showSuccess('Activity logged')
      onSuccess()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to log activity'
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

  const clientOptions = [{ value: '', label: 'Select client (required)' }, ...clients.map((c) => ({ value: c.id, label: c.name }))]

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      {!initialClientId && (
        <Select label="Client" name="client_id" value={formData.client_id} onChange={(v) => { setFormData((p) => ({ ...p, client_id: v as string })); if (errors.client_id) setErrors((e) => ({ ...e, client_id: '' })) }} options={clientOptions} error={errors.client_id} required placeholder="Select client" />
      )}
      <Select label="Type" name="activity_type" value={formData.activity_type} onChange={(v) => { setFormData((p) => ({ ...p, activity_type: v as ActivityType })); if (errors.activity_type) setErrors((e) => ({ ...e, activity_type: '' })) }} options={typeOptions} error={errors.activity_type} required placeholder="Select type" />
      <FormField label="Title" name="title" value={formData.title} onChange={(e) => setFormData((p) => ({ ...p, title: e.target.value }))} placeholder="Optional short title" compact />
      <FormField label="Description" name="description" type="textarea" rows={3} value={formData.description} onChange={(e) => setFormData((p) => ({ ...p, description: e.target.value }))} placeholder="Optional" compact />
      <div>
        <label htmlFor="occurred_at" className="block text-safe text-sm font-medium mb-1">Date &amp; Time (required)</label>
        <input
          id="occurred_at"
          type="datetime-local"
          value={formData.occurred_at}
          onChange={(e) => { setFormData((p) => ({ ...p, occurred_at: e.target.value })); if (errors.occurred_at) setErrors((e) => ({ ...e, occurred_at: '' })) }}
          className="w-full px-4 py-2 bg-calm border border-[0.5px] border-safe/30 text-safe rounded-none focus:outline-none focus:border-natural"
        />
        {errors.occurred_at && <p className="text-nurturing text-sm mt-1">{errors.occurred_at}</p>}
      </div>

      <div className="flex gap-2 pt-2">
        <button type="submit" disabled={loading} className="flex-1 px-4 py-2 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Logging...</span> : 'Log Activity'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
