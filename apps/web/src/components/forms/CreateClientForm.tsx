/**
 * Create Client Form
 * Used inside CreateModal on clients list page
 */

import { useState } from 'react'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { clientsApi } from '@/api/endpoints/clients'

export interface CreateClientFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateClientForm({ onSuccess, onCancel, onLoadingChange }: CreateClientFormProps) {
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
      const clientData: any = { name: formData.name.trim() }
      if (formData.industry_id) clientData.industry_id = formData.industry_id.trim() || null
      if (formData.tax_id) clientData.tax_id = formData.tax_id.trim() || null
      if (formData.registration_number) clientData.registration_number = formData.registration_number.trim() || null
      if (formData.street || formData.city || formData.state || formData.postal_code || formData.country) {
        clientData.address = {
          street: formData.street.trim() || null,
          city: formData.city.trim() || null,
          state: formData.state.trim() || null,
          postal_code: formData.postal_code.trim() || null,
          country: formData.country.trim() || null,
        }
      }
      if (formData.email || formData.phone || formData.mobile) {
        clientData.contact_info = {
          email: formData.email.trim() || null,
          phone: formData.phone.trim() || null,
          mobile: formData.mobile.trim() || null,
        }
      }
      await clientsApi.create(clientData)
      showSuccess('Client created successfully')
      onSuccess()
    } catch (err: any) {
      showError(err.message || 'Failed to create client')
      if (err.details) {
        const map: Record<string, string> = {}
        err.details.forEach((d: any) => { if (d.field) map[d.field] = d.message })
        setErrors(map)
      }
    } finally {
      setLoadingState(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
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
      />
      <FormField label="Industry ID" name="industry_id" value={formData.industry_id} onChange={(e) => setFormData({ ...formData, industry_id: e.target.value })} placeholder="Optional" />
      <FormField label="Tax ID" name="tax_id" value={formData.tax_id} onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })} placeholder="Optional" />
      <FormField label="Registration Number" name="registration_number" value={formData.registration_number} onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })} placeholder="Optional" />

      <h3 className="text-sm font-semibold text-safe mt-4">Address (Optional)</h3>
      <FormField label="Street" name="street" value={formData.street} onChange={(e) => setFormData({ ...formData, street: e.target.value })} placeholder="Street" />
      <div className="grid grid-cols-2 gap-4">
        <FormField label="City" name="city" value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} placeholder="City" />
        <FormField label="State" name="state" value={formData.state} onChange={(e) => setFormData({ ...formData, state: e.target.value })} placeholder="State" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Postal Code" name="postal_code" value={formData.postal_code} onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })} placeholder="Postal code" />
        <FormField label="Country" name="country" value={formData.country} onChange={(e) => setFormData({ ...formData, country: e.target.value })} placeholder="Country" />
      </div>

      <h3 className="text-sm font-semibold text-safe mt-4">Contact (Optional)</h3>
      <FormField label="Email" name="email" type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder="Email" />
      <FormField label="Phone" name="phone" type="tel" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} placeholder="Phone" />
      <FormField label="Mobile" name="mobile" type="tel" value={formData.mobile} onChange={(e) => setFormData({ ...formData, mobile: e.target.value })} placeholder="Mobile" />

      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Creating...</span> : 'Create Client'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
