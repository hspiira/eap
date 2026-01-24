/**
 * Create Activity Page
 * Log a client interaction (CALL, EMAIL, MEETING, NOTE)
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { activitiesApi } from '@/api/endpoints/activities'
import { clientsApi } from '@/api/endpoints/clients'
import { ActivityType } from '@/types/enums'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/activities/new')({
  component: CreateActivityPage,
})

const typeOptions = [
  { value: '', label: 'Select type (required)' },
  { value: ActivityType.CALL, label: 'Call' },
  { value: ActivityType.EMAIL, label: 'Email' },
  { value: ActivityType.MEETING, label: 'Meeting' },
  { value: ActivityType.NOTE, label: 'Note' },
]

function CreateActivityPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({
    client_id: '',
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
      } catch (err) {
        console.error('Error fetching clients:', err)
      }
    }
    load()
  }, [])

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
      setLoading(true)
      await activitiesApi.create({
        client_id: formData.client_id,
        activity_type: formData.activity_type as ActivityType,
        title: formData.title.trim() || null,
        description: formData.description.trim() || null,
        occurred_at: new Date(formData.occurred_at).toISOString(),
      })
      showSuccess('Activity logged')
      navigate({ to: '/activities' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to log activity'
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

  const clientOptions = [
    { value: '', label: 'Select client (required)' },
    ...clients.map((c) => ({ value: c.id, label: c.name })),
  ]

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/activities' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Activities</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Log Activity</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <Select
            label="Client"
            name="client_id"
            value={formData.client_id}
            onChange={(v) => {
              setFormData((p) => ({ ...p, client_id: v as string }))
              if (errors.client_id) setErrors((e) => ({ ...e, client_id: '' }))
            }}
            options={clientOptions}
            error={errors.client_id}
            required
            placeholder="Select client"
          />

          <Select
            label="Type"
            name="activity_type"
            value={formData.activity_type}
            onChange={(v) => {
              setFormData((p) => ({ ...p, activity_type: v as ActivityType }))
              if (errors.activity_type) setErrors((e) => ({ ...e, activity_type: '' }))
            }}
            options={typeOptions}
            error={errors.activity_type}
            required
            placeholder="Select type"
          />

          <FormField
            label="Title"
            name="title"
            value={formData.title}
            onChange={(e) => setFormData((p) => ({ ...p, title: e.target.value }))}
            placeholder="Optional short title"
          />

          <div className="mb-4">
            <label htmlFor="occurred_at" className="block text-safe text-sm font-medium mb-2">
              Date &amp; time <span className="text-nurturing">*</span>
            </label>
            <input
              id="occurred_at"
              type="datetime-local"
              value={formData.occurred_at}
              onChange={(e) => {
                setFormData((p) => ({ ...p, occurred_at: e.target.value }))
                if (errors.occurred_at) setErrors((e) => ({ ...e, occurred_at: '' }))
              }}
              className={`w-full px-4 py-2 bg-calm border border-[0.5px] ${
                errors.occurred_at ? 'border-nurturing' : 'border-safe'
              } rounded-none focus:outline-none focus:border-natural`}
            />
            {errors.occurred_at && (
              <p className="mt-1 text-sm text-nurturing">{errors.occurred_at}</p>
            )}
          </div>

          <FormField
            label="Description / notes"
            name="description"
            type="textarea"
            value={formData.description}
            onChange={(e) => setFormData((p) => ({ ...p, description: e.target.value }))}
            rows={4}
            placeholder="Notes (optional)"
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
                  Logging...
                </span>
              ) : (
                'Log Activity'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/activities' })}
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
