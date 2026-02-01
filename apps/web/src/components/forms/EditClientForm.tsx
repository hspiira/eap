import { useState, useEffect } from 'react'
import { CheckCircle } from 'lucide-react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { FormAccordionSection } from '@/components/common/FormAccordionSection'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { useTenant } from '@/hooks/useTenant'
import { clientsApi } from '@/api/endpoints/clients'
import { industriesApi } from '@/api/endpoints/industries'
import type { Client, Industry } from '@/types/entities'

export interface EditClientFormProps {
  client: Client
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_REGEX = /^[\d\s\-+().]{7,30}$/
const MAX_TEXT_LENGTH = 255
const MAX_POSTAL_CODE_LENGTH = 20
const CODE_LENGTH_MIN = 3
const CODE_LENGTH_MAX = 5

const PREFERRED_CONTACT_OPTIONS = [
  { value: '', label: 'Select (optional)' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
]

export function EditClientForm({
  client,
  onSuccess,
  onCancel,
  onLoadingChange,
}: EditClientFormProps) {
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
    setFormData({
      name: client.name ?? '',
      code: client.code ?? '',
      industry_id: client.industry_id ?? '',
      parent_client_id: client.parent_client_id ?? '',
      preferred_contact_method: client.preferred_contact_method ?? '',
      contact_phone: client.contact_info?.phone ?? '',
      contact_email: client.contact_info?.email ?? '',
      contact_address: client.contact_info?.address ?? '',
      billing_street: client.billing_address?.street ?? '',
      billing_city: client.billing_address?.city ?? '',
      billing_country: client.billing_address?.country ?? '',
      billing_postal_code: client.billing_address?.postal_code ?? '',
    })
  }, [client])

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
        setClients(res.items.filter((c) => c.id !== client.id).map((c) => ({ id: c.id, name: c.name })))
      } catch (err) {
        console.error('Error fetching clients:', err)
        setClients([])
      } finally {
        setClientsLoading(false)
      }
    }
    fetchClients()
  }, [currentTenant, client.id])

  const setLoadingState = (v: boolean) => {
    setLoading(v)
    onLoadingChange?.(v)
  }

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.name.trim()) next.name = 'Client name is required'
    else if (formData.name.length > MAX_TEXT_LENGTH) next.name = `Client name must be ${MAX_TEXT_LENGTH} characters or less`
    const codeTrimmed = formData.code.trim()
    if (codeTrimmed && (codeTrimmed.length < CODE_LENGTH_MIN || codeTrimmed.length > CODE_LENGTH_MAX)) {
      next.code = `Code must be ${CODE_LENGTH_MIN}–${CODE_LENGTH_MAX} characters`
    }
    const emailTrimmed = formData.contact_email.trim()
    if (emailTrimmed && !EMAIL_REGEX.test(emailTrimmed)) next.contact_email = 'Enter a valid email address'
    const phoneTrimmed = formData.contact_phone.trim()
    if (phoneTrimmed && !PHONE_REGEX.test(phoneTrimmed)) next.contact_phone = 'Enter a valid phone number'
    if (formData.billing_street.trim().length > MAX_TEXT_LENGTH) next.billing_street = `Street must be ${MAX_TEXT_LENGTH} characters or less`
    if (formData.billing_city.trim().length > MAX_TEXT_LENGTH) next.billing_city = `City must be ${MAX_TEXT_LENGTH} characters or less`
    if (formData.billing_country.trim().length > MAX_TEXT_LENGTH) next.billing_country = `Country must be ${MAX_TEXT_LENGTH} characters or less`
    if (formData.billing_postal_code.trim().length > MAX_POSTAL_CODE_LENGTH) next.billing_postal_code = `Postal code must be ${MAX_POSTAL_CODE_LENGTH} characters or less`
    if (formData.contact_address.trim().length > MAX_TEXT_LENGTH) next.contact_address = `Address must be ${MAX_TEXT_LENGTH} characters or less`
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      setLoadingState(true)
      const payload: Parameters<typeof clientsApi.update>[1] = {
        name: formData.name.trim(),
      }
      if (formData.code.trim()) payload.code = formData.code.trim() || null
      if (formData.industry_id.trim()) payload.industry_id = formData.industry_id.trim() || null
      if (formData.parent_client_id.trim()) payload.parent_client_id = formData.parent_client_id.trim() || null
      if (formData.preferred_contact_method) payload.preferred_contact_method = formData.preferred_contact_method || null
      payload.contact_info = {
        phone: formData.contact_phone.trim() || null,
        email: formData.contact_email.trim() || null,
        address: formData.contact_address.trim() || null,
      }
      payload.billing_address = {
        street: formData.billing_street.trim() || null,
        city: formData.billing_city.trim() || null,
        country: formData.billing_country.trim() || null,
        postal_code: formData.billing_postal_code.trim() || null,
      }
      await clientsApi.update(client.id, payload)
      showSuccess('Client updated successfully')
      onSuccess()
    } catch (err: unknown) {
      const e = err as { message?: string; details?: Array<{ field?: string; message?: string }> }
      showError(e?.message || 'Failed to update client')
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
      {client.is_verified && (
        <div className="flex items-center gap-2 px-3 py-2 bg-natural/10 border border-[0.5px] border-natural/30 text-natural text-sm">
          <CheckCircle size={18} />
          <span>Verified client</span>
        </div>
      )}
      <FormField
        label="Client name"
        name="name"
        value={formData.name}
        onChange={(e) => {
          setFormData({ ...formData, name: e.target.value })
          if (errors.name) setErrors((prev) => ({ ...prev, name: '' }))
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
          if (errors.code) setErrors((prev) => ({ ...prev, code: '' }))
        }}
        error={errors.code}
        placeholder="3–5 character code"
        compact
      />
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

      <FormAccordionSection title="Contact (optional)">
        <FormField
          label="Phone"
          name="contact_phone"
          type="tel"
          value={formData.contact_phone}
          onChange={(e) => {
            setFormData({ ...formData, contact_phone: e.target.value })
            if (errors.contact_phone) setErrors((prev) => ({ ...prev, contact_phone: '' }))
          }}
          error={errors.contact_phone}
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
            if (errors.contact_email) setErrors((prev) => ({ ...prev, contact_email: '' }))
          }}
          error={errors.contact_email}
          placeholder="Email"
          compact
        />
        <FormField
          label="Address (line)"
          name="contact_address"
          value={formData.contact_address}
          onChange={(e) => {
            setFormData({ ...formData, contact_address: e.target.value })
            if (errors.contact_address) setErrors((prev) => ({ ...prev, contact_address: '' }))
          }}
          error={errors.contact_address}
          placeholder="Contact address"
          compact
        />
      </FormAccordionSection>

      <FormAccordionSection title="Billing address (optional)">
        <FormField
          label="Street"
          name="billing_street"
          value={formData.billing_street}
          onChange={(e) => {
            setFormData({ ...formData, billing_street: e.target.value })
            if (errors.billing_street) setErrors((prev) => ({ ...prev, billing_street: '' }))
          }}
          error={errors.billing_street}
          placeholder="Street"
          compact
        />
        <div className="grid grid-cols-2 gap-2">
          <FormField
            label="City"
            name="billing_city"
            value={formData.billing_city}
            onChange={(e) => {
              setFormData({ ...formData, billing_city: e.target.value })
              if (errors.billing_city) setErrors((prev) => ({ ...prev, billing_city: '' }))
            }}
            error={errors.billing_city}
            placeholder="City"
            compact
          />
          <FormField
            label="Country"
            name="billing_country"
            value={formData.billing_country}
            onChange={(e) => {
              setFormData({ ...formData, billing_country: e.target.value })
              if (errors.billing_country) setErrors((prev) => ({ ...prev, billing_country: '' }))
            }}
            error={errors.billing_country}
            placeholder="Country"
            compact
          />
        </div>
        <FormField
          label="Postal code"
          name="billing_postal_code"
          value={formData.billing_postal_code}
          onChange={(e) => {
            setFormData({ ...formData, billing_postal_code: e.target.value })
            if (errors.billing_postal_code) setErrors((prev) => ({ ...prev, billing_postal_code: '' }))
          }}
          error={errors.billing_postal_code}
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
              Saving…
            </span>
          ) : (
            'Save changes'
          )}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
