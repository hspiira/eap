/**
 * Create Contact Page
 * Form to create a new contact with client selection and contact information
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { contactsApi } from '@/api/endpoints/contacts'
import { clientsApi } from '@/api/endpoints/clients'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/contacts/new')({
  component: CreateContactPage,
})

const preferredMethodOptions = [
  { value: '', label: 'Select preferred method (optional)' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
  { value: 'sms', label: 'SMS' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'wechat', label: 'WeChat' },
]

function CreateContactPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({
    client_id: '',
    first_name: '',
    last_name: '',
    title: '',
    email: '',
    phone: '',
    mobile: '',
    preferred_method: '',
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

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.client_id) next.client_id = 'Client is required'
    if (!formData.first_name.trim()) next.first_name = 'First name is required'
    if (!formData.last_name.trim()) next.last_name = 'Last name is required'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      setLoading(true)
      await contactsApi.create({
        client_id: formData.client_id,
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        title: formData.title.trim() || null,
        contact_info:
          formData.email || formData.phone || formData.mobile
            ? {
                email: formData.email.trim() || null,
                phone: formData.phone.trim() || null,
                mobile: formData.mobile.trim() || null,
                preferred_method:
                  (formData.preferred_method as 'email' | 'phone' | 'sms' | 'whatsapp' | 'wechat') || null,
              }
            : null,
      })
      showSuccess('Contact created successfully')
      navigate({ to: '/contacts' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create contact'
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
          onClick={() => navigate({ to: '/contacts' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Contacts</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Create New Contact</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Contact Information</h2>

          <Select
            label="Client"
            name="client_id"
            value={formData.client_id}
            onChange={(v) => {
              setFormData((prev) => ({ ...prev, client_id: v as string }))
              if (errors.client_id) setErrors((e) => ({ ...e, client_id: '' }))
            }}
            options={clientOptions}
            error={errors.client_id}
            required
            placeholder="Select client"
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="First name"
              name="first_name"
              value={formData.first_name}
              onChange={(e) => {
                setFormData((prev) => ({ ...prev, first_name: e.target.value }))
                if (errors.first_name) setErrors((e) => ({ ...e, first_name: '' }))
              }}
              error={errors.first_name}
              required
              placeholder="First name"
            />
            <FormField
              label="Last name"
              name="last_name"
              value={formData.last_name}
              onChange={(e) => {
                setFormData((prev) => ({ ...prev, last_name: e.target.value }))
                if (errors.last_name) setErrors((e) => ({ ...e, last_name: '' }))
              }}
              error={errors.last_name}
              required
              placeholder="Last name"
            />
          </div>

          <FormField
            label="Title"
            name="title"
            value={formData.title}
            onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
            placeholder="e.g. HR Manager (optional)"
          />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Contact Details</h2>

          <FormField
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
            placeholder="Email (optional)"
          />
          <FormField
            label="Phone"
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData((prev) => ({ ...prev, phone: e.target.value }))}
            placeholder="Phone (optional)"
          />
          <FormField
            label="Mobile"
            name="mobile"
            type="tel"
            value={formData.mobile}
            onChange={(e) => setFormData((prev) => ({ ...prev, mobile: e.target.value }))}
            placeholder="Mobile (optional)"
          />

          <Select
            label="Preferred contact method"
            name="preferred_method"
            value={formData.preferred_method}
            onChange={(v) => setFormData((prev) => ({ ...prev, preferred_method: v as string }))}
            options={preferredMethodOptions}
            placeholder="Optional"
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
                'Create Contact'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/contacts' })}
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
