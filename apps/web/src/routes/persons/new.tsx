/**
 * Create Person Page
 * Form to create a new person with type selection
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { personsApi } from '@/api/endpoints/persons'
import { clientsApi } from '@/api/endpoints/clients'
import type { PersonType } from '@/types/enums'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/persons/new')({
  component: CreatePersonPage,
})

const personTypeOptions = [
  { value: 'ClientEmployee', label: 'Client Employee' },
  { value: 'Dependent', label: 'Dependent' },
  { value: 'ServiceProvider', label: 'Service Provider' },
  { value: 'PlatformStaff', label: 'Platform Staff' },
]

function CreatePersonPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    middle_name: '',
    person_type: '' as PersonType | '',
    date_of_birth: '',
    gender: '',
    client_id: '',
    // Contact
    email: '',
    phone: '',
    mobile: '',
    // Address
    street: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    // Employment (for ClientEmployee)
    employee_id: '',
    department: '',
    position: '',
    hire_date: '',
    // License (for ServiceProvider)
    license_number: '',
    license_type: '',
    issuing_authority: '',
    license_issue_date: '',
    license_expiry_date: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const response = await clientsApi.list({ limit: 100 })
        setClients(response.items.map(c => ({ id: c.id, name: c.name })))
      } catch (error) {
        console.error('Error fetching clients:', error)
      }
    }
    fetchClients()
  }, [])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required'
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required'
    }

    if (!formData.person_type) {
      newErrors.person_type = 'Person type is required'
    }

    if ((formData.person_type === 'ClientEmployee' || formData.person_type === 'Dependent') && !formData.client_id) {
      newErrors.client_id = 'Client is required for employees and dependents'
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
      const personData: any = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        person_type: formData.person_type as PersonType,
        middle_name: formData.middle_name.trim() || null,
        date_of_birth: formData.date_of_birth || null,
        gender: formData.gender.trim() || null,
        client_id: formData.client_id || null,
      }

      // Contact info
      if (formData.email || formData.phone || formData.mobile) {
        personData.contact_info = {
          email: formData.email.trim() || null,
          phone: formData.phone.trim() || null,
          mobile: formData.mobile.trim() || null,
        }
      }

      // Address
      if (formData.street || formData.city || formData.state || formData.postal_code || formData.country) {
        personData.address = {
          street: formData.street.trim() || null,
          city: formData.city.trim() || null,
          state: formData.state.trim() || null,
          postal_code: formData.postal_code.trim() || null,
          country: formData.country.trim() || null,
        }
      }

      // Employment info (for ClientEmployee)
      if (formData.person_type === 'ClientEmployee' && (formData.employee_id || formData.department || formData.position || formData.hire_date)) {
        personData.employment_info = {
          employee_id: formData.employee_id.trim() || null,
          department: formData.department.trim() || null,
          position: formData.position.trim() || null,
          hire_date: formData.hire_date || null,
        }
      }

      // License info (for ServiceProvider)
      if (formData.person_type === 'ServiceProvider' && (formData.license_number || formData.license_type || formData.issuing_authority)) {
        personData.license_info = {
          license_number: formData.license_number.trim() || null,
          license_type: formData.license_type.trim() || null,
          issuing_authority: formData.issuing_authority.trim() || null,
          issue_date: formData.license_issue_date || null,
          expiry_date: formData.license_expiry_date || null,
        }
      }

      await personsApi.create(personData)
      showSuccess('Person created successfully')
      navigate({ to: '/persons' })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create person'
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

  const clientOptions = [
    { value: '', label: 'Select client (required for employees/dependents)' },
    ...clients.map(c => ({ value: c.id, label: c.name })),
  ]

  const showClientField = formData.person_type === 'ClientEmployee' || formData.person_type === 'Dependent'
  const showEmploymentFields = formData.person_type === 'ClientEmployee'
  const showLicenseFields = formData.person_type === 'ServiceProvider'

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/persons' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Persons</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Create New Person</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Basic Information</h2>

          <Select
            label="Person Type"
            name="person_type"
            value={formData.person_type}
            onChange={(value) => {
              setFormData({ ...formData, person_type: value as PersonType, client_id: '' })
              if (errors.person_type) setErrors({ ...errors, person_type: '' })
            }}
            options={personTypeOptions}
            error={errors.person_type}
            required
            placeholder="Select person type"
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="First Name"
              name="first_name"
              value={formData.first_name}
              onChange={(e) => {
                setFormData({ ...formData, first_name: e.target.value })
                if (errors.first_name) setErrors({ ...errors, first_name: '' })
              }}
              error={errors.first_name}
              required
            />
            <FormField
              label="Last Name"
              name="last_name"
              value={formData.last_name}
              onChange={(e) => {
                setFormData({ ...formData, last_name: e.target.value })
                if (errors.last_name) setErrors({ ...errors, last_name: '' })
              }}
              error={errors.last_name}
              required
            />
          </div>

          <FormField
            label="Middle Name"
            name="middle_name"
            value={formData.middle_name}
            onChange={(e) => setFormData({ ...formData, middle_name: e.target.value })}
          />

          <DatePicker
            label="Date of Birth"
            name="date_of_birth"
            value={formData.date_of_birth}
            onChange={(value) => setFormData({ ...formData, date_of_birth: value })}
          />

          <FormField
            label="Gender"
            name="gender"
            value={formData.gender}
            onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
            placeholder="Optional"
          />

          {showClientField && (
            <Select
              label="Client"
              name="client_id"
              value={formData.client_id}
              onChange={(value) => {
                setFormData({ ...formData, client_id: value as string })
                if (errors.client_id) setErrors({ ...errors, client_id: '' })
              }}
              options={clientOptions}
              error={errors.client_id}
              required={showClientField}
              placeholder="Select client"
            />
          )}

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Contact Information (Optional)</h2>

          <FormField
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />

          <FormField
            label="Phone"
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          />

          <FormField
            label="Mobile"
            name="mobile"
            type="tel"
            value={formData.mobile}
            onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
          />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Address (Optional)</h2>

          <FormField
            label="Street"
            name="street"
            value={formData.street}
            onChange={(e) => setFormData({ ...formData, street: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="City"
              name="city"
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
            />
            <FormField
              label="State"
              name="state"
              value={formData.state}
              onChange={(e) => setFormData({ ...formData, state: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="Postal Code"
              name="postal_code"
              value={formData.postal_code}
              onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
            />
            <FormField
              label="Country"
              name="country"
              value={formData.country}
              onChange={(e) => setFormData({ ...formData, country: e.target.value })}
            />
          </div>

          {/* Employment Information (for ClientEmployee) */}
          {showEmploymentFields && (
            <>
              <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Employment Information (Optional)</h2>

              <FormField
                label="Employee ID"
                name="employee_id"
                value={formData.employee_id}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="Department"
                  name="department"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                />
                <FormField
                  label="Position"
                  name="position"
                  value={formData.position}
                  onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                />
              </div>

              <DatePicker
                label="Hire Date"
                name="hire_date"
                value={formData.hire_date}
                onChange={(value) => setFormData({ ...formData, hire_date: value })}
              />
            </>
          )}

          {/* License Information (for ServiceProvider) */}
          {showLicenseFields && (
            <>
              <h2 className="text-lg font-semibold text-safe mb-4 mt-6">License Information (Optional)</h2>

              <FormField
                label="License Number"
                name="license_number"
                value={formData.license_number}
                onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
              />

              <FormField
                label="License Type"
                name="license_type"
                value={formData.license_type}
                onChange={(e) => setFormData({ ...formData, license_type: e.target.value })}
              />

              <FormField
                label="Issuing Authority"
                name="issuing_authority"
                value={formData.issuing_authority}
                onChange={(e) => setFormData({ ...formData, issuing_authority: e.target.value })}
              />

              <div className="grid grid-cols-2 gap-4">
                <DatePicker
                  label="Issue Date"
                  name="license_issue_date"
                  value={formData.license_issue_date}
                  onChange={(value) => setFormData({ ...formData, license_issue_date: value })}
                />
                <DatePicker
                  label="Expiry Date"
                  name="license_expiry_date"
                  value={formData.license_expiry_date}
                  onChange={(value) => setFormData({ ...formData, license_expiry_date: value })}
                />
              </div>
            </>
          )}

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
                'Create Person'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/persons' })}
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
