/**
 * Create Client Page
 * Form to create a new client within the current tenant
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { clientsApi } from '@/api/endpoints/clients'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/clients/new')({
  component: CreateClientPage,
})

function CreateClientPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    industry_id: '',
    tax_id: '',
    registration_number: '',
    // Address
    street: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    // Contact
    email: '',
    phone: '',
    mobile: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Client name is required'
    } else if (formData.name.length > 255) {
      newErrors.name = 'Client name must be 255 characters or less'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    try {
      setLoading(true)
      const clientData: any = {
        name: formData.name.trim(),
      }

      if (formData.industry_id) {
        clientData.industry_id = formData.industry_id.trim() || null
      }
      if (formData.tax_id) {
        clientData.tax_id = formData.tax_id.trim() || null
      }
      if (formData.registration_number) {
        clientData.registration_number = formData.registration_number.trim() || null
      }

      // Address
      if (formData.street || formData.city || formData.state || formData.postal_code || formData.country) {
        clientData.address = {
          street: formData.street.trim() || null,
          city: formData.city.trim() || null,
          state: formData.state.trim() || null,
          postal_code: formData.postal_code.trim() || null,
          country: formData.country.trim() || null,
        }
      }

      // Contact info
      if (formData.email || formData.phone || formData.mobile) {
        clientData.contact_info = {
          email: formData.email.trim() || null,
          phone: formData.phone.trim() || null,
          mobile: formData.mobile.trim() || null,
        }
      }

      await clientsApi.create(clientData)
      showSuccess('Client created successfully')
      navigate({ to: '/clients' })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create client'
      showError(errorMessage)
      if (error.details) {
        const fieldErrors: Record<string, string> = {}
        error.details.forEach((detail: any) => {
          if (detail.field) {
            fieldErrors[detail.field] = detail.message
          }
        })
        setErrors(fieldErrors)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/clients' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Clients</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Create New Client</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Basic Information</h2>
          
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

          <FormField
            label="Industry ID"
            name="industry_id"
            value={formData.industry_id}
            onChange={(e) => setFormData({ ...formData, industry_id: e.target.value })}
            placeholder="Enter industry ID (optional)"
          />

          <FormField
            label="Tax ID"
            name="tax_id"
            value={formData.tax_id}
            onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
            placeholder="Enter tax ID (optional)"
          />

          <FormField
            label="Registration Number"
            name="registration_number"
            value={formData.registration_number}
            onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
            placeholder="Enter registration number (optional)"
          />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Address (Optional)</h2>

          <FormField
            label="Street"
            name="street"
            value={formData.street}
            onChange={(e) => setFormData({ ...formData, street: e.target.value })}
            placeholder="Enter street address"
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="City"
              name="city"
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              placeholder="Enter city"
            />
            <FormField
              label="State"
              name="state"
              value={formData.state}
              onChange={(e) => setFormData({ ...formData, state: e.target.value })}
              placeholder="Enter state"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="Postal Code"
              name="postal_code"
              value={formData.postal_code}
              onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
              placeholder="Enter postal code"
            />
            <FormField
              label="Country"
              name="country"
              value={formData.country}
              onChange={(e) => setFormData({ ...formData, country: e.target.value })}
              placeholder="Enter country"
            />
          </div>

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Contact Information (Optional)</h2>

          <FormField
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="Enter email address"
          />

          <FormField
            label="Phone"
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder="Enter phone number"
          />

          <FormField
            label="Mobile"
            name="mobile"
            type="tel"
            value={formData.mobile}
            onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
            placeholder="Enter mobile number"
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
                'Create Client'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/clients' })}
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
