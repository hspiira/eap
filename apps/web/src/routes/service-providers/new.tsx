/**
 * Create Service Provider Page
 * Type fixed to ServiceProvider. PlatformStaff / Client people excluded.
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { personsApi } from '@/api/endpoints/persons'
import type { PersonType } from '@/types/enums'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/service-providers/new')({
  component: CreateServiceProviderPage,
})

function CreateServiceProviderPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    middle_name: '',
    date_of_birth: '',
    gender: '',
    email: '',
    phone: '',
    mobile: '',
    street: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    license_number: '',
    license_type: '',
    issuing_authority: '',
    license_issue_date: '',
    license_expiry_date: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = () => {
    const next: Record<string, string> = {}
    if (!formData.first_name.trim()) next.first_name = 'First name is required'
    if (!formData.last_name.trim()) next.last_name = 'Last name is required'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    try {
      setLoading(true)
      const personData: Record<string, unknown> = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        person_type: 'ServiceProvider' as PersonType,
        middle_name: formData.middle_name.trim() || null,
        date_of_birth: formData.date_of_birth || null,
        gender: formData.gender.trim() || null,
        client_id: null,
      }
      if (formData.email || formData.phone || formData.mobile) {
        ;(personData as any).contact_info = {
          email: formData.email.trim() || null,
          phone: formData.phone.trim() || null,
          mobile: formData.mobile.trim() || null,
        }
      }
      if (formData.street || formData.city || formData.state || formData.postal_code || formData.country) {
        ;(personData as any).address = {
          street: formData.street.trim() || null,
          city: formData.city.trim() || null,
          state: formData.state.trim() || null,
          postal_code: formData.postal_code.trim() || null,
          country: formData.country.trim() || null,
        }
      }
      if (formData.license_number || formData.license_type || formData.issuing_authority) {
        ;(personData as any).license_info = {
          license_number: formData.license_number.trim() || null,
          license_type: formData.license_type.trim() || null,
          issuing_authority: formData.issuing_authority.trim() || null,
          issue_date: formData.license_issue_date || null,
          expiry_date: formData.license_expiry_date || null,
        }
      }

      await personsApi.create(personData as any)
      showSuccess('Service provider created')
      navigate({ to: '/service-providers' })
    } catch (err: any) {
      showError(err?.message || 'Failed to create service provider')
      if (err?.details) {
        const map: Record<string, string> = {}
        err.details.forEach((d: any) => { if (d.field) map[d.field] = d.message })
        setErrors(map)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/service-providers' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Service providers</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Add service provider</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Basic</h2>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="First name"
              name="first_name"
              value={formData.first_name}
              onChange={(e) => { setFormData((p) => ({ ...p, first_name: e.target.value })); if (errors.first_name) setErrors((e2) => ({ ...e2, first_name: '' })) }}
              error={errors.first_name}
              required
            />
            <FormField
              label="Last name"
              name="last_name"
              value={formData.last_name}
              onChange={(e) => { setFormData((p) => ({ ...p, last_name: e.target.value })); if (errors.last_name) setErrors((e2) => ({ ...e2, last_name: '' })) }}
              error={errors.last_name}
              required
            />
          </div>

          <FormField label="Middle name" name="middle_name" value={formData.middle_name} onChange={(e) => setFormData((p) => ({ ...p, middle_name: e.target.value }))} />
          <DatePicker label="Date of birth" name="date_of_birth" value={formData.date_of_birth} onChange={(v) => setFormData((p) => ({ ...p, date_of_birth: v }))} />
          <FormField label="Gender" name="gender" value={formData.gender} onChange={(e) => setFormData((p) => ({ ...p, gender: e.target.value }))} />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Contact (optional)</h2>
          <FormField label="Email" name="email" type="email" value={formData.email} onChange={(e) => setFormData((p) => ({ ...p, email: e.target.value }))} />
          <FormField label="Phone" name="phone" type="tel" value={formData.phone} onChange={(e) => setFormData((p) => ({ ...p, phone: e.target.value }))} />
          <FormField label="Mobile" name="mobile" type="tel" value={formData.mobile} onChange={(e) => setFormData((p) => ({ ...p, mobile: e.target.value }))} />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Address (optional)</h2>
          <FormField label="Street" name="street" value={formData.street} onChange={(e) => setFormData((p) => ({ ...p, street: e.target.value }))} />
          <div className="grid grid-cols-2 gap-4">
            <FormField label="City" name="city" value={formData.city} onChange={(e) => setFormData((p) => ({ ...p, city: e.target.value }))} />
            <FormField label="State" name="state" value={formData.state} onChange={(e) => setFormData((p) => ({ ...p, state: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Postal code" name="postal_code" value={formData.postal_code} onChange={(e) => setFormData((p) => ({ ...p, postal_code: e.target.value }))} />
            <FormField label="Country" name="country" value={formData.country} onChange={(e) => setFormData((p) => ({ ...p, country: e.target.value }))} />
          </div>

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">License (optional)</h2>
          <FormField label="License number" name="license_number" value={formData.license_number} onChange={(e) => setFormData((p) => ({ ...p, license_number: e.target.value }))} />
          <FormField label="License type" name="license_type" value={formData.license_type} onChange={(e) => setFormData((p) => ({ ...p, license_type: e.target.value }))} />
          <FormField label="Issuing authority" name="issuing_authority" value={formData.issuing_authority} onChange={(e) => setFormData((p) => ({ ...p, issuing_authority: e.target.value }))} />
          <div className="grid grid-cols-2 gap-4">
            <DatePicker label="Issue date" name="license_issue_date" value={formData.license_issue_date} onChange={(v) => setFormData((p) => ({ ...p, license_issue_date: v }))} />
            <DatePicker label="Expiry date" name="license_expiry_date" value={formData.license_expiry_date} onChange={(v) => setFormData((p) => ({ ...p, license_expiry_date: v }))} />
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50"
            >
              {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" /> Creating...</span> : 'Create'}
            </button>
            <button type="button" onClick={() => navigate({ to: '/service-providers' })} className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </AppLayout>
  )
}
