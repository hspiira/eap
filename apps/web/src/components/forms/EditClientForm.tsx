/**
 * Edit Client Form
 * Used inside CreateModal on client detail page
 */

import { useState, useEffect } from 'react'
import { FormField } from '@/components/common/FormField'
import { FormAccordionSection } from '@/components/common/FormAccordionSection'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { clientsApi } from '@/api/endpoints/clients'
import type { Client } from '@/types/entities'

export interface EditClientFormProps {
  client: Client
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function EditClientForm({
  client,
  onSuccess,
  onCancel,
  onLoadingChange,
}: EditClientFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    industry_id: '',
    tax_id: '',
    registration_number: '',
    street: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    email: '',
    phone: '',
    mobile: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    setFormData({
      name: client.name ?? '',
      industry_id: client.industry_id ?? '',
      tax_id: client.tax_id ?? '',
      registration_number: client.registration_number ?? '',
      street: client.address?.street ?? '',
      city: client.address?.city ?? '',
      state: client.address?.state ?? '',
      postal_code: client.address?.postal_code ?? '',
      country: client.address?.country ?? '',
      email: client.contact_info?.email ?? '',
      phone: client.contact_info?.phone ?? '',
      mobile: client.contact_info?.mobile ?? '',
    })
  }, [client])

  const setLoadingState = (v: boolean) => {
    setLoading(v)
    onLoadingChange?.(v)
  }

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.name.trim()) next.name = 'Client name is required'
    else if (formData.name.length > 255) next.name = 'Client name must be 255 characters or less'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      setLoadingState(true)
      const clientData: Record<string, unknown> = { name: formData.name.trim() }
      if (formData.industry_id) (clientData as any).industry_id = formData.industry_id.trim() || null
      if (formData.tax_id) (clientData as any).tax_id = formData.tax_id.trim() || null
      if (formData.registration_number)
        (clientData as any).registration_number = formData.registration_number.trim() || null
      if (
        formData.street ||
        formData.city ||
        formData.state ||
        formData.postal_code ||
        formData.country
      ) {
        ;(clientData as any).address = {
          street: formData.street.trim() || null,
          city: formData.city.trim() || null,
          state: formData.state.trim() || null,
          postal_code: formData.postal_code.trim() || null,
          country: formData.country.trim() || null,
        }
      }
      if (formData.email || formData.phone || formData.mobile) {
        ;(clientData as any).contact_info = {
          email: formData.email.trim() || null,
          phone: formData.phone.trim() || null,
          mobile: formData.mobile.trim() || null,
        }
      }
      await clientsApi.update(client.id, clientData as any)
      showSuccess('Client updated successfully')
      onSuccess()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update client'
      showError(msg)
      if (
        err &&
        typeof err === 'object' &&
        'details' in err &&
        Array.isArray((err as { details: unknown[] }).details)
      ) {
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

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <h3 className="text-sm font-semibold text-safe">Basic Information</h3>
      <FormField
        label="Client Name"
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
        label="Industry ID"
        name="industry_id"
        value={formData.industry_id}
        onChange={(e) => setFormData({ ...formData, industry_id: e.target.value })}
        placeholder="Optional"
        compact
      />
      <FormField
        label="Tax ID"
        name="tax_id"
        value={formData.tax_id}
        onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
        placeholder="Optional"
        compact
      />
      <FormField
        label="Registration Number"
        name="registration_number"
        value={formData.registration_number}
        onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
        placeholder="Optional"
        compact
      />

      <FormAccordionSection title="Address (Optional)">
        <FormField
          label="Street"
          name="street"
          value={formData.street}
          onChange={(e) => setFormData({ ...formData, street: e.target.value })}
          placeholder="Street"
          compact
        />
        <div className="grid grid-cols-2 gap-2">
          <FormField
            label="City"
            name="city"
            value={formData.city}
            onChange={(e) => setFormData({ ...formData, city: e.target.value })}
            placeholder="City"
            compact
          />
          <FormField
            label="State"
            name="state"
            value={formData.state}
            onChange={(e) => setFormData({ ...formData, state: e.target.value })}
            placeholder="State"
            compact
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <FormField
            label="Postal Code"
            name="postal_code"
            value={formData.postal_code}
            onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
            placeholder="Postal code"
            compact
          />
          <FormField
            label="Country"
            name="country"
            value={formData.country}
            onChange={(e) => setFormData({ ...formData, country: e.target.value })}
            placeholder="Country"
            compact
          />
        </div>
      </FormAccordionSection>

      <FormAccordionSection title="Contact (Optional)">
        <FormField
          label="Email"
          name="email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          placeholder="Email"
          compact
        />
        <FormField
          label="Phone"
          name="phone"
          type="tel"
          value={formData.phone}
          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          placeholder="Phone"
          compact
        />
        <FormField
          label="Mobile"
          name="mobile"
          type="tel"
          value={formData.mobile}
          onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
          placeholder="Mobile"
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
          className="px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
