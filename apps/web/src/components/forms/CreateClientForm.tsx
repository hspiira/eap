import { useState, useEffect } from 'react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { FormAccordionSection } from '@/components/common/FormAccordionSection'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { useTenant } from '@/hooks/useTenant'
import { clientsApi } from '@/api/endpoints/clients'
import { industriesApi } from '@/api/endpoints/industries'
import type { Industry } from '@/types/entities'

export interface CreateClientFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

const PREFERRED_CONTACT_OPTIONS = [
  { value: '', label: 'Select (optional)' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
]

export function CreateClientForm({ onSuccess, onCancel, onLoadingChange }: CreateClientFormProps) {
  const { showSuccess, showError } = useToast()
  const { currentTenant, isLoading: tenantLoading } = useTenant()
  const [loading, setLoading] = useState(false)
  const [industries, setIndustries] = useState<Industry[]>([])
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [industriesLoading, setIndustriesLoading] = useState(true)
  const [clientsLoading, setClientsLoading] = useState(true)
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    industry_id: '',
    parent_client_id: '',
    preferred_contact_method: '',
    contact_phone: '',
    contact_email: '',
    contact_address: '',
    billing_street: '',
    billing_city: '',
    billing_country: '',
    billing_postal_code: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const fetchIndustries = async () => {
      if (tenantLoading) {
        setIndustriesLoading(true)
        return
      }
      if (!currentTenant) {
        setIndustriesLoading(false)
        setIndustries([])
        return
      }
      try {
        setIndustriesLoading(true)
        const res = await industriesApi.list({
          tenant_id: currentTenant.id,
          page: 1,
          limit: 500,
        })
        setIndustries(res.items || [])
      } catch (err) {
        console.error('Error fetching industries:', err)
        showError('Failed to load industries')
      } finally {
        setIndustriesLoading(false)
      }
    }
    fetchIndustries()
  }, [tenantLoading, currentTenant, showError])

  useEffect(() => {
    const fetchClients = async () => {
      if (!currentTenant) {
        setClientsLoading(false)
        setClients([])
        return
      }
      try {
        setClientsLoading(true)
        const res = await clientsApi.list({ limit: 500 })
        setClients(res.items.map((c) => ({ id: c.id, name: c.name })))
      } catch (err) {
        console.error('Error fetching clients:', err)
        setClients([])
      } finally {
        setClientsLoading(false)
      }
    }
    fetchClients()
  }, [currentTenant])

  const setLoadingState = (v: boolean) => {
    setLoading(v)
    onLoadingChange?.(v)
  }

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.name.trim()) next.name = 'Client name is required'
    else if (formData.name.length > 255) next.name = 'Client name must be 255 characters or less'
    const code = formData.code.trim()
    if (!code) next.code = 'Code is required'
    else if (code.length < 3 || code.length > 5) next.code = 'Code must be 3–5 characters'
    else if (!/^[a-zA-Z0-9]+$/.test(code)) next.code = 'Code must be alphanumeric only'
    const hasContact =
      formData.contact_phone.trim() || formData.contact_email.trim() || formData.contact_address.trim()
    if (!hasContact) next.contact_info = 'At least one contact field is required (phone, email, or address)'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      setLoadingState(true)
      const payload: Parameters<typeof clientsApi.create>[0] = {
        name: formData.name.trim(),
        code: formData.code.trim(),
        contact_info: {
          phone: formData.contact_phone.trim() || null,
          email: formData.contact_email.trim() || null,
          address: formData.contact_address.trim() || null,
        },
      }
      if (formData.industry_id.trim()) payload.industry_id = formData.industry_id.trim() || null
      if (formData.parent_client_id.trim()) payload.parent_client_id = formData.parent_client_id.trim() || null
      if (formData.preferred_contact_method) payload.preferred_contact_method = formData.preferred_contact_method || null
      if (
        formData.billing_street.trim() ||
        formData.billing_city.trim() ||
        formData.billing_country.trim() ||
        formData.billing_postal_code.trim()
      ) {
        payload.billing_address = {
          street: formData.billing_street.trim() || null,
          city: formData.billing_city.trim() || null,
          country: formData.billing_country.trim() || null,
          postal_code: formData.billing_postal_code.trim() || null,
        }
      }
      await clientsApi.create(payload)
      showSuccess('Client created successfully')
      onSuccess()
    } catch (err: unknown) {
      const e = err as { message?: string; details?: Array<{ field?: string; message?: string }> }
      showError(e?.message || 'Failed to create client')
      if (e?.details?.length) {
        const map: Record<string, string> = {}
        e.details.forEach((d) => {
          if (d.field) map[d.field] = d.message ?? ''
        })
        setErrors(map)
      }
    } finally {
      setLoadingState(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <h3 className="text-sm font-semibold text-safe">Basic information</h3>
      <FormField
        label="Client name"
        name="name"
        value={formData.name}
        onChange={(e) => {
          setFormData({ ...formData, name: e.target.value })
          if (errors.name) setErrors({ ...errors, name: '' })
        }}
        error={errors.name}
        required
        placeholder="Enter client name"
        compact
      />
      <FormField
        label="Code"
        name="code"
        value={formData.code}
        onChange={(e) => {
          setFormData({ ...formData, code: e.target.value })
          if (errors.code) setErrors({ ...errors, code: '' })
        }}
        error={errors.code}
        required
        placeholder="e.g. MNT (3–5 chars)"
        compact
      />
      <p className="text-xs text-safe-light -mt-1">Code will be used for employee codes (e.g., MNT).</p>
      <Select
        label="Industry"
        name="industry_id"
        value={formData.industry_id}
        onChange={(v) => setFormData({ ...formData, industry_id: v as string })}
        options={[
          { value: '', label: 'Select industry (optional)' },
          ...industries.map((ind) => ({ value: ind.id, label: ind.name })),
        ]}
        placeholder="Select industry"
        disabled={industriesLoading}
        searchable
        compact
      />
      <Select
        label="Parent client"
        name="parent_client_id"
        value={formData.parent_client_id}
        onChange={(v) => setFormData({ ...formData, parent_client_id: v as string })}
        options={[
          { value: '', label: 'None' },
          ...clients.map((c) => ({ value: c.id, label: c.name })),
        ]}
        placeholder="None"
        disabled={clientsLoading}
        searchable
        compact
      />
      <Select
        label="Preferred contact method"
        name="preferred_contact_method"
        value={formData.preferred_contact_method}
        onChange={(v) => setFormData({ ...formData, preferred_contact_method: v as string })}
        options={PREFERRED_CONTACT_OPTIONS}
        compact
      />

      <FormAccordionSection title="Contact (required – at least one)">
        {errors.contact_info && (
          <p className="text-sm text-danger mb-2">{errors.contact_info}</p>
        )}
        <FormField
          label="Phone"
          name="contact_phone"
          type="tel"
          value={formData.contact_phone}
          onChange={(e) => {
            setFormData({ ...formData, contact_phone: e.target.value })
            if (errors.contact_info) setErrors({ ...errors, contact_info: '' })
          }}
          placeholder="Phone"
          compact
        />
        <FormField
          label="Email"
          name="contact_email"
          type="email"
          value={formData.contact_email}
          onChange={(e) => {
            setFormData({ ...formData, contact_email: e.target.value })
            if (errors.contact_info) setErrors({ ...errors, contact_info: '' })
          }}
          placeholder="Email"
          compact
        />
        <FormField
          label="Address (line)"
          name="contact_address"
          value={formData.contact_address}
          onChange={(e) => {
            setFormData({ ...formData, contact_address: e.target.value })
            if (errors.contact_info) setErrors({ ...errors, contact_info: '' })
          }}
          placeholder="Contact address"
          compact
        />
      </FormAccordionSection>

      <FormAccordionSection title="Billing address (optional)">
        <FormField
          label="Street"
          name="billing_street"
          value={formData.billing_street}
          onChange={(e) => setFormData({ ...formData, billing_street: e.target.value })}
          placeholder="Street"
          compact
        />
        <div className="grid grid-cols-2 gap-2">
          <FormField
            label="City"
            name="billing_city"
            value={formData.billing_city}
            onChange={(e) => setFormData({ ...formData, billing_city: e.target.value })}
            placeholder="City"
            compact
          />
          <FormField
            label="Country"
            name="billing_country"
            value={formData.billing_country}
            onChange={(e) => setFormData({ ...formData, billing_country: e.target.value })}
            placeholder="Country"
            compact
          />
        </div>
        <FormField
          label="Postal code"
          name="billing_postal_code"
          value={formData.billing_postal_code}
          onChange={(e) => setFormData({ ...formData, billing_postal_code: e.target.value })}
          placeholder="Postal code"
          compact
        />
      </FormAccordionSection>

      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 px-4 py-2 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <LoadingSpinner size="sm" color="white" />
              Creating…
            </span>
          ) : (
            'Create client'
          )}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
