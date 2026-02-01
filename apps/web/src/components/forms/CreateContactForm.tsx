import { useState, useEffect } from 'react'
import { FormField } from '@/components/common/FormField'
import { FormAccordionSection } from '@/components/common/FormAccordionSection'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { contactsApi } from '@/api/endpoints/contacts'
import { clientsApi } from '@/api/endpoints/clients'

const preferredMethodOptions = [
  { value: '', label: 'Select preferred method (optional)' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
  { value: 'sms', label: 'SMS' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'wechat', label: 'WeChat' },
]

export interface CreateContactFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
  /** Pre-fill client and hide selector (e.g. when opened from client detail) */
  initialClientId?: string
}

export function CreateContactForm({
  onSuccess,
  onCancel,
  onLoadingChange,
  initialClientId,
}: CreateContactFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({
    client_id: initialClientId ?? '',
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

  useEffect(() => {
    if (initialClientId) setFormData((p) => ({ ...p, client_id: initialClientId }))
  }, [initialClientId])

  const setLoadingState = (v: boolean) => {
    setLoading(v)
    onLoadingChange?.(v)
  }

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
      setLoadingState(true)
      await contactsApi.create({
        client_id: formData.client_id,
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        title: formData.title.trim() || null,
        contact_info: formData.email || formData.phone || formData.mobile
          ? {
              email: formData.email.trim() || null,
              phone: formData.phone.trim() || null,
              mobile: formData.mobile.trim() || null,
              preferred_method: (formData.preferred_method as 'email' | 'phone' | 'sms' | 'whatsapp' | 'wechat') || null,
            }
          : null,
      })
      showSuccess('Contact created successfully')
      onSuccess()
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
      setLoadingState(false)
    }
  }

  const clientOptions = [{ value: '', label: 'Select client (required)' }, ...clients.map((c) => ({ value: c.id, label: c.name }))]

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <h3 className="text-sm font-semibold text-safe">Contact Information</h3>
      {!initialClientId && (
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
      )}
      <div className="grid grid-cols-2 gap-2">
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
          compact
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
          compact
        />
      </div>
      <FormField label="Title" name="title" value={formData.title} onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))} placeholder="e.g. HR Manager (optional)" compact />

      <FormAccordionSection title="Contact Details (Optional)">
        <FormField label="Email" name="email" type="email" value={formData.email} onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))} placeholder="Optional" compact />
        <FormField label="Phone" name="phone" type="tel" value={formData.phone} onChange={(e) => setFormData((prev) => ({ ...prev, phone: e.target.value }))} placeholder="Optional" compact />
        <FormField label="Mobile" name="mobile" type="tel" value={formData.mobile} onChange={(e) => setFormData((prev) => ({ ...prev, mobile: e.target.value }))} placeholder="Optional" compact />
        <Select label="Preferred contact method" name="preferred_method" value={formData.preferred_method} onChange={(v) => setFormData((prev) => ({ ...prev, preferred_method: v as string }))} options={preferredMethodOptions} placeholder="Optional" />
      </FormAccordionSection>

      <div className="flex gap-2 pt-2">
        <button type="submit" disabled={loading} className="flex-1 px-4 py-2 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Creating...</span> : 'Create Contact'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
