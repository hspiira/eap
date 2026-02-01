/**
 * Activity Detail Page
 * Displays activity details and edit form
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { useToast } from '@/contexts/ToastContext'
import { activitiesApi } from '@/api/endpoints/activities'
import { clientsApi } from '@/api/endpoints/clients'
import type { Activity } from '@/types/entities'
import { ActivityType } from '@/types/enums'
import { Edit, Calendar, Building2, Phone, Mail, Users, FileText } from 'lucide-react'

export const Route = createFileRoute('/activities/$activityId')({
  component: ActivityDetailPage,
})

const typeIcons: Record<string, typeof Phone> = {
  CALL: Phone,
  EMAIL: Mail,
  MEETING: Users,
  NOTE: FileText,
}

const typeOptions = [
  { value: ActivityType.CALL, label: 'Call' },
  { value: ActivityType.EMAIL, label: 'Email' },
  { value: ActivityType.MEETING, label: 'Meeting' },
  { value: ActivityType.NOTE, label: 'Note' },
]

function ActivityDetailPage() {
  const { activityId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [activity, setActivity] = useState<Activity | null>(null)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState({
    activity_type: '' as ActivityType | '',
    title: '',
    description: '',
    occurred_at: '',
    client_id: '',
  })

  const fetchActivity = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await activitiesApi.getById(activityId)
      setActivity(data)
      setFormData({
        activity_type: data.activity_type as ActivityType,
        title: data.title ?? '',
        description: data.description ?? '',
        occurred_at: data.occurred_at ? data.occurred_at.slice(0, 16) : '',
        client_id: data.client_id,
      })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load activity'
      setError(msg)
      showError('Failed to load activity')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchActivity()
  }, [activityId])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await clientsApi.list({ limit: 100 })
        setClients(res.items.map((c) => ({ id: c.id, name: c.name })))
      } catch {
        /* ignore */
      }
    }
    load()
  }, [])

  const handleSave = async () => {
    if (!activity) return
    try {
      setSaving(true)
      const updated = await activitiesApi.update(activityId, {
        activity_type: formData.activity_type as ActivityType,
        title: formData.title.trim() || null,
        description: formData.description.trim() || null,
        occurred_at: formData.occurred_at ? new Date(formData.occurred_at).toISOString() : activity.occurred_at,
        client_id: formData.client_id || activity.client_id,
      })
      setActivity(updated)
      setEditing(false)
      showSuccess('Activity updated')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Update failed'
      showError(msg)
    } finally {
      setSaving(false)
    }
  }

  const clientOptions = clients.map((c) => ({ value: c.id, label: c.name }))
  const client = activity ? clients.find((c) => c.id === activity.client_id) : null
  const Icon = activity ? typeIcons[activity.activity_type] ?? FileText : FileText

  if (loading) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error || !activity) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay error={error ?? 'Activity not found'} onRetry={fetchActivity} />
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-safe mb-2 flex items-center gap-2">
              <Icon size={28} />
              {activity.title || activity.activity_type}
            </h1>
            <div className="flex items-center gap-4 text-safe-light text-sm">
              <span className="flex items-center gap-1">
                <Calendar size={16} />
                {new Date(activity.occurred_at).toLocaleString()}
              </span>
              {client && (
                <span className="flex items-center gap-1">
                  <Building2 size={16} />
                  {client.name}
                </span>
              )}
            </div>
          </div>
          {!editing ? (
            <button
              onClick={() => setEditing(true)}
              className="flex items-center gap-2 px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-none transition-colors disabled:opacity-50"
              >
                {saving ? <LoadingSpinner size="sm" color="white" /> : null}
                <span>Save</span>
              </button>
              <button
                onClick={() => {
                  setEditing(false)
                  setFormData({
                    activity_type: activity.activity_type as ActivityType,
                    title: activity.title ?? '',
                    description: activity.description ?? '',
                    occurred_at: activity.occurred_at ? activity.occurred_at.slice(0, 16) : '',
                    client_id: activity.client_id,
                  })
                }}
                className="px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {editing ? (
          <div className="bg-white border border-[0.5px] border-safe/30 p-6 max-w-2xl">
            <h2 className="text-lg font-semibold text-safe mb-4">Edit Activity</h2>
            <div className="space-y-4">
              <Select
                label="Type"
                name="activity_type"
                value={formData.activity_type}
                onChange={(v) => setFormData((p) => ({ ...p, activity_type: v as ActivityType }))}
                options={[{ value: '', label: 'Select type' }, ...typeOptions]}
                required
              />
              <Select
                label="Client"
                name="client_id"
                value={formData.client_id}
                onChange={(v) => setFormData((p) => ({ ...p, client_id: v as string }))}
                options={[{ value: '', label: 'Select client' }, ...clientOptions]}
                required
              />
              <FormField
                label="Title"
                name="title"
                value={formData.title}
                onChange={(e) => setFormData((p) => ({ ...p, title: e.target.value }))}
                placeholder="Optional"
              />
              <div className="mb-4">
                <label htmlFor="occurred_at" className="block text-safe text-sm font-medium mb-2">
                  Occurred at <span className="text-nurturing">*</span>
                </label>
                <input
                  id="occurred_at"
                  type="datetime-local"
                  value={formData.occurred_at}
                  onChange={(e) => setFormData((p) => ({ ...p, occurred_at: e.target.value }))}
                  className="w-full px-4 py-2 bg-white border border-[0.5px] border-safe/30 rounded-none focus:outline-none focus:border-natural"
                />
              </div>
              <FormField
                label="Description"
                name="description"
                type="textarea"
                value={formData.description}
                onChange={(e) => setFormData((p) => ({ ...p, description: e.target.value }))}
                rows={4}
                placeholder="Notes"
              />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border border-[0.5px] border-safe/30 p-6">
              <h2 className="text-lg font-semibold text-safe mb-4">Details</h2>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-safe-light">Type</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <Icon size={16} />
                    {activity.activity_type}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-safe-light">Client</dt>
                  <dd className="text-safe mt-1">
                    {client ? (
                      <button
                        onClick={() => navigate({ to: `/clients/${activity.client_id}` })}
                        className="text-natural hover:text-natural-dark"
                      >
                        {client.name}
                      </button>
                    ) : (
                      activity.client_id
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-safe-light">Occurred at</dt>
                  <dd className="text-safe mt-1">
                    {new Date(activity.occurred_at).toLocaleString()}
                  </dd>
                </div>
                {activity.title && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Title</dt>
                    <dd className="text-safe mt-1">{activity.title}</dd>
                  </div>
                )}
              </dl>
            </div>
            {(activity.description || activity.created_at) && (
              <div className="bg-white border border-[0.5px] border-safe/30 p-6">
                <h2 className="text-lg font-semibold text-safe mb-4">Description &amp; meta</h2>
                {activity.description && (
                  <p className="text-safe mb-4 whitespace-pre-wrap">{activity.description}</p>
                )}
                <dl className="space-y-2 text-sm">
                  <div>
                    <dt className="text-safe-light">Created</dt>
                    <dd className="text-safe">{new Date(activity.created_at).toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt className="text-safe-light">Updated</dt>
                    <dd className="text-safe">{new Date(activity.updated_at).toLocaleString()}</dd>
                  </div>
                </dl>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
